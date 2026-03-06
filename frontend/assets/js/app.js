/**
 * Kikuyu Voice Chatbot - Frontend Application
 * Handles all chat interactions, API calls, and UI updates
 */

// ============================================
// CONFIGURATION
// ============================================
const CONFIG = {
    API_BASE_URL: 'http://localhost:8000/api/v1',
    API_TIMEOUT: 30000,
    MAX_RETRIES: 3,
    TYPING_DELAY: 1000,
    AUTO_SCROLL_DELAY: 100
};

// ============================================
// STATE MANAGEMENT
// ============================================
const State = {
    sessionId: null,
    messageCount: 0,
    confidenceScores: [],
    isTyping: false,
    currentTheme: 'light'
};

// ============================================
// DOM ELEMENTS
// ============================================
const DOM = {
    // Main elements
    welcomeScreen: document.getElementById('welcomeScreen'),
    messagesContainer: document.getElementById('messagesContainer'),
    messageInput: document.getElementById('messageInput'),
    sendBtn: document.getElementById('sendBtn'),
    typingIndicator: document.getElementById('typingIndicator'),
    
    // Sidebar
    sessionIdDisplay: document.getElementById('sessionId'),
    messageCountDisplay: document.getElementById('messageCount'),
    avgConfidenceDisplay: document.getElementById('avgConfidence'),
    
    // Buttons
    newChatBtn: document.getElementById('newChatBtn'),
    themeToggle: document.getElementById('themeToggle'),
    infoBtn: document.getElementById('infoBtn'),
    voiceBtn: document.getElementById('voiceBtn'),
    emojiBtn: document.getElementById('emojiBtn'),
    
    // Modal
    infoModal: document.getElementById('infoModal'),
    closeModal: document.getElementById('closeModal'),
    
    // Containers
    toastContainer: document.getElementById('toastContainer')
};

// ============================================
// API SERVICE
// ============================================
class ChatAPI {
    static async createSession() {
        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}/session/create`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            return data.session_id;
        } catch (error) {
            console.error('Error creating session:', error);
            throw error;
        }
    }
    
    static async sendMessage(text, sessionId) {
        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}/chat/text`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    text: text,
                    session_id: sessionId
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('Error sending message:', error);
            throw error;
        }
    }
    
    static async sendVoiceMessage(audioBlob, sessionId) {
        try {
            const formData = new FormData();
            // IMPORTANT: Now sending WAV format (not WebM/Opus)
            // Wav2Vec2-BERT cannot decode Opus - it needs raw PCM WAV
            formData.append('audio', audioBlob, 'recording.wav');
            if (sessionId) {
                formData.append('session_id', sessionId);
            }
            
            const response = await fetch(`${CONFIG.API_BASE_URL}/chat/voice`, {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('Error sending voice message:', error);
            throw error;
        }
    }
    
    static async getHealth() {
        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}/health`);
            return await response.json();
        } catch (error) {
            console.error('Error checking health:', error);
            return { status: 'error' };
        }
    }
    
    static async lookupWord(word) {
        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}/vocabulary/${encodeURIComponent(word)}`);
            return await response.json();
        } catch (error) {
            console.error('Error looking up word:', error);
            throw error;
        }
    }
}

// ============================================
// AUDIO RECORDING
// ============================================
class AudioRecorder {
    constructor() {
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.isRecording = false;
    }
    
