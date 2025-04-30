#!/usr/bin/env python3
"""
RAG API Controller Implementation.

This module implements the controller logic for RAG API routes,
handling project, document, and search operations.
"""

from typing import Dict, Any, Tuple, Optional, List
import json
import traceback
import logging

from web.api.controllers import Controller
from rag_support.utils.project_manager import project_manager
from rag_support.utils.search import search_engine, HAS_HYBRID_SEARCH
from rag_support.utils.context_manager import ContextManager

logger = logging.getLogger(__name__)


class RagController(Controller):
    """Controller for RAG API operations."""
    
    def __init__(self):
        """Initialize RAG controller."""
        super().__init__()
        self.project_manager = project_manager
        self.search_engine = search_engine
        self.context_manager = ContextManager()
    
    def list_projects(self) -> Tuple[int, Dict[str, Any]]:
        """List all RAG projects.
        
        Returns:
            Tuple containing status code and response dict
        """
        try:
            projects = self.project_manager.get_projects()
            
            # Add document counts to projects
            for project in projects:
                project_id = project.get('id')
                if project_id:
                    doc_count = len(self.project_manager.get_documents(project_id))
                    project['document_count'] = doc_count
            
            return self.format_success_response(
                projects,
                "Projects retrieved successfully",
                {"count": len(projects)}
            )
        except Exception as e:
            logger.error(f"Error listing projects: {str(e)}")
            return self.format_error_response(
                "Failed to retrieve projects",
                str(e),
                status_code=500
            )
    
    def get_project(self, project_id: str) -> Tuple[int, Dict[str, Any]]:
        """Get a specific RAG project.
        
        Args:
            project_id: ID of the project to retrieve
            
        Returns:
            Tuple containing status code and response dict
        """
        try:
            project = self.project_manager.get_project(project_id)
            if not project:
                return self.format_error_response(
                    "Project not found",
                    f"No project found with ID: {project_id}",
                    "project_not_found",
                    status_code=404
                )
            
            # Add document count
            doc_count = len(self.project_manager.get_documents(project_id))
            project['document_count'] = doc_count
            
            return self.format_success_response(
                project,
                f"Project {project_id} retrieved successfully"
            )
        except Exception as e:
            logger.error(f"Error retrieving project {project_id}: {str(e)}")
            return self.format_error_response(
                "Failed to retrieve project",
                str(e),
                status_code=500
            )
    
    def create_project(self, data: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        """Create a new RAG project.
        
        Args:
            data: Project data
            
        Returns:
            Tuple containing status code and response dict
        """
        try:
            if not data:
                return self.format_error_response(
                    "Invalid request",
                    "Request body is empty or not valid JSON",
                    "invalid_request"
                )
            
            # Create project
            project = self.project_manager.create_project(
                data['name'],
                data.get('description', '')
            )
            
            return self.format_success_response(
                project,
                "Project created successfully",
                status_code=201
            )
        except Exception as e:
            logger.error(f"Error creating project: {str(e)}")
            return self.format_error_response(
                "Failed to create project",
                str(e),
                status_code=500
            )
    
    def delete_project(self, project_id: str) -> Tuple[int, Dict[str, Any]]:
        """Delete a RAG project.
        
        Args:
            project_id: ID of the project to delete
            
        Returns:
            Tuple containing status code and response dict
        """
        try:
            # Check if project exists
            project = self.project_manager.get_project(project_id)
            if not project:
                return self.format_error_response(
                    "Project not found",
                    f"No project found with ID: {project_id}",
                    "project_not_found",
                    status_code=404
                )
            
            # Delete project
            success = self.project_manager.delete_project(project_id)
            if not success:
                return self.format_error_response(
                    "Failed to delete project",
                    "Project could not be deleted",
                    status_code=500
                )
            
            return self.format_success_response(
                {"id": project_id},
                "Project deleted successfully"
            )
        except Exception as e:
            logger.error(f"Error deleting project {project_id}: {str(e)}")
            return self.format_error_response(
                "Failed to delete project",
                str(e),
                status_code=500
            )
    
    def list_documents(self, project_id: str) -> Tuple[int, Dict[str, Any]]:
        """List all documents in a RAG project.
        
        Args:
            project_id: ID of the project
            
        Returns:
            Tuple containing status code and response dict
        """
        try:
            # Check if project exists
            project = self.project_manager.get_project(project_id)
            if not project:
                return self.format_error_response(
                    "Project not found",
                    f"No project found with ID: {project_id}",
                    "project_not_found",
                    status_code=404
                )
            
            documents = self.project_manager.get_documents(project_id)
            
            return self.format_success_response(
                documents,
                "Documents retrieved successfully",
                {"count": len(documents), "project_id": project_id}
            )
        except Exception as e:
            logger.error(f"Error listing documents for project {project_id}: {str(e)}")
            return self.format_error_response(
                "Failed to retrieve documents",
                str(e),
                status_code=500
            )
    
    def get_document(self, project_id: str, document_id: str) -> Tuple[int, Dict[str, Any]]:
        """Get a specific document from a RAG project.
        
        Args:
            project_id: ID of the project
            document_id: ID of the document
            
        Returns:
            Tuple containing status code and response dict
        """
        try:
            # Check if project exists
            project = self.project_manager.get_project(project_id)
            if not project:
                return self.format_error_response(
                    "Project not found",
                    f"No project found with ID: {project_id}",
                    "project_not_found",
                    status_code=404
                )
            
            document = self.project_manager.get_document(project_id, document_id)
            if not document:
                return self.format_error_response(
                    "Document not found",
                    f"No document found with ID: {document_id} in project {project_id}",
                    "document_not_found",
                    status_code=404
                )
            
            return self.format_success_response(
                document,
                f"Document {document_id} retrieved successfully"
            )
        except Exception as e:
            logger.error(f"Error retrieving document {document_id} from project {project_id}: {str(e)}")
            return self.format_error_response(
                "Failed to retrieve document",
                str(e),
                status_code=500
            )
    
    def create_document(self, project_id: str, data: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        """Create a new document in a RAG project.
        
        Args:
            project_id: ID of the project
            data: Document data
            
        Returns:
            Tuple containing status code and response dict
        """
        try:
            # Check if project exists
            project = self.project_manager.get_project(project_id)
            if not project:
                return self.format_error_response(
                    "Project not found",
                    f"No project found with ID: {project_id}",
                    "project_not_found",
                    status_code=404
                )
            
            if not data:
                return self.format_error_response(
                    "Invalid request",
                    "Request body is empty or not valid JSON",
                    "invalid_request"
                )
            
            # Create document
            document = self.project_manager.add_document(
                project_id,
                data['title'],
                data['content'],
                data.get('tags', [])
            )
            
            return self.format_success_response(
                document,
                "Document created successfully",
                status_code=201
            )
        except Exception as e:
            logger.error(f"Error creating document in project {project_id}: {str(e)}")
            return self.format_error_response(
                "Failed to create document",
                str(e),
                status_code=500
            )
    
    def delete_document(self, project_id: str, document_id: str) -> Tuple[int, Dict[str, Any]]:
        """Delete a document from a RAG project.
        
        Args:
            project_id: ID of the project
            document_id: ID of the document
            
        Returns:
            Tuple containing status code and response dict
        """
        try:
            # Check if project exists
            project = self.project_manager.get_project(project_id)
            if not project:
                return self.format_error_response(
                    "Project not found",
                    f"No project found with ID: {project_id}",
                    "project_not_found",
                    status_code=404
                )
            
            # Check if document exists
            document = self.project_manager.get_document(project_id, document_id)
            if not document:
                return self.format_error_response(
                    "Document not found",
                    f"No document found with ID: {document_id} in project {project_id}",
                    "document_not_found",
                    status_code=404
                )
            
            # Delete document
            success = self.project_manager.delete_document(project_id, document_id)
            if not success:
                return self.format_error_response(
                    "Failed to delete document",
                    "Document could not be deleted",
                    status_code=500
                )
            
            return self.format_success_response(
                {"id": document_id, "project_id": project_id},
                "Document deleted successfully"
            )
        except Exception as e:
            logger.error(f"Error deleting document {document_id} from project {project_id}: {str(e)}")
            return self.format_error_response(
                "Failed to delete document",
                str(e),
                status_code=500
            )
    
    def search_documents(
        self, 
        project_id: str, 
        query: str,
        options: Dict[str, Any] = None
    ) -> Tuple[int, Dict[str, Any]]:
        """Search for documents in a RAG project.
        
        Args:
            project_id: ID of the project
            query: Search query
            options: Optional search options
            
        Returns:
            Tuple containing status code and response dict
        """
        try:
            # Check if project exists
            project = self.project_manager.get_project(project_id)
            if not project:
                return self.format_error_response(
                    "Project not found",
                    f"No project found with ID: {project_id}",
                    "project_not_found",
                    status_code=404
                )
            
            # Get search options if provided
            if options:
                max_results = options.get('max_results', 10)
                semantic_weight = options.get('semantic_weight', 0.5)
                keyword_weight = options.get('keyword_weight', 0.5)
            else:
                max_results = 10
                semantic_weight = 0.5
                keyword_weight = 0.5
            
            # Determine search type
            search_type = "keyword"
            if HAS_HYBRID_SEARCH:
                from rag_support.utils.hybrid_search import hybrid_search
                results = hybrid_search(
                    project_id, 
                    query, 
                    semantic_weight=semantic_weight,
                    keyword_weight=keyword_weight,
                    max_results=max_results
                )
                search_type = "hybrid"
            else:
                results = self.search_engine.search(project_id, query, max_results=max_results)
            
            return self.format_success_response(
                results,
                "Search completed successfully",
                {
                    "count": len(results),
                    "query": query,
                    "search_type": search_type,
                    "max_results": max_results
                }
            )
        except Exception as e:
            logger.error(f"Error searching documents in project {project_id}: {str(e)}")
            return self.format_error_response(
                "Failed to search documents",
                str(e),
                status_code=500
            )
    
    def generate_context(
        self, 
        project_id: str, 
        query: str,
        max_tokens: int = 2000,
        document_ids: Optional[List[str]] = None
    ) -> Tuple[int, Dict[str, Any]]:
        """Generate context for a query from project documents.
        
        Args:
            project_id: ID of the project
            query: Query text
            max_tokens: Maximum tokens for context
            document_ids: Optional list of document IDs to use
            
        Returns:
            Tuple containing status code and response dict
        """
        try:
            # Check if project exists
            project = self.project_manager.get_project(project_id)
            if not project:
                return self.format_error_response(
                    "Project not found",
                    f"No project found with ID: {project_id}",
                    "project_not_found",
                    status_code=404
                )
            
            # Generate context
            context, used_docs, truncated = self.context_manager.generate_context(
                project_id,
                query,
                max_tokens=max_tokens,
                document_ids=document_ids
            )
            
            return self.format_success_response(
                {
                    "context": context,
                    "documents": used_docs,
                    "truncated": truncated
                },
                "Context generated successfully",
                {
                    "tokens": len(context.split()),
                    "document_count": len(used_docs)
                }
            )
        except Exception as e:
            logger.error(f"Error generating context for project {project_id}: {str(e)}")
            return self.format_error_response(
                "Failed to generate context",
                str(e),
                status_code=500
            )
    
    def handle_request(
        self,
        path: str,
        method: str,
        query_params: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None
    ) -> Tuple[int, Dict[str, Any]]:
        """Handle a RAG API request.
        
        Args:
            path: Request path
            method: HTTP method
            query_params: Optional query parameters
            body: Optional request body
            
        Returns:
            Tuple containing status code and response dict
        """
        try:
            # Parse path to determine endpoint and extract path parameters
            path_parts = path.strip('/').split('/')
            
            # Ensure path starts with /api/projects
            if not path.startswith('/api/projects'):
                return self.format_error_response(
                    "Invalid path",
                    f"Path must start with /api/projects, got {path}",
                    "invalid_path",
                    status_code=404
                )
            
            # Remove /api prefix
            path_parts = path_parts[1:]
            
            # Handle project endpoints
            if len(path_parts) == 1 and path_parts[0] == "projects":
                # /api/projects endpoint
                if method == "GET":
                    return self.list_projects()
                elif method == "POST":
                    return self.create_project(body)
                else:
                    return self.format_error_response(
                        "Method not allowed",
                        f"Method {method} not allowed for {path}",
                        "method_not_allowed",
                        status_code=405
                    )
            
            # Get project ID
            if len(path_parts) >= 2 and path_parts[0] == "projects":
                project_id = path_parts[1]
                
                # /api/projects/{project_id} endpoint
                if len(path_parts) == 2:
                    if method == "GET":
                        return self.get_project(project_id)
                    elif method == "DELETE":
                        return self.delete_project(project_id)
                    else:
                        return self.format_error_response(
                            "Method not allowed",
                            f"Method {method} not allowed for {path}",
                            "method_not_allowed",
                            status_code=405
                        )
                
                # Handle project document endpoints
                if len(path_parts) >= 3 and path_parts[2] == "documents":
                    if len(path_parts) == 3:
                        # /api/projects/{project_id}/documents endpoint
                        if method == "GET":
                            return self.list_documents(project_id)
                        elif method == "POST":
                            return self.create_document(project_id, body)
                        else:
                            return self.format_error_response(
                                "Method not allowed",
                                f"Method {method} not allowed for {path}",
                                "method_not_allowed",
                                status_code=405
                            )
                    elif len(path_parts) == 4:
                        # /api/projects/{project_id}/documents/{document_id} endpoint
                        document_id = path_parts[3]
                        if method == "GET":
                            return self.get_document(project_id, document_id)
                        elif method == "DELETE":
                            return self.delete_document(project_id, document_id)
                        else:
                            return self.format_error_response(
                                "Method not allowed",
                                f"Method {method} not allowed for {path}",
                                "method_not_allowed",
                                status_code=405
                            )
                
                # Handle search endpoint
                if len(path_parts) == 3 and path_parts[2] == "search":
                    if method == "POST":
                        if not body or "query" not in body:
                            return self.format_error_response(
                                "Invalid request",
                                "Request must include a 'query' field",
                                "invalid_request"
                            )
                        return self.search_documents(
                            project_id, 
                            body["query"],
                            body.get("options")
                        )
                    else:
                        return self.format_error_response(
                            "Method not allowed",
                            f"Method {method} not allowed for {path}",
                            "method_not_allowed",
                            status_code=405
                        )
                
                # Handle context endpoint
                if len(path_parts) == 3 and path_parts[2] == "context":
                    if method == "POST":
                        if not body or "query" not in body:
                            return self.format_error_response(
                                "Invalid request",
                                "Request must include a 'query' field",
                                "invalid_request"
                            )
                        return self.generate_context(
                            project_id,
                            body["query"],
                            body.get("max_tokens", 2000),
                            body.get("document_ids")
                        )
                    else:
                        return self.format_error_response(
                            "Method not allowed",
                            f"Method {method} not allowed for {path}",
                            "method_not_allowed",
                            status_code=405
                        )
            
            # If we reached here, the endpoint is not supported
            return self.format_error_response(
                "Not found",
                f"Endpoint {path} not found",
                "endpoint_not_found",
                status_code=404
            )
            
        except Exception as e:
            logger.error(f"Error handling request: {str(e)}\n{traceback.format_exc()}")
            return self.format_error_response(
                "Internal server error",
                str(e),
                "internal_error",
                status_code=500
            )


# Create controller instance
rag_controller = RagController()