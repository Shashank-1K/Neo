/**
 * NEXUS — AI Workspace Assistant
 * Complete Frontend Application
 */

// ═══════════════════════════════════════
//  STATE MANAGEMENT
// ═══════════════════════════════════════

const state = {
    currentMode: 'chat',
    currentConversationId: null,
    conversations: [],
    isLoading: false,
    isRecording: false,
    mediaRecorder: null,
    audioChunks: [],
    attachments: [],
    settings: {
        systemPrompt: 'You are NEXUS, an advanced AI workspace assistant. You are helpful, knowledgeable, and capable.',
        temperature: 0.7,
        maxTokens: 4096,
        safetyEnabled: true,
        streamEnabled: true,
    },
};

// ═══════════════════════════════════════
//  DOM REFERENCES
// ═══════════════════════════════════════

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

const dom = {
    sidebar: $('#sidebar'),
    messagesList: $('#messagesList'),
    messagesArea: $('#messagesArea'),
    welcomeScreen: $('#welcomeScreen'),
    messageInput: $('#messageInput'),
    sendBtn: $('#sendBtn'),
    modelSelect: $('#modelSelect'),
    currentMode: $('#currentMode'),
    conversationsList: $('#conversationsList'),
    latencyBadge: $('#latencyBadge'),
    latencyValue: $('#latencyValue'),
    voiceControls: $('#voiceControls'),
    textInputArea: $('#textInputArea'),
    recordBtn: $('#recordBtn'),
    voiceStatus: $('#voiceStatus'),
    voiceSelect: $('#voiceSelect'),
    attachmentPreview: $('#attachmentPreview'),
    attachmentList: $('#attachmentList'),
    fileInput: $('#fileInput'),
};

// ═══════════════════════════════════════
//  API CLIENT
// ═══════════════════════════════════════

const API = {
    baseUrl: '',

    async post(endpoint, data, isFormData = false) {
        const options = {
            method: 'POST',
            ...(isFormData
                ? { body: data }
                : {
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data),
                }),
        };

        const response = await fetch(`${this.baseUrl}${endpoint}`, options);
        if (!response.ok) {
            const err = await response.json().catch(() => ({ detail: response.statusText }));
            throw new Error(err.detail || 'API Error');
        }
        return response;
    },

    async get(endpoint) {
        const response = await fetch(`${this.baseUrl}${endpoint}`);
        if (!response.ok) throw new Error('API Error');
        return response.json();
    },

    async delete(endpoint) {
        const response = await fetch(`${this.baseUrl}${endpoint}`, { method: 'DELETE' });
        return response.json();
    },

    // Chat
    async chat(message, conversationId, model, images = []) {
        const data = {
            message,
            conversation_id: conversationId,
            model,
            system_prompt: state.settings.systemPrompt,
            temperature: state.settings.temperature,
            max_tokens: state.settings.maxTokens,
            images: images.length > 0 ? images : undefined,
        };
        const resp = await this.post('/api/chat/', data);
        return resp.json();
    },

    async chatStream(message, conversationId, model) {
        const data = {
            message,
            conversation_id: conversationId,
            model,
            system_prompt: state.settings.systemPrompt,
            temperature: state.settings.temperature,
            max_tokens: state.settings.maxTokens,
        };
        return this.post('/api/chat/stream', data);
    },

    // Research
    async research(query, model = 'compound') {
        const resp = await this.post('/api/research/', { query, model, include_citations: true });
        return resp.json();
    },

    // Code
    async generateCode(prompt, language = 'python', execute = false) {
        const resp = await this.post('/api/code/generate', { prompt, language, execute, model: 'coding' });
        return resp.json();
    },

    async executeCode(code, language = 'python') {
        const resp = await this.post(`/api/code/execute?code=${encodeURIComponent(code)}&language=${language}`, {});
        return resp.json();
    },

    // Math
    async solveMath(query) {
        const resp = await this.post('/api/math/solve', { query, use_wolfram: true });
        return resp.json();
    },

    // Voice
    async transcribe(audioBlob) {
        const formData = new FormData();
        formData.append('file', audioBlob, 'recording.wav');
        const resp = await this.post('/api/voice/transcribe', formData, true);
        return resp.json();
    },

    async speak(text, voice = 'Fritz-PlayAI') {
        const resp = await this.post('/api/voice/speak', { text, voice });
        return resp.blob();
    },

    async voicePipeline(audioBlob, conversationId, model, voice) {
        const formData = new FormData();
        formData.append('file', audioBlob, 'recording.wav');
        if (conversationId) formData.append('conversation_id', conversationId);
        formData.append('model', model);
        formData.append('voice', voice);
        formData.append('system_prompt', state.settings.systemPrompt);
        const resp = await this.post('/api/voice/pipeline', formData, true);
        return resp.json();
    },

    // Vision
    async analyzeImage(imageBase64, prompt = 'Describe this image in detail') {
        const resp = await this.post('/api/vision/analyze', {
            prompt,
            image_base64: imageBase64,
            model: 'vision_scout',
        });
        return resp.json();
    },

    // Structured Data
    async extractStructured(content, preset) {
        const resp = await this.post(
            `/api/structured/extract-preset?content=${encodeURIComponent(content)}&preset=${preset}&model=general`,
            {}
        );
        return resp.json();
    },

    // Conversations
    async getConversations() {
        return this.get('/api/conversations/');
    },

    async getConversation(id) {
        return this.get(`/api/conversations/${id}`);
    },

    async deleteConversation(id) {
        return this.delete(`/api/conversations/${id}`);
    },

    async newConversation() {
        const resp = await this.post('/api/conversations/new?model=general', {});
        return resp.json();
    },

    // Health
    async getHealth() {
        return this.get('/api/workspace/health');
    },

    async getUsage() {
        return this.get('/api/workspace/usage');
    },
};