    async startRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                } 
            });
            
            // Always use WebM - we'll convert to WAV using AudioContext after recording
            // This is more reliable than trying to use WAV directly
            this.mediaRecorder = new MediaRecorder(stream, {
                mimeType: 'audio/webm;codecs=opus'
            });
            
            this.audioChunks = [];
            
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };
            
            this.mediaRecorder.start(100);  // Collect data every 100ms
            this.isRecording = true;
            this.micStream = stream;
            
            console.log('🎤 Recording started (WebM/Opus - will convert to WAV)');
            
        } catch (error) {
            console.error('Error starting recording:', error);
            throw new Error('Microphone access denied or not available');
        }
    }
    
    async stopRecording() {
        return new Promise((resolve, reject) => {
            if (!this.mediaRecorder || !this.isRecording) {
                reject(new Error('Not currently recording'));
                return;
            }
            
            this.mediaRecorder.onstop = async () => {
                try {
                    // Stop microphone
                    if (this.micStream) {
                        this.micStream.getTracks().forEach(track => track.stop());
                    }
                    
                    // Create blob
                    const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
                    
                    // Convert to WAV 16kHz using AudioContext
                    const wavBlob = await this.convertToWav(audioBlob);
                    
                    this.isRecording = false;
                    this.audioChunks = [];
                    
                    console.log('🎤 Recording stopped, WAV size:', wavBlob.size, 'bytes');
                    
                    resolve(wavBlob);
                    
                } catch (error) {
                    console.error('Error converting audio:', error);
                    reject(error);
                }
            };
            
            this.mediaRecorder.stop();
        });
    }
    
    async convertToWav(blob) {
        // Use AudioContext to decode and convert to 16kHz WAV
        const audioContext = new AudioContext({ sampleRate: 16000 });
        
        // Convert blob to array buffer
        const arrayBuffer = await blob.arrayBuffer();
        
        // Decode the audio data
        const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
        
        // Get the audio data
        const channelData = audioBuffer.getChannelData(0);
        
        // Resample to 16kHz if needed
        let resampledData = channelData;
        if (audioBuffer.sampleRate !== 16000) {
            resampledData = this.resample(channelData, audioBuffer.sampleRate, 16000);
        }
        
        // Normalize to prevent clipping
        const maxVal = Math.max(...resampledData.map(Math.abs));
        if (maxVal > 0) {
            const scale = 0.9 / maxVal;
            for (let i = 0; i < resampledData.length; i++) {
                resampledData[i] *= scale;
            }
        }
        
        // Close AudioContext
        await audioContext.close();
        
        // Encode to WAV
        return this.encodeWAV(resampledData, 16000);
    }
    
    resample(audio, fromRate, toRate) {
        if (fromRate === toRate) return audio;
        
        const ratio = fromRate / toRate;
        const newLength = Math.round(audio.length / ratio);
        const result = new Float32Array(newLength);
        
        for (let i = 0; i < newLength; i++) {
            result[i] = audio[Math.round(i * ratio)];
        }
        
        return result;
    }
    
    // Convert Float32 PCM to WAV blob
    encodeWAV(samples, sampleRate) {
        const buffer = new ArrayBuffer(44 + samples.length * 2);
        const view = new DataView(buffer);
        
        // RIFF identifier
        this.writeString(view, 0, 'RIFF');
        // file length
        view.setUint32(4, 36 + samples.length * 2, true);
        // RIFF type
        this.writeString(view, 8, 'WAVE');
        // format chunk identifier
        this.writeString(view, 12, 'fmt ');
        // format chunk length
        view.setUint32(16, 16, true);
        // sample format (raw)
        view.setUint16(20, 1, true);
        // channel count (mono)
        view.setUint16(22, 1, true);
        // sample rate
        view.setUint32(24, sampleRate, true);
        // byte rate (sample rate * channels * bits per sample / 8)
        view.setUint32(28, sampleRate * 2, true);
        // block align (channels * bits per sample / 8)
        view.setUint16(32, 2, true);
        // bits per sample
        view.setUint16(34, 16, true);
        // data chunk identifier
        this.writeString(view, 36, 'data');
        // data chunk length
        view.setUint32(40, samples.length * 2, true);
        
        // Write PCM samples
        let offset = 44;
        for (let i = 0; i < samples.length; i++) {
            const s = Math.max(-1, Math.min(1, samples[i]));
            view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
            offset += 2;
        }
        
        return new Blob([buffer], { type: 'audio/wav' });
    }
    
    writeString(view, offset, string) {
        for (let i = 0; i < string.length; i++) {
            view.setUint8(offset + i, string.charCodeAt(i));
        }
    }
    
    cancelRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            if (this.micStream) {
                this.micStream.getTracks().forEach(track => track.stop());
            }
            this.isRecording = false;
            this.audioChunks = [];
        }
    }
}

