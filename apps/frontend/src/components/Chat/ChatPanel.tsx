import React, { useState } from 'react';
import { ChatHistory } from './ChatHistory';
import { ChatInput } from './ChatInput';
import { FileUpload } from './FileUpload';
import { ChatMessage } from '../../types/chat';
import { chatApi } from '../../services/api';

export interface ChatPanelProps {}

export const ChatPanel: React.FC<ChatPanelProps> = () => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Temporary userId - in a real app, this would come from authentication
  const userId = "123";

  const handleFileUpload = async (file: File) => {
    try {
      setIsLoading(true);
      setError(null);
      await chatApi.uploadPdf(file, userId);
      setMessages(prev => [...prev, {
        content: 'PDF uploaded successfully. You can now ask questions about it.',
        role: 'assistant'
      }]);
    } catch (err) {
      setError('Failed to upload PDF');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSendMessage = async (message: string) => {
    try {
      setIsLoading(true);
      setError(null);
      
      // Add user message to chat
      setMessages(prev => [...prev, { content: message, role: 'user' }]);
      
      // Get response from API
      const response = await chatApi.sendMessage(message, userId);
      
      // Add assistant response to chat
      setMessages(prev => [...prev, { content: response.message, role: 'assistant' }]);
    } catch (err) {
      setError('Failed to send message');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={`chat-panel ${isExpanded ? 'expanded' : 'collapsed'}`}>
      <button 
        className="chat-toggle"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        {isExpanded ? '→' : '←'} Chat
      </button>
      
      {isExpanded && (
        <div className="chat-content">
          <FileUpload onUpload={handleFileUpload} />
          <ChatHistory messages={messages} isLoading={isLoading} error={error} />
          <ChatInput onSendMessage={handleSendMessage} disabled={isLoading} />
        </div>
      )}
    </div>
  );
};