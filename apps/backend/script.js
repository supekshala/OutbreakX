const chatMessages = document.getElementById('chat-messages');
const chatInput = document.getElementById('chat-input');
const sendButton = document.getElementById('send-button');
const pdfUpload = document.getElementById('pdf-upload');
const uploadButton = document.getElementById('upload-button');
const uploadLoader = document.getElementById('upload-loader');
const uploadStatus = document.getElementById('upload-status');
const typingIndicator = document.querySelector('.typing-indicator');

let accessToken = 1234;
let chatHistory = [];
const userId = sessionStorage.getItem('userId') || uuid.v4();
sessionStorage.setItem('userId', userId);
window.configs={"serviceUrl":"http://localhost:8000"}

async function getAccessToken() {
    const response = await fetch(window.configs.tokenUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: `grant_type=client_credentials&client_id=${window.configs.clientId}&client_secret=${window.configs.clientSecret}`
    });
    const data = await response.json();
    accessToken = data.access_token;
}

async function sendMessage() {
    const message = chatInput.value.trim();
    if (message) {
        addMessageToChat('user', message);
        chatInput.value = '';
        disableInput(true);
        showTypingIndicator(true);

        try {
            const response = await fetch(`${window.configs.serviceUrl}/ask_question`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${accessToken}`
                },
                body: JSON.stringify({
                    user_id: userId,
                    message: message,
                    chat_history: chatHistory
                })
            });
            const data = await response.json();
            addMessageToChat('ai', data.response, true);
            updateChatHistory('human', message);
            updateChatHistory('ai', data.response);
        } catch (error) {
            console.error('Error:', error);
            addMessageToChat('ai', 'Sorry, there was an error processing your request.');
        } finally {
            disableInput(false);
            showTypingIndicator(false);
        }
    }
}

function addMessageToChat(role, content, isMarkdown = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    const avatar = document.createElement('div');
    avatar.className = 'avatar';
    avatar.textContent = role === 'user' ? 'U' : 'AI';

    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';

    if (isMarkdown) {
        messageContent.innerHTML = marked(content);
    } else {
        messageContent.textContent = content;
    }

    messageDiv.appendChild(avatar);
    messageDiv.appendChild(messageContent);
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function addSystemMessage(message) {
    const systemMessageDiv = document.createElement('div');
    systemMessageDiv.className = 'system-message';
    systemMessageDiv.textContent = message;
    chatMessages.appendChild(systemMessageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function updateChatHistory(role, content) {
    chatHistory.push({ role, content });
    if (chatHistory.length > 5) {
        chatHistory = chatHistory.slice(-5);
    }
}

function disableInput(disabled) {
    chatInput.disabled = disabled;
    sendButton.disabled = disabled;
}

function showTypingIndicator(show) {
    typingIndicator.style.display = show ? 'block' : 'none';
}

async function uploadPDF() {
    const file = pdfUpload.files[0];
    if (file) {
        uploadLoader.style.display = 'inline-block';
        uploadStatus.textContent = 'Uploading...';
        disableInput(true);

        const formData = new FormData();
        formData.append('file', file);
        formData.append('user_id', userId);

        try {
            const response = await fetch(`${window.configs.serviceUrl}/upload_pdf`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${accessToken}`
                },
                body: formData
            });
            const data = await response.json();
            uploadStatus.textContent = 'Upload successful!';
            addSystemMessage(`Uploaded ${file.name}`);
        } catch (error) {
            console.error('Error:', error);
            uploadStatus.textContent = 'Upload failed. Please try again.';
        } finally {
            uploadLoader.style.display = 'none';
            disableInput(false);
        }
    }
}

sendButton.addEventListener('click', sendMessage);
chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
});
pdfUpload.addEventListener('change', uploadPDF);

// // Initialize
// getAccessToken();