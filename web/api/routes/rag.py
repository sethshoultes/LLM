#!/usr/bin/env python3
"""
API routes for RAG in the LLM Platform.

Provides routes for managing projects, documents, searches, and RAG functionality.
"""

import sys
import logging
from typing import Dict, List, Any, Optional, Union

# Import from parent package
from web.api import logger

# Import from web server modules
from web.router import Router

# Import schemas and controllers
from web.api.responses import success_response, error_response, not_found_response

# Import RAG API handler
try:
    from rag_support.api_extensions import api_handler as rag_api_handler
    HAS_RAG = True
except ImportError:
    logger.warning("rag_support.api_extensions not found. RAG routes will not be available.")
    HAS_RAG = False


def register_rag_routes(router: Router) -> Router:
    """
    Register RAG-related API routes.
    
    Args:
        router: Router to register routes with
        
    Returns:
        Router with routes registered
    """
    if not HAS_RAG:
        # Register placeholder route that returns an error
        @router.all("/projects{path:.*}")
        def rag_disabled(request, response):
            """Handle RAG API requests when RAG is disabled."""
            status, data = error_response(
                error="RAG support is not available",
                detail="The RAG support modules could not be imported",
                code="rag_disabled",
                status=501
            )
            response.status_code = status
            response.json(data)
        
        return router
    
    # Create route group for RAG
    rag_group = router.group("/projects")
    
    # Generic handler that delegates to the RAG API handler
    def rag_handler(request, response):
        """Handle RAG API requests by delegating to the RAG API handler."""
        try:
            # Get full path
            path_suffix = request.path_params.get("path", "")
            full_path = f"/api/projects{path_suffix}"
            
            # Process query parameters
            query_params = request.query_params
            
            # Get request body
            body = request.body
            
            # Call RAG API handler
            status_code, result = rag_api_handler.handle_request(
                path=full_path,
                method=request.method,
                query_params=query_params,
                body=body
            )
            
            # Set response
            response.status_code = status_code
            response.json(result)
        except Exception as e:
            logger.error(f"Error handling RAG API request: {e}")
            status, data = error_response(
                error=e,
                detail="Failed to process RAG API request",
                code="rag_api_error",
                status=500
            )
            response.status_code = status
            response.json(data)
    
    # Register generic handler for all RAG routes
    @rag_group.all("{path:.*}")
    def catch_all_rag(request, response):
        """Catch-all route for all RAG API endpoints."""
        rag_handler(request, response)
    
    # Register common RAG endpoints for better documentation
    
    # Projects
    @rag_group.get("/")
    def list_projects(request, response):
        """List all projects."""
        rag_handler(request, response)
    
    @rag_group.post("/")
    def create_project(request, response):
        """Create a new project."""
        rag_handler(request, response)
    
    @rag_group.get("/{project_id}")
    def get_project(request, response):
        """Get a specific project."""
        rag_handler(request, response)
    
    @rag_group.delete("/{project_id}")
    def delete_project(request, response):
        """Delete a project."""
        rag_handler(request, response)
    
    # Documents
    @rag_group.get("/{project_id}/documents")
    def list_documents(request, response):
        """List all documents in a project."""
        rag_handler(request, response)
    
    @rag_group.post("/{project_id}/documents")
    def create_document(request, response):
        """Create a new document in a project."""
        rag_handler(request, response)
    
    @rag_group.get("/{project_id}/documents/{doc_id}")
    def get_document(request, response):
        """Get a specific document."""
        rag_handler(request, response)
    
    @rag_group.delete("/{project_id}/documents/{doc_id}")
    def delete_document(request, response):
        """Delete a document."""
        rag_handler(request, response)
    
    # Search
    @rag_group.get("/{project_id}/search")
    def search_documents(request, response):
        """Search documents in a project."""
        rag_handler(request, response)
    
    # Suggestions
    @rag_group.get("/{project_id}/suggest")
    def suggest_documents(request, response):
        """Get document suggestions for a query."""
        rag_handler(request, response)
    
    # Chats
    @rag_group.get("/{project_id}/chats")
    def list_chats(request, response):
        """List all chats in a project."""
        rag_handler(request, response)
    
    @rag_group.post("/{project_id}/chats")
    def create_chat(request, response):
        """Create a new chat in a project."""
        rag_handler(request, response)
    
    @rag_group.post("/{project_id}/chats/{chat_id}/messages")
    def add_message(request, response):
        """Add a message to a chat."""
        rag_handler(request, response)
    
    # Merge routes back to main router
    rag_group.merge()
    
    # Return router
    return router