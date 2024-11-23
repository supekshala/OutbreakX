import React, { useState } from 'react';

export interface ChatInputProps {
  onSendMessage: (message: string) => void;
  disabled?: boolean;
}

export interface ChatInputProps {
  onSendMessage: (message: string) => void;
  disabled?: boolean;
}

export const ChatInput: React.FC<ChatInputProps> = ({ onSendMessage, disabled }) => {
  const [message, setMessage] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim()) {
      onSendMessage(message.trim());
      setMessage('');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="chat-input">
      <input
        type="text"
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder="Type a message..."
        disabled={disabled}
      />
      <button type="submit" disabled={disabled || !message.trim()}>
        Send
      </button>
    </form>
  );
}; 