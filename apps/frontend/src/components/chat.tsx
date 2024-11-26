// apps/frontend/src/components/RAGChatAgent.tsx
import React, { useState, useEffect, useRef } from 'react';
import { v4 as uuidv4 } from 'uuid';
import axios from 'axios';
import { marked } from 'marked';
import './ChatStyles.css';

const RAGChatAgent: React.FC = () => {
  
  const [chatHistory, setChatHistory] = useState<{ role: string; content: string }[]>([]);
  const [message, setMessage] = useState('');
  //const [accessToken, setAccessToken] = useState<string | null>(null);
  const [accessToken] = useState<string | null>(null);
  const [uploadStatus, setUploadStatus] = useState('');
  const [loading, setLoading] = useState(false);
  const chatMessagesRef = useRef<HTMLDivElement | null>(null);
  const userId = sessionStorage.getItem('userId') || uuidv4();

  useEffect(() => {
    sessionStorage.setItem('userId', userId);
    // getAccessToken(); // Uncomment if you need to fetch access token on mount
  }, [userId]);

  const sendMessage = async () => {
    if (!message.trim()) return;

    addMessageToChat('user', message);
    setMessage('');
    setLoading(true);

    try {
      await axios.post(`${window.configs.serviceUrl}/ask_question`, {
        user_id: userId,
        message: message,
        chat_history: chatHistory
      }, {
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`
        }
      });
      addMessageToChat('ai', 'Response from AI', true);
      updateChatHistory('user', message);
      updateChatHistory('ai', 'Response from AI');
    } catch (error) {
      console.error('Error:', error);
      addMessageToChat('ai', 'Sorry, there was an error processing your request.');
    } finally {
      setLoading(false);
    }
  };

  const addMessageToChat = (role: string, content: string, isMarkdown = false) => {
    const newMessage = { role, content: isMarkdown ? marked(content) : content };
    setChatHistory((prev) => [...prev, newMessage]);
    if (chatMessagesRef.current) {
      chatMessagesRef.current.scrollTop = chatMessagesRef.current.scrollHeight;
    }
  };

  const updateChatHistory = (role: string, content: string) => {
    setChatHistory((prev) => {
      const newHistory = [...prev, { role, content }];
      return newHistory.length > 5 ? newHistory.slice(-5) : newHistory;
    });
  };

  const uploadPDF = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setLoading(true);
      setUploadStatus('Uploading...');

      const formData = new FormData();
      formData.append('file', file);
      formData.append('user_id', userId);

      try {
        const response = await axios.post(`${window.configs.serviceUrl}/upload_pdf`, formData, {
          headers: {
            'Authorization': `Bearer ${accessToken}`
          }
        });
        setUploadStatus('Upload successful!');
        addMessageToChat('system', `Uploaded ${file.name}`);
      } catch (error) {
        console.error('Error:', error);
        setUploadStatus('Upload failed. Please try again.');
      } finally {
        setLoading(false);
      }
    }
  };

  console.log(window.configs);

  return (
    <div className="container">
      <div className="left-panel">
        <h2>Data Sources</h2>
        <div className="upload-section">
          <h3>Document Upload</h3>
          <div className="upload-area">
            <input type="file" id="pdf-upload" accept=".pdf,.csv,.geojson,.shp" onChange={uploadPDF} />
            <label htmlFor="pdf-upload" id="upload-button">
              <i className="fas fa-cloud-upload-alt"></i> Upload Files
            </label>
            <div className="file-types">Supported: PDF, CSV, GeoJSON, Shapefile</div>
            <div className="loader" id="upload-loader" style={{ display: loading ? 'inline-block' : 'none' }}></div>
            <p id="upload-status">{uploadStatus}</p>
          </div>
        </div>
        {/* Analysis options can be added here */}
      </div>

      <div className="chat-area">
        <div className="chat-header">
          <div className="header-title">
            <i className="fas fa-globe-americas"></i>
            Geospatial Analysis Assistant
          </div>
          <div className="header-controls">
            <button id="export-btn" title="Export Analysis">
              <i className="fas fa-download"></i>
            </button>
            <button id="clear-btn" title="Clear Chat">
              <i className="fas fa-trash-alt"></i>
            </button>
          </div>
        </div>
        <div className="visualization-area" id="map-view"></div>
        <div className="chat-messages" id="chat-messages" ref={chatMessagesRef}>
          {chatHistory.map((chat, index) => (
            <div key={index} className={`message ${chat.role}`}>
              <div className="avatar">{chat.role === 'user' ? 'U' : 'AI'}</div>
              <div className="message-content" dangerouslySetInnerHTML={{ __html: chat.content }}></div>
            </div>
          ))}
        </div>
        <div className="typing-indicator" style={{ display: loading ? 'block' : 'none' }}>
          <span></span><span></span><span></span>
        </div>
        <div className="input-area">
          <textarea
            id="chat-input"
            placeholder="Ask questions about your geospatial data or request specific analyses..."
            rows={2}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            disabled={loading}
          />
          <button id="send-button" onClick={sendMessage} disabled={loading}>
            <i className="fas fa-paper-plane"></i>
          </button>
        </div>
      </div>
    </div>
  );
};


export default RAGChatAgent;