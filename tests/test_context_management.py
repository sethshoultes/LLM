#!/usr/bin/env python3
"""
Unit tests for the context management modules.

Tests the functionality of the token management, context handling,
token allocation, document prioritization, and context formatting
modules of the RAG system.
"""

import sys
import unittest
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the modules to test
from rag.tokens import TokenManager
from rag.context import ContextManager
from rag.allocator import TokenAllocator
from rag.prioritizer import DocumentPrioritizer
from rag.formatter import ContextFormatter


class TestTokenManager(unittest.TestCase):
    """Tests for the TokenManager class."""
    
    def setUp(self):
        """Set up test environment."""
        self.token_manager = TokenManager()
    
    def test_estimate_tokens(self):
        """Test token estimation."""
        # Test empty text
        self.assertEqual(self.token_manager.estimate_tokens(""), 0)
        
        # Test short text
        text = "This is a short text."
        tokens = self.token_manager.estimate_tokens(text)
        self.assertGreater(tokens, 0)
        self.assertLess(tokens, len(text))  # Tokens should be fewer than characters
        
        # Test longer text
        long_text = "This is a longer text with multiple sentences. " * 10
        long_tokens = self.token_manager.estimate_tokens(long_text)
        self.assertGreater(long_tokens, tokens)  # Longer text should have more tokens
    
    def test_estimate_prompt_tokens(self):
        """Test prompt token estimation."""
        # Test empty messages
        self.assertEqual(self.token_manager.estimate_prompt_tokens([])["total"], 0)
        
        # Test with messages
        messages = [
            {"role": "user", "content": "Hello, how are you?"},
            {"role": "assistant", "content": "I'm doing well, how can I help you today?"},
            {"role": "user", "content": "Tell me about context management."}
        ]
        
        result = self.token_manager.estimate_prompt_tokens(messages)
        self.assertIsInstance(result, dict)
        self.assertIn("total", result)
        self.assertIn("messages", result)
        self.assertIn("message_count", result)
        self.assertEqual(result["message_count"], 3)
        self.assertGreater(result["total"], 0)
    
    def test_get_context_window(self):
        """Test context window determination."""
        # Test default
        self.assertGreater(self.token_manager.get_context_window(), 0)
        
        # Test with different model paths
        self.assertEqual(self.token_manager.get_context_window(model_path="/models/llama-7b.gguf"), 4096)
        self.assertEqual(self.token_manager.get_context_window(model_path="/models/tiny-1b.gguf"), 2048)
        self.assertEqual(self.token_manager.get_context_window(model_path="/models/llama-70b.gguf"), 8192)
    
    def test_allocate_tokens(self):
        """Test token allocation."""
        # Test basic allocation
        allocation = self.token_manager.allocate_tokens(
            context_window=4096,
            system_tokens=100,
            message_tokens=500
        )
        
        self.assertIsInstance(allocation, dict)
        self.assertEqual(allocation["context_window"], 4096)
        self.assertEqual(allocation["system_tokens"], 100)
        self.assertEqual(allocation["message_tokens"], 500)
        self.assertGreater(allocation["reserved_tokens"], 0)
        self.assertGreater(allocation["available_for_context"], 0)
        self.assertFalse(allocation["is_over_limit"])
        
        # Test over limit
        over_allocation = self.token_manager.allocate_tokens(
            context_window=1000,
            system_tokens=500,
            message_tokens=600
        )
        
        self.assertTrue(over_allocation["is_over_limit"])
        self.assertEqual(over_allocation["available_for_context"], 0)


class TestContextManager(unittest.TestCase):
    """Tests for the ContextManager class."""
    
    def setUp(self):
        """Set up test environment."""
        self.context_manager = ContextManager(model_id="test_model")
        
        # Create test documents
        self.test_docs = [
            {
                "id": "doc1",
                "title": "Document 1",
                "content": "This is the content of document 1. It contains information about testing.",
                "score": 0.9
            },
            {
                "id": "doc2",
                "title": "Document 2",
                "content": "This is the content of document 2. It has different information.",
                "score": 0.7
            },
            {
                "id": "doc3",
                "title": "Document 3",
                "content": "This is the content of document 3. More test content here.",
                "score": 0.5
            }
        ]
    
    def test_select_documents(self):
        """Test document selection based on token budget."""
        # Test with enough tokens for all documents
        selected = self.context_manager.select_documents(
            documents=self.test_docs,
            query="test information",
            available_tokens=1000
        )
        
        self.assertEqual(len(selected), 3)
        self.assertEqual(selected[0]["id"], "doc1")  # Highest score should be first
        self.assertFalse(selected[0]["truncated"])
        
        # Test with limited tokens
        small_selected = self.context_manager.select_documents(
            documents=self.test_docs,
            query="test information",
            available_tokens=50
        )
        
        self.assertLessEqual(len(small_selected), 1)
        if small_selected:
            self.assertTrue(small_selected[0]["truncated"])
    
    def test_format_context(self):
        """Test context formatting."""
        # Test with documents
        context_text, metadata = self.context_manager.format_context(
            documents=self.test_docs,
            query="test information"
        )
        
        self.assertIsInstance(context_text, str)
        self.assertGreater(len(context_text), 0)
        self.assertEqual(len(metadata), 3)
        
        # Verify that document titles are included in the context
        for doc in self.test_docs:
            self.assertIn(doc["title"], context_text)
        
        # Test with empty documents
        empty_text, empty_meta = self.context_manager.format_context([], "")
        self.assertEqual(empty_text, "")
        self.assertEqual(empty_meta, [])