// ═══════════════════════════════════════
//  UI RENDERING
// ═══════════════════════════════════════

function renderMessage(role, content, meta = {}) {
    const div = document.createElement('div');
    div.className = `message message-${role}`;

    const icon = role === 'user' ? 'fa-user' : 'fa-atom';
    const name = role === 'user' ? 'You' : 'NEXUS';

    // Process markdown-like formatting
    const formatted = formatContent(content);

    div.innerHTML = `
        <div class="message-avatar">
            <i class="fas ${icon}"></i>
        </div>
        <div class="message-body">
            <div class="message-sender">${name}</div>
            <div class="message-content">${formatted}</div>
            ${meta.model || meta.latency ? `
                <div class="message-meta">
                    ${meta.model ? `<span><i class="fas fa-microchip"></i> ${meta.model}</span>` : ''}
                    ${meta.latency ? `<span><i class="fas fa-bolt"></i> ${Math.round(meta.latency)}ms</span>` : ''}
                    ${meta.tokens ? `<span><i class="fas fa-coins"></i> ${meta.tokens} tokens</span>` : ''}
                </div>
            ` : ''}
        </div>
    `;

    dom.messagesList.appendChild(div);
    scrollToBottom();
    return div;
}

function renderStreamMessage() {
    const div = document.createElement('div');
    div.className = 'message message-assistant';
    div.id = 'streamingMessage';

    div.innerHTML = `
        <div class="message-avatar">
            <i class="fas fa-atom"></i>
        </div>
        <div class="message-body">
            <div class="message-sender">NEXUS</div>
            <div class="message-content" id="streamContent"></div>
        </div>
    `;

    dom.messagesList.appendChild(div);
    scrollToBottom();
    return div;
}

function showLoading() {
    const div = document.createElement('div');
    div.className = 'message message-assistant';
    div.id = 'loadingMessage';

    div.innerHTML = `
        <div class="message-avatar">
            <i class="fas fa-atom"></i>
        </div>
        <div class="message-body">
            <div class="message-sender">NEXUS</div>
            <div class="typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        </div>
    `;

    dom.messagesList.appendChild(div);
    scrollToBottom();
}

function hideLoading() {
    const el = $('#loadingMessage');
    if (el) el.remove();
}

function scrollToBottom() {
    dom.messagesArea.scrollTop = dom.messagesArea.scrollHeight;
}

function formatContent(text) {
    if (!text) return '';

    // Escape HTML
    let html = text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');

    // Code blocks
    html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (_, lang, code) => {
        return `<pre><code class="language-${lang}">${code.trim()}</code></pre>`;
    });

    // Inline code
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

    // Bold
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

    // Italic
    html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');

    // Line breaks
    html = html.replace(/\n/g, '<br>');

    return html;
}

function showLatency(ms) {
    dom.latencyBadge.style.display = 'flex';
    dom.latencyValue.textContent = Math.round(ms);
}

// ═══════════════════════════════════════
//  CONVERSATIONS
// ═══════════════════════════════════════

