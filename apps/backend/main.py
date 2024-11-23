import tempfile
from typing import List, Optional

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware

# FastAPI app initialization
app = FastAPI()

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenAI embeddings
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# Initialize Pinecone vector store
vector_store = PineconeVectorStore(embedding=embeddings)

# Initialize OpenAI language model
llm = ChatOpenAI(model_name="gpt-4o-mini")


# Pydantic models for request validation
class Message(BaseModel):
    role: str
    content: Optional[str] = ""


class ConversationRequest(BaseModel):
    user_id: str
    message: str
    chat_history: List[Message]


@app.post("/upload_pdf")
async def upload_pdf(file: UploadFile = File(...), user_id: str = Form(...)):
    """
    Add data from a PDF file to the vector store.

    Args:
        file (UploadFile): The uploaded PDF file.
        user_id (str): The user ID associated with the upload.

    Returns:
        dict: A message indicating success.

    Raises:
        HTTPException: If there's an error processing the request.
    """
    try:
        # Create a temporary file to store the uploaded PDF
        with tempfile.NamedTemporaryFile() as temp_file:
            temp_file.write(await file.read())
            temp_file_path = temp_file.name

            # Load the PDF
            loader = PyPDFLoader(temp_file_path)
            docs = await loader.aload()

        # Split the document into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
        )
        chunks = text_splitter.split_documents(docs)

        # Add user_id to metadata
        for chunk in chunks:
            chunk.metadata["user_id"] = user_id

        # Add chunks to vector store
        await vector_store.aadd_documents(chunks)
        return {"message": "PDF data added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Instructions for the LLM to reformulate the latest user question using chat history context.
contextualize_q_system_prompt = """Given a chat history and the latest user question \
which might reference context in the chat history, formulate a standalone question \
which can be understood without the chat history. Do NOT answer the question, \
just reformulate it if needed and otherwise return it as is."""

# Instructions for the LLM to generate an answer to the user question using the provided context.
qa_system_prompt = """You are an assistant for question-answering tasks. \
Use the following retrieved context to answer the question. \
Only refer to the provided context when forming your answer. \
If there isn't enough information to answer the question, \
simply state that you don't have sufficient information. \
Provide concise answers, structured neatly using simple Markdown.

{context}"""


@app.post("/ask_question")
async def ask_question(request: ConversationRequest):
    """
       Process a conversation request and generate a response.

       Args:
           request (ConversationRequest): The conversation request details.

       Returns:
           dict: The AI-generated response.

       Raises:
           HTTPException: If there's an error processing the request.
       """
    try:
        # Extract user ID and the current message from the request.
        user_id = request.user_id
        message = request.message

        # Convert chat history to a list of tuples containing roles and message content.
        chat_history = [(msg.role, msg.content) for msg in request.chat_history]

        # Initialize a retriever from the vector store.
        # Filtered by user ID and limiting to 5 results.
        retriever = vector_store.as_retriever(
            search_kwargs={"filter": {"user_id": user_id}, "k": 5}
        )

        # Create a prompt template for the history aware retriever
        contextualize_q_prompt = ChatPromptTemplate.from_messages([
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}")
        ])

        # Create a retriever that uses question and chat history to retrieve context
        history_aware_retriever = create_history_aware_retriever(
            llm, retriever, contextualize_q_prompt
        )

        # Create a prompt template for the answer generation
        qa_prompt = ChatPromptTemplate.from_messages([
            ("system", qa_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])

        # Create a chain that processes retrieved documents to generate an answer.
        question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)

        # Create a RAG chain that combines history-aware retrieval and answer generation.
        rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

        # Invoke the RAG chain with the user's input and chat history to get the response.
        response = await rag_chain.ainvoke({"input": message, "chat_history": chat_history})
        return {"response": response['answer']}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
