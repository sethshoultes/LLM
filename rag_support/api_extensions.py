#!/usr/bin/env python3
"""
API extensions for RAG support in the LLM Platform.

Provides API endpoints and handlers for RAG functionality, including
project management, document operations, search, and context handling.
"""

import sys
import logging
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple

# Import core modules
try:
    from core.logging import get_logger
    from core.paths import get_base_dir
except ImportError:
    # Fallback if core modules are not available
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    get_logger = lambda name: logging.getLogger(name)
    get_base_dir = lambda: Path(__file__).resolve().parent.parent

# Get logger for this module
logger = get_logger("rag_support.api_extensions")

# Get base directory
BASE_DIR = get_base_dir()

# Set up paths
scripts_dir = BASE_DIR / "scripts"
if str(scripts_dir) not in sys.path:
    sys.path.append(str(scripts_dir))

# Import RAG utilities
from rag_support.utils import project_manager
from rag_support.utils.search import search_engine

try:
    from rag_support.utils.hybrid_search import hybrid_search

    HAS_HYBRID_SEARCH = True
except ImportError:
    HAS_HYBRID_SEARCH = False
    logger.warning(
        "Could not import hybrid_search module. Semantic and hybrid search will not be available."
    )

# Import from rag modules if available
try:
    from rag.context import context_manager

    HAS_RAG_MODULES = True
except ImportError:
    HAS_RAG_MODULES = False
    logger.warning("Could not import rag.context module. Using legacy context management.")

# Try to import inference module
try:
    import minimal_inference_quiet as minimal_inference

    HAS_INFERENCE_MODULE = True
except ImportError:
    HAS_INFERENCE_MODULE = False
    logger.warning("Could not import minimal_inference_quiet module. Some features may not work.")

# Import web API modules
try:
    HAS_WEB_API = True
except ImportError:
    HAS_WEB_API = False
    logger.warning("Could not import web.api modules. Using legacy response formatting.")


