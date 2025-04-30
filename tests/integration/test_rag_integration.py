#!/usr/bin/env python3
"""
Integration tests for RAG system components.

Tests the integration between document management, search, and context generation,
ensuring all RAG components work together correctly.
"""

import unittest
import os
import tempfile
import shutil
import json
import uuid
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import core modules
from core.paths import get_app_path

# Import RAG modules
from rag_support.utils.project_manager import ProjectManager
from rag_support.utils.search import SearchEngine
from rag_support.utils.context_manager import ContextManager
from rag_support.utils.hybrid_search import hybrid_search, HAS_HYBRID_SEARCH


class RagIntegrationTest(unittest.TestCase):
    """Integration tests for RAG system components."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment for all tests."""
        # Create temporary test directory
        cls.temp_dir = Path(tempfile.mkdtemp())
        
        # Create test directories
        cls.projects_dir = cls.temp_dir / "projects"
        cls.embeddings_dir = cls.temp_dir / "embeddings"
        
        os.makedirs(cls.projects_dir)
        os.makedirs(cls.embeddings_dir)
        
        # Set up patchers for external dependencies
        cls.get_app_path_patcher = patch('core.paths.get_app_path')
        cls.mock_get_app_path = cls.get_app_path_patcher.start()
        cls.mock_get_app_path.return_value = cls.temp_dir
        
        # Mock embeddings functionality
        cls.mock_embeddings = MagicMock()
        cls.mock_embeddings.embed.return_value = [0.1, 0.2, 0.3, 0.4, 0.5]
        
        cls.get_embeddings_patcher = patch('rag_support.utils.search.get_embeddings')
        cls.mock_get_embeddings = cls.get_embeddings_patcher.start()
        cls.mock_get_embeddings.return_value = cls.mock_embeddings
        
        # Create test instances
        cls.project_manager = ProjectManager(cls.projects_dir)
        cls.search_engine = SearchEngine()
        cls.context_manager = ContextManager()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests."""
        # Stop patchers
        cls.get_app_path_patcher.stop()
        cls.get_embeddings_patcher.stop()
        
        # Remove temporary directory
        shutil.rmtree(cls.temp_dir)
    
    def setUp(self):
        """Set up test environment for each test."""
        # Create test project
        self.test_project = self.project_manager.create_project(
            "Test Project",
            "A test project for integration testing"
        )
        self.test_project_id = self.test_project["id"]
        
        # Create test documents
        self.test_documents = []
        for i in range(5):
            doc = self.project_manager.add_document(
                self.test_project_id,
                f"Test Document {i}",
                f"This is test document {i} with some content for testing. " 
                f"It contains information about topic {i} and related concepts.",
                [f"tag{i}", "test"]
            )
            self.test_documents.append(doc)
    
    def tearDown(self):
        """Clean up after each test."""
        # Remove test project
        for project in self.project_manager.get_projects():
            self.project_manager.delete_project(project["id"])
    
    def test_project_document_integration(self):
        """Test project and document management integration."""
        # Get all projects
        projects = self.project_manager.get_projects()
        
        # Check that test project is in the list
        self.assertEqual(len(projects), 1)
        self.assertEqual(projects[0]["id"], self.test_project_id)
        
        # Get project by ID
        project = self.project_manager.get_project(self.test_project_id)
        self.assertEqual(project["name"], "Test Project")
        
        # Get all documents for project
        documents = self.project_manager.get_documents(self.test_project_id)
        
        # Check that all test documents are present
        self.assertEqual(len(documents), 5)
        
        # Get a specific document
        document_id = self.test_documents[0]["id"]
        document = self.project_manager.get_document(self.test_project_id, document_id)
        
        # Check document properties
        self.assertEqual(document["title"], "Test Document 0")
        self.assertIn("tag0", document["tags"])
        
        # Update a document
        updated_document = self.project_manager.update_document(
            self.test_project_id,
            document_id,
            "Updated Document",
            "Updated content",
            ["updated", "test"]
        )
        
        # Check updated document
        self.assertEqual(updated_document["title"], "Updated Document")
        self.assertEqual(updated_document["content"], "Updated content")
        self.assertIn("updated", updated_document["tags"])
        
        # Delete a document
        self.project_manager.delete_document(self.test_project_id, document_id)
        
        # Check that document is deleted
        documents = self.project_manager.get_documents(self.test_project_id)
        self.assertEqual(len(documents), 4)
        self.assertIsNone(self.project_manager.get_document(self.test_project_id, document_id))
    
    def test_search_integration(self):
        """Test search functionality integration."""
        # Perform keyword search
        results = self.search_engine.search(self.test_project_id, "document")
        
        # Check search results
        self.assertGreater(len(results), 0)
        
        # All results should be from the test project
        for doc in results:
            self.assertEqual(doc["project_id"], self.test_project_id)
        
        # Test search with tag filter
        results = self.search_engine.search(self.test_project_id, "test", tags=["tag0"])
        
        # Check that results are filtered by tag
        self.assertEqual(len(results), 1)
        self.assertIn("tag0", results[0]["tags"])
    
    @unittest.skipIf(not HAS_HYBRID_SEARCH, "Hybrid search not available")
    def test_hybrid_search_integration(self):
        """Test hybrid search functionality integration."""
        # Perform hybrid search
        results = hybrid_search(
            self.test_project_id,
            "information about topics",
            semantic_weight=0.6,
            keyword_weight=0.4,
            max_results=3
        )
        
        # Check search results
        self.assertLessEqual(len(results), 3)
        
        # All results should be from the test project
        for doc in results:
            self.assertEqual(doc["project_id"], self.test_project_id)
    
    def test_context_generation_integration(self):
        """Test context generation integration."""
        # Generate context
        context, used_docs, truncated = self.context_manager.generate_context(
            self.test_project_id,
            "test information topics",
            max_tokens=1000
        )
        
        # Check context properties
        self.assertIsInstance(context, str)
        self.assertGreater(len(context), 0)
        self.assertGreater(len(used_docs), 0)
        
        # Check that used documents are from the project
        for doc_id in used_docs:
            doc = self.project_manager.get_document(self.test_project_id, doc_id)
            self.assertIsNotNone(doc)
        
        # Test context generation with specific document IDs
        doc_ids = [self.test_documents[0]["id"], self.test_documents[1]["id"]]
        context, used_docs, truncated = self.context_manager.generate_context(
            self.test_project_id,
            "test query",
            max_tokens=1000,
            document_ids=doc_ids
        )
        
        # Check that only specified documents are used
        self.assertLessEqual(set(used_docs), set(doc_ids))
    
    def test_end_to_end_rag_pipeline(self):
        """Test end-to-end RAG pipeline."""
        # Create a project
        project = self.project_manager.create_project(
            "E2E Test Project",
            "Project for end-to-end testing"
        )
        project_id = project["id"]
        
        # Add documents
        docs = []
        for i in range(3):
            doc = self.project_manager.add_document(
                project_id,
                f"E2E Document {i}",
                f"This document contains information about the RAG system. "
                f"Retrieval Augmented Generation is a technique that combines "
                f"retrieval of documents with text generation. "
                f"This is document {i} in the collection.",
                ["rag", f"doc{i}"]
            )
            docs.append(doc)
        
        # Search for documents
        results = self.search_engine.search(project_id, "retrieval augmented generation")
        self.assertGreater(len(results), 0)
        
        # Generate context
        context, used_docs, truncated = self.context_manager.generate_context(
            project_id,
            "What is RAG?",
            max_tokens=1000
        )
        self.assertGreater(len(context), 0)
        self.assertGreater(len(used_docs), 0)
        
        # Clean up
        self.project_manager.delete_project(project_id)


if __name__ == "__main__":
    unittest.main()