async function loadConversations() {
    try {
        state.conversations = await API.getConversations();
        renderConversationsList();
    } catch (e) {
        console.error('Failed to load conversations:', e);
    }
}

function renderConversationsList() {
    const container = dom.conversationsList;
    const label = container.querySelector('.section-label');

    // Remove old items but keep label
    container.querySelectorAll('.conv-item').forEach(el => el.remove());

    state.conversations.forEach(conv => {
        const div = document.createElement('div');
        div.className = `conv-item ${conv.id === state.currentConversationId ? 'active' : ''}`;
        div.innerHTML = `
            <i class="fas fa-message"></i>
            <span class="conv-item-text">${conv.title || 'New Conversation'}</span>
            <button class="conv-item-delete" title="Delete">
                <i class="fas fa-trash"></i>
            </button>
        `;

        div.addEventListener('click', (e) => {
            if (!e.target.closest('.conv-item-delete')) {
                loadConversation(conv.id);
            }
        });

        div.querySelector('.conv-item-delete').addEventListener('click', async (e) => {
            e.stopPropagation();
            await API.deleteConversation(conv.id);
            if (state.currentConversationId === conv.id) {
                state.currentConversationId = null;
                dom.messagesList.innerHTML = '';
                dom.welcomeScreen.style.display = 'flex';
            }
            loadConversations();
        });

        container.appendChild(div);
    });
}

async function loadConversation(conversationId) {
    try {
        const data = await API.getConversation(conversationId);
        state.currentConversationId = conversationId;

        dom.welcomeScreen.style.display = 'none';
        dom.messagesList.innerHTML = '';

        data.messages.forEach(msg => {
            renderMessage(msg.role, msg.content, {
                model: msg.model_used,
                latency: msg.latency_ms,
                tokens: msg.tokens_used,
            });
        });

        renderConversationsList();
    } catch (e) {
        console.error('Failed to load conversation:', e);
    }
}

async function startNewChat() {
    state.currentConversationId = null;
    dom.messagesList.innerHTML = '';
    dom.welcomeScreen.style.display = 'flex';
    dom.messageInput.focus();
    renderConversationsList();
}

// ═══════════════════════════════════════
//  MESSAGE SENDING
// ═══════════════════════════════════════

async function sendMessage() {
    const message = dom.messageInput.value.trim();
    if (!message && state.attachments.length === 0) return;
    if (state.isLoading) return;

    const model = dom.modelSelect.value;
    state.isLoading = true;
    dom.sendBtn.disabled = true;
    dom.messageInput.value = '';
    autoResizeTextarea();

    // Hide welcome screen
    dom.welcomeScreen.style.display = 'none';

    // Get image attachments as base64
    const images = [];
    for (const att of state.attachments) {
        if (att.type.startsWith('image/')) {
            images.push(att.base64);
        }
    }
    clearAttachments();

    // Render user message
    renderMessage('user', message);

    try {
        let result;

        // Route based on mode
        switch (state.currentMode) {
            case 'research':
                showLoading();
                result = await API.research(message, 'compound');
                hideLoading();
                renderMessage('assistant', result.response, {
                    model: result.model_used,
                    latency: result.latency_ms,
                });
                if (result.citations && result.citations.length > 0) {
                    renderMessage('assistant', '📚 **Citations:**\n' +
                        result.citations.map((c, i) => `${i + 1}. ${JSON.stringify(c)}`).join('\n'));
                }
                break;

            case 'code':
                showLoading();
                result = await API.generateCode(message, 'python', model === 'compound');
                hideLoading();
                renderMessage('assistant', result.code || result.content, {
                    model: result.model_used,
                    latency: result.latency_ms,
                });
                break;

            case 'math':
                showLoading();
                result = await API.solveMath(message);
                hideLoading();
                renderMessage('assistant', result.solution, {
                    model: result.model_used,
                    latency: result.latency_ms,
                });
                break;

            default:
                // Standard chat
                if (state.settings.streamEnabled && images.length === 0) {
                    // Streaming response
                    const response = await API.chatStream(message, state.currentConversationId, model);
                    renderStreamMessage();
                    const streamContent = $('#streamContent');
                    const reader = response.body.getReader();
                    const decoder = new TextDecoder();
                    let fullText = '';

                    while (true) {
                        const { done, value } = await reader.read();
                        if (done) break;

                        const text = decoder.decode(value, { stream: true });
                        const lines = text.split('\n');

                        for (const line of lines) {
                            if (line.startsWith('data: ')) {
                                try {
                                    const data = JSON.parse(line.slice(6));
                                    if (data.content) {
                                        fullText += data.content;
                                        streamContent.innerHTML = formatContent(fullText);
                                        scrollToBottom();
                                    }
                                    if (data.done) {
                                        state.currentConversationId = data.conversation_id;
                                    }
                                } catch (e) { /* ignore parse errors in stream */ }
                            }
                        }
                    }

                    // Remove streaming message ID
                    const streamMsg = $('#streamingMessage');
                    if (streamMsg) streamMsg.removeAttribute('id');

                } else {
                    // Non-streaming or vision
                    showLoading();
                    result = await API.chat(message, state.currentConversationId, model, images);
                    hideLoading();
                    state.currentConversationId = result.conversation_id;
                    renderMessage('assistant', result.response, {
                        model: result.model_used,
                        latency: result.latency_ms,
                        tokens: result.tokens_used,
                    });
                    showLatency(result.latency_ms);
                }
                break;
        }

        loadConversations();

    } catch (error) {
        hideLoading();
        renderMessage('assistant', `❌ **Error:** ${error.message}`);
        console.error('Send error:', error);
    } finally {
        state.isLoading = false;
        dom.sendBtn.disabled = false;
        dom.messageInput.focus();
    }
}

