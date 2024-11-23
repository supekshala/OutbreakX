import OpenAI from "openai";
import { PineconeClient } from "@pinecone-database/pinecone";
import { ChatCompletionMessageParam } from "openai/resources/chat/completions";

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

const pinecone = new PineconeClient();

export class ChatService {
  private static instance: ChatService;
  private initialized = false;

  private constructor() {}

  public static getInstance(): ChatService {
    if (!ChatService.instance) {
      ChatService.instance = new ChatService();
    }
    return ChatService.instance;
  }

  async initialize() {
    if (!this.initialized) {
      await pinecone.init({
        environment: process.env.PINECONE_ENVIRONMENT!,
        apiKey: process.env.PINECONE_API_KEY!,
      });
      this.initialized = true;
    }
  }

  async getEmbedding(text: string) {
    const embedding = await openai.embeddings.create({
      model: "text-embedding-3-small",
      input: text,
    });
    return embedding.data[0].embedding;
  }

  async queryPinecone(embedding: number[], userId: string) {
    const index = pinecone.Index(process.env.PINECONE_INDEX!);
    return await index.query({
      vector: embedding,
      filter: { userId },
      topK: 5,
    });
  }

  async generateResponse(
    message: string,
    chatHistory: ChatCompletionMessageParam[]
  ) {
    const completion = await openai.chat.completions.create({
      model: "gpt-4",
      messages: [
        {
          role: "system",
          content: "You are a helpful assistant. Use the provided context to answer questions.",
        },
        ...chatHistory,
        { role: "user", content: message },
      ],
    });
    return completion.choices[0].message.content;
  }
} 