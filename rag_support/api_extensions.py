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
        
    def _format_error_response(self, status_code: int, error: str, 
                              detail: str = None, code: str = None) -> Tuple[int, Dict[str, Any]]:
        """Format a standardized error response
        
        Args:
            status_code: HTTP status code
            error: Short error message
            detail: Detailed error explanation
            code: Error code for client handling
            
        Returns:
            Tuple of (status_code, response_dict)
        """
        response = {
            "error": error,
            "status": status_code
        }
        
        if detail:
            response["detail"] = detail
            
        if code:
            response["code"] = code
            
        return status_code, response
        
    def _format_success_response(self, data: Any, message: str = None, 
                               meta: Dict[str, Any] = None) -> Tuple[int, Dict[str, Any]]:
        """Format a standardized success response
        
        Args:
            data: Response data
            message: Optional success message
            meta: Optional metadata
            
        Returns:
            Tuple of (200, response_dict)
        """
        response = {
            "status": "success",
            "data": data
        }
        
        if message:
            response["message"] = message
            
        if meta:
            response["meta"] = meta
            
        return 200, response
        
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
            return self._format_error_response(404, "Not found", "The provided path does not start with /api")
        
        # Remove 'api' prefix
        parts = parts[1:]
        
        if len(parts) == 0:
            return self._format_error_response(404, "Invalid API endpoint", "No endpoint specified after /api")
        
        # Token estimation endpoint
        if parts[0] == 'tokens' and method == 'POST':
            return self._estimate_tokens(body)
        
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
        try:
            projects = project_manager.get_projects()
            meta = {
                "count": len(projects),
                "timestamp": datetime.now().isoformat()
            }
            return self._format_success_response(
                data=projects,
                message="Projects retrieved successfully",
                meta=meta
            )
        except Exception as e:
            return self._format_error_response(
                500,
                "Failed to retrieve projects",
                f"Error: {str(e)}",
                "projects_retrieval_error"
            )
    
    def _create_project(self, data: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        """Create a new project"""
        try:
            # Validate required inputs
            name = data.get('name', '').strip()
            description = data.get('description', '').strip()
            
            if not name:
                return self._format_error_response(
                    400, 
                    "Missing required field", 
                    "Project name is required", 
                    "missing_required_field"
                )
            
            # Create project
            project_id = project_manager.create_project(name, description)
            project = project_manager.get_project(project_id)
            
            if not project:
                return self._format_error_response(
                    500, 
                    "Failed to create project", 
                    "Project was created but could not be retrieved", 
                    "project_creation_error"
                )
            
            # Return success response
            return 201, {
                "status": "success",
                "message": "Project created successfully",
                "data": project
            }
        except Exception as e:
            return self._format_error_response(
                500,
                "Project creation failed",
                f"Error: {str(e)}",
                "project_creation_error"
            )
    
    def _get_project(self, project_id: str) -> Tuple[int, Dict[str, Any]]:
        """Get a project by ID"""
        try:
            # Parameter validation
            if not project_id:
                return self._format_error_response(
                    400, 
                    "Missing project ID", 
                    "Project ID is required", 
                    "missing_project_id"
                )
            
            # Get project
            project = project_manager.get_project(project_id)
            
            if project is None:
                return self._format_error_response(
                    404, 
                    "Project not found", 
                    f"No project exists with ID: {project_id}", 
                    "project_not_found"
                )
            
            # Format document counts for UI display
            meta = {
                "retrieved_at": datetime.now().isoformat(),
                "document_count": project.get("document_count", 0),
                "chat_count": project.get("chat_count", 0),
                "artifact_count": project.get("artifact_count", 0)
            }
            
            # Return success response
            return self._format_success_response(
                data=project,
                message="Project retrieved successfully",
                meta=meta
            )
        except Exception as e:
            return self._format_error_response(
                500,
                "Failed to retrieve project",
                f"Error: {str(e)}",
                "project_retrieval_error"
            )
    
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
        try:
            # Validate parameters
            if not project_id:
                return self._format_error_response(
                    400,
                    "Missing project ID",
                    "Project ID is required for search",
                    "missing_project_id"
                )
            
            # Check project exists
            project = project_manager.get_project(project_id)
            if not project:
                return self._format_error_response(
                    404,
                    "Project not found",
                    f"No project exists with ID: {project_id}",
                    "project_not_found"
                )
            
            # Handle empty query
            if not query:
                return self._format_success_response(
                    data=[],
                    message="Empty search query provided",
                    meta={"count": 0, "query": query}
                )
            
            # Perform search
            start_time = time.time()
            results = search_engine.search(project_id, query)
            search_time = time.time() - start_time
            
            # Return results with metadata
            meta = {
                "count": len(results),
                "query": query,
                "project_id": project_id,
                "project_name": project.get("name", "Unknown Project"),
                "search_time_ms": round(search_time * 1000, 2)
            }
            
            return self._format_success_response(
                data=results,
                message=f"Found {len(results)} documents matching query",
                meta=meta
            )
        except Exception as e:
            return self._format_error_response(
                500,
                "Search failed",
                f"Error: {str(e)}",
                "search_error"
            )
    
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
        try:
            # Parameter validation
            if not project_id:
                return self._format_error_response(
                    400, 
                    "Missing project ID", 
                    "Project ID is required", 
                    "missing_project_id"
                )
                
            if not chat_id:
                return self._format_error_response(
                    400, 
                    "Missing chat ID", 
                    "Chat ID is required", 
                    "missing_chat_id"
                )
            
            # Verify project exists
            project = project_manager.get_project(project_id)
            if not project:
                return self._format_error_response(
                    404, 
                    "Project not found", 
                    f"No project exists with ID: {project_id}", 
                    "project_not_found"
                )
            
            # Verify chat exists
            chat = project_manager.get_chat(project_id, chat_id)
            if not chat:
                return self._format_error_response(
                    404, 
                    "Chat not found", 
                    f"No chat exists with ID: {chat_id} in project {project_id}", 
                    "chat_not_found"
                )
            
            # Extract and validate parameters
            content = data.get('content', '').strip()
            context_docs = data.get('context_docs', [])
            modelPath = data.get('model', '')
            temperature = data.get('temperature', 0.7)
            max_tokens = data.get('max_tokens', 1024)
            top_p = data.get('top_p', 0.95)
            
            # Validate content
            if not content:
                return self._format_error_response(
                    400, 
                    "Missing message content", 
                    "Message content is required", 
                    "missing_message_content"
                )
            
            # Add user message to chat
            success = project_manager.add_message(project_id, chat_id, 'user', content)
            
            if not success:
                return self._format_error_response(
                    500, 
                    "Failed to add message", 
                    "The message could not be saved to the chat", 
                    "message_save_error"
                )
            
            # Load context documents
            start_time = time.time()
            context_content = ''
            context_metadata = []
            total_context_tokens = 0
            
            if context_docs:
                for doc_id in context_docs:
                    doc = project_manager.get_document(project_id, doc_id)
                    if doc:
                        # Prepare document content
                        doc_title = doc.get('title', 'Document')
                        doc_content = doc.get('content', '')
                        doc_text = f"# {doc_title}\n\n{doc_content}\n\n"
                        
                        # Estimate tokens for this document
                        doc_tokens = search_engine.estimate_token_count(doc_text)
                        total_context_tokens += doc_tokens
                        
                        # Add document to context
                        context_content += doc_text
                        context_metadata.append({
                            "id": doc_id,
                            "title": doc_title,
                            "tokens": doc_tokens
                        })
            
            # Get AI response by connecting to the LLM generation code
            try:
                import sys
                from pathlib import Path
                
                # Ensure the scripts directory is in the path
                scripts_dir = Path(BASE_DIR) / "scripts"
                if str(scripts_dir) not in sys.path:
                    sys.path.append(str(scripts_dir))
                
                # Import the inference module
                import minimal_inference_quiet as minimal_inference
                
                # Get available models if none specified
                if not modelPath:
                    models = minimal_inference.list_models()
                    if models and len(models) > 0:
                        modelPath = models[0]["path"]
                    else:
                        raise ValueError("No models available and no model specified")
                
                # Prepare system message with context
                system_prompt = "You are a helpful assistant."
                if context_content:
                    system_prompt += "\n\nUse the following information to answer the user's question:\n\n" + context_content
                
                # Generate response
                generation_start = time.time()
                result = minimal_inference.generate(
                    model_path=modelPath,
                    prompt=content,
                    system_prompt=system_prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p
                )
                generation_time = time.time() - generation_start
                
                if "error" in result:
                    # Handle generation error
                    error_message = f"Error generating response: {result['error']}"
                    
                    # Save error as assistant response
                    project_manager.add_message(
                        project_id, 
                        chat_id, 
                        'assistant', 
                        error_message,
                        context_docs
                    )
                    
                    return self._format_error_response(
                        500,
                        "LLM generation failed",
                        error_message,
                        "llm_generation_error"
                    )
                else:
                    # Handle successful generation
                    response = result['response']
                    
                    # Save the assistant's response
                    project_manager.add_message(
                        project_id, 
                        chat_id, 
                        'assistant', 
                        response, 
                        context_docs
                    )
                    
                    # Build response metadata
                    meta = {
                        "chat_id": chat_id,
                        "project_id": project_id,
                        "model_path": modelPath,
                        "model_type": result.get('model_type'),
                        "model_format": result.get('model_format'),
                        "tokens_generated": result.get('tokens_generated', 0),
                        "generation_time_s": result.get('time_taken', generation_time),
                        "total_time_s": time.time() - start_time,
                        "context_documents": {
                            "count": len(context_docs),
                            "tokens": total_context_tokens,
                            "sources": context_metadata
                        },
                        "parameters": {
                            "temperature": temperature,
                            "max_tokens": max_tokens,
                            "top_p": top_p
                        }
                    }
                    
                    # Return success response
                    return self._format_success_response(
                        data={
                            "response": response,
                            "chat_id": chat_id,
                            "message_id": None  # In future, could return the created message ID
                        },
                        message="LLM response generated successfully",
                        meta=meta
                    )
            
            except ImportError as e:
                error_message = f"Error: Could not load inference module. {str(e)}"
                project_manager.add_message(project_id, chat_id, 'assistant', error_message, context_docs)
                
                return self._format_error_response(
                    500,
                    "Inference module not available",
                    error_message,
                    "inference_module_error"
                )
            
            except Exception as e:
                error_message = f"Error generating response: {str(e)}"
                project_manager.add_message(project_id, chat_id, 'assistant', error_message, context_docs)
                
                return self._format_error_response(
                    500,
                    "LLM generation failed",
                    error_message,
                    "llm_generation_error"
                )
                
        except Exception as e:
            return self._format_error_response(
                500,
                "Chat message processing failed",
                f"Error: {str(e)}",
                "message_processing_error"
            )
    
    # Token estimation methods
    def _estimate_tokens(self, data: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        """Estimate token counts for text and provide context window information"""
        try:
            # Extract parameters
            text = data.get('text', '')
            context_docs = data.get('context_docs', [])
            project_id = data.get('project_id', '')
            model_path = data.get('model', '')
            
            # Parameter validation
            if not text and not context_docs:
                return self._format_error_response(
                    400,
                    "Missing required parameters",
                    "Either text or context_docs must be provided",
                    "missing_parameters"
                )
            
            if context_docs and not project_id:
                return self._format_error_response(
                    400,
                    "Missing project ID",
                    "Project ID is required when providing context_docs",
                    "missing_project_id"
                )
            
            # Import search engine for token estimation
            from rag_support.utils.search import search_engine
            
            # Get model context window size (default to 4096 if not specified)
            context_window = 4096
            reserved_tokens = 1024  # Reserved for system prompt and response
            
            # Try to get model-specific context window
            if model_path:
                try:
                    import sys
                    from pathlib import Path
                    
                    # Ensure the scripts directory is in the path
                    scripts_dir = Path(BASE_DIR) / "scripts"
                    if str(scripts_dir) not in sys.path:
                        sys.path.append(str(scripts_dir))
                    
                    # Import the inference module
                    import minimal_inference_quiet as minimal_inference
                    
                    # Get model info if available
                    models = minimal_inference.list_models()
                    for model in models:
                        if model['path'] == model_path:
                            # Some models expose their context window
                            if 'context_window' in model:
                                context_window = model['context_window']
                except Exception:
                    # If we can't get model-specific context window, use default
                    pass
                    
            # Initialize token counts
            total_tokens = 0
            text_tokens = 0
            context_tokens = 0
            contexts = []
            
            # Estimate text tokens
            if text:
                text_tokens = search_engine.estimate_token_count(text)
                total_tokens += text_tokens
            
            # Load and estimate context tokens
            if context_docs and project_id:
                # Verify project exists
                project = project_manager.get_project(project_id)
                if not project:
                    return self._format_error_response(
                        404,
                        "Project not found",
                        f"No project exists with ID: {project_id}",
                        "project_not_found"
                    )
                
                # Process each document
                for doc_id in context_docs:
                    doc = project_manager.get_document(project_id, doc_id)
                    if doc:
                        content = doc.get('content', '')
                        title = doc.get('title', 'Document')
                        doc_text = f"# {title}\n\n{content}"
                        doc_tokens = search_engine.estimate_token_count(doc_text)
                        
                        contexts.append({
                            "id": doc_id,
                            "title": title,
                            "tokens": doc_tokens,
                            "percentage": 0  # Will update after calculating total
                        })
                        
                        context_tokens += doc_tokens
                
                # Update percentages
                if context_tokens > 0:
                    for context in contexts:
                        context["percentage"] = round((context["tokens"] / context_tokens) * 100, 1)
                
                # Add to total tokens
                total_tokens += context_tokens
            
            # Calculate available tokens and percentages
            available_tokens = context_window - total_tokens - reserved_tokens
            available_percentage = round((available_tokens / context_window) * 100, 1)
            usage_percentage = round((total_tokens / context_window) * 100, 1)
            is_over_limit = available_tokens < 0
            
            # Build response data
            token_data = {
                "total_tokens": total_tokens,
                "text_tokens": text_tokens,
                "context_tokens": context_tokens,
                "contexts": contexts,
                "model_context_window": context_window,
                "available_tokens": available_tokens,
                "available_percentage": available_percentage,
                "usage_percentage": usage_percentage,
                "is_over_limit": is_over_limit,
                "reserved_tokens": reserved_tokens
            }
            
            # Build metadata
            meta = {
                "timestamp": datetime.now().isoformat(),
                "model_path": model_path,
                "context_count": len(context_docs),
                "estimation_method": "character-based-approximation"
            }
            
            # Return formatted response
            return self._format_success_response(
                data=token_data,
                message="Token estimation completed successfully",
                meta=meta
            )
            
        except Exception as e:
            return self._format_error_response(
                500,
                "Token estimation failed",
                f"Error: {str(e)}",
                "token_estimation_error"
            )
    
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