// ═══════════════════════════════════════
//  VOICE HANDLING
// ═══════════════════════════════════════

async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        state.mediaRecorder = new MediaRecorder(stream);
        state.audioChunks = [];

        state.mediaRecorder.ondataavailable = (e) => {
            if (e.data.size > 0) {
                state.audioChunks.push(e.data);
            }
        };

        state.mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(state.audioChunks, { type: 'audio/wav' });
            stream.getTracks().forEach(t => t.stop());
            await processVoiceInput(audioBlob);
        };

        state.mediaRecorder.start();
        state.isRecording = true;
        dom.recordBtn.classList.add('recording');
        dom.voiceStatus.textContent = '🔴 Recording...';
    } catch (e) {
        console.error('Microphone error:', e);
        dom.voiceStatus.textContent = '❌ Microphone access denied';
    }
}

function stopRecording() {
    if (state.mediaRecorder && state.isRecording) {
        state.mediaRecorder.stop();
        state.isRecording = false;
        dom.recordBtn.classList.remove('recording');
        dom.voiceStatus.textContent = '⏳ Processing...';
    }
}

async function processVoiceInput(audioBlob) {
    try {
        const model = dom.modelSelect.value;
        const voice = dom.voiceSelect.value;

        dom.welcomeScreen.style.display = 'none';

        const result = await API.voicePipeline(
            audioBlob,
            state.currentConversationId,
            model,
            voice
        );

        state.currentConversationId = result.conversation_id;

        // Show messages
        renderMessage('user', `🎤 ${result.user_text}`);
        renderMessage('assistant', result.response_text, {
            model: result.model_used,
            latency: result.latency.total_ms,
        });

        // Play audio response
        if (result.audio_base64) {
            const audio = new Audio(`data:audio/wav;base64,${result.audio_base64}`);
            audio.play().catch(console.error);
        }

        dom.voiceStatus.textContent = 'Press & hold to talk';
        showLatency(result.latency.total_ms);
        loadConversations();

    } catch (error) {
        console.error('Voice pipeline error:', error);
        dom.voiceStatus.textContent = `❌ ${error.message}`;
        renderMessage('assistant', `❌ Voice error: ${error.message}`);
    }
}

// ═══════════════════════════════════════
//  FILE ATTACHMENTS
// ═══════════════════════════════════════

function handleFileSelect(files) {
    for (const file of files) {
        const reader = new FileReader();
        reader.onload = (e) => {
            const base64 = e.target.result.split(',')[1];
            state.attachments.push({
                file,
                name: file.name,
                type: file.type,
                base64,
                preview: file.type.startsWith('image/') ? e.target.result : null,
            });
            renderAttachments();
        };
        reader.readAsDataURL(file);
    }
}

function renderAttachments() {
    if (state.attachments.length === 0) {
        dom.attachmentPreview.style.display = 'none';
        return;
    }

    dom.attachmentPreview.style.display = 'block';
    dom.attachmentList.innerHTML = state.attachments.map((att, i) => `
        <div class="attachment-item">
            ${att.preview ? `<img src="${att.preview}" alt="${att.name}">` : `<i class="fas fa-file"></i>`}
            <span>${att.name}</span>
            <button class="remove-attachment" onclick="removeAttachment(${i})">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `).join('');
}

