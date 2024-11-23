import express, { Request, Response, NextFunction } from "express";
import bodyParser from "body-parser";
import { sequelize } from "./config/database";
import Marker from "./models/Marker";
import cors from "cors";
import path from "path";
import chatRouter from "./routes/chat.routes";

import dotenv from "dotenv";
dotenv.config();

// Initialize express app
const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors());
app.use(bodyParser.json());
app.use('/uploads', express.static(path.join(__dirname, 'uploads')));

// Create uploads directory if it doesn't exist
import fs from 'fs';
const uploadsDir = path.join(__dirname, 'uploads');
if (!fs.existsSync(uploadsDir)) {
  fs.mkdirSync(uploadsDir, { recursive: true });
}

// Database connection
sequelize
  .sync()
  .then(() => console.log("Database connected"))
  .catch((err) => console.error("Database connection error:", err));

// Marker routes
app.post("/markers", async (req: Request, res: Response, next: NextFunction) => {
  const { location, description } = req.body;
  
  if (!location || !description) {
    return res.status(400).json({ error: "Location and description are required" });
  }

  try {
    const marker = await Marker.create({
      location,
      description,
    });
    res.json(marker);
  } catch (error) {
    next(error);
  }
});

app.get("/markers", async (req: Request, res: Response, next: NextFunction) => {
  try {
    const markers = await Marker.findAll();
    res.json(markers);
  } catch (error) {
    next(error);
  }
});

// Chat routes
app.use('/chat', chatRouter);

// Error handling middleware
app.use((err: Error, req: Request, res: Response, next: NextFunction) => {
  console.error('Error:', err);
  res.status(500).json({ 
    error: "Internal server error",
    message: process.env.NODE_ENV === 'development' ? err.message : undefined
  });
});

// 404 handler
app.use((req: Request, res: Response) => {
  res.status(404).json({ error: "Route not found" });
});

// Start server
app.listen(PORT, () => {
  console.log(`Server is running on http://localhost:${PORT}`);
}).on('error', (err) => {
  console.error('Failed to start server:', err);
  process.exit(1);
});

// Handle uncaught exceptions
process.on('uncaughtException', (err) => {
  console.error('Uncaught Exception:', err);
  process.exit(1);
});

process.on('unhandledRejection', (err) => {
  console.error('Unhandled Rejection:', err);
  process.exit(1);
});
