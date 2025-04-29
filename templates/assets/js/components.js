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
            const contextDocs = LLM.Components.RAGSidebar ? 
                LLM.Components.RAGSidebar.getSelectedDocuments() : [];
                
            if (contextDocs && contextDocs.length > 0) {
                params.context_docs = contextDocs;
                params.project_id = LLM.Components.RAGSidebar.getCurrentProject();
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
            
            // Update token count
            this.currentTokens += doc.tokens || 0;
            
            // Update UI
            this.updateUI();
            
            // Show context bar
            const contextBar = document.getElementById('contextBar');
            if (contextBar) contextBar.style.display = 'block';
        },
        
        // Remove document from context
        removeDocument: function(docId) {
            // Find document in context
            const docIndex = this.documents.findIndex(d => d.id === docId);
            if (docIndex === -1) return;
            
            // Subtract tokens
            this.currentTokens -= this.documents[docIndex].tokens || 0;
            
            // Remove document from context
            this.documents.splice(docIndex, 1);
            
            // Update UI
            this.updateUI();
            
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
                item.innerHTML = `
                    <div class="context-item-title" title="${doc.title}">${doc.title}</div>
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
            
            // Update token count
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
            if (!this.autoSuggest) return;
            
            // In a real implementation, this would make an API call to the backend
            console.log('Auto-suggesting context for:', message);
            
            // For now, we'll just display a placeholder message
            console.log('Auto-suggest is enabled but not implemented yet');
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
        showDocumentPreview: function(doc) {
            const preview = document.getElementById('documentPreview');
            const title = document.getElementById('previewTitle');
            const content = document.getElementById('previewContent');
            
            if (!preview || !title || !content) return;
            
            this.previewedDocument = doc;
            
            title.textContent = doc.title || 'Document Preview';
            content.innerHTML = `<div class="preview-text">${doc.content || 'No content available'}</div>`;
            
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
                content.innerHTML += metaHTML;
            }
            
            // Show the preview
            preview.style.display = 'flex';
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
            
            // For demo purposes, just show a simple prompt
            const title = prompt('Enter document title:');
            const content = prompt('Enter document content:');
            
            if (title && content) {
                // In a real implementation, this would make an API call
                alert('Document upload is not implemented in this demo. In a real system, this would upload the document to the selected project.');
            }
        },
        
        // Show new project dialog
        showNewProjectDialog: function() {
            // For demo purposes, just show a simple prompt
            const name = prompt('Enter project name:');
            
            if (name) {
                // In a real implementation, this would make an API call
                alert('Project creation is not implemented in this demo. In a real system, this would create a new project with the name: ' + name);
            }
        },
        
        // Handle document search
        handleSearch: function(e) {
            const input = document.getElementById('documentSearch');
            const query = input ? input.value.toLowerCase() : '';
            
            if (!this.currentProject) return;
            
            if (query === '') {
                // If search is cleared, just reload documents
                this.loadDocuments(this.currentProject);
                return;
            }
            
            // For demo purposes, filter the documents client-side
            // In a real implementation, this would make an API call
            const documentItems = document.querySelectorAll('.document-item');
            
            documentItems.forEach(item => {
                const docName = item.querySelector('.document-name').textContent.toLowerCase();
                if (docName.includes(query)) {
                    item.style.display = 'block';
                } else {
                    item.style.display = 'none';
                }
            });
        },
        
        // Load projects from API
        loadProjects: function() {
            const projectList = document.getElementById('projectList');
            if (!projectList) return;
            
            projectList.innerHTML = '<div class="empty-state">Loading projects...</div>';
            
            // For demo purposes, use mock data instead of actual API call
            this.getMockProjects()
                .then(data => {
                    if (data.projects && data.projects.length > 0) {
                        let html = '<ul class="project-list-items">';
                        data.projects.forEach(project => {
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
                        if (data.projects.length > 0) {
                            this.loadDocuments(data.projects[0].id);
                            this.currentProject = data.projects[0].id;
                            document.querySelector('.project-item').classList.add('selected');
                        }
                    } else {
                        projectList.innerHTML = '<div class="empty-state">No projects found. Create a project to get started.</div>';
                    }
                })
                .catch(error => {
                    projectList.innerHTML = `<div class="empty-state">Error loading projects: ${error.message}</div>`;
                });
        },
        
        // Get mock projects for demo
        getMockProjects: function() {
            return new Promise((resolve) => {
                // Simulate API delay
                setTimeout(() => {
                    const projects = [
                        {
                            id: 'project1',
                            name: 'Research Documents',
                            document_count: 3
                        },
                        {
                            id: 'project2',
                            name: 'Technical Guides',
                            document_count: 2
                        },
                        {
                            id: 'project3',
                            name: 'Meeting Notes',
                            document_count: 1
                        }
                    ];
                    
                    resolve({ projects });
                }, 300);
            });
        },
        
        // Load documents for a project
        loadDocuments: function(projectId) {
            const documentList = document.getElementById('documentList');
            if (!documentList) return;
            
            documentList.innerHTML = '<div class="empty-state">Loading documents...</div>';
            
            // In a real implementation, this would call the actual API
            // For demo, we'll create some mock documents
            this.getMockDocuments(projectId)
                .then(data => {
                    if (data.documents && data.documents.length > 0) {
                        let html = '<ul class="document-list">';
                        data.documents.forEach(doc => {
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
                        
                        // Store documents in memory
                        this.documents = data.documents;
                        
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
                                const doc = this.documents.find(d => d.id === docId);
                                if (doc) {
                                    this.showDocumentPreview(doc);
                                }
                            });
                        });
                        
                        // Add double-click preview on document names
                        document.querySelectorAll('.document-name').forEach(nameEl => {
                            nameEl.addEventListener('dblclick', () => {
                                const docId = nameEl.closest('.document-item').getAttribute('data-document-id');
                                const doc = this.documents.find(d => d.id === docId);
                                if (doc) {
                                    this.showDocumentPreview(doc);
                                }
                            });
                        });
                    } else {
                        documentList.innerHTML = '<div class="empty-state">No documents found in this project.</div>';
                    }
                })
                .catch(error => {
                    documentList.innerHTML = `<div class="empty-state">Error loading documents: ${error.message}</div>`;
                });
        },
        
        // Get mock documents for demo
        getMockDocuments: function(projectId) {
            return new Promise((resolve) => {
                // Simulate API delay
                setTimeout(() => {
                    const documents = [
                        {
                            id: 'doc1',
                            title: 'Getting Started with LLMs',
                            content: 'Large Language Models (LLMs) are versatile AI systems that can generate and understand text. They are trained on vast amounts of text data, allowing them to learn patterns, relationships, and facts about the world. This document explains how to get started using them effectively.',
                            tokens: 200,
                            metadata: {
                                author: 'AI Research Team',
                                created: '2023-05-15',
                                category: 'Guide'
                            }
                        },
                        {
                            id: 'doc2',
                            title: 'Understanding Context Windows',
                            content: 'Context windows determine how much text an LLM can process at once. Models with larger context windows can understand and reference information from more text in a single prompt, making them more useful for tasks that require analyzing long documents or maintaining extended conversations.',
                            tokens: 150,
                            metadata: {
                                author: 'Technical Documentation',
                                created: '2023-06-22',
                                category: 'Technical'
                            }
                        },
                        {
                            id: 'doc3',
                            title: 'RAG Implementation Guide',
                            content: 'Retrieval-Augmented Generation (RAG) enhances LLM capabilities by retrieving relevant information from a knowledge base before generating a response. This allows the model to access knowledge beyond its training data and provide more accurate, up-to-date information. This document covers implementation details for a RAG system.',
                            tokens: 250,
                            metadata: {
                                author: 'System Architecture Team',
                                created: '2023-08-10',
                                category: 'Technical'
                            }
                        }
                    ];
                    
                    resolve({ documents });
                }, 500);
            });
        },
        
        // Update token count for selected documents
        updateTokenCount: function() {
            if (!this.currentProject || this.selectedDocuments.length === 0) return;
            
            const tokenCounter = document.getElementById('tokenCounter');
            if (!tokenCounter) return;
            
            tokenCounter.innerHTML = 'Calculating tokens...';
            
            // For demo purposes, calculate tokens from local documents
            // In a real implementation, this would make an API call
            setTimeout(() => {
                let totalTokens = 0;
                this.selectedDocuments.forEach(docId => {
                    const doc = this.documents.find(d => d.id === docId);
                    if (doc && doc.tokens) {
                        totalTokens += doc.tokens;
                    }
                });
                
                tokenCounter.innerHTML = `Selected: ${this.selectedDocuments.length} documents, ${totalTokens} tokens`;
            }, 300);
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