// ============================================
// TEXT-TO-SPEECH
// ============================================
class TextToSpeech {
    static speak(text, lang = 'sw-KE') {
        // Cancel any ongoing speech
        window.speechSynthesis.cancel();
        
        const utterance = new SpeechSynthesisUtterance(text);
        
        // Set language for Kikuyu/Swahili
        utterance.lang = lang;
        utterance.rate = 0.9;  // Slightly slower for clarity
        utterance.pitch = 1.0;
        utterance.volume = 1.0;
        
        // Try to find a suitable voice
        const voices = window.speechSynthesis.getVoices();
        
        // Prefer Swahili or English voices
        const preferredVoices = voices.filter(v => 
            v.lang.startsWith('sw') || 
            v.lang.startsWith('en') ||
            v.lang.startsWith('kik')
        );
        
        if (preferredVoices.length > 0) {
            utterance.voice = preferredVoices[0];
        }
        
        // Handle errors
        utterance.onerror = (event) => {
            console.error('TTS Error:', event.error);
        };
        
        window.speechSynthesis.speak(utterance);
        console.log('🔊 Speaking:', text);
    }
    
    static stop() {
        window.speechSynthesis.cancel();
    }
}

// Preload voices (some browsers need this)
if (window.speechSynthesis) {
    window.speechSynthesis.getVoices();
    window.speechSynthesis.onvoiceschanged = () => {
        console.log('🔊 Voices loaded:', window.speechSynthesis.getVoices().length);
    };
}

// ============================================
// UI FUNCTIONS
// ============================================
class UI {
    static showTypingIndicator() {
        DOM.typingIndicator.style.display = 'flex';
        State.isTyping = true;
        this.scrollToBottom();
    }
    
    static hideTypingIndicator() {
        DOM.typingIndicator.style.display = 'none';
        State.isTyping = false;
    }
    
    static hideWelcomeScreen() {
        DOM.welcomeScreen.style.display = 'none';
        DOM.messagesContainer.classList.add('active');
    }
    
    static showWelcomeScreen() {
        DOM.welcomeScreen.style.display = 'flex';
        DOM.messagesContainer.classList.remove('active');
        DOM.messagesContainer.innerHTML = '';
    }
    
    static addMessage(text, sender, metadata = {}) {
        this.hideWelcomeScreen();
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        const bubbleDiv = document.createElement('div');
        bubbleDiv.className = 'message-bubble';
        
        // Message text
        const textDiv = document.createElement('div');
        textDiv.className = 'message-text';
        textDiv.textContent = text;
        bubbleDiv.appendChild(textDiv);
        
        // Translation (for bot messages)
        if (sender === 'bot' && metadata.translation) {
            const translationDiv = document.createElement('div');
            translationDiv.className = 'message-translation';
            translationDiv.textContent = metadata.translation;
            bubbleDiv.appendChild(translationDiv);
        }
        
        contentDiv.appendChild(bubbleDiv);
        
        // Metadata (for bot messages)
        if (sender === 'bot' && (metadata.confidence !== undefined || metadata.intent_name)) {
            const metaDiv = document.createElement('div');
            metaDiv.className = 'message-meta';
            
            if (metadata.confidence !== undefined) {
                const confidenceBadge = document.createElement('span');
                confidenceBadge.className = 'confidence-badge';
                confidenceBadge.textContent = `${Math.round(metadata.confidence * 100)}% confident`;
                metaDiv.appendChild(confidenceBadge);
            }
            
            if (metadata.intent_name) {
                const intentBadge = document.createElement('span');
                intentBadge.className = 'intent-badge';
                intentBadge.textContent = metadata.intent_name;
                metaDiv.appendChild(intentBadge);
            }
            
            // Timestamp
            const timeSpan = document.createElement('span');
            timeSpan.textContent = new Date().toLocaleTimeString('en-US', { 
                hour: '2-digit', 
                minute: '2-digit' 
            });
            metaDiv.appendChild(timeSpan);
            
            contentDiv.appendChild(metaDiv);
        }
        
        messageDiv.appendChild(contentDiv);
        DOM.messagesContainer.appendChild(messageDiv);
        
        this.scrollToBottom();
    }
    
