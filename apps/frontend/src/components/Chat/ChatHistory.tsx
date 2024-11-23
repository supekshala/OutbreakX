import React from 'react';
import { ChatMessage } from '../../types/chat';

export interface ChatHistoryProps {
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
}

export const ChatHistory: React.FC<ChatHistoryProps> = ({ messages, isLoading, error }) => {
  return (
    <div className="chat-history">
      {messages.map((message, index) => (
        <div key={index} className={`message ${message.role}`}>
          <div className="message-content">{message.content}</div>
        </div>
      ))}
      {isLoading && <div className="message loading">Loading...</div>}
      {error && <div className="message error">{error}</div>}
    </div>
  );
};

export {};