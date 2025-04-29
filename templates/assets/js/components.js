/**
 * Component Controllers for LLM Interface
 * Handles UI component interactions and state management
 */

// Use namespaces to avoid global scope pollution
window.LLM = window.LLM || {};

LLM.Components = {
    /**
     * Chat Interface Component Controller
     */
    ChatInterface: {
        // Properties
        chatHistory: [],
        currentChatId: Date.now().toString(),
        
        // Initialize the component
        init: function() {
            // Setup event listeners
            const sendButton = document.getElementById('sendBtn');
            const userInput = document.getElementById('userInput');
            const newChatButton = document.getElementById('newChatBtn');
            const exportChatButton = document.getElementById('exportChatBtn');
            
            if (sendButton) {
                sendButton.addEventListener('click', this.sendMessage.bind(this));
            }
            
            if (userInput) {
                userInput.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        this.sendMessage();
                    }
                });
            }
            
            if (newChatButton) {
                newChatButton.addEventListener('click', this.newChat.bind(this));
            }
            
            if (exportChatButton) {
                exportChatButton.addEventListener('click', this.exportChat.bind(this));
            }
            
            // Load saved chat history
            this.loadChatHistory();
        },
        
        // Load chat history from localStorage
        loadChatHistory: function() {
            const savedHistory = localStorage.getItem('llm_chat_history');
            if (savedHistory) {
                try {
                    const savedData = JSON.parse(savedHistory);
                    if (savedData.currentChatId && savedData.chats && savedData.chats[savedData.currentChatId]) {
                        this.currentChatId = savedData.currentChatId;
                        this.chatHistory = savedData.chats[this.currentChatId] || [];
                        this.renderChatHistory();
                    }
                } catch (e) {
                    console.error('Error loading chat history:', e);
                }
            }
        },
        
        // Save chat history to localStorage
        saveChatHistory: function() {
            try {
                const allChats = JSON.parse(localStorage.getItem('llm_chats') || '{}');
                allChats[this.currentChatId] = this.chatHistory;
                localStorage.setItem('llm_chats', JSON.stringify(allChats));
                localStorage.setItem('llm_chat_history', JSON.stringify({
                    currentChatId: this.currentChatId,
                    chats: { [this.currentChatId]: this.chatHistory }
                }));
            } catch (e) {
                console.error('Error saving chat history:', e);
            }
        },
        
        // Render chat history in the UI
        renderChatHistory: function() {
            const chatHistoryDiv = document.getElementById('chatHistory');
            if (!chatHistoryDiv) return;
            
            if (!this.chatHistory || this.chatHistory.length === 0) {
                chatHistoryDiv.innerHTML = '<div class="empty-chat">No messages yet. Start a conversation!</div>';
                return;
            }
            
            let html = '';
            this.chatHistory.forEach(message => {
                const timestamp = new Date(message.timestamp).toLocaleTimeString();
                if (message.role === 'user') {
                    html += `
                        <div class="chat-message">
                            <div class="message-user">${this.escapeHtml(message.content)}</div>
                            <div class="message-meta">${timestamp}</div>
                        </div>
                    `;
                } else if (message.role === 'assistant') {
                    html += `
                        <div class="chat-message">
                            <div class="message-assistant">${this.escapeHtml(message.content)}</div>
                            <div class="message-meta">${timestamp}</div>
                        </div>
                    `;
                }
            });
            
            chatHistoryDiv.innerHTML = html;
            
            // Scroll to bottom
            chatHistoryDiv.scrollTop = chatHistoryDiv.scrollHeight;
        },
        
        // Helper function to escape HTML
        escapeHtml: function(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        },
        
        // Add message to chat history
        addMessageToHistory: function(role, content) {
            this.chatHistory.push({
                role,
                content,
                timestamp: Date.now()
            });
            this.saveChatHistory();
            this.renderChatHistory();
        },
        
        // Send a message to the API
        sendMessage: function() {
            const modelSelect = document.getElementById('modelSelect');
            const userInput = document.getElementById('userInput');
            const systemInput = document.getElementById('systemInput');
            const temperature = document.getElementById('temperature');
            const maxTokens = document.getElementById('maxTokens');
            const topP = document.getElementById('topP');
            const freqPenalty = document.getElementById('freqPenalty');
            const spinner = document.getElementById('spinner');
            const statsDiv = document.getElementById('stats');
            
            if (!modelSelect || !userInput) return;
            
            const modelPath = modelSelect.value;
            const message = userInput.value;
            
            if (!modelPath) {
                alert('Please select a model first');
                return;
            }
            
            if (!message.trim()) {
                alert('Please enter a message');
                return;
            }
            
            // Add user message to chat history
            this.addMessageToHistory('user', message);
            
            // Clear input field
            userInput.value = '';
            
            // Show spinner
            if (spinner) spinner.style.display = 'inline-block';
            if (statsDiv) statsDiv.style.display = 'none';
            
            // Disable send button while processing
            const sendBtn = document.getElementById('sendBtn');
            if (sendBtn) sendBtn.disabled = true;
            
            // Prepare parameters for API
            const params = {
                model: modelPath,
                message: message,
                system: systemInput ? systemInput.value : '',
                temperature: temperature ? parseFloat(temperature.value) : 0.7,
                max_tokens: maxTokens ? parseInt(maxTokens.value) : 1024,
                top_p: topP ? parseFloat(topP.value) : 0.95,
                frequency_penalty: freqPenalty ? parseFloat(freqPenalty.value) : 0.0,
                history: this.chatHistory.map(msg => ({
                    role: msg.role,
                    content: msg.content
                }))
            };
            
            // Get context documents if RAG is enabled
            let contextDocs = [];
            let projectId = null;
            
            // Check RAG components
            if (LLM.Components.RAGSidebar) {
                contextDocs = LLM.Components.RAGSidebar.getSelectedDocuments();
                projectId = LLM.Components.RAGSidebar.getCurrentProject();
            }
            
            // If using auto-suggest, suggest relevant documents
            if (LLM.Components.ContextManager && LLM.Components.ContextManager.autoSuggest) {
                LLM.Components.ContextManager.suggestDocuments(message);
                
                // Update context docs with the latest from ContextManager after suggesting
                if (LLM.Components.ContextManager.getDocuments().length > 0) {
                    contextDocs = LLM.Components.ContextManager.getDocuments().map(doc => doc.id);
                }
            }
                
            if (contextDocs && contextDocs.length > 0) {
                params.context_docs = contextDocs;
                params.project_id = projectId;
            }
            
            // Send message to API
            API.sendMessage(params)
                .then(data => {
                    // Hide spinner
                    if (spinner) spinner.style.display = 'none';
                    
                    if (data.error) {
                        // Add error message to chat
                        this.addMessageToHistory('assistant', 'Error: ' + data.error);
                    } else {
                        // Add assistant message to chat history
                        this.addMessageToHistory('assistant', data.response || 'No response from model');
                        
                        // Show stats if available
                        if (statsDiv && (data.time_taken || data.tokens_generated)) {
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
                    if (sendBtn) sendBtn.disabled = false;
                })
                .catch(error => {
                    if (spinner) spinner.style.display = 'none';
                    this.addMessageToHistory('assistant', 'Error: ' + error.message);
                    if (sendBtn) sendBtn.disabled = false;
                });
        },
        
        // Start a new chat
        newChat: function() {
            if (confirm('Start a new chat? This will clear the current conversation.')) {
                this.chatHistory = [];
                this.currentChatId = Date.now().toString();
                this.saveChatHistory();
                this.renderChatHistory();
                
                const userInput = document.getElementById('userInput');
                const systemInput = document.getElementById('systemInput');
                const statsDiv = document.getElementById('stats');
                
                if (userInput) userInput.value = '';
                if (systemInput) systemInput.value = '';
                if (statsDiv) statsDiv.style.display = 'none';
            }
        },
        
        // Export the current chat
        exportChat: function() {
            if (this.chatHistory.length === 0) {
                alert('No chat to export');
                return;
            }
            
            const modelSelect = document.getElementById('modelSelect');
            const systemInput = document.getElementById('systemInput');
            
            const exportData = {
                timestamp: Date.now(),
                model: modelSelect ? modelSelect.value : 'unknown',
                systemPrompt: systemInput ? systemInput.value : '',
                messages: this.chatHistory
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
    },
    
    /**
     * Model Selector Component Controller
     */
    ModelSelector: {
        // Initialize the component
        init: function() {
            this.loadModels();
        },
        
        // Load models from API
        loadModels: function() {
            const modelList = document.getElementById('modelList');
            const modelSelect = document.getElementById('modelSelect');
            
            if (!modelList || !modelSelect) return;
            
            API.getModels()
                .then(data => {
                    if (data.models && data.models.length > 0) {
                        let html = '';
                        modelSelect.innerHTML = '<option value="">Select a model</option>';
                        
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
                    } else {
                        modelList.innerHTML = 'No models found. Download models using: <code>./llm.sh download</code>';
                    }
                })
                .catch(error => {
                    modelList.innerHTML = 'Error loading models: ' + error.message;
                });
        }
    },
    
    /**
     * Parameter Controls Component Controller
     */
    ParameterControls: {
        // Initialize the component
        init: function() {
            // Add tooltips or advanced controls if needed
        },
        
        // Get current parameter values
        getParameters: function() {
            return {
                temperature: parseFloat(document.getElementById('temperature').value),
                maxTokens: parseInt(document.getElementById('maxTokens').value),
                topP: parseFloat(document.getElementById('topP').value),
                frequencyPenalty: parseFloat(document.getElementById('freqPenalty').value)
            };
        }
    },
    
    /**
     * Context Management
     */
    ContextManager: {
        documents: [],
        maxTokens: 2048,
        currentTokens: 0,
        autoSuggest: false,
        currentProject: null,
        
        // Initialize the component
        init: function() {
            // Only initialize if context bar exists
            const contextBar = document.getElementById('contextBar');
            if (!contextBar) return;
            
            // Setup event listeners
            const clearContextBtn = document.getElementById('clearContextBtn');
            const autoContextToggle = document.getElementById('autoContextToggle');
            
            if (clearContextBtn) {
                clearContextBtn.addEventListener('click', this.clearContext.bind(this));
            }
            
            if (autoContextToggle) {
                autoContextToggle.addEventListener('change', (e) => {
                    this.autoSuggest = e.target.checked;
                });
            }
            
            // Expose methods to window for backward compatibility
            window.addToContext = this.addDocument.bind(this);
            window.removeFromContext = this.removeDocument.bind(this);
            window.suggestContext = this.suggestDocuments.bind(this);
        },
        
        // Add document to context
        addDocument: function(doc) {
            // Check if document is already in context
            if (this.documents.some(d => d.id === doc.id)) {
                return;
            }
            
            // Add document to context
            this.documents.push(doc);
            
            // Set current project if not already set
            if (!this.currentProject && LLM.Components.RAGSidebar) {
                this.currentProject = LLM.Components.RAGSidebar.getCurrentProject();
            }
            
            // Show context bar
            const contextBar = document.getElementById('contextBar');
            if (contextBar) contextBar.style.display = 'block';
            
            // Update token counts via API
            this.updateTokenCounts();
        },
        
        // Remove document from context
        removeDocument: function(docId) {
            // Find document in context
            const docIndex = this.documents.findIndex(d => d.id === docId);
            if (docIndex === -1) return;
            
            // Remove document from context
            this.documents.splice(docIndex, 1);
            
            // Update UI with new token counts
            this.updateTokenCounts();
            
            // Hide context bar if empty
            if (this.documents.length === 0) {
                const contextBar = document.getElementById('contextBar');
                if (contextBar) contextBar.style.display = 'none';
            }
        },
        
        // Clear all context
        clearContext: function() {
            this.documents = [];
            this.currentTokens = 0;
            this.updateUI();
            
            const contextBar = document.getElementById('contextBar');
            if (contextBar) contextBar.style.display = 'none';
        },
        
        // Update token counts from API
        updateTokenCounts: function() {
            // Show loading state
            const tokenCount = document.getElementById('tokenCount');
            const tokenUsed = document.getElementById('tokenUsed');
            
            if (tokenCount) tokenCount.textContent = 'Calculating...';
            if (tokenUsed) tokenUsed.style.width = '0%';
            
            // Update the UI first with what we have
            this.updateUI();
            
            // If no documents or no project, just return
            if (this.documents.length === 0 || !this.currentProject) {
                return;
            }
            
            // Get document IDs
            const documentIds = this.documents.map(doc => doc.id);
            
            // Call API to get token counts
            API.RAG.getTokenInfo(this.currentProject, documentIds)
                .then(data => {
                    const tokenData = data.data || {};
                    
                    // Update token counts
                    this.currentTokens = tokenData.total_tokens || 0;
                    this.maxTokens = tokenData.model_context_window || 2048;
                    
                    // Update documents with individual token counts
                    const contexts = tokenData.contexts || [];
                    contexts.forEach(context => {
                        const doc = this.documents.find(d => d.id === context.id);
                        if (doc) {
                            doc.tokens = context.tokens;
                            doc.percentage = context.percentage;
                        }
                    });
                    
                    // Update UI with new token counts
                    this.updateUI();
                    
                    // Add warning if over limit
                    if (tokenData.is_over_limit) {
                        const contextBar = document.getElementById('contextBar');
                        if (contextBar) contextBar.classList.add('token-warning');
                    } else {
                        const contextBar = document.getElementById('contextBar');
                        if (contextBar) contextBar.classList.remove('token-warning');
                    }
                })
                .catch(error => {
                    console.error('Error updating token counts:', error);
                    // Still update UI with what we have
                    this.updateUI();
                });
        },
        
        // Update context UI
        updateUI: function() {
            const contextItems = document.getElementById('contextItems');
            const tokenCount = document.getElementById('tokenCount');
            const tokenLimit = document.getElementById('tokenLimit');
            const tokenUsed = document.getElementById('tokenUsed');
            
            if (!contextItems || !tokenCount || !tokenLimit || !tokenUsed) return;
            
            // Update context items
            contextItems.innerHTML = '';
            this.documents.forEach(doc => {
                const item = document.createElement('div');
                item.className = 'context-item';
                
                // Include token count if available
                const tokenInfo = doc.tokens ? ` (${doc.tokens} tokens)` : '';
                
                item.innerHTML = `
                    <div class="context-item-title" title="${doc.title}">${doc.title}${tokenInfo}</div>
                    <div class="context-item-remove" data-id="${doc.id}">×</div>
                `;
                contextItems.appendChild(item);
                
                // Add event listener to remove button
                const removeBtn = item.querySelector('.context-item-remove');
                if (removeBtn) {
                    removeBtn.addEventListener('click', () => {
                        this.removeDocument(doc.id);
                    });
                }
            });
            
            // Update token count display
            tokenCount.textContent = this.currentTokens;
            tokenLimit.textContent = this.maxTokens;
            
            // Update token bar
            const percentage = Math.min(100, (this.currentTokens / this.maxTokens) * 100);
            tokenUsed.style.width = `${percentage}%`;
            
            // Update token bar color based on usage
            tokenUsed.className = 'token-used';
            if (percentage > 90) {
                tokenUsed.classList.add('token-high');
            } else if (percentage > 70) {
                tokenUsed.classList.add('token-medium');
            } else {
                tokenUsed.classList.add('token-low');
            }
        },
        
        // Suggest documents based on message
        suggestDocuments: function(message) {
            if (!this.autoSuggest || !this.currentProject) return;
            
            const contextItems = document.getElementById('contextItems');
            if (!contextItems) return;
            
            // Show loading state
            const suggestionIndicator = document.createElement('div');
            suggestionIndicator.className = 'suggestion-indicator';
            suggestionIndicator.textContent = 'Finding relevant documents...';
            contextItems.appendChild(suggestionIndicator);
            
            // Call the API to get suggestions
            API.RAG.suggestDocuments(this.currentProject, message)
                .then(data => {
                    // Remove loading indicator
                    contextItems.removeChild(suggestionIndicator);
                    
                    const suggestions = data.suggestions || [];
                    
                    if (suggestions.length === 0) {
                        console.log('No document suggestions found');
                        return;
                    }
                    
                    // Add suggested documents to context
                    suggestions.forEach(suggestion => {
                        // Only add if not already in context
                        if (!this.documents.some(d => d.id === suggestion.id)) {
                            API.RAG.getDocument(this.currentProject, suggestion.id)
                                .then(doc => {
                                    this.addDocument(doc);
                                })
                                .catch(error => {
                                    console.error('Error fetching suggested document:', error);
                                });
                        }
                    });
                })
                .catch(error => {
                    console.error('Error getting document suggestions:', error);
                    // Remove loading indicator
                    if (suggestionIndicator.parentNode === contextItems) {
                        contextItems.removeChild(suggestionIndicator);
                    }
                });
        },
        
        // Get all documents in context
        getDocuments: function() {
            return this.documents;
        },
        
        // Get total token count
        getTokenCount: function() {
            return this.currentTokens;
        }
    },
    
    /**
     * RAG Sidebar Component Controller (only active when RAG is enabled)
     */
    RAGSidebar: {
        currentProject: null,
        selectedDocuments: [],
        previewedDocument: null,
        documents: [],  // Store loaded documents for the current project
        
        // Initialize the component
        init: function() {
            // Only initialize if RAG is enabled
            if (!document.body.getAttribute('data-rag-enabled')) return;
            
            console.log("Initializing RAG sidebar");
            
            // Load projects
            this.loadProjects();
            
            // Set up event listeners
            const sidebar = document.querySelector('.sidebar');
            const sidebarToggle = document.querySelector('.sidebar-toggle');
            const addDocumentBtn = document.getElementById('addDocumentBtn');
            const refreshDocsBtn = document.getElementById('refreshDocsBtn');
            const newProjectBtn = document.getElementById('newProjectBtn');
            const documentSearch = document.getElementById('documentSearch');
            const clearSearch = document.getElementById('clearSearch');
            const documentPreview = document.getElementById('documentPreview');
            const closePreview = document.getElementById('closePreview');
            const addToContextBtn = document.getElementById('addToContextBtn');
            
            if (sidebarToggle) {
                sidebarToggle.addEventListener('click', () => {
                    document.body.classList.toggle('sidebar-collapsed');
                });
            }
            
            if (addDocumentBtn) {
                addDocumentBtn.addEventListener('click', this.showAddDocumentDialog.bind(this));
            }
            
            if (refreshDocsBtn) {
                refreshDocsBtn.addEventListener('click', () => {
                    if (this.currentProject) {
                        this.loadDocuments(this.currentProject);
                    }
                });
            }
            
            if (newProjectBtn) {
                newProjectBtn.addEventListener('click', this.showNewProjectDialog.bind(this));
            }
            
            if (documentSearch && clearSearch) {
                documentSearch.addEventListener('input', this.handleSearch.bind(this));
                clearSearch.addEventListener('click', () => {
                    documentSearch.value = '';
                    this.handleSearch();
                });
            }
            
            if (closePreview) {
                closePreview.addEventListener('click', this.closeDocumentPreview.bind(this));
            }
            
            if (addToContextBtn) {
                addToContextBtn.addEventListener('click', () => {
                    if (this.previewedDocument) {
                        this.addDocumentToContext(this.previewedDocument);
                        this.closeDocumentPreview();
                    }
                });
            }
            
            // Make preview draggable
            if (documentPreview) {
                this.makePreviewDraggable(documentPreview);
            }
        },
        
        // Make document preview draggable
        makePreviewDraggable: function(element) {
            const header = element.querySelector('.preview-header');
            if (!header) return;
            
            let pos1 = 0, pos2 = 0, pos3 = 0, pos4 = 0;
            
            header.onmousedown = dragMouseDown;
            
            function dragMouseDown(e) {
                e.preventDefault();
                pos3 = e.clientX;
                pos4 = e.clientY;
                document.onmouseup = closeDragElement;
                document.onmousemove = elementDrag;
            }
            
            function elementDrag(e) {
                e.preventDefault();
                pos1 = pos3 - e.clientX;
                pos2 = pos4 - e.clientY;
                pos3 = e.clientX;
                pos4 = e.clientY;
                
                const top = (element.offsetTop - pos2);
                const left = (element.offsetLeft - pos1);
                
                element.style.top = top + "px";
                element.style.left = left + "px";
                element.style.transform = "none";
            }
            
            function closeDragElement() {
                document.onmouseup = null;
                document.onmousemove = null;
            }
        },
        
        // Show document preview dialog
        showDocumentPreview: function(docId) {
            const preview = document.getElementById('documentPreview');
            const title = document.getElementById('previewTitle');
            const content = document.getElementById('previewContent');
            
            if (!preview || !title || !content) return;
            
            // Show loading state
            preview.style.display = 'flex';
            title.textContent = 'Loading...';
            content.innerHTML = '<div class="loading-spinner"></div>';
            
            // Check if we already have the document loaded
            let doc = null;
            if (typeof docId === 'object' && docId !== null) {
                // If a document object was passed directly, use it
                doc = docId;
                this.displayDocumentPreview(doc, title, content);
            } else {
                // Otherwise fetch the document by ID
                API.RAG.getDocument(this.currentProject, docId)
                    .then(data => {
                        console.log("Document preview API response:", data);
                        
                        // Handle different response formats
                        let document = data;
                        if (data.data) {
                            // Standard success response format
                            document = data.data;
                        }
                        
                        this.displayDocumentPreview(document, title, content);
                    })
                    .catch(error => {
                        content.innerHTML = `<div class="error-message">Error loading document: ${error.message}</div>`;
                    });
            }
        },
        
        // Display document in preview panel
        displayDocumentPreview: function(doc, titleElement, contentElement) {
            // Store reference to the document
            this.previewedDocument = doc;
            
            // Update title
            titleElement.textContent = doc.title || 'Document Preview';
            
            // Update content
            contentElement.innerHTML = `<div class="preview-text">${doc.content || 'No content available'}</div>`;
            
            // Add metadata if available
            if (doc.metadata) {
                const metaHTML = `
                    <div class="preview-metadata">
                        <h4>Metadata</h4>
                        <ul>
                            ${Object.entries(doc.metadata).map(([key, value]) => 
                                `<li><strong>${key}:</strong> ${value}</li>`
                            ).join('')}
                        </ul>
                    </div>
                `;
                contentElement.innerHTML += metaHTML;
            }
        },
        
        // Close document preview dialog
        closeDocumentPreview: function() {
            const preview = document.getElementById('documentPreview');
            if (preview) {
                preview.style.display = 'none';
            }
            this.previewedDocument = null;
        },
        
        // Add document to context
        addDocumentToContext: function(doc) {
            // Check if we have the ContextManager
            if (LLM.Components.ContextManager) {
                LLM.Components.ContextManager.addDocument(doc);
            } else if (typeof window.addToContext === 'function') {
                // Fallback to window method
                window.addToContext(doc);
            } else {
                console.error("No context management available");
            }
        },
        
        // Show add document dialog
        showAddDocumentDialog: function() {
            if (!this.currentProject) {
                alert('Please select a project first');
                return;
            }
            
            // Create a form for document upload
            const dialog = document.createElement('div');
            dialog.className = 'modal-dialog';
            dialog.innerHTML = `
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>Add Document</h3>
                        <button class="close-button">&times;</button>
                    </div>
                    <div class="modal-body">
                        <form id="documentUploadForm">
                            <div class="form-group">
                                <label for="documentTitle">Title</label>
                                <input type="text" id="documentTitle" class="form-control" required>
                            </div>
                            <div class="form-group">
                                <label for="documentContent">Content</label>
                                <textarea id="documentContent" class="form-control" rows="10" required></textarea>
                            </div>
                            <div class="form-group">
                                <label for="documentTags">Tags (comma-separated)</label>
                                <input type="text" id="documentTags" class="form-control">
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button id="cancelDocumentBtn" class="secondary-btn">Cancel</button>
                        <button id="submitDocumentBtn" class="primary-btn">Add Document</button>
                    </div>
                </div>
            `;
            
            // Add the dialog to the page
            document.body.appendChild(dialog);
            
            // Set up event listeners
            const closeButton = dialog.querySelector('.close-button');
            const cancelButton = document.getElementById('cancelDocumentBtn');
            const submitButton = document.getElementById('submitDocumentBtn');
            
            const closeDialog = () => {
                document.body.removeChild(dialog);
            };
            
            closeButton.addEventListener('click', closeDialog);
            cancelButton.addEventListener('click', closeDialog);
            
            submitButton.addEventListener('click', () => {
                const title = document.getElementById('documentTitle').value.trim();
                const content = document.getElementById('documentContent').value.trim();
                const tagsInput = document.getElementById('documentTags').value.trim();
                
                if (!title || !content) {
                    alert('Please provide both title and content');
                    return;
                }
                
                // Parse tags
                const tags = tagsInput ? tagsInput.split(',').map(tag => tag.trim()) : [];
                
                // Show loading state
                submitButton.disabled = true;
                submitButton.textContent = 'Adding...';
                
                // Call API to create the document
                API.RAG.createDocument(this.currentProject, {
                    title: title,
                    content: content,
                    tags: tags
                })
                .then(response => {
                    // Close the dialog
                    closeDialog();
                    
                    // Reload documents
                    this.loadDocuments(this.currentProject);
                    
                    // Show success message
                    alert('Document added successfully!');
                })
                .catch(error => {
                    alert(`Error adding document: ${error.message}`);
                    submitButton.disabled = false;
                    submitButton.textContent = 'Add Document';
                });
            });
        },
        
        // Show new project dialog
        showNewProjectDialog: function() {
            // Create a dialog for creating a new project
            const dialog = document.createElement('div');
            dialog.className = 'modal-dialog';
            dialog.innerHTML = `
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>Create New Project</h3>
                        <button class="close-button">&times;</button>
                    </div>
                    <div class="modal-body">
                        <form id="newProjectForm">
                            <div class="form-group">
                                <label for="projectName">Project Name</label>
                                <input type="text" id="projectName" class="form-control" required>
                            </div>
                            <div class="form-group">
                                <label for="projectDescription">Description (optional)</label>
                                <textarea id="projectDescription" class="form-control" rows="3"></textarea>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button id="cancelProjectBtn" class="secondary-btn">Cancel</button>
                        <button id="createProjectBtn" class="primary-btn">Create Project</button>
                    </div>
                </div>
            `;
            
            // Add the dialog to the page
            document.body.appendChild(dialog);
            
            // Set up event listeners
            const closeButton = dialog.querySelector('.close-button');
            const cancelButton = document.getElementById('cancelProjectBtn');
            const createButton = document.getElementById('createProjectBtn');
            
            const closeDialog = () => {
                document.body.removeChild(dialog);
            };
            
            closeButton.addEventListener('click', closeDialog);
            cancelButton.addEventListener('click', closeDialog);
            
            createButton.addEventListener('click', () => {
                const name = document.getElementById('projectName').value.trim();
                const description = document.getElementById('projectDescription').value.trim();
                
                if (!name) {
                    alert('Please provide a project name');
                    return;
                }
                
                // Show loading state
                createButton.disabled = true;
                createButton.textContent = 'Creating...';
                
                // Call API to create the project
                API.RAG.createProject({
                    name: name,
                    description: description
                })
                .then(response => {
                    // Close the dialog
                    closeDialog();
                    
                    // Reload projects
                    this.loadProjects();
                    
                    // Show success message
                    alert('Project created successfully!');
                })
                .catch(error => {
                    alert(`Error creating project: ${error.message}`);
                    createButton.disabled = false;
                    createButton.textContent = 'Create Project';
                });
            });
        },
        
        // Handle document search
        handleSearch: function(e) {
            const input = document.getElementById('documentSearch');
            const query = input ? input.value.trim() : '';
            
            if (!this.currentProject) return;
            
            if (query === '') {
                // If search is cleared, just reload documents
                this.loadDocuments(this.currentProject);
                return;
            }
            
            // Show loading state
            const documentList = document.getElementById('documentList');
            if (documentList) {
                documentList.innerHTML = '<div class="loading-spinner"></div>';
            }
            
            // Call the search API
            API.RAG.searchDocuments(this.currentProject, query)
                .then(data => {
                    // Store documents in memory
                    this.documents = data.data || [];
                    
                    // Render the documents
                    this.renderDocuments(this.documents);
                })
                .catch(error => {
                    if (documentList) {
                        documentList.innerHTML = `<div class="error-message">Error searching documents: ${error.message}</div>`;
                    }
                });
        },
        
        // Load projects from API
        loadProjects: function() {
            const projectList = document.getElementById('projectList');
            if (!projectList) return;
            
            projectList.innerHTML = '<div class="loading-spinner"></div>';
            
            // Call the real API
            API.RAG.getProjects()
                .then(data => {
                    // Check and log the actual response format
                    console.log("Project API response:", data);
                    
                    // Handle different response formats
                    let projects = [];
                    if (data.data) {
                        // Standard success response format
                        projects = data.data;
                        console.log(`Found ${projects.length} projects in data.data`);
                    } else if (data.projects) {
                        // Alternative format
                        projects = data.projects;
                        console.log(`Found ${projects.length} projects in data.projects`);
                    } else if (Array.isArray(data)) {
                        // Direct array format
                        projects = data;
                        console.log(`Found ${projects.length} projects in direct array`);
                    } else {
                        console.error("Unknown project data format:", data);
                    }
                    
                    if (projects.length > 0) {
                        let html = '<ul class="project-list-items">';
                        projects.forEach(project => {
                            html += `<li class="project-item" data-project-id="${project.id}">
                                <span class="project-name">${project.name}</span>
                                <span class="document-count">${project.document_count} docs</span>
                            </li>`;
                        });
                        html += '</ul>';
                        projectList.innerHTML = html;
                        
                        // Add click handlers
                        document.querySelectorAll('.project-item').forEach(item => {
                            item.addEventListener('click', () => {
                                const projectId = item.getAttribute('data-project-id');
                                this.loadDocuments(projectId);
                                this.currentProject = projectId;
                                
                                // Highlight selected project
                                document.querySelectorAll('.project-item').forEach(p => {
                                    p.classList.remove('selected');
                                });
                                item.classList.add('selected');
                            });
                        });
                        
                        // Select first project by default
                        if (projects.length > 0) {
                            this.loadDocuments(projects[0].id);
                            this.currentProject = projects[0].id;
                            document.querySelector('.project-item').classList.add('selected');
                        }
                    } else {
                        projectList.innerHTML = '<div class="empty-state">No projects found. Create a project to get started.</div>';
                    }
                })
                .catch(error => {
                    projectList.innerHTML = `<div class="error-message">Error loading projects: ${error.message}</div>`;
                });
        },
        
        // Load documents for a project
        loadDocuments: function(projectId) {
            const documentList = document.getElementById('documentList');
            if (!documentList) return;
            
            documentList.innerHTML = '<div class="loading-spinner"></div>';
            
            // Call the real API
            API.RAG.getDocuments(projectId)
                .then(data => {
                    console.log("Document API response:", data);
                    
                    // Handle different response formats
                    let documents = [];
                    if (data.data) {
                        // Standard success response format
                        documents = data.data;
                        console.log(`Found ${documents.length} documents in data.data`);
                    } else if (data.documents) {
                        // Alternative format
                        documents = data.documents;
                        console.log(`Found ${documents.length} documents in data.documents`);
                    } else if (Array.isArray(data)) {
                        // Direct array format
                        documents = data;
                        console.log(`Found ${documents.length} documents in direct array`);
                    } else {
                        console.error("Unknown document data format:", data);
                    }
                    
                    // Store documents in memory
                    this.documents = documents;
                    
                    // Render the documents
                    this.renderDocuments(this.documents);
                })
                .catch(error => {
                    documentList.innerHTML = `<div class="error-message">Error loading documents: ${error.message}</div>`;
                });
        },
        
        // Render documents in the UI
        renderDocuments: function(documents) {
            const documentList = document.getElementById('documentList');
            if (!documentList) return;
            
            if (documents.length > 0) {
                let html = '<ul class="document-list">';
                documents.forEach(doc => {
                    html += `<li class="document-item" data-document-id="${doc.id}">
                        <div class="document-selector">
                            <input type="checkbox" class="document-checkbox" id="doc-${doc.id}">
                            <label for="doc-${doc.id}" class="document-name">${doc.title}</label>
                        </div>
                        <div class="document-actions">
                            <button class="preview-btn" data-id="${doc.id}" title="Preview">👁️</button>
                        </div>
                    </li>`;
                });
                html += '</ul>';
                documentList.innerHTML = html;
                
                // Add click handlers for document selection
                document.querySelectorAll('.document-checkbox').forEach(checkbox => {
                    checkbox.addEventListener('change', () => {
                        const docId = checkbox.closest('.document-item').getAttribute('data-document-id');
                        if (checkbox.checked) {
                            this.selectedDocuments.push(docId);
                        } else {
                            this.selectedDocuments = this.selectedDocuments.filter(id => id !== docId);
                        }
                        this.updateTokenCount();
                    });
                });
                
                // Add preview handlers
                document.querySelectorAll('.preview-btn').forEach(btn => {
                    btn.addEventListener('click', () => {
                        const docId = btn.getAttribute('data-id');
                        this.showDocumentPreview(docId);
                    });
                });
                
                // Add double-click preview on document names
                document.querySelectorAll('.document-name').forEach(nameEl => {
                    nameEl.addEventListener('dblclick', () => {
                        const docId = nameEl.closest('.document-item').getAttribute('data-document-id');
                        this.showDocumentPreview(docId);
                    });
                });
            } else {
                documentList.innerHTML = '<div class="empty-state">No documents found in this project.</div>';
            }
        },
        
        // Update token count for selected documents
        updateTokenCount: function() {
            if (!this.currentProject || this.selectedDocuments.length === 0) return;
            
            const tokenCounter = document.getElementById('tokenCounter');
            if (!tokenCounter) return;
            
            tokenCounter.innerHTML = '<div class="loading-spinner"></div>';
            
            // Call the token estimation API
            API.RAG.getTokenInfo(this.currentProject, this.selectedDocuments)
                .then(data => {
                    const tokenData = data.data || {};
                    const totalTokens = tokenData.total_tokens || 0;
                    
                    // Update the token counter
                    tokenCounter.innerHTML = `Selected: ${this.selectedDocuments.length} documents, ${totalTokens} tokens`;
                    
                    // If token usage is getting high, add a warning class
                    if (tokenData.is_over_limit) {
                        tokenCounter.classList.add('token-warning');
                    } else {
                        tokenCounter.classList.remove('token-warning');
                    }
                })
                .catch(error => {
                    tokenCounter.innerHTML = `Error calculating tokens: ${error.message}`;
                });
        },
        
        // Get currently selected documents
        getSelectedDocuments: function() {
            return this.selectedDocuments;
        },
        
        // Get current project
        getCurrentProject: function() {
            return this.currentProject;
        }
    }
};

// Initialization is now handled in the main layout template
// to ensure proper loading order