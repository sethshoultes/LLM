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
         * Get token information for a project
         * @param {string} projectId - The project ID
         * @returns {Promise} Promise that resolves to the token information
         */
        getTokenInfo: async function(projectId) {
            try {
                const response = await fetch(`/api/tokens/info?project_id=${encodeURIComponent(projectId)}`);
                if (!response.ok) {
                    throw new Error(`Error fetching token info: ${response.status} ${response.statusText}`);
                }
                return await response.json();
            } catch (error) {
                console.error('Error fetching token info:', error);
                throw error;
            }
        }
    }
};