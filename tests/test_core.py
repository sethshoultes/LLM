#!/usr/bin/env python3
"""
Unit tests for the core module.

Tests the basic functionality of the core module components:
- Paths
- Configuration
- Logging
- Error handling
- Utilities
"""

import os
import sys
import unittest
from pathlib import Path

# Ensure base directories are in path
SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Import modules to test
from core import initialize as init_core
from core.paths import get_path, resolve_path, ensure_dir
from core.errors import LLMError, ModelError
from core.utils import parse_frontmatter, format_with_frontmatter, estimate_tokens

class TestCorePaths(unittest.TestCase):
    """Test the core.paths module."""
    
    def test_get_path(self):
        """Test getting standard paths."""
        # Get base directory
        base_dir = get_path("base")
        self.assertTrue(isinstance(base_dir, Path))
        self.assertTrue(base_dir.exists())
        
        # Get core directory
        core_dir = get_path("core")
        self.assertTrue(isinstance(core_dir, Path))
        self.assertTrue(core_dir.exists())
        
        # Check relative path
        self.assertEqual(core_dir.relative_to(base_dir), Path("core"))
    
    def test_resolve_path(self):
        """Test resolving paths."""
        # Resolve absolute path
        absolute_path = Path("/tmp/test")
        resolved = resolve_path(absolute_path)
        self.assertEqual(resolved, absolute_path)
        
        # Resolve relative path
        relative_path = Path("core/paths.py")
        resolved = resolve_path(relative_path)
        self.assertEqual(resolved, get_path("base") / relative_path)
        
        # Resolve with relative_to
        relative_path = Path("paths.py")
        resolved = resolve_path(relative_path, "core")
        self.assertEqual(resolved, get_path("core") / relative_path)
    
    def test_ensure_dir(self):
        """Test directory creation."""
        # Create a test directory
        test_dir = get_path("base") / "tests" / "test_dir"
        
        # Ensure it exists
        created_dir = ensure_dir(test_dir)
        self.assertTrue(created_dir.exists())
        self.assertTrue(created_dir.is_dir())
        
        # Clean up
        try:
            os.rmdir(test_dir)
        except:
            pass

class TestCoreConfig(unittest.TestCase):
    """Test the core.config module."""
    
    def test_get_config(self):
        """Test getting configuration values."""
        # Get default debug setting
        debug = get("debug", False)
        self.assertIsInstance(debug, bool)
        
        # Get non-existent setting with default
        test_value = get("non_existent_key", "default_value")
        self.assertEqual(test_value, "default_value")
    
    def test_set_config(self):
        """Test setting configuration values."""
        # Set a test value
        set_value("test_key", "test_value")
        
        # Get the value back
        value = get("test_key")
        self.assertEqual(value, "test_value")
        
        # Clean up
        set_value("test_key", None)

class TestCoreErrors(unittest.TestCase):
    """Test the core.errors module."""
    
    def test_error_hierarchy(self):
        """Test error class hierarchy."""
        # Create a base error
        base_error = LLMError("Base error")
        self.assertIsInstance(base_error, Exception)
        self.assertEqual(str(base_error), "Base error")
        
        # Create a model error
        model_error = ModelError("Model error")
        self.assertIsInstance(model_error, LLMError)
        self.assertEqual(str(model_error), "Model error")
    
    def test_error_to_dict(self):
        """Test error conversion to dictionary."""
        # Create an error with details
        error = LLMError("Test error", "test_code", {"detail": "test detail"})
        
        # Convert to dictionary
        error_dict = error.to_dict()
        
        # Check dictionary contents
        self.assertEqual(error_dict["error"], "Test error")
        self.assertEqual(error_dict["error_type"], "LLMError")
        self.assertEqual(error_dict["code"], "test_code")
        self.assertEqual(error_dict["details"]["detail"], "test detail")

class TestCoreUtils(unittest.TestCase):
    """Test the core.utils module."""
    
    def test_parse_frontmatter(self):
        """Test frontmatter parsing."""
        # Create a test document with frontmatter
        document = """---
title: Test Document
tags: ["test", "example"]
count: 42
---

This is the content of the document."""

        # Parse frontmatter
        metadata, content = parse_frontmatter(document)
        
        # Check metadata
        self.assertEqual(metadata["title"], "Test Document")
        self.assertEqual(metadata["count"], 42)
        self.assertEqual(metadata["tags"], ["test", "example"])
        
        # Check content
        self.assertEqual(content, "This is the content of the document.")
    
    def test_format_with_frontmatter(self):
        """Test frontmatter formatting."""
        # Create test data
        metadata = {
            "title": "Test Document",
            "tags": ["test", "example"],
            "count": 42
        }
        content = "This is the content of the document."
        
        # Format with frontmatter
        formatted = format_with_frontmatter(metadata, content)
        
        # Parse the formatted document
        parsed_metadata, parsed_content = parse_frontmatter(formatted)
        
        # Check that parsing preserves the original data
        self.assertEqual(parsed_metadata["title"], metadata["title"])
        self.assertEqual(parsed_metadata["count"], metadata["count"])
        self.assertEqual(parsed_metadata["tags"], metadata["tags"])
        self.assertEqual(parsed_content, content)
    
    def test_estimate_tokens(self):
        """Test token estimation."""
        # Empty text
        self.assertEqual(estimate_tokens(""), 0)
        
        # Short text (less than 4 characters)
        self.assertEqual(estimate_tokens("abc"), 1)
        
        # Normal text
        text = "This is a test sentence with exactly 12 words and some punctuation marks."
        tokens = estimate_tokens(text)
        self.assertTrue(tokens > 10 and tokens < 30, f"Expected token count between 10-30, got {tokens}")

if __name__ == "__main__":
    # Initialize core module
    init_core()
    
    # Run the tests
    unittest.main()