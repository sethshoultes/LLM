#!/usr/bin/env python3
"""
Unit tests for the API extensions module.

Tests the functionality of the RAG API extensions, including
project management, document operations, search, and context handling.
"""

import sys
import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the module to test
from rag_support.api_extensions_new import RagApiHandler


class TestRagApiHandler(unittest.TestCase):
    """Tests for the RagApiHandler class."""
    
    def setUp(self):
        """Set up test environment."""
        # Create temporary test directory
        self.temp_dir = tempfile.mkdtemp()
        
        # Create API handler
        self.api_handler = RagApiHandler()
        
        # Mock project manager
        self.mock_project_manager = MagicMock()
        
        # Create patch for project_manager
        self.project_manager_patch = patch('rag_support.api_extensions_new.project_manager', self.mock_project_manager)
        self.project_manager_patch.start()
        
        # Create mock search engine
        self.mock_search_engine = MagicMock()
        
        # Create patch for search_engine
        self.search_engine_patch = patch('rag_support.api_extensions_new.search_engine', self.mock_search_engine)
        self.search_engine_patch.start()
        
        # Test data
        self.test_project_id = "test-project-id"
        self.test_project = {
            "id": self.test_project_id,
            "name": "Test Project",
            "description": "Test project description",
            "document_count": 5,
            "chat_count": 2,
            "artifact_count": 1
        }
        
        self.test_document_id = "test-document-id"
        self.test_document = {
            "id": self.test_document_id,
            "title": "Test Document",
            "content": "Test document content",
            "tags": ["test", "document"]
        }
        
        # Set up mock returns
        self.mock_project_manager.get_project.return_value = self.test_project
        self.mock_project_manager.get_document.return_value = self.test_document
    
    def tearDown(self):
        """Clean up test environment."""
        # Stop patches
        self.project_manager_patch.stop()
        self.search_engine_patch.stop()
        
        # Remove temporary directory
        shutil.rmtree(self.temp_dir)
    
    def test_format_error_response(self):
        """Test error response formatting."""
        status, response = self.api_handler._format_error_response(
            400, "Test error", "Test error detail", "test_error_code"
        )
        
        self.assertEqual(status, 400)
        self.assertEqual(response["error"], "Test error")
        self.assertEqual(response["detail"], "Test error detail")
        self.assertEqual(response["code"], "test_error_code")
    
    def test_format_success_response(self):
        """Test success response formatting."""
        status, response = self.api_handler._format_success_response(
            {"key": "value"}, "Test message", {"meta_key": "meta_value"}
        )
        
        self.assertEqual(status, 200)
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["data"], {"key": "value"})
        self.assertEqual(response["message"], "Test message")
        self.assertEqual(response["meta"]["meta_key"], "meta_value")
    
    def test_list_projects(self):
        """Test listing projects."""
        # Set up mock response
        self.mock_project_manager.get_projects.return_value = [self.test_project]
        
        # Call method
        status, response = self.api_handler._list_projects()
        
        # Verify response
        self.assertEqual(status, 200)
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["data"], [self.test_project])
        self.assertEqual(response["meta"]["count"], 1)
    
    def test_get_project(self):
        """Test getting a project."""
        # Call method
        status, response = self.api_handler._get_project(self.test_project_id)
        
        # Verify response
        self.assertEqual(status, 200)
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["data"], self.test_project)
        
        # Test nonexistent project
        self.mock_project_manager.get_project.return_value = None
        status, response = self.api_handler._get_project("nonexistent")
        
        self.assertEqual(status, 404)
        self.assertEqual(response["error"], "Project not found")
    
    def test_create_project(self):
        """Test creating a project."""
        # Set up mock response
        self.mock_project_manager.create_project.return_value = self.test_project_id
        
        # Call method
        status, response = self.api_handler._create_project({
            "name": "Test Project",
            "description": "Test project description"
        })
        
        # Verify response
        self.assertEqual(status, 200)
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["data"], self.test_project)
        
        # Test missing name
        status, response = self.api_handler._create_project({
            "description": "Test project description"
        })
        
        self.assertEqual(status, 400)
        self.assertEqual(response["error"], "Missing required field")
    
    def test_delete_project(self):
        """Test deleting a project."""
        # Set up mock response
        self.mock_project_manager.delete_project.return_value = True
        
        # Call method
        status, response = self.api_handler._delete_project(self.test_project_id)
        
        # Verify response
        self.assertEqual(status, 200)
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["data"], {"id": self.test_project_id})
        
        # Test nonexistent project
        self.mock_project_manager.get_project.return_value = None
        status, response = self.api_handler._delete_project("nonexistent")
        
        self.assertEqual(status, 404)
        self.assertEqual(response["error"], "Project not found")
    
    def test_list_documents(self):
        """Test listing documents."""
        # Set up mock response
        self.mock_project_manager.list_documents.return_value = [self.test_document]
        
        # Call method
        status, response = self.api_handler._list_documents(self.test_project_id)
        
        # Verify response
        self.assertEqual(status, 200)
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["data"], [self.test_document])
        self.assertEqual(response["meta"]["count"], 1)
        
        # Test nonexistent project
        self.mock_project_manager.get_project.return_value = None
        status, response = self.api_handler._list_documents("nonexistent")
        
        self.assertEqual(status, 404)
        self.assertEqual(response["error"], "Project not found")
    
    def test_get_document(self):
        """Test getting a document."""
        # Call method
        status, response = self.api_handler._get_document(self.test_project_id, self.test_document_id)
        
        # Verify response
        self.assertEqual(status, 200)
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["data"], self.test_document)
        
        # Test nonexistent document
        self.mock_project_manager.get_document.return_value = None
        status, response = self.api_handler._get_document(self.test_project_id, "nonexistent")
        
        self.assertEqual(status, 404)
        self.assertEqual(response["error"], "Document not found")
    
    def test_create_document(self):
        """Test creating a document."""
        # Set up mock response
        self.mock_project_manager.add_document.return_value = self.test_document_id
        
        # Call method
        status, response = self.api_handler._create_document(self.test_project_id, {
            "title": "Test Document",
            "content": "Test document content",
            "tags": ["test", "document"]
        })
        
        # Verify response
        self.assertEqual(status, 200)
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["data"], self.test_document)
        
        # Test missing title
        status, response = self.api_handler._create_document(self.test_project_id, {
            "content": "Test document content"
        })
        
        self.assertEqual(status, 400)
        self.assertEqual(response["error"], "Missing document title")
        
        # Test missing content
        status, response = self.api_handler._create_document(self.test_project_id, {
            "title": "Test Document"
        })
        
        self.assertEqual(status, 400)
        self.assertEqual(response["error"], "Missing document content")
    
    def test_delete_document(self):
        """Test deleting a document."""
        # Set up mock response
        self.mock_project_manager.delete_document.return_value = True
        
        # Call method
        status, response = self.api_handler._delete_document(self.test_project_id, self.test_document_id)
        
        # Verify response
        self.assertEqual(status, 200)
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["data"], {"id": self.test_document_id})
        
        # Test nonexistent document
        self.mock_project_manager.get_document.return_value = None
        status, response = self.api_handler._delete_document(self.test_project_id, "nonexistent")
        
        self.assertEqual(status, 404)
        self.assertEqual(response["error"], "Document not found")
    
    @patch('rag_support.api_extensions_new.HAS_HYBRID_SEARCH', False)
    def test_search_documents(self):
        """Test searching documents."""
        # Set up mock response
        self.mock_search_engine.search.return_value = [self.test_document]
        
        # Call method
        status, response = self.api_handler._search_documents(self.test_project_id, "test query")
        
        # Verify response
        self.assertEqual(status, 200)
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["data"], [self.test_document])
        self.assertEqual(response["meta"]["count"], 1)
        self.assertEqual(response["meta"]["query"], "test query")
        self.assertEqual(response["meta"]["search_type"], "keyword")
        
        # Test empty query
        status, response = self.api_handler._search_documents(self.test_project_id, "")
        
        self.assertEqual(status, 200)
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["data"], [])
        self.assertEqual(response["meta"]["count"], 0)
    
    @patch('rag_support.api_extensions_new.HAS_HYBRID_SEARCH', False)
    def test_suggest_documents(self):
        """Test suggesting documents."""
        # Set up mock response
        self.mock_search_engine.search.return_value = [self.test_document]
        
        # Call method
        status, response = self.api_handler._suggest_documents(self.test_project_id, "test query")
        
        # Verify response
        self.assertEqual(status, 200)
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["data"], [self.test_document])
        self.assertEqual(response["meta"]["count"], 1)
        self.assertEqual(response["meta"]["query"], "test query")
        self.assertEqual(response["meta"]["search_type"], "keyword")
        
        # Test empty query
        status, response = self.api_handler._suggest_documents(self.test_project_id, "")
        
        self.assertEqual(status, 200)
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["data"], [])
        self.assertEqual(response["meta"]["count"], 0)
    
    def test_handle_request(self):
        """Test request handling."""
        # Mock response for list_projects
        self.mock_project_manager.get_projects.return_value = [self.test_project]
        
        # Test list projects endpoint
        status, response = self.api_handler.handle_request(
            path="/api/projects",
            method="GET"
        )
        
        self.assertEqual(status, 200)
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["data"], [self.test_project])
        
        # Test invalid endpoint
        status, response = self.api_handler.handle_request(
            path="/api/invalid",
            method="GET"
        )
        
        self.assertEqual(status, 404)
        self.assertEqual(response["error"], "Endpoint not found")
        
        # Test invalid method
        status, response = self.api_handler.handle_request(
            path="/api/projects",
            method="PUT"
        )
        
        self.assertEqual(status, 405)
        self.assertEqual(response["error"], "Method not allowed")


if __name__ == "__main__":
    unittest.main()