class TestTokenAllocator(unittest.TestCase):
    """Tests for the TokenAllocator class."""
    
    def setUp(self):
        """Set up test environment."""
        self.allocator = TokenAllocator()
        
        # Create test documents
        self.test_docs = [
            {
                "id": "doc1",
                "title": "Document 1",
                "content": "This is the content of document 1. It contains information about testing.",
                "score": 0.9,
                "total_tokens": 30
            },
            {
                "id": "doc2",
                "title": "Document 2",
                "content": "This is the content of document 2. It has different information.",
                "score": 0.7,
                "total_tokens": 25
            },
            {
                "id": "doc3",
                "title": "Document 3",
                "content": "This is the content of document 3. More test content here.",
                "score": 0.5,
                "total_tokens": 20
            }
        ]
    
    def test_allocate_equal(self):
        """Test equal token allocation."""
        allocated = self.allocator._allocate_equal(self.test_docs, 300)
        
        self.assertEqual(len(allocated), 3)
        # Should have similar allocations
        self.assertAlmostEqual(allocated[0]["allocated_tokens"], 
                              allocated[1]["allocated_tokens"], delta=5)
    
    def test_allocate_proportional(self):
        """Test proportional token allocation."""
        allocated = self.allocator._allocate_proportional(self.test_docs, 300)
        
        self.assertEqual(len(allocated), 3)
        # Higher score should get more tokens
        self.assertGreater(allocated[0]["allocated_tokens"], 
                          allocated[2]["allocated_tokens"])
    
    def test_allocate_prioritized(self):
        """Test prioritized token allocation."""
        allocated = self.allocator._allocate_prioritized(self.test_docs, 100)
        
        # Should prioritize highest scoring documents
        self.assertEqual(allocated[0]["id"], "doc1")
        
        # Test with very limited tokens
        limited = self.allocator._allocate_prioritized(self.test_docs, 40)
        self.assertEqual(len(limited), 1)  # Should only include one document
        self.assertEqual(limited[0]["id"], "doc1")  # Should be the highest scoring
    
    def test_allocate_tokens(self):
        """Test the main allocation method."""
        # Test with default strategy
        allocated = self.allocator.allocate_tokens(
            documents=self.test_docs,
            available_tokens=200
        )
        
        self.assertIsInstance(allocated, list)
        self.assertGreater(len(allocated), 0)
        
        # Test with different strategies
        strategies = ["equal", "proportional", "prioritized", "adaptive"]
        for strategy in strategies:
            result = self.allocator.allocate_tokens(
                documents=self.test_docs,
                available_tokens=200,
                strategy=strategy,
                query="test query" if strategy == "adaptive" else None
            )
            self.assertIsInstance(result, list)
            self.assertGreater(len(result), 0)


