#!/usr/bin/env python3
# api_extensions.py - Extensions to the quiet_interface.py API for RAG support

import os
import json
import urllib.parse
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple

# Import BASE_DIR from rag_support
try:
    from rag_support import BASE_DIR
except ImportError:
    # Fallback if the import fails
    import os
    SCRIPT_DIR = Path(__file__).resolve().parent
    BASE_DIR = SCRIPT_DIR.parent
    # Use environment variable if available
    BASE_DIR = Path(os.environ.get("LLM_BASE_DIR", str(BASE_DIR)))

# Import RAG utilities
from rag_support.utils import project_manager, search_engine

class RagApiHandler:
    """Handles RAG-related API requests for the quiet_interface"""
    
    def __init__(self, base_url="/api"):
        """Initialize the API handler"""
        self.base_url = base_url
        
    def handle_request(self, path: str, method: str, query_params: Dict[str, str] = None, 
                     body: Dict[str, Any] = None) -> Tuple[int, Dict[str, Any]]:
        """Handle an API request and return a response
        
        Args:
            path: The request path
            method: The HTTP method (GET, POST, PUT, DELETE)
            query_params: Query parameters dictionary
            body: Request body (for POST, PUT)
            
        Returns:
            Tuple of (status_code, response_dict)
        """
        query_params = query_params or {}
        body = body or {}
        
        # Parse path to determine endpoint
        parts = path.strip('/').split('/')
        
        if len(parts) == 0 or parts[0] != 'api':
            return 404, {"error": "Not found"}
        
        # Remove 'api' prefix
        parts = parts[1:]
        
        if len(parts) == 0:
            return 404, {"error": "Invalid API endpoint"}
        
        # Project endpoints
        if parts[0] == 'projects':
            if len(parts) == 1:
                # /api/projects
                if method == 'GET':
                    return self._list_projects()
                elif method == 'POST':
                    return self._create_project(body)
                else:
                    return 405, {"error": "Method not allowed"}
            
            elif len(parts) == 2:
                # /api/projects/{id}
                project_id = parts[1]
                if method == 'GET':
                    return self._get_project(project_id)
                elif method == 'DELETE':
                    return self._delete_project(project_id)
                else:
                    return 405, {"error": "Method not allowed"}
            
            elif len(parts) == 3 and parts[2] == 'documents':
                # /api/projects/{id}/documents
                project_id = parts[1]
                if method == 'GET':
                    return self._list_documents(project_id)
                elif method == 'POST':
                    return self._create_document(project_id, body)
                else:
                    return 405, {"error": "Method not allowed"}
            
            elif len(parts) == 4 and parts[2] == 'documents':
                # /api/projects/{id}/documents/{doc_id}
                project_id = parts[1]
                doc_id = parts[3]
                if method == 'GET':
                    return self._get_document(project_id, doc_id)
                elif method == 'DELETE':
                    return self._delete_document(project_id, doc_id)
                else:
                    return 405, {"error": "Method not allowed"}
            
            elif len(parts) == 3 and parts[2] == 'search':
                # /api/projects/{id}/search
                project_id = parts[1]
                query = query_params.get('q', '')
                return self._search_documents(project_id, query)
            
            elif len(parts) == 3 and parts[2] == 'suggest':
                # /api/projects/{id}/suggest
                project_id = parts[1]
                query = query_params.get('q', '')
                return self._suggest_documents(project_id, query)
            
            elif len(parts) == 3 and parts[2] == 'chats':
                # /api/projects/{id}/chats
                project_id = parts[1]
                if method == 'GET':
                    return self._list_chats(project_id)
                elif method == 'POST':
                    return self._create_chat(project_id, body)
                else:
                    return 405, {"error": "Method not allowed"}
            
            elif len(parts) == 5 and parts[2] == 'chats' and parts[4] == 'messages':
                # /api/projects/{id}/chats/{chat_id}/messages
                project_id = parts[1]
                chat_id = parts[3]
                if method == 'POST':
                    return self._add_message(project_id, chat_id, body)
                else:
                    return 405, {"error": "Method not allowed"}
            
            elif len(parts) == 3 and parts[2] == 'artifacts':
                # /api/projects/{id}/artifacts
                project_id = parts[1]
                if method == 'GET':
                    return self._list_artifacts(project_id)
                elif method == 'POST':
                    return self._create_artifact(project_id, body)
                else:
                    return 405, {"error": "Method not allowed"}
            
            elif len(parts) == 4 and parts[2] == 'artifacts':
                # /api/projects/{id}/artifacts/{artifact_id}
                project_id = parts[1]
                artifact_id = parts[3]
                if method == 'GET':
                    return self._get_artifact(project_id, artifact_id)
                elif method == 'DELETE':
                    return self._delete_artifact(project_id, artifact_id)
                else:
                    return 405, {"error": "Method not allowed"}
        
        return 404, {"error": "Endpoint not found"}
    
    # Project methods
    def _list_projects(self) -> Tuple[int, Dict[str, Any]]:
        """List all projects"""
        projects = project_manager.get_projects()
        return 200, {"projects": projects}
    
    def _create_project(self, data: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        """Create a new project"""
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        
        if not name:
            return 400, {"error": "Project name is required"}
        
        project_id = project_manager.create_project(name, description)
        project = project_manager.get_project(project_id)
        
        return 201, project
    
    def _get_project(self, project_id: str) -> Tuple[int, Dict[str, Any]]:
        """Get a project by ID"""
        project = project_manager.get_project(project_id)
        
        if project is None:
            return 404, {"error": "Project not found"}
        
        return 200, project
    
    def _delete_project(self, project_id: str) -> Tuple[int, Dict[str, Any]]:
        """Delete a project"""
        success = project_manager.delete_project(project_id)
        
        if not success:
            return 404, {"error": "Project not found"}
        
        return 200, {"message": "Project deleted"}
    
    # Document methods
    def _list_documents(self, project_id: str) -> Tuple[int, Dict[str, Any]]:
        """List all documents in a project"""
        if not project_manager.get_project(project_id):
            return 404, {"error": "Project not found"}
        
        documents = project_manager.list_documents(project_id)
        return 200, {"documents": documents}
    
    def _create_document(self, project_id: str, data: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        """Create a new document"""
        if not project_manager.get_project(project_id):
            return 404, {"error": "Project not found"}
        
        title = data.get('title', '').strip()
        content = data.get('content', '').strip()
        tags = data.get('tags', [])
        
        if not title:
            return 400, {"error": "Document title is required"}
        
        if not content:
            return 400, {"error": "Document content is required"}
        
        doc_id = project_manager.add_document(project_id, title, content, tags)
        
        if doc_id is None:
            return 500, {"error": "Failed to create document"}
        
        return 201, {"id": doc_id, "title": title}
    
    def _get_document(self, project_id: str, doc_id: str) -> Tuple[int, Dict[str, Any]]:
        """Get a document by ID"""
        if not project_manager.get_project(project_id):
            return 404, {"error": "Project not found"}
        
        document = project_manager.get_document(project_id, doc_id)
        
        if document is None:
            return 404, {"error": "Document not found"}
        
        return 200, document
    
    def _delete_document(self, project_id: str, doc_id: str) -> Tuple[int, Dict[str, Any]]:
        """Delete a document"""
        if not project_manager.get_project(project_id):
            return 404, {"error": "Project not found"}
        
        success = project_manager.delete_document(project_id, doc_id)
        
        if not success:
            return 404, {"error": "Document not found"}
        
        return 200, {"message": "Document deleted"}
    
    def _search_documents(self, project_id: str, query: str) -> Tuple[int, Dict[str, Any]]:
        """Search documents in a project"""
        if not project_manager.get_project(project_id):
            return 404, {"error": "Project not found"}
        
        if not query:
            return 200, {"results": []}
        
        results = search_engine.search(project_id, query)
        return 200, {"results": results}
    
    def _suggest_documents(self, project_id: str, query: str) -> Tuple[int, Dict[str, Any]]:
        """Suggest relevant documents for a query"""
        if not project_manager.get_project(project_id):
            return 404, {"error": "Project not found"}
        
        if not query:
            return 200, {"suggestions": []}
        
        # Limit to a few top results
        results = search_engine.search(project_id, query, max_results=3)
        return 200, {"suggestions": results}
    
    # Chat methods
    def _list_chats(self, project_id: str) -> Tuple[int, Dict[str, Any]]:
        """List all chats in a project"""
        if not project_manager.get_project(project_id):
            return 404, {"error": "Project not found"}
        
        chats = project_manager.list_chats(project_id)
        return 200, {"chats": chats}
    
    def _create_chat(self, project_id: str, data: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        """Create a new chat"""
        if not project_manager.get_project(project_id):
            return 404, {"error": "Project not found"}
        
        title = data.get('title', '').strip()
        
        chat_id = project_manager.add_chat(project_id, title)
        
        if chat_id is None:
            return 500, {"error": "Failed to create chat"}
        
        return 201, {"id": chat_id}
    
    def _add_message(self, project_id: str, chat_id: str, data: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        """Add a message to a chat and get AI response"""
        if not project_manager.get_project(project_id):
            return 404, {"error": "Project not found"}
        
        chat = project_manager.get_chat(project_id, chat_id)
        if not chat:
            return 404, {"error": "Chat not found"}
        
        content = data.get('content', '').strip()
        context_docs = data.get('context_docs', [])
        
        if not content:
            return 400, {"error": "Message content is required"}
        
        # Add user message to chat
        success = project_manager.add_message(project_id, chat_id, 'user', content)
        
        if not success:
            return 500, {"error": "Failed to add message"}
        
        # Load any context documents
        context_content = ''
        if context_docs:
            for doc_id in context_docs:
                doc = project_manager.get_document(project_id, doc_id)
                if doc:
                    # Add document content to context
                    context_content += f"# {doc.get('title', 'Document')}\n\n"
                    context_content += doc.get('content', '') + "\n\n"
        
        # Get AI response - this is a placeholder, the actual implementation
        # will depend on how we connect to the existing LLM generation code
        # in quiet_interface.py
        response = "This is a placeholder AI response. In the final implementation, " + \
                  "we will connect to the existing LLM generation code."
        
        # Save the assistant's response
        project_manager.add_message(project_id, chat_id, 'assistant', response, context_docs)
        
        return 200, {
            "response": response,
            "chat_id": chat_id,
            "context_used": bool(context_docs)
        }
    
    # Artifact methods
    def _list_artifacts(self, project_id: str) -> Tuple[int, Dict[str, Any]]:
        """List all artifacts in a project"""
        if not project_manager.get_project(project_id):
            return 404, {"error": "Project not found"}
        
        artifacts = project_manager.list_artifacts(project_id)
        return 200, {"artifacts": artifacts}
    
    def _create_artifact(self, project_id: str, data: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        """Create a new artifact"""
        if not project_manager.get_project(project_id):
            return 404, {"error": "Project not found"}
        
        title = data.get('title', '').strip()
        content = data.get('content', '').strip()
        file_ext = data.get('file_ext', 'md').strip()
        
        if not content:
            return 400, {"error": "Artifact content is required"}
        
        artifact_id = project_manager.save_artifact(project_id, content, title, file_ext)
        
        if artifact_id is None:
            return 500, {"error": "Failed to create artifact"}
        
        return 201, {"id": artifact_id}
    
    def _get_artifact(self, project_id: str, artifact_id: str) -> Tuple[int, Dict[str, Any]]:
        """Get an artifact by ID"""
        if not project_manager.get_project(project_id):
            return 404, {"error": "Project not found"}
        
        artifact = project_manager.get_artifact(project_id, artifact_id)
        
        if artifact is None:
            return 404, {"error": "Artifact not found"}
        
        return 200, artifact
    
    def _delete_artifact(self, project_id: str, artifact_id: str) -> Tuple[int, Dict[str, Any]]:
        """Delete an artifact"""
        if not project_manager.get_project(project_id):
            return 404, {"error": "Project not found"}
        
        success = project_manager.delete_artifact(project_id, artifact_id)
        
        if not success:
            return 404, {"error": "Artifact not found"}
        
        return 200, {"message": "Artifact deleted"}

# Create a singleton instance
api_handler = RagApiHandler()