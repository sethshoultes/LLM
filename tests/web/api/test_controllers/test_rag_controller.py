#!/usr/bin/env python3
"""
Unit tests for RAG API controller.

Tests the functionality of the RAG API controller, validating
project management, document operations, search, and request handling.
"""

import unittest
from unittest.mock import patch, MagicMock
import tempfile
import shutil

from web.api.controllers.rag import RagController


class TestRagController(unittest.TestCase):
    """Test RAG API controller functionality."""
    
    def setUp(self):
        """Set up test environment."""
        # Create temporary test directory
        self.temp_dir = tempfile.mkdtemp()
        
        # Create controller
        self.controller = RagController()
        
        # Mock project manager
        self.mock_project_manager = MagicMock()
        
        # Create patch for project_manager
        self.project_manager_patch = patch('web.api.controllers.rag.project_manager', self.mock_project_manager)
        self.project_manager_patch.start()
        
        # Mock search engine
        self.mock_search_engine = MagicMock()
        
        # Create patch for search_engine
        self.search_engine_patch = patch('web.api.controllers.rag.search_engine', self.mock_search_engine)
        self.search_engine_patch.start()
        
        # Mock context manager
        self.mock_context_manager = MagicMock()
        
        # Create patch for ContextManager
        self.context_manager_patch = patch('web.api.controllers.rag.ContextManager')
        mock_context_manager_class = self.context_manager_patch.start()
        mock_context_manager_class.return_value = self.mock_context_manager
        
        # Set up test data
        self.test_project_id = "test_project_id"
        self.test_document_id = "test_document_id"
        
        self.test_project = {
            "id": self.test_project_id,
            "name": "Test Project",
            "description": "Test project description"
        }
        
        self.test_document = {
            "id": self.test_document_id,
            "project_id": self.test_project_id,
            "title": "Test Document",
            "content": "Test document content"
        }
    
    def tearDown(self):
        """Clean up after tests."""
        # Stop patches
        self.project_manager_patch.stop()
        self.search_engine_patch.stop()
        self.context_manager_patch.stop()
        
        # Remove temporary directory
        shutil.rmtree(self.temp_dir)
    
    def test_format_success_response(self):
        """Test success response formatting."""
        status, response = self.controller.format_success_response(
            {"key": "value"}, "Test message", {"meta_key": "meta_value"}
        )
        
        self.assertEqual(status, 200)
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["data"], {"key": "value"})
        self.assertEqual(response["message"], "Test message")
        self.assertEqual(response["meta"]["meta_key"], "meta_value")
    
    def test_format_error_response(self):
        """Test error response formatting."""
        status, response = self.controller.format_error_response(
            "Error message", "Error details", "error_code", 400
        )
        
        self.assertEqual(status, 400)
        self.assertEqual(response["status"], "error")
        self.assertEqual(response["error"], "Error message")
        self.assertEqual(response["detail"], "Error details")
        self.assertEqual(response["code"], "error_code")
    
    def test_list_projects(self):
        """Test listing projects."""
        # Set up mock response
        self.mock_project_manager.get_projects.return_value = [self.test_project]
        self.mock_project_manager.get_documents.return_value = []
        
        # Call method
        status, response = self.controller.list_projects()
        
        # Verify response
        self.assertEqual(status, 200)
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["data"], [self.test_project])
        self.assertEqual(response["meta"]["count"], 1)
        
        # Verify mock calls
        self.mock_project_manager.get_projects.assert_called_once()
    
    def test_get_project(self):
        """Test getting a project."""
        # Set up mock response
        self.mock_project_manager.get_project.return_value = self.test_project
        self.mock_project_manager.get_documents.return_value = []
        
        # Call method
        status, response = self.controller.get_project(self.test_project_id)
        
        # Verify response
        self.assertEqual(status, 200)
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["data"], self.test_project)
        
        # Verify mock calls
        self.mock_project_manager.get_project.assert_called_once_with(self.test_project_id)
    
    def test_get_project_not_found(self):
        """Test getting a non-existent project."""
        # Set up mock response
        self.mock_project_manager.get_project.return_value = None
        
        # Call method
        status, response = self.controller.get_project(self.test_project_id)
        
        # Verify response
        self.assertEqual(status, 404)
        self.assertEqual(response["status"], "error")
        self.assertEqual(response["error"], "Project not found")
        
        # Verify mock calls
        self.mock_project_manager.get_project.assert_called_once_with(self.test_project_id)
    
    def test_create_project(self):
        """Test creating a project."""
        # Set up mock response
        self.mock_project_manager.create_project.return_value = self.test_project
        
        # Call method
        project_data = {"name": "Test Project", "description": "Test project description"}
        status, response = self.controller.create_project(project_data)
        
        # Verify response
        self.assertEqual(status, 201)
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["data"], self.test_project)
        
        # Verify mock calls
        self.mock_project_manager.create_project.assert_called_once_with(
            "Test Project", "Test project description"
        )
    
    def test_delete_project(self):
        """Test deleting a project."""
        # Set up mock response
        self.mock_project_manager.get_project.return_value = self.test_project
        self.mock_project_manager.delete_project.return_value = True
        
        # Call method
        status, response = self.controller.delete_project(self.test_project_id)
        
        # Verify response
        self.assertEqual(status, 200)
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["data"], {"id": self.test_project_id})
        
        # Verify mock calls
        self.mock_project_manager.get_project.assert_called_once_with(self.test_project_id)
        self.mock_project_manager.delete_project.assert_called_once_with(self.test_project_id)
    
    def test_delete_project_not_found(self):
        """Test deleting a non-existent project."""
        # Set up mock response
        self.mock_project_manager.get_project.return_value = None
        
        # Call method
        status, response = self.controller.delete_project(self.test_project_id)
        
        # Verify response
        self.assertEqual(status, 404)
        self.assertEqual(response["status"], "error")
        self.assertEqual(response["error"], "Project not found")
        
        # Verify mock calls
        self.mock_project_manager.get_project.assert_called_once_with(self.test_project_id)
        self.mock_project_manager.delete_project.assert_not_called()
    
    def test_list_documents(self):
        """Test listing documents."""
        # Set up mock response
        self.mock_project_manager.get_project.return_value = self.test_project
        self.mock_project_manager.get_documents.return_value = [self.test_document]
        
        # Call method
        status, response = self.controller.list_documents(self.test_project_id)
        
        # Verify response
        self.assertEqual(status, 200)
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["data"], [self.test_document])
        self.assertEqual(response["meta"]["count"], 1)
        self.assertEqual(response["meta"]["project_id"], self.test_project_id)
        
        # Verify mock calls
        self.mock_project_manager.get_project.assert_called_once_with(self.test_project_id)
        self.mock_project_manager.get_documents.assert_called_once_with(self.test_project_id)
    
    def test_get_document(self):
        """Test getting a document."""
        # Set up mock response
        self.mock_project_manager.get_project.return_value = self.test_project
        self.mock_project_manager.get_document.return_value = self.test_document
        
        # Call method
        status, response = self.controller.get_document(self.test_project_id, self.test_document_id)
        
        # Verify response
        self.assertEqual(status, 200)
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["data"], self.test_document)
        
        # Verify mock calls
        self.mock_project_manager.get_project.assert_called_once_with(self.test_project_id)
        self.mock_project_manager.get_document.assert_called_once_with(self.test_project_id, self.test_document_id)
    
    def test_get_document_not_found(self):
        """Test getting a non-existent document."""
        # Set up mock response
        self.mock_project_manager.get_project.return_value = self.test_project
        self.mock_project_manager.get_document.return_value = None
        
        # Call method
        status, response = self.controller.get_document(self.test_project_id, self.test_document_id)
        
        # Verify response
        self.assertEqual(status, 404)
        self.assertEqual(response["status"], "error")
        self.assertEqual(response["error"], "Document not found")
        
        # Verify mock calls
        self.mock_project_manager.get_project.assert_called_once_with(self.test_project_id)
        self.mock_project_manager.get_document.assert_called_once_with(self.test_project_id, self.test_document_id)
    
    def test_create_document(self):
        """Test creating a document."""
        # Set up mock response
        self.mock_project_manager.get_project.return_value = self.test_project
        self.mock_project_manager.add_document.return_value = self.test_document
        
        # Call method
        document_data = {
            "title": "Test Document",
            "content": "Test document content",
            "tags": ["test"]
        }
        status, response = self.controller.create_document(self.test_project_id, document_data)
        
        # Verify response
        self.assertEqual(status, 201)
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["data"], self.test_document)
        
        # Verify mock calls
        self.mock_project_manager.get_project.assert_called_once_with(self.test_project_id)
        self.mock_project_manager.add_document.assert_called_once_with(
            self.test_project_id, "Test Document", "Test document content", ["test"]
        )
    
    def test_delete_document(self):
        """Test deleting a document."""
        # Set up mock response
        self.mock_project_manager.get_project.return_value = self.test_project
        self.mock_project_manager.get_document.return_value = self.test_document
        self.mock_project_manager.delete_document.return_value = True
        
        # Call method
        status, response = self.controller.delete_document(self.test_project_id, self.test_document_id)
        
        # Verify response
        self.assertEqual(status, 200)
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["data"], {
            "id": self.test_document_id,
            "project_id": self.test_project_id
        })
        
        # Verify mock calls
        self.mock_project_manager.get_project.assert_called_once_with(self.test_project_id)
        self.mock_project_manager.get_document.assert_called_once_with(self.test_project_id, self.test_document_id)
        self.mock_project_manager.delete_document.assert_called_once_with(self.test_project_id, self.test_document_id)
    
    @patch('web.api.controllers.rag.HAS_HYBRID_SEARCH', True)
    @patch('web.api.controllers.rag.hybrid_search')
    def test_search_documents_hybrid(self, mock_hybrid_search):
        """Test searching documents with hybrid search."""
        # Set up mock response
        self.mock_project_manager.get_project.return_value = self.test_project
        mock_hybrid_search.return_value = [self.test_document]
        
        # Call method
        status, response = self.controller.search_documents(
            self.test_project_id, "test query", {"max_results": 5}
        )
        
        # Verify response
        self.assertEqual(status, 200)
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["data"], [self.test_document])
        self.assertEqual(response["meta"]["count"], 1)
        self.assertEqual(response["meta"]["query"], "test query")
        self.assertEqual(response["meta"]["search_type"], "hybrid")
        self.assertEqual(response["meta"]["max_results"], 5)
        
        # Verify mock calls
        self.mock_project_manager.get_project.assert_called_once_with(self.test_project_id)
        mock_hybrid_search.assert_called_once_with(
            self.test_project_id, "test query", 
            semantic_weight=0.5, keyword_weight=0.5, max_results=5
        )
    
    @patch('web.api.controllers.rag.HAS_HYBRID_SEARCH', False)
    def test_search_documents_keyword(self):
        """Test searching documents with keyword search."""
        # Set up mock response
        self.mock_project_manager.get_project.return_value = self.test_project
        self.mock_search_engine.search.return_value = [self.test_document]
        
        # Call method
        status, response = self.controller.search_documents(self.test_project_id, "test query")
        
        # Verify response
        self.assertEqual(status, 200)
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["data"], [self.test_document])
        self.assertEqual(response["meta"]["count"], 1)
        self.assertEqual(response["meta"]["query"], "test query")
        self.assertEqual(response["meta"]["search_type"], "keyword")
        
        # Verify mock calls
        self.mock_project_manager.get_project.assert_called_once_with(self.test_project_id)
        self.mock_search_engine.search.assert_called_once_with(
            self.test_project_id, "test query", max_results=10
        )
    
    def test_generate_context(self):
        """Test generating context."""
        # Set up mock response
        self.mock_project_manager.get_project.return_value = self.test_project
        self.mock_context_manager.generate_context.return_value = (
            "Generated context", [self.test_document_id], False
        )
        
        # Call method
        status, response = self.controller.generate_context(
            self.test_project_id, "test query", 1000, [self.test_document_id]
        )
        
        # Verify response
        self.assertEqual(status, 200)
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["data"]["context"], "Generated context")
        self.assertEqual(response["data"]["documents"], [self.test_document_id])
        self.assertEqual(response["data"]["truncated"], False)
        
        # Verify mock calls
        self.mock_project_manager.get_project.assert_called_once_with(self.test_project_id)
        self.mock_context_manager.generate_context.assert_called_once_with(
            self.test_project_id, "test query", max_tokens=1000, document_ids=[self.test_document_id]
        )
    
    def test_handle_request_list_projects(self):
        """Test handling request for listing projects."""
        # Set up mock response
        self.mock_project_manager.get_projects.return_value = [self.test_project]
        self.mock_project_manager.get_documents.return_value = []
        
        # Call method
        status, response = self.controller.handle_request(
            path="/api/projects",
            method="GET"
        )
        
        # Verify response
        self.assertEqual(status, 200)
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["data"], [self.test_project])
    
    def test_handle_request_get_project(self):
        """Test handling request for getting a project."""
        # Set up mock response
        self.mock_project_manager.get_project.return_value = self.test_project
        self.mock_project_manager.get_documents.return_value = []
        
        # Call method
        status, response = self.controller.handle_request(
            path=f"/api/projects/{self.test_project_id}",
            method="GET"
        )
        
        # Verify response
        self.assertEqual(status, 200)
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["data"], self.test_project)
    
    def test_handle_request_search_documents(self):
        """Test handling request for searching documents."""
        # Set up mock response
        self.mock_project_manager.get_project.return_value = self.test_project
        self.mock_search_engine.search.return_value = [self.test_document]
        
        # Call method
        status, response = self.controller.handle_request(
            path=f"/api/projects/{self.test_project_id}/search",
            method="POST",
            body={"query": "test query"}
        )
        
        # Verify response
        self.assertEqual(status, 200)
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["data"], [self.test_document])
    
    def test_handle_request_invalid_path(self):
        """Test handling request with invalid path."""
        # Call method
        status, response = self.controller.handle_request(
            path="/invalid/path",
            method="GET"
        )
        
        # Verify response
        self.assertEqual(status, 404)
        self.assertEqual(response["status"], "error")
        self.assertEqual(response["error"], "Invalid path")
    
    def test_handle_request_method_not_allowed(self):
        """Test handling request with method not allowed."""
        # Call method
        status, response = self.controller.handle_request(
            path="/api/projects",
            method="PUT"
        )
        
        # Verify response
        self.assertEqual(status, 405)
        self.assertEqual(response["status"], "error")
        self.assertEqual(response["error"], "Method not allowed")


if __name__ == "__main__":
    unittest.main()