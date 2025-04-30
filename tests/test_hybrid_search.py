#!/usr/bin/env python3
"""
Unit tests for the hybrid search functionality.
"""

import sys
import unittest
import tempfile
import shutil
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the modules to test


class TestHybridSearch(unittest.TestCase):
    """Tests for the HybridSearch class."""
    
    def setUp(self):
        """Set up test environment."""
        # Create temp directory for test data
        self.test_dir = tempfile.mkdtemp()
        self.test_project_id = "test_project"
        
        # Create mock documents
        self.mock_docs = [
            {
                "id": "doc1",
                "title": "Machine Learning Basics",
                "content": "Machine learning is a subfield of artificial intelligence that focuses on algorithms that learn from data.",
                "tags": ["ML", "AI", "algorithms"]
            },
            {
                "id": "doc2",
                "title": "Deep Learning Networks",
                "content": "Neural networks with multiple layers (deep learning) have revolutionized computer vision and natural language processing.",
                "tags": ["DL", "neural networks", "AI"]
            },
            {
                "id": "doc3",
                "title": "Reinforcement Learning",
                "content": "Reinforcement learning is training algorithms to make decisions by rewarding desired behaviors and punishing undesired ones.",
                "tags": ["RL", "AI", "algorithms"]
            }
        ]
        
        # Create mock embeddings
        self.mock_embeddings = {
            "doc1": np.array([0.1, 0.2, 0.3, 0.4]),
            "doc2": np.array([0.2, 0.3, 0.4, 0.5]),
            "doc3": np.array([0.3, 0.4, 0.5, 0.6])
        }
        
        # Initialize the search object
        self.search = HybridSearch()
        
        # Mock embedding model
        self.search.model_loaded = True
        self.search.embedding_model = MagicMock()
        
        # Setup query embedding return value
        self.query_embedding = np.array([0.2, 0.3, 0.4, 0.5])  # Similar to doc2
        self.search.embedding_model.encode.return_value = self.query_embedding
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove temp directory
        shutil.rmtree(self.test_dir)
    
    @patch('rag_support.utils.hybrid_search.tfidf_search')
    def test_get_embedding(self, mock_tfidf):
        """Test getting embeddings for text."""
        # Arrange
        text = "Test sentence for embedding"
        
        # Act
        embedding = self.search.get_embedding(text)
        
        # Assert
        self.assertIsNotNone(embedding)
        self.search.embedding_model.encode.assert_called_once_with(text, normalize_embeddings=True)
        self.assertTrue(np.array_equal(embedding, self.query_embedding))
    
    @patch('rag_support.utils.hybrid_search.tfidf_search')
    @patch('rag_support.utils.hybrid_search.project_manager')
    def test_semantic_search(self, mock_pm, mock_tfidf):
        """Test semantic search functionality."""
        # Arrange
        query = "neural networks for computer vision"
        
        # Mock load_document_embeddings
        self.search.load_document_embeddings = MagicMock(return_value=self.mock_embeddings)
        
        # Mock project_manager.get_document to return our mock docs
        def mock_get_document(project_id, doc_id):
            for doc in self.mock_docs:
                if doc["id"] == doc_id:
                    return doc
            return None
        
        mock_pm.get_document.side_effect = mock_get_document
        
        # Act
        results = self.search.semantic_search(self.test_project_id, query)
        
        # Assert
        self.assertEqual(len(results), 3)  # Should return all documents
        # Doc2 should be most similar to query embedding
        self.assertEqual(results[0]["id"], "doc2")
    
    @patch('rag_support.utils.hybrid_search.tfidf_search')
    def test_hybrid_search(self, mock_tfidf):
        """Test hybrid search functionality."""
        # Arrange
        query = "neural networks for computer vision"
        
        # Mock semantic_search to return results
        semantic_results = [
            {"id": "doc2", "score": 0.9, "title": "Deep Learning Networks"},
            {"id": "doc1", "score": 0.6, "title": "Machine Learning Basics"},
            {"id": "doc3", "score": 0.5, "title": "Reinforcement Learning"}
        ]
        self.search.semantic_search = MagicMock(return_value=semantic_results)
        
        # Mock tfidf_search.search to return results
        keyword_results = [
            {"id": "doc1", "score": 0.8, "title": "Machine Learning Basics"},
            {"id": "doc2", "score": 0.7, "title": "Deep Learning Networks"},
            {"id": "doc3", "score": 0.3, "title": "Reinforcement Learning"}
        ]
        mock_tfidf.search.return_value = keyword_results
        
        # Act
        results = self.search.hybrid_search(
            self.test_project_id, 
            query, 
            semantic_weight=0.6, 
            keyword_weight=0.4
        )
        
        # Assert
        self.assertEqual(len(results), 3)
        
        # Doc2 should be first (high in both semantic and keyword)
        self.assertEqual(results[0]["id"], "doc2")
        
        # Check that score combines both semantic and keyword
        # doc2: (0.9 * 0.6) + (0.7 * 0.4) = 0.54 + 0.28 = 0.82
        self.assertAlmostEqual(results[0]["score"], 0.82, places=2)
        
        # Verify score breakdown
        self.assertEqual(results[0]["score_breakdown"]["semantic_weight"], 0.6)
        self.assertEqual(results[0]["score_breakdown"]["keyword_weight"], 0.4)
    
    @patch('rag_support.utils.hybrid_search.np.savez_compressed')
    @patch('rag_support.utils.hybrid_search.open')
    @patch('rag_support.utils.hybrid_search.project_manager')
    def test_save_embeddings_to_cache(self, mock_pm, mock_open, mock_savez):
        """Test saving embeddings to cache."""
        # Arrange
        mock_pm.list_documents.return_value = [
            {"id": "doc1", "title": "Doc 1", "updated_at": "2025-04-29"},
            {"id": "doc2", "title": "Doc 2", "updated_at": "2025-04-29"}
        ]
        
        embeddings = {
            "doc1": np.array([0.1, 0.2]),
            "doc2": np.array([0.3, 0.4])
        }
        
        # Act
        self.search._save_embeddings_to_cache(self.test_project_id, embeddings)
        
        # Assert
        mock_savez.assert_called_once()
        mock_open.assert_called_once()


if __name__ == "__main__":
    unittest.main()