function removeAttachment(index) {
    state.attachments.splice(index, 1);
    renderAttachments();
}

function clearAttachments() {
    state.attachments = [];
    renderAttachments();
    dom.fileInput.value = '';
}

// ═══════════════════════════════════════
//  MODE SWITCHING
// ═══════════════════════════════════════

function setMode(mode) {
    state.currentMode = mode;

    // Update mode buttons
    $$('.mode-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.mode === mode);
    });

    // Update mode indicator
    const modeConfig = {
        chat: { icon: 'fa-comments', label: 'Chat', placeholder: 'Message NEXUS...' },
        voice: { icon: 'fa-microphone', label: 'Voice', placeholder: 'Use the microphone...' },
        vision: { icon: 'fa-eye', label: 'Vision', placeholder: 'Describe what to analyze...' },
        research: { icon: 'fa-search', label: 'Research', placeholder: 'What should I research?' },
        code: { icon: 'fa-code', label: 'Code', placeholder: 'Describe what code to write...' },
        math: { icon: 'fa-calculator', label: 'Math', placeholder: 'Enter a math/science problem...' },
        data: { icon: 'fa-database', label: 'Data', placeholder: 'Paste data to structure...' },
    };

    const config = modeConfig[mode] || modeConfig.chat;
    dom.currentMode.innerHTML = `<i class="fas ${config.icon}"></i> ${config.label}`;
    dom.messageInput.placeholder = config.placeholder;

    // Toggle voice/text controls
    if (mode === 'voice') {
        dom.voiceControls.style.display = 'flex';
        dom.textInputArea.style.display = 'none';
    } else {
        dom.voiceControls.style.display = 'none';
        dom.textInputArea.style.display = 'flex';
    }

    // Auto-select appropriate model
    if (mode === 'research') {
        dom.modelSelect.value = 'compound';
    } else if (mode === 'code') {
        dom.modelSelect.value = 'coding';
    } else if (mode === 'math') {
        dom.modelSelect.value = 'compound';
    } else if (mode === 'vision') {
        dom.modelSelect.value = 'general';
    }
}

// ═══════════════════════════════════════
//  MODALS
// ═══════════════════════════════════════

function openModal(id) {
    document.getElementById(id).style.display = 'flex';
}

function closeModal(id) {
    document.getElementById(id).style.display = 'none';
}

async function showHealth() {
    openModal('healthModal');
    const content = $('#healthContent');
    content.innerHTML = 'Loading...';

    try {
        const health = await API.getHealth();
        const usage = await API.getUsage();

        let html = '<h3 style="margin-bottom:12px">API Key Status</h3>';
        health.api_keys.forEach(key => {
            const status = key.is_available ? 'healthy' : (key.consecutive_failures > 3 ? 'down' : 'degraded');
            html += `
                <div class="health-card">
                    <div class="health-card-header">
                        <span class="key-name">${key.key_prefix}</span>
                        <span class="health-status ${status}"></span>
                    </div>
                    <div class="health-stats">
                        <span>Requests: ${key.total_requests}</span>
                        <span>Failures: ${key.failed_requests}</span>
                        <span>Rate: ${key.failure_rate}</span>
                    </div>
                </div>
            `;
        });

        if (usage.usage && usage.usage.length > 0) {
            html += '<h3 style="margin:16px 0 12px">Usage Stats</h3>';
            usage.usage.forEach(u => {
                html += `
                    <div class="health-card">
                        <div class="health-card-header">
                            <span class="key-name">${u.model}</span>
                            <span style="font-size:11px;color:var(--text-tertiary)">${u.operation}</span>
                        </div>
                        <div class="health-stats">
                            <span>Calls: ${u.total_calls}</span>
                            <span>Avg: ${Math.round(u.avg_latency_ms)}ms</span>
                            <span>Tokens: ${(u.total_input_tokens || 0) + (u.total_output_tokens || 0)}</span>
                        </div>
                    </div>
                `;
            });
        }

        content.innerHTML = html;
    } catch (e) {
        content.innerHTML = `<p style="color:var(--danger)">Error: ${e.message}</p>`;
    }
}

// ═══════════════════════════════════════
//  TEXTAREA AUTO-RESIZE
// ═══════════════════════════════════════

function autoResizeTextarea() {
    const ta = dom.messageInput;
    ta.style.height = 'auto';
    ta.style.height = Math.min(ta.scrollHeight, 200) + 'px';
}

