#!/usr/bin/env python3
"""
Flask implementation of RAG API routes.

This module defines the Flask routes for the RAG API, handling project, document,
and search functionality using the RagController.
"""

import logging

from web.api.controllers.rag import rag_controller

# Create blueprint
rag_api = Blueprint('rag_api', __name__)
logger = logging.getLogger(__name__)


@rag_api.route('/projects', methods=['GET'])
def list_projects():
    """List all RAG projects.
    
    Returns:
        JSON response with list of projects
    """
    try:
        status, response = rag_controller.list_projects()
        return jsonify(response), status
    except Exception as e:
        logger.error(f"Error listing projects: {str(e)}")
        status, response = rag_controller.format_error_response(
            "Failed to retrieve projects",
            str(e),
            status_code=500
        )
        return jsonify(response), status


@rag_api.route('/projects/<project_id>', methods=['GET'])
def get_project(project_id):
    """Get a specific RAG project.
    
    Args:
        project_id: ID of the project to retrieve
        
    Returns:
        JSON response with project details
    """
    try:
        status, response = rag_controller.get_project(project_id)
        return jsonify(response), status
    except Exception as e:
        logger.error(f"Error retrieving project {project_id}: {str(e)}")
        status, response = rag_controller.format_error_response(
            "Failed to retrieve project",
            str(e),
            status_code=500
        )
        return jsonify(response), status


@rag_api.route('/projects', methods=['POST'])
def create_project():
    """Create a new RAG project.
    
    Returns:
        JSON response with created project details
    """
    try:
        data = request.json
        status, response = rag_controller.create_project(data)
        return jsonify(response), status
    except Exception as e:
        logger.error(f"Error creating project: {str(e)}")
        status, response = rag_controller.format_error_response(
            "Failed to create project",
            str(e),
            status_code=500
        )
        return jsonify(response), status


@rag_api.route('/projects/<project_id>', methods=['DELETE'])
def delete_project(project_id):
    """Delete a RAG project.
    
    Args:
        project_id: ID of the project to delete
        
    Returns:
        JSON response indicating success or failure
    """
    try:
        status, response = rag_controller.delete_project(project_id)
        return jsonify(response), status
    except Exception as e:
        logger.error(f"Error deleting project {project_id}: {str(e)}")
        status, response = rag_controller.format_error_response(
            "Failed to delete project",
            str(e),
            status_code=500
        )
        return jsonify(response), status


@rag_api.route('/projects/<project_id>/documents', methods=['GET'])
def list_documents(project_id):
    """List all documents in a RAG project.
    
    Args:
        project_id: ID of the project
        
    Returns:
        JSON response with list of documents
    """
    try:
        status, response = rag_controller.list_documents(project_id)
        return jsonify(response), status
    except Exception as e:
        logger.error(f"Error listing documents for project {project_id}: {str(e)}")
        status, response = rag_controller.format_error_response(
            "Failed to retrieve documents",
            str(e),
            status_code=500
        )
        return jsonify(response), status


@rag_api.route('/projects/<project_id>/documents/<document_id>', methods=['GET'])
def get_document(project_id, document_id):
    """Get a specific document from a RAG project.
    
    Args:
        project_id: ID of the project
        document_id: ID of the document
        
    Returns:
        JSON response with document details
    """
    try:
        status, response = rag_controller.get_document(project_id, document_id)
        return jsonify(response), status
    except Exception as e:
        logger.error(f"Error retrieving document {document_id} from project {project_id}: {str(e)}")
        status, response = rag_controller.format_error_response(
            "Failed to retrieve document",
            str(e),
            status_code=500
        )
        return jsonify(response), status


@rag_api.route('/projects/<project_id>/documents', methods=['POST'])
def create_document(project_id):
    """Create a new document in a RAG project.
    
    Args:
        project_id: ID of the project
        
    Returns:
        JSON response with created document details
    """
    try:
        data = request.json
        status, response = rag_controller.create_document(project_id, data)
        return jsonify(response), status
    except Exception as e:
        logger.error(f"Error creating document in project {project_id}: {str(e)}")
        status, response = rag_controller.format_error_response(
            "Failed to create document",
            str(e),
            status_code=500
        )
        return jsonify(response), status


@rag_api.route('/projects/<project_id>/documents/<document_id>', methods=['DELETE'])
def delete_document(project_id, document_id):
    """Delete a document from a RAG project.
    
    Args:
        project_id: ID of the project
        document_id: ID of the document
        
    Returns:
        JSON response indicating success or failure
    """
    try:
        status, response = rag_controller.delete_document(project_id, document_id)
        return jsonify(response), status
    except Exception as e:
        logger.error(f"Error deleting document {document_id} from project {project_id}: {str(e)}")
        status, response = rag_controller.format_error_response(
            "Failed to delete document",
            str(e),
            status_code=500
        )
        return jsonify(response), status


@rag_api.route('/projects/<project_id>/search', methods=['POST'])
def search_documents(project_id):
    """Search for documents in a RAG project.
    
    Args:
        project_id: ID of the project
        
    Returns:
        JSON response with search results
    """
    try:
        data = request.json
        
        if not data or "query" not in data:
            status, response = rag_controller.format_error_response(
                "Invalid request",
                "Request must include a 'query' field",
                "invalid_request"
            )
            return jsonify(response), status
        
        query = data["query"]
        options = data.get("options")
        
        status, response = rag_controller.search_documents(project_id, query, options)
        return jsonify(response), status
    except Exception as e:
        logger.error(f"Error searching documents in project {project_id}: {str(e)}")
        status, response = rag_controller.format_error_response(
            "Failed to search documents",
            str(e),
            status_code=500
        )
        return jsonify(response), status


@rag_api.route('/projects/<project_id>/context', methods=['POST'])
def generate_context(project_id):
    """Generate context for a query from project documents.
    
    Args:
        project_id: ID of the project
        
    Returns:
        JSON response with generated context
    """
    try:
        data = request.json
        
        if not data or "query" not in data:
            status, response = rag_controller.format_error_response(
                "Invalid request",
                "Request must include a 'query' field",
                "invalid_request"
            )
            return jsonify(response), status
        
        query = data["query"]
        max_tokens = data.get("max_tokens", 2000)
        document_ids = data.get("document_ids")
        
        status, response = rag_controller.generate_context(
            project_id, query, max_tokens, document_ids
        )
        return jsonify(response), status
    except Exception as e:
        logger.error(f"Error generating context for project {project_id}: {str(e)}")
        status, response = rag_controller.format_error_response(
            "Failed to generate context",
            str(e),
            status_code=500
        )
        return jsonify(response), status