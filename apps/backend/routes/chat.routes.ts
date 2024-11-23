import express from 'express';
import multer from 'multer';
import path from 'path';
import { ChatService } from '../services/chatService';
import Chat from '../models/Chat';

const router = express.Router();

// Configure multer for file uploads
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, path.join(__dirname, '../uploads/'));
  },
  filename: (req, file, cb) => {
    const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
    cb(null, uniqueSuffix + path.extname(file.originalname));
  }
});

const upload = multer({
  storage: storage,
  fileFilter: (req, file, cb) => {
    if (file.mimetype === 'application/pdf') {
      cb(null, true);
    } else {
      cb(null, false);
      return cb(new Error('Only PDF files are allowed!'));
    }
  }
});

// PDF upload route
router.post('/upload', upload.single('file'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: "No file uploaded" });
    }
    
    const userId = req.body.userId;
    if (!userId) {
      return res.status(400).json({ error: "userId is required" });
    }

    // Initialize chat service
    const chatService = ChatService.getInstance();
    await chatService.initialize();

    // TODO: Process PDF and create embeddings
    
    res.json({ 
      message: "PDF uploaded successfully",
      file: req.file.filename
    });
  } catch (error) {
    console.error('Upload error:', error);
    res.status(500).json({ 
      error: "Error uploading PDF",
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// Chat message route
router.post('/message', async (req, res) => {
  try {
    const { message, userId } = req.body;

    if (!message) {
      return res.status(400).json({ error: "Message is required" });
    }

    if (!userId) {
      return res.status(400).json({ error: "userId is required" });
    }

    // Get chat history
    const chatHistory = await Chat.findAll({
      where: { userId },
      order: [['createdAt', 'ASC']],
      limit: 10,
    });

    // Initialize chat service
    const chatService = ChatService.getInstance();
    await chatService.initialize();

    // Get embedding for the question
    const embedding = await chatService.getEmbedding(message);

    // Query Pinecone for relevant context
    const queryResponse = await chatService.queryPinecone(embedding, userId);

    // Generate response
    const response = await chatService.generateResponse(
      message,
      chatHistory.map(chat => ({
        role: chat.role as "user" | "assistant",
        content: chat.message,
      }))
    );

    // Save the conversation
    await Chat.create({
      userId,
      message,
      role: "user",
    });

    await Chat.create({
      userId,
      message: response,
      role: "assistant",
    });

    res.json({ response });
  } catch (error) {
    console.error('Chat error:', error);
    res.status(500).json({ 
      error: "Error processing message",
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// Make sure to export like this:
module.exports = router; 