// ═══════════════════════════════════════
//  EVENT LISTENERS
// ═══════════════════════════════════════

function initEventListeners() {
    // Send message
    dom.sendBtn.addEventListener('click', sendMessage);

    dom.messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    dom.messageInput.addEventListener('input', autoResizeTextarea);

    // New chat
    $('#newChatBtn').addEventListener('click', startNewChat);

    // Mode switching
    $$('.mode-btn').forEach(btn => {
        btn.addEventListener('click', () => setMode(btn.dataset.mode));
    });

    // Capability cards
    $$('.cap-card').forEach(card => {
        card.addEventListener('click', () => setMode(card.dataset.mode));
    });

    // Voice recording
    dom.recordBtn.addEventListener('mousedown', startRecording);
    dom.recordBtn.addEventListener('mouseup', stopRecording);
    dom.recordBtn.addEventListener('mouseleave', () => {
        if (state.isRecording) stopRecording();
    });
    dom.recordBtn.addEventListener('touchstart', (e) => {
        e.preventDefault();
        startRecording();
    });
    dom.recordBtn.addEventListener('touchend', (e) => {
        e.preventDefault();
        stopRecording();
    });

    // File attachment
    $('#attachBtn').addEventListener('click', () => dom.fileInput.click());
    dom.fileInput.addEventListener('change', (e) => {
        handleFileSelect(e.target.files);
    });

    // Drag and drop
    dom.messagesArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        dom.messagesArea.style.border = '2px dashed var(--accent-primary)';
    });

    dom.messagesArea.addEventListener('dragleave', () => {
        dom.messagesArea.style.border = 'none';
    });

    dom.messagesArea.addEventListener('drop', (e) => {
        e.preventDefault();
        dom.messagesArea.style.border = 'none';
        if (e.dataTransfer.files.length > 0) {
            handleFileSelect(e.dataTransfer.files);
        }
    });

    // Settings
    $('#settingsBtn').addEventListener('click', () => openModal('settingsModal'));

    // Save settings on change
    $('#systemPrompt').addEventListener('input', (e) => {
        state.settings.systemPrompt = e.target.value;
    });
    $('#temperature').addEventListener('input', (e) => {
        state.settings.temperature = parseFloat(e.target.value);
    });
    $('#maxTokens').addEventListener('input', (e) => {
        state.settings.maxTokens = parseInt(e.target.value);
    });
    $('#safetyEnabled').addEventListener('change', (e) => {
        state.settings.safetyEnabled = e.target.checked;
    });
    $('#streamEnabled').addEventListener('change', (e) => {
        state.settings.streamEnabled = e.target.checked;
    });

    // Health
    $('#healthBtn').addEventListener('click', showHealth);

    // Sidebar toggle
    $('#sidebarToggle').addEventListener('click', () => {
        dom.sidebar.classList.toggle('open');
    });

    // Close modals on overlay click
    $$('.modal-overlay').forEach(overlay => {
        overlay.addEventListener('click', () => {
            overlay.closest('.modal').style.display = 'none';
        });
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        // Ctrl+N: New chat
        if (e.ctrlKey && e.key === 'n') {
            e.preventDefault();
            startNewChat();
        }
        // Ctrl+K: Focus search/input
        if (e.ctrlKey && e.key === 'k') {
            e.preventDefault();
            dom.messageInput.focus();
        }
        // Escape: Close modals
        if (e.key === 'Escape') {
            $$('.modal').forEach(m => m.style.display = 'none');
        }
    });

    // Paste images
    document.addEventListener('paste', (e) => {
        const items = e.clipboardData?.items;
        if (!items) return;

        for (const item of items) {
            if (item.type.startsWith('image/')) {
                e.preventDefault();
                const file = item.getAsFile();
                if (file) handleFileSelect([file]);
            }
        }
    });
}

// ═══════════════════════════════════════
//  INITIALIZATION
// ═══════════════════════════════════════

async function init() {
    console.log('🚀 NEXUS AI Workspace initializing...');

    initEventListeners();
    await loadConversations();

    // Set initial mode
    setMode('chat');

    // Focus input
    dom.messageInput.focus();

    console.log('✅ NEXUS ready!');
}

// Make functions globally available for inline handlers
window.closeModal = closeModal;
window.removeAttachment = removeAttachment;

// Start the app
document.addEventListener('DOMContentLoaded', init);