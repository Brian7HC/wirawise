/**
 * Kikuyu Voice Chatbot - Simple Frontend
 * Direct event handlers for sending messages
 */

// Configuration
const API_BASE_URL = 'http://localhost:8000/api/v1';
let sessionId = null;
let messageCount = 0;

// DOM Elements
const messageInput = document.getElementById('chatTa');
const sendBtn = document.getElementById('sndBtn');
const messagesContainer = document.getElementById('messagesContainer');
const welcomeScreen = document.getElementById('welcomeScreen');
const chatWin = document.getElementById('chatWin');

// Initialize on page load
document.addEventListener('DOMContentLoaded', async () => {
    console.log('Initializing chatbot...');
    
    // Create session
    try {
        const response = await fetch(`${API_BASE_URL}/session/create`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await response.json();
        sessionId = data.session_id;
        console.log('Session created:', sessionId);
    } catch (error) {
        console.error('Failed to create session:', error);
    }
    
    // Setup event listeners
    if (sendBtn) {
        sendBtn.addEventListener('click', sendMessage);
        console.log('Send button listener attached');
    } else {
        console.error('Send button not found!');
    }
    
    if (messageInput) {
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        console.log('Input listener attached');
    } else {
        console.error('Message input not found!');
    }
});

// Send message function
async function sendMessage() {
    const text = messageInput.value.trim();
    if (!text) {
        console.log('Empty message');
        return;
    }
    
    console.log('Sending:', text);
    
    // Show user message
    addMessage(text, 'user');
    messageInput.value = '';
    
    // Show typing indicator
    showTyping();
    
    try {
        // Determine if it's an agriculture query
        const isAgri = isAgricultureQuery(text);
        const endpoint = isAgri ? '/chat/agriculture' : '/chat/text';
        
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: text,
                session_id: sessionId,
                generate_audio: false,
                include_sources: false
            })
        });
        
        const data = await response.json();
        console.log('Response:', data);
        
        // Hide typing
        hideTyping();
        
        // Show bot response
        const botText = data.response_text || data.response || 'No response';
        addMessage(botText, 'bot');
        
    } catch (error) {
        console.error('Error:', error);
        hideTyping();
        addMessage('Error: ' + error.message, 'bot');
    }
}

// Add message to chat
function addMessage(text, sender) {
    // Hide welcome, show chat
    if (welcomeScreen) welcomeScreen.style.display = 'none';
    if (chatWin) chatWin.style.display = 'block';
    
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${sender}`;
    msgDiv.textContent = text;
    
    if (messagesContainer) {
        messagesContainer.appendChild(msgDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
}

// Show typing indicator
function showTyping() {
    const existing = document.getElementById('typingIndicator');
    if (existing) existing.remove();
    
    const typing = document.createElement('div');
    typing.id = 'typingIndicator';
    typing.className = 'message bot typing';
    typing.textContent = '...';
    
    if (messagesContainer) {
        messagesContainer.appendChild(typing);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
}

// Hide typing indicator
function hideTyping() {
    const typing = document.getElementById('typingIndicator');
    if (typing) typing.remove();
}

// Check if agriculture query
function isAgricultureQuery(text) {
    const keywords = ['crop', 'crops', 'plant', 'farm', 'agriculture', 'harvest', 
        'soil', 'seed', 'fertilizer', 'pest', 'disease', 'rain', 'irrigation',
        'maize', 'wheat', 'beans', 'coffee', 'potato', 'vegetable',
        'waru', 'mboga', 'ira', 'ngima', 'kuhamba', 'kurima', 'kuvuna'];
    
    const lower = text.toLowerCase();
    return keywords.some(k => lower.includes(k));
}

// Make sendMessage available globally for inline handlers
window.sendMessageFromInput = sendMessage;