    static scrollToBottom() {
        setTimeout(() => {
            DOM.messagesContainer.scrollTop = DOM.messagesContainer.scrollHeight;
        }, CONFIG.AUTO_SCROLL_DELAY);
    }
    
    static updateStats() {
        // Update message count
        DOM.messageCountDisplay.textContent = State.messageCount;
        
        // Update average confidence
        if (State.confidenceScores.length > 0) {
            const avg = State.confidenceScores.reduce((a, b) => a + b, 0) / State.confidenceScores.length;
            DOM.avgConfidenceDisplay.textContent = `${Math.round(avg * 100)}%`;
        }
    }
    
    static updateSessionDisplay(sessionId) {
        const shortId = sessionId.split('-')[0];
        DOM.sessionIdDisplay.innerHTML = `<small>Session: ${shortId}...</small>`;
    }
    
    static showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const icon = type === 'success' ? '✓' : type === 'error' ? '✗' : 'ℹ';
        toast.innerHTML = `
            <span style="font-size: 20px;">${icon}</span>
            <span>${message}</span>
        `;
        
        DOM.toastContainer.appendChild(toast);
        
        setTimeout(() => {
            toast.style.animation = 'toastSlideIn 0.3s ease reverse';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
    
    static clearInput() {
        DOM.messageInput.value = '';
        DOM.messageInput.focus();
    }
    
    static disableInput() {
        DOM.messageInput.disabled = true;
        DOM.sendBtn.disabled = true;
    }
    
    static enableInput() {
        DOM.messageInput.disabled = false;
        DOM.sendBtn.disabled = false;
        DOM.messageInput.focus();
    }
    
    static toggleTheme() {
        State.currentTheme = State.currentTheme === 'light' ? 'dark' : 'light';
        document.documentElement.setAttribute('data-theme', State.currentTheme);
        
        const icon = DOM.themeToggle.querySelector('i');
        icon.className = State.currentTheme === 'light' ? 'fas fa-moon' : 'fas fa-sun';
        
        localStorage.setItem('theme', State.currentTheme);
    }
    
    static loadTheme() {
        const savedTheme = localStorage.getItem('theme') || 'light';
        State.currentTheme = savedTheme;
        document.documentElement.setAttribute('data-theme', savedTheme);
        
        const icon = DOM.themeToggle.querySelector('i');
        icon.className = savedTheme === 'light' ? 'fas fa-moon' : 'fas fa-sun';
    }
    
    static showModal(modalElement) {
        modalElement.classList.add('active');
    }
    
    static hideModal(modalElement) {
        modalElement.classList.remove('active');
    }
}

// ============================================
// CHAT CONTROLLER
// ============================================
class ChatController {
    static async initialize() {
        console.log('🇰🇪 Initializing Kikuyu Chatbot...');
        
        // Load theme
        UI.loadTheme();
        
        // Check API health
        this.checkHealth();
        
        // Create session
        await this.createSession();
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Focus input
        DOM.messageInput.focus();
        
        console.log('✅ Chatbot initialized successfully');
    }
    
    static async checkHealth() {
        try {
            const health = await ChatAPI.getHealth();
            if (health.status === 'healthy') {
                console.log('✅ API is healthy');
                UI.showToast('Connected to chatbot', 'success');
            } else {
                console.warn('⚠️ API health check failed');
                UI.showToast('API connection issues', 'error');
            }
        } catch (error) {
            console.error('❌ Health check failed:', error);
            UI.showToast('Cannot connect to API', 'error');
        }
    }
    
    static async createSession() {
        try {
            State.sessionId = await ChatAPI.createSession();
            UI.updateSessionDisplay(State.sessionId);
            console.log('Session created:', State.sessionId);
        } catch (error) {
            console.error('Failed to create session:', error);
            UI.showToast('Failed to create session', 'error');
        }
    }
    
    static setupEventListeners() {
        // Send message on button click
        DOM.sendBtn.addEventListener('click', () => this.handleSendMessage());
        
        // Send message on Enter key
        DOM.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.handleSendMessage();
            }
        });
        