class RagApiHandler:
    """
    Handles RAG-related API requests.

    Provides endpoints for project management, document operations,
    search, and RAG context handling.
    """

    def __init__(self, base_url="/api"):
        """
        Initialize the API handler.

        Args:
            base_url: Base URL for API endpoints
        """
        self.base_url = base_url

    def _format_error_response(
        self, status_code: int, error: str, detail: str = None, code: str = None
    ) -> Tuple[int, Dict[str, Any]]:
        """
        Format a standardized error response.

        Args:
            status_code: HTTP status code
            error: Short error message
            detail: Detailed error explanation
            code: Error code for client handling

        Returns:
            Tuple of (status_code, response_dict)
        """
        # Use web.api.responses if available
        if HAS_WEB_API:
            return error_response(error, detail, code, status_code)

        # Legacy implementation
        response = {"error": error, "status": status_code}

        if detail:
            response["detail"] = detail

        if code:
            response["code"] = code

        return status_code, response

    def _format_success_response(
        self, data: Any, message: str = None, meta: Dict[str, Any] = None
    ) -> Tuple[int, Dict[str, Any]]:
        """
        Format a standardized success response.

        Args:
            data: Response data
            message: Optional success message
            meta: Optional metadata

        Returns:
            Tuple of (200, response_dict)
        """
        # Use web.api.responses if available
        if HAS_WEB_API:
            return success_response(data, message, meta)

        # Legacy implementation
        response = {"status": "success", "data": data}

        if message:
            response["message"] = message

        if meta:
            response["meta"] = meta

        return 200, response

    def handle_request(
        self,
        path: str,
        method: str,
        query_params: Dict[str, str] = None,
        body: Dict[str, Any] = None,
    ) -> Tuple[int, Dict[str, Any]]:
        """
        Handle an API request and return a response.

        Args:
            path: The request path
            method: The HTTP method (GET, POST, PUT, DELETE)
            query_params: Query parameters dictionary
            body: Request body (for POST, PUT)

        Returns:
            Tuple of (status_code, response_dict)
        """
        # Add detailed logging for debugging
        logger.debug(f"API Request: {method} {path}")
        logger.debug(f"Query params: {query_params}")
        logger.debug(f"Body: {body}")

        # Initialize defaults
        query_params = query_params or {}
        body = body or {}

        # Parse path to determine endpoint
        parts = path.strip("/").split("/")

        if len(parts) == 0 or parts[0] != "api":
            return self._format_error_response(
                404, "Not found", "The provided path does not start with /api"
            )

        # Remove 'api' prefix
        parts = parts[1:]

        if len(parts) == 0:
            return self._format_error_response(
                404, "Invalid API endpoint", "No endpoint specified after /api"
            )

        # Token estimation endpoint
        if parts[0] == "tokens" and method == "POST":
            return self._estimate_tokens(body)

        # Project endpoints
        if parts[0] == "projects":
            if len(parts) == 1:
                # /api/projects
                if method == "GET":
                    return self._list_projects()
                elif method == "POST":
                    return self._create_project(body)
                else:
                    return 405, {"error": "Method not allowed"}

            elif len(parts) == 2:
                # /api/projects/{id}
                project_id = parts[1]
                if method == "GET":
                    return self._get_project(project_id)
                elif method == "DELETE":
                    return self._delete_project(project_id)
                else:
                    return 405, {"error": "Method not allowed"}

            elif len(parts) == 3 and parts[2] == "documents":
                # /api/projects/{id}/documents
                project_id = parts[1]
                if method == "GET":
                    return self._list_documents(project_id)
                elif method == "POST":
                    return self._create_document(project_id, body)
                else:
                    return 405, {"error": "Method not allowed"}

            elif len(parts) == 4 and parts[2] == "documents":
                # /api/projects/{id}/documents/{doc_id}
                project_id = parts[1]
                doc_id = parts[3]
                if method == "GET":
                    return self._get_document(project_id, doc_id)
                elif method == "DELETE":
                    return self._delete_document(project_id, doc_id)
                else:
                    return 405, {"error": "Method not allowed"}

            elif len(parts) == 3 and parts[2] == "search":
                # /api/projects/{id}/search
                project_id = parts[1]
                query = query_params.get("q", "")
                search_type = query_params.get("search_type", "keyword")

                if search_type == "hybrid" and HAS_HYBRID_SEARCH:
                    semantic_weight = float(query_params.get("semantic_weight", 0.6))
                    keyword_weight = float(query_params.get("keyword_weight", 0.4))
                    return self._hybrid_search_documents(
                        project_id, query, semantic_weight, keyword_weight
                    )
                elif search_type == "semantic" and HAS_HYBRID_SEARCH:
                    return self._semantic_search_documents(project_id, query)
                else:
                    return self._search_documents(project_id, query)

            elif len(parts) == 3 and parts[2] == "suggest":
                # /api/projects/{id}/suggest
                project_id = parts[1]
                query = query_params.get("q", "")
                return self._suggest_documents(project_id, query)

            elif len(parts) == 3 and parts[2] == "chats":
                # /api/projects/{id}/chats
                project_id = parts[1]
                if method == "GET":
                    return self._list_chats(project_id)
                elif method == "POST":
                    return self._create_chat(project_id, body)
                else:
                    return 405, {"error": "Method not allowed"}

            elif len(parts) == 5 and parts[2] == "chats" and parts[4] == "messages":
                # /api/projects/{id}/chats/{chat_id}/messages
                project_id = parts[1]
                chat_id = parts[3]
                if method == "POST":
                    return self._add_message(project_id, chat_id, body)
                else:
                    return 405, {"error": "Method not allowed"}

            elif len(parts) == 3 and parts[2] == "artifacts":
                # /api/projects/{id}/artifacts
                project_id = parts[1]
                if method == "GET":
                    return self._list_artifacts(project_id)
                elif method == "POST":
                    return self._create_artifact(project_id, body)
                else:
                    return 405, {"error": "Method not allowed"}

            elif len(parts) == 4 and parts[2] == "artifacts":
                # /api/projects/{id}/artifacts/{artifact_id}
                project_id = parts[1]
                artifact_id = parts[3]
                if method == "GET":
                    return self._get_artifact(project_id, artifact_id)
                elif method == "DELETE":
                    return self._delete_artifact(project_id, artifact_id)
                else:
                    return 405, {"error": "Method not allowed"}

        return 404, {"error": "Endpoint not found"}

    # Project methods
    def _list_projects(self) -> Tuple[int, Dict[str, Any]]:
        """List all projects."""
        try:
            # Log debug information
            logger.debug("Entering _list_projects method")

            # Access project_manager safely
            if not hasattr(project_manager, "get_projects"):
                logger.error("project_manager does not have get_projects method")
                return self._format_error_response(
                    500,
                    "Invalid project manager configuration",
                    "The project manager object is missing required methods",
                    "project_manager_error",
                )

            # Get the projects with detailed logging
            logger.debug("Calling project_manager.get_projects()")
            projects = project_manager.get_projects()
            logger.debug(f"Retrieved {len(projects) if projects else 0} projects")

            # Create response metadata
            meta = {"count": len(projects), "timestamp": datetime.now().isoformat()}

            logger.debug("Formatting success response")
            return self._format_success_response(
                data=projects, message="Projects retrieved successfully", meta=meta
            )
        except Exception as e:
            # Log the full exception with traceback
            logger.error(f"Error in _list_projects: {str(e)}")
            logger.error(traceback.format_exc())

            return self._format_error_response(
                500, "Failed to retrieve projects", f"Error: {str(e)}", "projects_retrieval_error"
            )

    def _create_project(self, data: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        """Create a new project."""
        try:
            # Validate required inputs
            name = data.get("name", "").strip()
            description = data.get("description", "").strip()

            if not name:
                return self._format_error_response(
                    400,
                    "Missing required field",
                    "Project name is required",
                    "missing_required_field",
                )

            # Create project
            project_id = project_manager.create_project(name, description)
            project = project_manager.get_project(project_id)

            if not project:
                return self._format_error_response(
                    500,
                    "Failed to create project",
                    "Project was created but could not be retrieved",
                    "project_creation_error",
                )

            # Return success response
            return self._format_success_response(
                data=project,
                message="Project created successfully",
                meta={"created_at": datetime.now().isoformat()},
            )
        except Exception as e:
            return self._format_error_response(
                500, "Project creation failed", f"Error: {str(e)}", "project_creation_error"
            )

    def _get_project(self, project_id: str) -> Tuple[int, Dict[str, Any]]:
        """Get a project by ID."""
        try:
            # Parameter validation
            if not project_id:
                return self._format_error_response(
                    400, "Missing project ID", "Project ID is required", "missing_project_id"
                )

            # Get project
            project = project_manager.get_project(project_id)

            if project is None:
                return self._format_error_response(
                    404,
                    "Project not found",
                    f"No project exists with ID: {project_id}",
                    "project_not_found",
                )

            # Format document counts for UI display
            meta = {
                "retrieved_at": datetime.now().isoformat(),
                "document_count": project.get("document_count", 0),
                "chat_count": project.get("chat_count", 0),
                "artifact_count": project.get("artifact_count", 0),
            }

            # Return success response
            return self._format_success_response(
                data=project, message="Project retrieved successfully", meta=meta
            )
        except Exception as e:
            return self._format_error_response(
                500, "Failed to retrieve project", f"Error: {str(e)}", "project_retrieval_error"
            )

    def _delete_project(self, project_id: str) -> Tuple[int, Dict[str, Any]]:
        """Delete a project."""
        try:
            # Parameter validation
            if not project_id:
                return self._format_error_response(
                    400, "Missing project ID", "Project ID is required", "missing_project_id"
                )

            # Check if project exists
            project = project_manager.get_project(project_id)
            if not project:
                return self._format_error_response(
                    404,
                    "Project not found",
                    f"No project exists with ID: {project_id}",
                    "project_not_found",
                )

            # Delete project
            success = project_manager.delete_project(project_id)

            if not success:
                return self._format_error_response(
                    500,
                    "Failed to delete project",
                    f"Project with ID {project_id} could not be deleted",
                    "project_deletion_error",
                )

            # Return success response
            return self._format_success_response(
                data={"id": project_id},
                message="Project deleted successfully",
                meta={"deleted_at": datetime.now().isoformat()},
            )
        except Exception as e:
            return self._format_error_response(
                500, "Failed to delete project", f"Error: {str(e)}", "project_deletion_error"
            )

    # Document methods
    def _list_documents(self, project_id: str) -> Tuple[int, Dict[str, Any]]:
        """List all documents in a project."""
        try:
            # Parameter validation
            if not project_id:
                return self._format_error_response(
                    400, "Missing project ID", "Project ID is required", "missing_project_id"
                )

            # Check if project exists
            project = project_manager.get_project(project_id)
            if not project:
                return self._format_error_response(
                    404,
                    "Project not found",
                    f"No project exists with ID: {project_id}",
                    "project_not_found",
                )

            # Get documents
            documents = project_manager.list_documents(project_id)

            # Return success response
            return self._format_success_response(
                data=documents,
                message="Documents retrieved successfully",
                meta={
                    "count": len(documents),
                    "project_id": project_id,
                    "project_name": project.get("name", "Unknown Project"),
                },
            )
        except Exception as e:
            return self._format_error_response(
                500, "Failed to list documents", f"Error: {str(e)}", "document_list_error"
            )

    def _create_document(self, project_id: str, data: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        """Create a new document."""
        try:
            # Parameter validation
            if not project_id:
                return self._format_error_response(
                    400, "Missing project ID", "Project ID is required", "missing_project_id"
                )

            # Check if project exists
            project = project_manager.get_project(project_id)
            if not project:
                return self._format_error_response(
                    404,
                    "Project not found",
                    f"No project exists with ID: {project_id}",
                    "project_not_found",
                )

            # Validate document data
            title = data.get("title", "").strip()
            content = data.get("content", "").strip()
            tags = data.get("tags", [])

            if not title:
                return self._format_error_response(
                    400, "Missing document title", "Document title is required", "missing_title"
                )

            if not content:
                return self._format_error_response(
                    400,
                    "Missing document content",
                    "Document content is required",
                    "missing_content",
                )

            # Create document
            doc_id = project_manager.add_document(project_id, title, content, tags)

            if not doc_id:
                return self._format_error_response(
                    500,
                    "Failed to create document",
                    "The document could not be created",
                    "document_creation_error",
                )

            # Get the created document
            document = project_manager.get_document(project_id, doc_id)

            # Return success response
            return self._format_success_response(
                data=document,
                message="Document created successfully",
                meta={
                    "project_id": project_id,
                    "project_name": project.get("name", "Unknown Project"),
                    "created_at": datetime.now().isoformat(),
                },
            )
        except Exception as e:
            return self._format_error_response(
                500, "Failed to create document", f"Error: {str(e)}", "document_creation_error"
            )

    def _get_document(self, project_id: str, doc_id: str) -> Tuple[int, Dict[str, Any]]:
        """Get a document by ID."""
        try:
            # Parameter validation
            if not project_id:
                return self._format_error_response(
                    400, "Missing project ID", "Project ID is required", "missing_project_id"
                )

            if not doc_id:
                return self._format_error_response(
                    400, "Missing document ID", "Document ID is required", "missing_document_id"
                )

            # Check if project exists
            project = project_manager.get_project(project_id)
            if not project:
                return self._format_error_response(
                    404,
                    "Project not found",
                    f"No project exists with ID: {project_id}",
                    "project_not_found",
                )

            # Get document
            document = project_manager.get_document(project_id, doc_id)

            if not document:
                return self._format_error_response(
                    404,
                    "Document not found",
                    f"No document exists with ID: {doc_id} in project {project_id}",
                    "document_not_found",
                )

            # Return success response
            return self._format_success_response(
                data=document,
                message="Document retrieved successfully",
                meta={
                    "project_id": project_id,
                    "project_name": project.get("name", "Unknown Project"),
                },
            )
        except Exception as e:
            return self._format_error_response(
                500, "Failed to retrieve document", f"Error: {str(e)}", "document_retrieval_error"
            )

    def _delete_document(self, project_id: str, doc_id: str) -> Tuple[int, Dict[str, Any]]:
        """Delete a document."""
        try:
            # Parameter validation
            if not project_id:
                return self._format_error_response(
                    400, "Missing project ID", "Project ID is required", "missing_project_id"
                )

            if not doc_id:
                return self._format_error_response(
                    400, "Missing document ID", "Document ID is required", "missing_document_id"
                )

            # Check if project exists
            project = project_manager.get_project(project_id)
            if not project:
                return self._format_error_response(
                    404,
                    "Project not found",
                    f"No project exists with ID: {project_id}",
                    "project_not_found",
                )

            # Check if document exists
            document = project_manager.get_document(project_id, doc_id)
            if not document:
                return self._format_error_response(
                    404,
                    "Document not found",
                    f"No document exists with ID: {doc_id} in project {project_id}",
                    "document_not_found",
                )

            # Delete document
            success = project_manager.delete_document(project_id, doc_id)

            if not success:
                return self._format_error_response(
                    500,
                    "Failed to delete document",
                    f"Document with ID {doc_id} could not be deleted",
                    "document_deletion_error",
                )

            # Return success response
            return self._format_success_response(
                data={"id": doc_id},
                message="Document deleted successfully",
                meta={
                    "project_id": project_id,
                    "project_name": project.get("name", "Unknown Project"),
                    "deleted_at": datetime.now().isoformat(),
                },
            )
        except Exception as e:
            return self._format_error_response(
                500, "Failed to delete document", f"Error: {str(e)}", "document_deletion_error"
            )

    # Search methods
    def _search_documents(self, project_id: str, query: str) -> Tuple[int, Dict[str, Any]]:
        """Search documents in a project using keyword search."""
        try:
            # Validate parameters
            if not project_id:
                return self._format_error_response(
                    400,
                    "Missing project ID",
                    "Project ID is required for search",
                    "missing_project_id",
                )

            # Check project exists
            project = project_manager.get_project(project_id)
            if not project:
                return self._format_error_response(
                    404,
                    "Project not found",
                    f"No project exists with ID: {project_id}",
                    "project_not_found",
                )

            # Handle empty query
            if not query:
                return self._format_success_response(
                    data=[],
                    message="Empty search query provided",
                    meta={"count": 0, "query": query},
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
                "search_time_ms": round(search_time * 1000, 2),
                "search_type": "keyword",
            }

            return self._format_success_response(
                data=results, message=f"Found {len(results)} documents matching query", meta=meta
            )
        except Exception as e:
            logger.error(f"Search error: {e}")
            logger.error(traceback.format_exc())
            return self._format_error_response(
                500, "Search failed", f"Error: {str(e)}", "search_error"
            )

    def _semantic_search_documents(self, project_id: str, query: str) -> Tuple[int, Dict[str, Any]]:
        """Search documents in a project using semantic search."""
        try:
            # Validate parameters
            if not project_id:
                return self._format_error_response(
                    400,
                    "Missing project ID",
                    "Project ID is required for search",
                    "missing_project_id",
                )

            # Check project exists
            project = project_manager.get_project(project_id)
            if not project:
                return self._format_error_response(
                    404,
                    "Project not found",
                    f"No project exists with ID: {project_id}",
                    "project_not_found",
                )

            # Handle empty query
            if not query:
                return self._format_success_response(
                    data=[],
                    message="Empty search query provided",
                    meta={"count": 0, "query": query},
                )

            # Check if hybrid search is available
            if not HAS_HYBRID_SEARCH:
                return self._format_error_response(
                    501,
                    "Semantic search not available",
                    "The hybrid_search module could not be imported",
                    "semantic_search_unavailable",
                )

            # Perform search
            start_time = time.time()
            results = hybrid_search.semantic_search(project_id, query)
            search_time = time.time() - start_time

            # Return results with metadata
            meta = {
                "count": len(results),
                "query": query,
                "project_id": project_id,
                "project_name": project.get("name", "Unknown Project"),
                "search_time_ms": round(search_time * 1000, 2),
                "search_type": "semantic",
            }

            return self._format_success_response(
                data=results,
                message=f"Found {len(results)} documents using semantic search",
                meta=meta,
            )
        except Exception as e:
            logger.error(f"Semantic search error: {e}")
            logger.error(traceback.format_exc())
            return self._format_error_response(
                500, "Semantic search failed", f"Error: {str(e)}", "semantic_search_error"
            )

    def _hybrid_search_documents(
        self, project_id: str, query: str, semantic_weight: float = 0.6, keyword_weight: float = 0.4
    ) -> Tuple[int, Dict[str, Any]]:
        """Search documents in a project using hybrid search."""
        try:
            # Validate parameters
            if not project_id:
                return self._format_error_response(
                    400,
                    "Missing project ID",
                    "Project ID is required for search",
                    "missing_project_id",
                )

            # Check project exists
            project = project_manager.get_project(project_id)
            if not project:
                return self._format_error_response(
                    404,
                    "Project not found",
                    f"No project exists with ID: {project_id}",
                    "project_not_found",
                )

            # Handle empty query
            if not query:
                return self._format_success_response(
                    data=[],
                    message="Empty search query provided",
                    meta={"count": 0, "query": query},
                )

            # Check if hybrid search is available
            if not HAS_HYBRID_SEARCH:
                return self._format_error_response(
                    501,
                    "Hybrid search not available",
                    "The hybrid_search module could not be imported",
                    "hybrid_search_unavailable",
                )

            # Perform search
            start_time = time.time()
            results = hybrid_search.hybrid_search(
                project_id, query, semantic_weight=semantic_weight, keyword_weight=keyword_weight
            )
            search_time = time.time() - start_time

            # Return results with metadata
            meta = {
                "count": len(results),
                "query": query,
                "project_id": project_id,
                "project_name": project.get("name", "Unknown Project"),
                "search_time_ms": round(search_time * 1000, 2),
                "search_type": "hybrid",
                "hybrid_params": {
                    "semantic_weight": semantic_weight,
                    "keyword_weight": keyword_weight,
                },
            }

            return self._format_success_response(
                data=results,
                message=f"Found {len(results)} documents using hybrid search",
                meta=meta,
            )
        except Exception as e:
            logger.error(f"Hybrid search error: {e}")
            logger.error(traceback.format_exc())
            return self._format_error_response(
                500, "Hybrid search failed", f"Error: {str(e)}", "hybrid_search_error"
            )

    def _suggest_documents(self, project_id: str, query: str) -> Tuple[int, Dict[str, Any]]:
        """Suggest relevant documents for a query."""
        try:
            # Validate parameters
            if not project_id:
                return self._format_error_response(
                    400, "Missing project ID", "Project ID is required", "missing_project_id"
                )

            # Check project exists
            project = project_manager.get_project(project_id)
            if not project:
                return self._format_error_response(
                    404,
                    "Project not found",
                    f"No project exists with ID: {project_id}",
                    "project_not_found",
                )

            # Handle empty query
            if not query:
                return self._format_success_response(
                    data=[], message="Empty query provided", meta={"count": 0, "query": query}
                )

            # Determine if hybrid search is available and use it for better suggestions
            start_time = time.time()
            if HAS_HYBRID_SEARCH:
                # Use hybrid search for better suggestions
                results = hybrid_search.hybrid_search(project_id, query, max_results=3)
                search_method = "hybrid"
            else:
                # Fall back to keyword search
                results = search_engine.search(project_id, query, max_results=3)
                search_method = "keyword"

            search_time = time.time() - start_time

            # Return success response
            return self._format_success_response(
                data=results,
                message=f"Found {len(results)} document suggestions",
                meta={
                    "count": len(results),
                    "query": query,
                    "project_id": project_id,
                    "project_name": project.get("name", "Unknown Project"),
                    "search_time_ms": round(search_time * 1000, 2),
                    "search_type": search_method,
                },
            )
        except Exception as e:
            logger.error(f"Document suggestion error: {e}")
            logger.error(traceback.format_exc())
            return self._format_error_response(
                500, "Document suggestion failed", f"Error: {str(e)}", "suggestion_error"
            )

    # Chat methods
    def _list_chats(self, project_id: str) -> Tuple[int, Dict[str, Any]]:
        """List all chats in a project."""
        try:
            # Validate parameters
            if not project_id:
                return self._format_error_response(
                    400, "Missing project ID", "Project ID is required", "missing_project_id"
                )

            # Check project exists
            project = project_manager.get_project(project_id)
            if not project:
                return self._format_error_response(
                    404,
                    "Project not found",
                    f"No project exists with ID: {project_id}",
                    "project_not_found",
                )

            # Get chats
            chats = project_manager.list_chats(project_id)

            # Return success response
            return self._format_success_response(
                data=chats,
                message="Chats retrieved successfully",
                meta={
                    "count": len(chats),
                    "project_id": project_id,
                    "project_name": project.get("name", "Unknown Project"),
                },
            )
        except Exception as e:
            return self._format_error_response(
                500, "Failed to list chats", f"Error: {str(e)}", "chat_list_error"
            )

    def _create_chat(self, project_id: str, data: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        """Create a new chat."""
        try:
            # Validate parameters
            if not project_id:
                return self._format_error_response(
                    400, "Missing project ID", "Project ID is required", "missing_project_id"
                )

            # Check project exists
            project = project_manager.get_project(project_id)
            if not project:
                return self._format_error_response(
                    404,
                    "Project not found",
                    f"No project exists with ID: {project_id}",
                    "project_not_found",
                )

            # Extract chat data
            title = data.get("title", "").strip()

            # Create chat
            chat_id = project_manager.add_chat(project_id, title)

            if not chat_id:
                return self._format_error_response(
                    500,
                    "Failed to create chat",
                    "The chat could not be created",
                    "chat_creation_error",
                )

            # Get the created chat
            chat = project_manager.get_chat(project_id, chat_id)

            # Return success response
            return self._format_success_response(
                data=chat,
                message="Chat created successfully",
                meta={
                    "project_id": project_id,
                    "project_name": project.get("name", "Unknown Project"),
                    "created_at": datetime.now().isoformat(),
                },
            )
        except Exception as e:
            return self._format_error_response(
                500, "Failed to create chat", f"Error: {str(e)}", "chat_creation_error"
            )

    def _add_message(
        self, project_id: str, chat_id: str, data: Dict[str, Any]
    ) -> Tuple[int, Dict[str, Any]]:
        """Add a message to a chat and get AI response."""
        try:
            # Parameter validation
            if not project_id:
                return self._format_error_response(
                    400, "Missing project ID", "Project ID is required", "missing_project_id"
                )

            if not chat_id:
                return self._format_error_response(
                    400, "Missing chat ID", "Chat ID is required", "missing_chat_id"
                )

            # Verify project exists
            project = project_manager.get_project(project_id)
            if not project:
                return self._format_error_response(
                    404,
                    "Project not found",
                    f"No project exists with ID: {project_id}",
                    "project_not_found",
                )

            # Verify chat exists
            chat = project_manager.get_chat(project_id, chat_id)
            if not chat:
                return self._format_error_response(
                    404,
                    "Chat not found",
                    f"No chat exists with ID: {chat_id} in project {project_id}",
                    "chat_not_found",
                )

            # Extract and validate parameters
            content = data.get("content", "").strip()
            context_docs = data.get("context_docs", [])
            modelPath = data.get("model", "")
            temperature = data.get("temperature", 0.7)
            max_tokens = data.get("max_tokens", 1024)
            top_p = data.get("top_p", 0.95)

            # Validate content
            if not content:
                return self._format_error_response(
                    400,
                    "Missing message content",
                    "Message content is required",
                    "missing_message_content",
                )

            # Add user message to chat
            success = project_manager.add_message(project_id, chat_id, "user", content)

            if not success:
                return self._format_error_response(
                    500,
                    "Failed to add message",
                    "The message could not be saved to the chat",
                    "message_save_error",
                )

            # Load context documents
            start_time = time.time()
            context_content = ""
            context_metadata = []
            total_context_tokens = 0

            if context_docs:
                # Use rag.context if available for better context management
                if HAS_RAG_MODULES:
                    # Get documents
                    documents = []
                    for doc_id in context_docs:
                        doc = project_manager.get_document(project_id, doc_id)
                        if doc:
                            documents.append(doc)

                    # Prepare context with token budget
                    system_prompt = ""
                    message_history = [{"role": "user", "content": content}]

                    context_text, context_info = context_manager.prepare_context_for_prompt(
                        documents=documents,
                        query=content,
                        system_message=system_prompt,
                        messages=message_history,
                    )

                    context_content = context_text
                    context_metadata = context_info
                    total_context_tokens = sum(doc["tokens"] for doc in context_info)
                else:
                    # Legacy implementation
                    for doc_id in context_docs:
                        doc = project_manager.get_document(project_id, doc_id)
                        if doc:
                            # Prepare document content
                            doc_title = doc.get("title", "Document")
                            doc_content = doc.get("content", "")
                            doc_text = f"# {doc_title}\n\n{doc_content}\n\n"

                            # Estimate tokens for this document
                            doc_tokens = search_engine.estimate_token_count(doc_text)
                            total_context_tokens += doc_tokens

                            # Add document to context
                            context_content += doc_text
                            context_metadata.append(
                                {"id": doc_id, "title": doc_title, "tokens": doc_tokens}
                            )

            # Get AI response by connecting to the LLM generation code
            try:
                # Check if inference module is available
                if not HAS_INFERENCE_MODULE:
                    raise ImportError("Inference module was not successfully imported")

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
                    system_prompt += (
                        "\n\nUse the following information to answer the user's question:\n\n"
                        + context_content
                    )

                # Generate response
                generation_start = time.time()
                result = minimal_inference.generate(
                    model_path=modelPath,
                    prompt=content,
                    system_prompt=system_prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                )
                generation_time = time.time() - generation_start

                if "error" in result:
                    # Handle generation error
                    error_message = f"Error generating response: {result['error']}"

                    # Save error as assistant response
                    project_manager.add_message(
                        project_id, chat_id, "assistant", error_message, context_docs
                    )

                    return self._format_error_response(
                        500, "LLM generation failed", error_message, "llm_generation_error"
                    )
                else:
                    # Handle successful generation
                    response = result["response"]

                    # Save the assistant's response
                    project_manager.add_message(
                        project_id, chat_id, "assistant", response, context_docs
                    )

                    # Build response metadata
                    meta = {
                        "chat_id": chat_id,
                        "project_id": project_id,
                        "model_path": modelPath,
                        "model_type": result.get("model_type"),
                        "model_format": result.get("model_format"),
                        "tokens_generated": result.get("tokens_generated", 0),
                        "generation_time_s": result.get("time_taken", generation_time),
                        "total_time_s": time.time() - start_time,
                        "context_documents": {
                            "count": len(context_docs),
                            "tokens": total_context_tokens,
                            "sources": context_metadata,
                        },
                        "parameters": {
                            "temperature": temperature,
                            "max_tokens": max_tokens,
                            "top_p": top_p,
                        },
                    }

                    # Return success response
                    return self._format_success_response(
                        data={
                            "response": response,
                            "chat_id": chat_id,
                            "message_id": None,  # In future, could return the created message ID
                        },
                        message="LLM response generated successfully",
                        meta=meta,
                    )

            except ImportError as e:
                error_message = f"Error: Could not load inference module. {str(e)}"
                project_manager.add_message(
                    project_id, chat_id, "assistant", error_message, context_docs
                )

                return self._format_error_response(
                    500, "Inference module not available", error_message, "inference_module_error"
                )

            except Exception as e:
                error_message = f"Error generating response: {str(e)}"
                project_manager.add_message(
                    project_id, chat_id, "assistant", error_message, context_docs
                )

                return self._format_error_response(
                    500, "LLM generation failed", error_message, "llm_generation_error"
                )

        except Exception as e:
            return self._format_error_response(
                500,
                "Chat message processing failed",
                f"Error: {str(e)}",
                "message_processing_error",
            )

    # Token estimation methods
    def _estimate_tokens(self, data: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        """Estimate token counts for text and provide context window information."""
        try:
            # Extract parameters
            text = data.get("text", "")
            context_docs = data.get("context_docs", [])
            project_id = data.get("project_id", "")
            model_path = data.get("model", "")

            # Parameter validation
            if not text and not context_docs:
                return self._format_error_response(
                    400,
                    "Missing required parameters",
                    "Either text or context_docs must be provided",
                    "missing_parameters",
                )

            if context_docs and not project_id:
                return self._format_error_response(
                    400,
                    "Missing project ID",
                    "Project ID is required when providing context_docs",
                    "missing_project_id",
                )

            # Use rag.tokens if available for better token estimation
            if HAS_RAG_MODULES:
                from rag.tokens import token_manager as rag_token_manager

                # Get model context window
                context_window = rag_token_manager.get_context_window(
                    model_id=None, model_path=model_path
                )

                # Create message history
                message_history = []
                if text:
                    message_history.append({"role": "user", "content": text})

                # Get token allocation
                allocation = rag_token_manager.allocate_context_budget(
                    context_window=context_window,
                    system_message="",
                    messages=message_history,
                    model_id=None,
                )

                # Get documents and their tokens
                contexts = []
                context_tokens = 0

                if context_docs and project_id:
                    # Get each document
                    for doc_id in context_docs:
                        doc = project_manager.get_document(project_id, doc_id)
                        if doc:
                            content = doc.get("content", "")
                            title = doc.get("title", "Document")
                            doc_text = f"# {title}\n\n{content}"
                            doc_tokens = rag_token_manager.estimate_tokens(doc_text)

                            contexts.append(
                                {
                                    "id": doc_id,
                                    "title": title,
                                    "tokens": doc_tokens,
                                    "percentage": 0,  # Will update after calculating total
                                }
                            )

                            context_tokens += doc_tokens

                    # Update percentages
                    if context_tokens > 0:
                        for context in contexts:
                            context["percentage"] = round(
                                (context["tokens"] / context_tokens) * 100, 1
                            )

                # Calculate available tokens
                text_tokens = rag_token_manager.estimate_tokens(text) if text else 0
                total_tokens = allocation["message_tokens"] + context_tokens
                available_tokens = context_window - total_tokens - allocation["reserved_tokens"]

                # Build response data
                token_data = {
                    "total_tokens": total_tokens,
                    "text_tokens": text_tokens,
                    "context_tokens": context_tokens,
                    "contexts": contexts,
                    "model_context_window": context_window,
                    "available_tokens": available_tokens,
                    "available_percentage": round((available_tokens / context_window) * 100, 1),
                    "usage_percentage": round((total_tokens / context_window) * 100, 1),
                    "is_over_limit": available_tokens < 0,
                    "reserved_tokens": allocation["reserved_tokens"],
                }
            else:
                # Legacy implementation using search engine for token estimation
                from rag_support.utils.search import search_engine

                # Get model context window size (default to 4096 if not specified)
                context_window = 4096
                reserved_tokens = 1024  # Reserved for system prompt and response

                # Try to get model-specific context window
                if model_path and HAS_INFERENCE_MODULE:
                    try:
                        # Get model info if available
                        models = minimal_inference.list_models()
                        for model in models:
                            if model["path"] == model_path:
                                # Some models expose their context window
                                if "context_window" in model:
                                    context_window = model["context_window"]
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
                            "project_not_found",
                        )

                    # Process each document
                    for doc_id in context_docs:
                        doc = project_manager.get_document(project_id, doc_id)
                        if doc:
                            content = doc.get("content", "")
                            title = doc.get("title", "Document")
                            doc_text = f"# {title}\n\n{content}"
                            doc_tokens = search_engine.estimate_token_count(doc_text)

                            contexts.append(
                                {
                                    "id": doc_id,
                                    "title": title,
                                    "tokens": doc_tokens,
                                    "percentage": 0,  # Will update after calculating total
                                }
                            )

                            context_tokens += doc_tokens

                    # Update percentages
                    if context_tokens > 0:
                        for context in contexts:
                            context["percentage"] = round(
                                (context["tokens"] / context_tokens) * 100, 1
                            )

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
                    "reserved_tokens": reserved_tokens,
                }

            # Build metadata
            meta = {
                "timestamp": datetime.now().isoformat(),
                "model_path": model_path,
                "context_count": len(context_docs),
                "estimation_method": (
                    "token_manager" if HAS_RAG_MODULES else "character-based-approximation"
                ),
            }

            # Return formatted response
            return self._format_success_response(
                data=token_data, message="Token estimation completed successfully", meta=meta
            )

        except Exception as e:
            return self._format_error_response(
                500, "Token estimation failed", f"Error: {str(e)}", "token_estimation_error"
            )

    # Artifact methods
    def _list_artifacts(self, project_id: str) -> Tuple[int, Dict[str, Any]]:
        """List all artifacts in a project."""
        try:
            # Validate parameters
            if not project_id:
                return self._format_error_response(
                    400, "Missing project ID", "Project ID is required", "missing_project_id"
                )

            # Check project exists
            project = project_manager.get_project(project_id)
            if not project:
                return self._format_error_response(
                    404,
                    "Project not found",
                    f"No project exists with ID: {project_id}",
                    "project_not_found",
                )

            # Get artifacts
            artifacts = project_manager.list_artifacts(project_id)

            # Return success response
            return self._format_success_response(
                data=artifacts,
                message="Artifacts retrieved successfully",
                meta={
                    "count": len(artifacts),
                    "project_id": project_id,
                    "project_name": project.get("name", "Unknown Project"),
                },
            )
        except Exception as e:
            return self._format_error_response(
                500, "Failed to list artifacts", f"Error: {str(e)}", "artifact_list_error"
            )

    def _create_artifact(self, project_id: str, data: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        """Create a new artifact."""
        try:
            # Validate parameters
            if not project_id:
                return self._format_error_response(
                    400, "Missing project ID", "Project ID is required", "missing_project_id"
                )

            # Check project exists
            project = project_manager.get_project(project_id)
            if not project:
                return self._format_error_response(
                    404,
                    "Project not found",
                    f"No project exists with ID: {project_id}",
                    "project_not_found",
                )

            # Extract artifact data
            title = data.get("title", "").strip()
            content = data.get("content", "").strip()
            file_ext = data.get("file_ext", "md").strip()

            # Validate content
            if not content:
                return self._format_error_response(
                    400,
                    "Missing artifact content",
                    "Artifact content is required",
                    "missing_content",
                )

            # Create artifact
            artifact_id = project_manager.save_artifact(project_id, content, title, file_ext)

            if not artifact_id:
                return self._format_error_response(
                    500,
                    "Failed to create artifact",
                    "The artifact could not be created",
                    "artifact_creation_error",
                )

            # Get the created artifact
            artifact = project_manager.get_artifact(project_id, artifact_id)

            # Return success response
            return self._format_success_response(
                data=artifact,
                message="Artifact created successfully",
                meta={
                    "project_id": project_id,
                    "project_name": project.get("name", "Unknown Project"),
                    "created_at": datetime.now().isoformat(),
                },
            )
        except Exception as e:
            return self._format_error_response(
                500, "Failed to create artifact", f"Error: {str(e)}", "artifact_creation_error"
            )

    def _get_artifact(self, project_id: str, artifact_id: str) -> Tuple[int, Dict[str, Any]]:
        """Get an artifact by ID."""
        try:
            # Validate parameters
            if not project_id:
                return self._format_error_response(
                    400, "Missing project ID", "Project ID is required", "missing_project_id"
                )

            if not artifact_id:
                return self._format_error_response(
                    400, "Missing artifact ID", "Artifact ID is required", "missing_artifact_id"
                )

            # Check project exists
            project = project_manager.get_project(project_id)
            if not project:
                return self._format_error_response(
                    404,
                    "Project not found",
                    f"No project exists with ID: {project_id}",
                    "project_not_found",
                )

            # Get artifact
            artifact = project_manager.get_artifact(project_id, artifact_id)

            if not artifact:
                return self._format_error_response(
                    404,
                    "Artifact not found",
                    f"No artifact exists with ID: {artifact_id} in project {project_id}",
                    "artifact_not_found",
                )

            # Return success response
            return self._format_success_response(
                data=artifact,
                message="Artifact retrieved successfully",
                meta={
                    "project_id": project_id,
                    "project_name": project.get("name", "Unknown Project"),
                },
            )
        except Exception as e:
            return self._format_error_response(
                500, "Failed to retrieve artifact", f"Error: {str(e)}", "artifact_retrieval_error"
            )

    def _delete_artifact(self, project_id: str, artifact_id: str) -> Tuple[int, Dict[str, Any]]:
        """Delete an artifact."""
        try:
            # Validate parameters
            if not project_id:
                return self._format_error_response(
                    400, "Missing project ID", "Project ID is required", "missing_project_id"
                )

            if not artifact_id:
                return self._format_error_response(
                    400, "Missing artifact ID", "Artifact ID is required", "missing_artifact_id"
                )

            # Check project exists
            project = project_manager.get_project(project_id)
            if not project:
                return self._format_error_response(
                    404,
                    "Project not found",
                    f"No project exists with ID: {project_id}",
                    "project_not_found",
                )

            # Check artifact exists
            artifact = project_manager.get_artifact(project_id, artifact_id)
            if not artifact:
                return self._format_error_response(
                    404,
                    "Artifact not found",
                    f"No artifact exists with ID: {artifact_id} in project {project_id}",
                    "artifact_not_found",
                )

            # Delete artifact
            success = project_manager.delete_artifact(project_id, artifact_id)

            if not success:
                return self._format_error_response(
                    500,
                    "Failed to delete artifact",
                    f"Artifact with ID {artifact_id} could not be deleted",
                    "artifact_deletion_error",
                )

            # Return success response
            return self._format_success_response(
                data={"id": artifact_id},
                message="Artifact deleted successfully",
                meta={
                    "project_id": project_id,
                    "project_name": project.get("name", "Unknown Project"),
                    "deleted_at": datetime.now().isoformat(),
                },
            )
        except Exception as e:
            return self._format_error_response(
                500, "Failed to delete artifact", f"Error: {str(e)}", "artifact_deletion_error"
            )


# Create a singleton instance
api_handler = RagApiHandler()
