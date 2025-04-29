<script>
// Initialize chat history
let chatHistory = [];
let currentChatId = Date.now().toString();

// Fetch models on page load
document.addEventListener('DOMContentLoaded', function() {
    // Fetch models
    fetch('/api/models')
        .then(response => response.json())
        .then(data => {
            const modelList = document.getElementById('modelList');
            const modelSelect = document.getElementById('modelSelect');
            
            if (data.models && data.models.length > 0) {
                let html = '';
                data.models.forEach(model => {
                    html += `<div class="model-item">
                        <div class="model-info">
                            <strong>${model.path.split('/').pop()}</strong><br>
                            <small>
                                Type: ${model.type}${model.family ? ' | Family: ' + model.family : ''} | 
                                Format: ${model.format || 'Unknown'} | Size: ${model.size_mb} MB
                            </small>
                        </div>
                    </div>`;
                    
                    const option = document.createElement('option');
                    option.value = model.path;
                    option.textContent = model.path.split('/').pop();
                    modelSelect.appendChild(option);
                });
                modelList.innerHTML = html;
                
                // Try to load saved chat history
                loadChatHistory();
            } else {
                modelList.innerHTML = 'No models found. Download models using: <code>./llm.sh download</code>';
            }
        })
        .catch(error => {
            document.getElementById('modelList').innerHTML = 'Error loading models: ' + error.message;
        });
    
    // Set up event listeners
    document.getElementById('sendBtn').addEventListener('click', sendMessage);
    document.getElementById('newChatBtn').addEventListener('click', newChat);
    document.getElementById('exportChatBtn').addEventListener('click', exportChat);
    
    // Allow pressing Enter to send message
    document.getElementById('userInput').addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
});

// Load chat history from localStorage if available
function loadChatHistory() {
    const savedHistory = localStorage.getItem('llm_chat_history');
    if (savedHistory) {
        try {
            const savedData = JSON.parse(savedHistory);
            if (savedData.currentChatId && savedData.chats && savedData.chats[savedData.currentChatId]) {
                currentChatId = savedData.currentChatId;
                chatHistory = savedData.chats[currentChatId] || [];
                renderChatHistory();
            }
        } catch (e) {
            console.error('Error loading chat history:', e);
        }
    }
}

// Save chat history to localStorage
function saveChatHistory() {
    try {
        const allChats = JSON.parse(localStorage.getItem('llm_chats') || '{}');
        allChats[currentChatId] = chatHistory;
        localStorage.setItem('llm_chats', JSON.stringify(allChats));
        localStorage.setItem('llm_chat_history', JSON.stringify({
            currentChatId,
            chats: { [currentChatId]: chatHistory }
        }));
    } catch (e) {
        console.error('Error saving chat history:', e);
    }
}

// Render chat history in the UI
function renderChatHistory() {
    const chatHistoryDiv = document.getElementById('chatHistory');
    if (!chatHistory || chatHistory.length === 0) {
        chatHistoryDiv.innerHTML = '<div class="empty-chat">No messages yet. Start a conversation!</div>';
        return;
    }
    
    let html = '';
    chatHistory.forEach(message => {
        const timestamp = new Date(message.timestamp).toLocaleTimeString();
        if (message.role === 'user') {
            html += `
                <div class="chat-message">
                    <div class="message-user">${escapeHtml(message.content)}</div>
                    <div class="message-meta">${timestamp}</div>
                </div>
            `;
        } else if (message.role === 'assistant') {
            html += `
                <div class="chat-message">
                    <div class="message-assistant">${escapeHtml(message.content)}</div>
                    <div class="message-meta">${timestamp}</div>
                </div>
            `;
        }
    });
    
    chatHistoryDiv.innerHTML = html;
    
    // Scroll to bottom
    chatHistoryDiv.scrollTop = chatHistoryDiv.scrollHeight;
}

// Helper function to escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Add message to chat history
function addMessageToHistory(role, content) {
    chatHistory.push({
        role,
        content,
        timestamp: Date.now()
    });
    saveChatHistory();
    renderChatHistory();
}

// Handle send button click
function sendMessage() {
    const modelPath = document.getElementById('modelSelect').value;
    const userInput = document.getElementById('userInput').value;
    const systemInput = document.getElementById('systemInput').value;
    const temperature = parseFloat(document.getElementById('temperature').value);
    const maxTokens = parseInt(document.getElementById('maxTokens').value);
    const topP = parseFloat(document.getElementById('topP').value);
    const freqPenalty = parseFloat(document.getElementById('freqPenalty').value);
    const spinner = document.getElementById('spinner');
    const statsDiv = document.getElementById('stats');
    
    if (!modelPath) {
        alert('Please select a model first');
        return;
    }
    
    if (!userInput.trim()) {
        alert('Please enter a message');
        return;
    }
    
    // Add user message to chat history
    addMessageToHistory('user', userInput);
    
    // Clear input field
    document.getElementById('userInput').value = '';
    
    // Show spinner
    spinner.style.display = 'inline-block';
    statsDiv.style.display = 'none';
    
    // Disable send button while processing
    document.getElementById('sendBtn').disabled = true;
    
    // Prepare conversation history for context
    const messages = chatHistory.map(msg => ({
        role: msg.role,
        content: msg.content
    }));
    
    // Send request to API
    fetch('/api/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            model: modelPath,
            message: userInput,
            system: systemInput,
            temperature: temperature,
            max_tokens: maxTokens,
            top_p: topP,
            frequency_penalty: freqPenalty,
            history: messages
        })
    })
    .then(response => response.json())
    .then(data => {
        // Hide spinner
        spinner.style.display = 'none';
        
        if (data.error) {
            // Add error message to chat
            addMessageToHistory('assistant', 'Error: ' + data.error);
        } else {
            // Add assistant message to chat history
            addMessageToHistory('assistant', data.response || 'No response from model');
            
            // Show stats if available
            if (data.time_taken || data.tokens_generated) {
                statsDiv.style.display = 'block';
                let statsText = `Generation time: ${data.time_taken}s | Tokens: ${data.tokens_generated}`;
                
                // Add model type and format if available
                if (data.model_type) {
                    statsText += ` | Type: ${data.model_type}`;
                }
                if (data.model_format) {
                    statsText += ` | Format: ${data.model_format}`;
                }
                
                statsDiv.textContent = statsText;
            }
        }
        
        // Re-enable send button
        document.getElementById('sendBtn').disabled = false;
    })
    .catch(error => {
        spinner.style.display = 'none';
        addMessageToHistory('assistant', 'Error: ' + error.message);
        document.getElementById('sendBtn').disabled = false;
    });
}

// Handle new chat button
function newChat() {
    if (confirm('Start a new chat? This will clear the current conversation.')) {
        chatHistory = [];
        currentChatId = Date.now().toString();
        saveChatHistory();
        renderChatHistory();
        document.getElementById('userInput').value = '';
        document.getElementById('systemInput').value = '';
        document.getElementById('stats').style.display = 'none';
    }
}

// Handle export chat button
function exportChat() {
    if (chatHistory.length === 0) {
        alert('No chat to export');
        return;
    }
    
    const exportData = {
        timestamp: Date.now(),
        model: document.getElementById('modelSelect').value,
        systemPrompt: document.getElementById('systemInput').value,
        messages: chatHistory
    };
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `chat_export_${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}
</script>