        // Quick action buttons
        document.querySelectorAll('.quick-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const text = btn.getAttribute('data-text');
                DOM.messageInput.value = text;
                this.handleSendMessage();
            });
        });
        
        // Suggestion chips
        document.querySelectorAll('.suggestion-chip').forEach(chip => {
            chip.addEventListener('click', () => {
                const text = chip.getAttribute('data-text');
                DOM.messageInput.value = text;
                this.handleSendMessage();
            });
        });
        
        // New chat button
        DOM.newChatBtn.addEventListener('click', () => this.handleNewChat());
        
        // Theme toggle
        DOM.themeToggle.addEventListener('click', () => UI.toggleTheme());
        
        // Info modal
        DOM.infoBtn.addEventListener('click', () => UI.showModal(DOM.infoModal));
        DOM.closeModal.addEventListener('click', () => UI.hideModal(DOM.infoModal));
        
        // Close modal on outside click
        DOM.infoModal.addEventListener('click', (e) => {
            if (e.target === DOM.infoModal) {
                UI.hideModal(DOM.infoModal);
            }
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Escape to close modals
            if (e.key === 'Escape') {
                UI.hideModal(DOM.infoModal);
            }
            
            // Ctrl+N for new chat
            if (e.ctrlKey && e.key === 'n') {
                e.preventDefault();
                this.handleNewChat();
            }
        });
        
        // Voice button - enable voice recording
        DOM.voiceBtn.addEventListener('click', () => this.handleVoiceToggle());
        DOM.voiceBtn.disabled = false;
        
        // Emoji button (placeholder)
        DOM.emojiBtn.addEventListener('click', () => {
            UI.showToast('Emoji picker coming soon!', 'info');
        });
    }
    
    static async handleSendMessage() {
        const text = DOM.messageInput.value.trim();
        
        if (!text) {
            return;
        }
        
        // Disable input while processing
        UI.disableInput();
        
        // Add user message to UI
        UI.addMessage(text, 'user');
        UI.clearInput();
        
        // Show typing indicator
        setTimeout(() => {
            UI.showTypingIndicator();
        }, 300);
        
        try {
            // Send to API
            const response = await ChatAPI.sendMessage(text, State.sessionId);
            
            // Hide typing indicator
            setTimeout(() => {
                UI.hideTypingIndicator();
                
                // Add bot response
                UI.addMessage(response.response_text, 'bot', {
                    translation: response.response_translation,
                    confidence: response.confidence,
                    intent_name: response.intent_name
                });
                
                // Play TTS response
                if (response.response_text) {
                    TextToSpeech.speak(response.response_text);
                }
                
                // Update stats
                State.messageCount++;
                if (response.confidence) {
                    State.confidenceScores.push(response.confidence);
                }
                UI.updateStats();
                
                // Re-enable input
                UI.enableInput();
                
            }, CONFIG.TYPING_DELAY);
            
        } catch (error) {
            console.error('Error sending message:', error);
            
            UI.hideTypingIndicator();
            UI.addMessage(
                'Ndĩ na mathina. Geria rĩngĩ. (I have a problem. Try again.)',
                'bot',
                { translation: 'Sorry, there was an error. Please try again.' }
            );
            
            UI.showToast('Failed to send message', 'error');
            UI.enableInput();
        }
    }
    
    static async handleNewChat() {
        if (confirm('Start a new conversation? Current chat will be cleared.')) {
            // Reset state
            State.messageCount = 0;
            State.confidenceScores = [];
            
            // Create new session
            await this.createSession();
            
            // Reset UI
            UI.showWelcomeScreen();
            UI.updateStats();
            UI.clearInput();
            
            UI.showToast('New conversation started', 'success');
        }
    }
    
    static async handleVoiceToggle() {
        if (!this.audioRecorder) {
            this.audioRecorder = new AudioRecorder();
        }
        
        if (this.audioRecorder.isRecording) {
            // Stop recording and send
            await this.stopVoiceRecording();
        } else {
            // Start recording
            await this.startVoiceRecording();
        }
    }
    
    static async startVoiceRecording() {
        try {
            await this.audioRecorder.startRecording();
            
            // Update UI
            DOM.voiceBtn.classList.add('recording');
            DOM.voiceBtn.innerHTML = '<i class="fas fa-stop"></i>';
            DOM.voiceBtn.style.background = 'linear-gradient(135deg, #dc143c 0%, #ff6b6b 100%)';
            
            UI.showToast('🎤 Recording... Click again to send', 'info');
            
        } catch (error) {
            console.error('Failed to start recording:', error);
            UI.showToast('Microphone access denied', 'error');
        }
    }
    
    static async stopVoiceRecording() {
        try {
            // Reset button UI
            DOM.voiceBtn.classList.remove('recording');
            DOM.voiceBtn.innerHTML = '<i class="fas fa-microphone"></i>';
            DOM.voiceBtn.style.background = '';
            
            // Stop recording and get audio
            const audioBlob = await this.audioRecorder.stopRecording();
            
            UI.showToast('Processing voice...', 'info');
            UI.disableInput();
            
            // Add visual indicator
            UI.addMessage('🎤 Voice message', 'user');
            UI.showTypingIndicator();
            
            try {
                // Send to API
                const response = await ChatAPI.sendVoiceMessage(audioBlob, State.sessionId);
                
                setTimeout(() => {
                    UI.hideTypingIndicator();
                    
                    // Add transcription message
                    if (response.metadata && response.metadata.transcribed_text) {
                        const transcribedDiv = document.createElement('div');
                        transcribedDiv.className = 'message-meta';
                        transcribedDiv.innerHTML = `
                            <small style="opacity: 0.7;">
                                Heard: "${response.metadata.transcribed_text}"
                            </small>
                        `;
                        const lastMessage = DOM.messagesContainer.lastElementChild;
                        if (lastMessage) {
                            lastMessage.querySelector('.message-content').appendChild(transcribedDiv);
                        }
                    }
                    
                    // Add bot response
                    UI.addMessage(response.response_text, 'bot', {
                        translation: response.response_translation,
                        confidence: response.confidence,
                        intent_name: response.intent_name
                    });
                    
                    // Play TTS response
                    if (response.response_text) {
                        TextToSpeech.speak(response.response_text);
                    }
                    
                    // Update stats
                    State.messageCount++;
                    if (response.confidence) {
                        State.confidenceScores.push(response.confidence);
                    }
                    UI.updateStats();
                    
                    UI.enableInput();
                    
                }, CONFIG.TYPING_DELAY);
                
            } catch (error) {
                UI.hideTypingIndicator();
                UI.addMessage(
                    'Sorry, I had trouble understanding. Please try again.',
                    'bot'
                );
                UI.showToast('Voice processing failed', 'error');
                UI.enableInput();
            }
            
        } catch (error) {
            console.error('Error stopping recording:', error);
            UI.showToast('Recording error', 'error');
            DOM.voiceBtn.classList.remove('recording');
            DOM.voiceBtn.innerHTML = '<i class="fas fa-microphone"></i>';
            DOM.voiceBtn.style.background = '';
        }
    }
}

// ============================================
// UTILITY FUNCTIONS
// ============================================
const Utils = {
    formatTimestamp(date) {
        return new Date(date).toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit'
        });
    },
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },
    
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            UI.showToast('Copied to clipboard', 'success');
        } catch (error) {
            console.error('Failed to copy:', error);
            UI.showToast('Failed to copy', 'error');
        }
    }
};

// ============================================
// ERROR HANDLING
// ============================================
window.addEventListener('error', (event) => {
    console.error('Global error:', event.error);
    UI.showToast('An unexpected error occurred', 'error');
});

window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', event.reason);
    UI.showToast('An unexpected error occurred', 'error');
});

// ============================================
// INITIALIZATION
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, initializing chatbot...');
    ChatController.initialize();
});

// Add to window for debugging
window.ChatApp = {
    State,
    API: ChatAPI,
    UI,
    Controller: ChatController,
    Utils
};

console.log('🇰🇪 Kikuyu Chatbot loaded. Access via window.ChatApp for debugging.');