class TestDocumentPrioritizer(unittest.TestCase):
    """Tests for the DocumentPrioritizer class."""
    
    def setUp(self):
        """Set up test environment."""
        self.prioritizer = DocumentPrioritizer()
        
        # Create test documents
        self.test_docs = [
            {
                "id": "doc1",
                "title": "Machine Learning Algorithms",
                "content": "This document covers various machine learning algorithms including neural networks and decision trees.",
                "score": 0.7,
                "tags": ["ML", "algorithms", "AI"]
            },
            {
                "id": "doc2",
                "title": "Neural Network Architecture",
                "content": "Deep dive into neural network architectures and their applications in computer vision and NLP.",
                "score": 0.8,
                "tags": ["neural networks", "deep learning", "AI"]
            },
            {
                "id": "doc3",
                "title": "Introduction to Python",
                "content": "Basic introduction to Python programming language and its data structures.",
                "score": 0.5,
                "tags": ["python", "programming"]
            }
        ]
        
        # Create test conversation history
        self.test_history = [
            {"role": "user", "content": "Tell me about machine learning algorithms"},
            {"role": "assistant", "content": "Machine learning algorithms are methods used to automatically find patterns in data and make predictions."},
            {"role": "user", "content": "How do neural networks work?"}
        ]
    
    def test_prioritize_documents(self):
        """Test document prioritization."""
        # Test basic prioritization
        prioritized = self.prioritizer.prioritize_documents(
            documents=self.test_docs,
            query="neural networks in machine learning",
            max_documents=3
        )
        
        self.assertEqual(len(prioritized), 3)
        # Neural networks document should be prioritized higher given the query
        self.assertEqual(prioritized[0]["id"], "doc2")
        
        # Test with history
        with_history = self.prioritizer.prioritize_documents(
            documents=self.test_docs,
            query="neural networks in machine learning",
            history=self.test_history,
            max_documents=3
        )
        
        self.assertEqual(len(with_history), 3)
        # Should keep neural networks document prioritized
        self.assertEqual(with_history[0]["id"], "doc2")
    
    def test_apply_query_analysis(self):
        """Test query analysis for prioritization."""
        # Apply query analysis
        analyzed = self.prioritizer._apply_query_analysis(
            documents=self.test_docs.copy(),
            query="neural networks for image recognition"
        )
        
        self.assertEqual(len(analyzed), 3)
        # All documents should have priority scores
        for doc in analyzed:
            self.assertIn("priority_score", doc)
            
        # Doc2 should have highest priority given the query
        doc2 = next(doc for doc in analyzed if doc["id"] == "doc2")
        doc3 = next(doc for doc in analyzed if doc["id"] == "doc3")
        self.assertGreater(doc2["priority_score"], doc3["priority_score"])
    
    def test_apply_diversity_promotion(self):
        """Test diversity promotion."""
        # Apply diversity promotion
        diverse = self.prioritizer._apply_diversity_promotion(
            documents=self.test_docs.copy()
        )
        
        self.assertEqual(len(diverse), 3)
        # All documents should have diversity scores
        for doc in diverse:
            self.assertIn("priority_score", doc)
            
        # Doc3 should get a diversity boost since it has unique tags
        doc3 = next(doc for doc in diverse if doc["id"] == "doc3")
        self.assertIn("diversity_score", doc3)


class TestContextFormatter(unittest.TestCase):
    """Tests for the ContextFormatter class."""
    
    def setUp(self):
        """Set up test environment."""
        self.formatter = ContextFormatter()
        
        # Create test document
        self.test_doc = {
            "id": "doc1",
            "title": "Test Document",
            "content": "This is a test document with sample content for testing context formatting.",
            "source": "Test Source"
        }
        
        # Create test documents list
        self.test_docs = [
            self.test_doc,
            {
                "id": "doc2",
                "title": "Another Document",
                "content": "This is another document with different content.",
                "source": "Another Source"
            }
        ]
    
    def test_format_document(self):
        """Test document formatting."""
        # Test basic formatting
        formatted, tokens = self.formatter.format_document(self.test_doc)
        
        self.assertIsInstance(formatted, str)
        self.assertGreater(tokens, 0)
        self.assertIn(self.test_doc["title"], formatted)
        self.assertIn(self.test_doc["content"], formatted)
        
        # Test with token limit
        limited, limited_tokens = self.formatter.format_document(self.test_doc, 20)
        
        self.assertIsInstance(limited, str)
        self.assertLessEqual(limited_tokens, 20)
        self.assertIn(self.test_doc["title"], limited)
        
        # Content might be truncated
        if len(self.test_doc["content"]) > 0 and self.test_doc["content"] not in limited:
            self.assertIn(self.test_doc["content"][:10], limited)
    
    def test_format_documents(self):
        """Test formatting multiple documents."""
        # Test basic formatting
        formatted, metadata = self.formatter.format_documents(self.test_docs)
        
        self.assertIsInstance(formatted, str)
        self.assertEqual(len(metadata), 2)
        
        # Should include all document titles
        for doc in self.test_docs:
            self.assertIn(doc["title"], formatted)
        
        # Test with token allocations
        allocations = {
            "doc1": 50,
            "doc2": 30
        }
        
        allocated, allocated_meta = self.formatter.format_documents(
            documents=self.test_docs,
            allocated_tokens=allocations
        )
        
        self.assertIsInstance(allocated, str)
        self.assertEqual(len(allocated_meta), 2)
    
    def test_create_system_prompt(self):
        """Test system prompt creation."""
        # Test with base prompt
        base_prompt = "Answer the following question based on the provided context:"
        system_prompt, metadata = self.formatter.create_system_prompt(
            base_prompt=base_prompt,
            documents=self.test_docs
        )
        
        self.assertIsInstance(system_prompt, str)
        self.assertIn(base_prompt, system_prompt)
        self.assertEqual(len(metadata), 2)
        
        # Test without base prompt
        no_base, no_base_meta = self.formatter.create_system_prompt(
            base_prompt="",
            documents=self.test_docs
        )
        
        self.assertIsInstance(no_base, str)
        self.assertGreater(len(no_base), 0)
        self.assertEqual(len(no_base_meta), 2)


if __name__ == "__main__":
    unittest.main()