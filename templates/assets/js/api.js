/**
 * API Client for the LLM Interface
 * Handles all API interactions with a standardized interface
 */

// Define API as a global object
window.API = {
    /**
     * Fetch models from the API
     * @returns {Promise} Promise that resolves to the model list
     */
    getModels: async function() {
        try {
            const response = await fetch('/api/models');
            if (!response.ok) {
                throw new Error(`Error fetching models: ${response.status} ${response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Error fetching models:', error);
            throw error;
        }
    },
    
    /**
     * Send a chat message to the API
     * @param {Object} params - The parameters for the chat request
     * @returns {Promise} Promise that resolves to the chat response
     */
    sendMessage: async function(params) {
        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    model: params.model,
                    message: params.message,
                    system: params.system || '',
                    temperature: params.temperature || 0.7,
                    max_tokens: params.max_tokens || 1024,
                    top_p: params.top_p || 0.95,
                    frequency_penalty: params.frequency_penalty || 0.0,
                    presence_penalty: params.presence_penalty || 0.0,
                    history: params.history || [],
                    context_docs: params.context_docs || [],
                    project_id: params.project_id || null
                })
            });
            
            if (!response.ok) {
                throw new Error(`Error sending message: ${response.status} ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('Error sending message:', error);
            throw error;
        }
    },
    
    /**
     * RAG API Functions (only available when RAG is enabled)
     */
    RAG: {
        /**
         * Get projects from the RAG API
         * @returns {Promise} Promise that resolves to the project list
         */
        getProjects: async function() {
            try {
                const response = await fetch('/api/projects');
                if (!response.ok) {
                    throw new Error(`Error fetching projects: ${response.status} ${response.statusText}`);
                }
                return await response.json();
            } catch (error) {
                console.error('Error fetching projects:', error);
                throw error;
            }
        },
        
        /**
         * Create a new project
         * @param {Object} projectData - The project data
         * @returns {Promise} Promise that resolves to the created project
         */
        createProject: async function(projectData) {
            try {
                const response = await fetch('/api/projects', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(projectData)
                });
                
                if (!response.ok) {
                    throw new Error(`Error creating project: ${response.status} ${response.statusText}`);
                }
                
                return await response.json();
            } catch (error) {
                console.error('Error creating project:', error);
                throw error;
            }
        },
        
        /**
         * Get a specific project by ID
         * @param {string} projectId - The project ID
         * @returns {Promise} Promise that resolves to the project
         */
        getProject: async function(projectId) {
            try {
                const response = await fetch(`/api/projects/${projectId}`);
                if (!response.ok) {
                    throw new Error(`Error fetching project: ${response.status} ${response.statusText}`);
                }
                return await response.json();
            } catch (error) {
                console.error('Error fetching project:', error);
                throw error;
            }
        },
        
        /**
         * Delete a project
         * @param {string} projectId - The project ID
         * @returns {Promise} Promise that resolves when the project is deleted
         */
        deleteProject: async function(projectId) {
            try {
                const response = await fetch(`/api/projects/${projectId}`, {
                    method: 'DELETE'
                });
                
                if (!response.ok) {
                    throw new Error(`Error deleting project: ${response.status} ${response.statusText}`);
                }
                
                return await response.json();
            } catch (error) {
                console.error('Error deleting project:', error);
                throw error;
            }
        },
        
        /**
         * Get documents for a project
         * @param {string} projectId - The project ID
         * @returns {Promise} Promise that resolves to the document list
         */
        getDocuments: async function(projectId) {
            try {
                const response = await fetch(`/api/projects/${projectId}/documents`);
                if (!response.ok) {
                    throw new Error(`Error fetching documents: ${response.status} ${response.statusText}`);
                }
                return await response.json();
            } catch (error) {
                console.error('Error fetching documents:', error);
                throw error;
            }
        },
        
        /**
         * Create a new document in a project
         * @param {string} projectId - The project ID
         * @param {Object} documentData - The document data
         * @returns {Promise} Promise that resolves to the created document
         */
        createDocument: async function(projectId, documentData) {
            try {
                const response = await fetch(`/api/projects/${projectId}/documents`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(documentData)
                });
                
                if (!response.ok) {
                    throw new Error(`Error creating document: ${response.status} ${response.statusText}`);
                }
                
                return await response.json();
            } catch (error) {
                console.error('Error creating document:', error);
                throw error;
            }
        },
        
        /**
         * Get a document by ID
         * @param {string} projectId - The project ID
         * @param {string} documentId - The document ID
         * @returns {Promise} Promise that resolves to the document
         */
        getDocument: async function(projectId, documentId) {
            try {
                const response = await fetch(`/api/projects/${projectId}/documents/${documentId}`);
                if (!response.ok) {
                    throw new Error(`Error fetching document: ${response.status} ${response.statusText}`);
                }
                return await response.json();
            } catch (error) {
                console.error('Error fetching document:', error);
                throw error;
            }
        },
        
        /**
         * Delete a document
         * @param {string} projectId - The project ID
         * @param {string} documentId - The document ID
         * @returns {Promise} Promise that resolves when the document is deleted
         */
        deleteDocument: async function(projectId, documentId) {
            try {
                const response = await fetch(`/api/projects/${projectId}/documents/${documentId}`, {
                    method: 'DELETE'
                });
                
                if (!response.ok) {
                    throw new Error(`Error deleting document: ${response.status} ${response.statusText}`);
                }
                
                return await response.json();
            } catch (error) {
                console.error('Error deleting document:', error);
                throw error;
            }
        },
        
        /**
         * Search documents in a project
         * @param {string} projectId - The project ID
         * @param {string} query - The search query
         * @returns {Promise} Promise that resolves to the search results
         */
        searchDocuments: async function(projectId, query) {
            try {
                const response = await fetch(`/api/projects/${projectId}/search?query=${encodeURIComponent(query)}`);
                if (!response.ok) {
                    throw new Error(`Error searching documents: ${response.status} ${response.statusText}`);
                }
                return await response.json();
            } catch (error) {
                console.error('Error searching documents:', error);
                throw error;
            }
        },
        
        /**
         * Get suggested documents for a query
         * @param {string} projectId - The project ID
         * @param {string} query - The search query
         * @returns {Promise} Promise that resolves to the suggested documents
         */
        suggestDocuments: async function(projectId, query) {
            try {
                const response = await fetch(`/api/projects/${projectId}/suggest?query=${encodeURIComponent(query)}`);
                if (!response.ok) {
                    throw new Error(`Error getting document suggestions: ${response.status} ${response.statusText}`);
                }
                return await response.json();
            } catch (error) {
                console.error('Error getting document suggestions:', error);
                throw error;
            }
        },
        
        /**
         * Get token information for selected documents
         * @param {string} projectId - The project ID
         * @param {Array<string>} documentIds - The document IDs to estimate tokens for
         * @returns {Promise} Promise that resolves to the token information
         */
        getTokenInfo: async function(projectId, documentIds = []) {
            try {
                const response = await fetch(`/api/tokens`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        project_id: projectId,
                        context_docs: documentIds
                    })
                });
                
                if (!response.ok) {
                    throw new Error(`Error estimating tokens: ${response.status} ${response.statusText}`);
                }
                
                return await response.json();
            } catch (error) {
                console.error('Error estimating tokens:', error);
                throw error;
            }
        },
        
        /**
         * Create a new chat in a project
         * @param {string} projectId - The project ID
         * @param {Object} chatData - The chat data
         * @returns {Promise} Promise that resolves to the created chat
         */
        createChat: async function(projectId, chatData) {
            try {
                const response = await fetch(`/api/projects/${projectId}/chats`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(chatData)
                });
                
                if (!response.ok) {
                    throw new Error(`Error creating chat: ${response.status} ${response.statusText}`);
                }
                
                return await response.json();
            } catch (error) {
                console.error('Error creating chat:', error);
                throw error;
            }
        },
        
        /**
         * Get chats for a project
         * @param {string} projectId - The project ID
         * @returns {Promise} Promise that resolves to the chat list
         */
        getChats: async function(projectId) {
            try {
                const response = await fetch(`/api/projects/${projectId}/chats`);
                if (!response.ok) {
                    throw new Error(`Error fetching chats: ${response.status} ${response.statusText}`);
                }
                return await response.json();
            } catch (error) {
                console.error('Error fetching chats:', error);
                throw error;
            }
        },
        
        /**
         * Add a message to a chat
         * @param {string} projectId - The project ID
         * @param {string} chatId - The chat ID
         * @param {Object} messageData - The message data
         * @returns {Promise} Promise that resolves to the LLM response
         */
        addChatMessage: async function(projectId, chatId, messageData) {
            try {
                const response = await fetch(`/api/projects/${projectId}/chats/${chatId}/messages`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(messageData)
                });
                
                if (!response.ok) {
                    throw new Error(`Error adding message: ${response.status} ${response.statusText}`);
                }
                
                return await response.json();
            } catch (error) {
                console.error('Error adding message:', error);
                throw error;
            }
        },
        
        /**
         * Create a new artifact in a project
         * @param {string} projectId - The project ID
         * @param {Object} artifactData - The artifact data
         * @returns {Promise} Promise that resolves to the created artifact
         */
        createArtifact: async function(projectId, artifactData) {
            try {
                const response = await fetch(`/api/projects/${projectId}/artifacts`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(artifactData)
                });
                
                if (!response.ok) {
                    throw new Error(`Error creating artifact: ${response.status} ${response.statusText}`);
                }
                
                return await response.json();
            } catch (error) {
                console.error('Error creating artifact:', error);
                throw error;
            }
        },
        
        /**
         * Get artifacts for a project
         * @param {string} projectId - The project ID
         * @returns {Promise} Promise that resolves to the artifact list
         */
        getArtifacts: async function(projectId) {
            try {
                const response = await fetch(`/api/projects/${projectId}/artifacts`);
                if (!response.ok) {
                    throw new Error(`Error fetching artifacts: ${response.status} ${response.statusText}`);
                }
                return await response.json();
            } catch (error) {
                console.error('Error fetching artifacts:', error);
                throw error;
            }
        }
    }
};