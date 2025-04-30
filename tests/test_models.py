#!/usr/bin/env python3
"""
Unit tests for the models module.

Tests the basic functionality of the models module components:
- Registry
- Loader
- Formatter
- Generation
- Caching
"""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure base directories are in path
SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Import core modules
from core import initialize as init_core

# Import modules to test
from models import initialize as init_models
from models.registry import get_models, get_model_info, find_models_by_family
from models.formatter import format_prompt, format_conversation
from models.caching import get_cache_stats

class TestModelRegistry(unittest.TestCase):
    """Test the models.registry module."""
    
    def test_get_models(self):
        """Test getting list of models."""
        # Get all models
        models = get_models()
        self.assertIsInstance(models, list)
        
        # Each model should have basic metadata
        for model in models:
            self.assertIn("path", model)
            self.assertIn("full_path", model)
            self.assertIn("family", model)
            self.assertIn("format", model)
    
    def test_get_model_info(self):
        """Test getting model info."""
        # Get all models
        models = get_models()
        
        if not models:
            self.skipTest("No models available for testing")
            return
        
        # Get info for the first model
        model_path = models[0]["path"]
        model_info = get_model_info(model_path)
        
        # Check model info
        self.assertIsNotNone(model_info)
        self.assertEqual(model_info["path"], model_path)
    
    def test_find_models_by_family(self):
        """Test finding models by family."""
        # Mock some models for testing
        with patch("models.registry.model_registry.models", {
            "model1": {"family": "llama", "path": "model1"},
            "model2": {"family": "mistral", "path": "model2"},
            "model3": {"family": "llama", "path": "model3"}
        }):
            # Find llama models
            llama_models = find_models_by_family("llama")
            self.assertEqual(len(llama_models), 2)
            
            # Find mistral models
            mistral_models = find_models_by_family("mistral")
            self.assertEqual(len(mistral_models), 1)
            
            # Find non-existent family
            phi_models = find_models_by_family("phi")
            self.assertEqual(len(phi_models), 0)

class TestModelFormatter(unittest.TestCase):
    """Test the models.formatter module."""
    
    def test_format_prompt(self):
        """Test prompt formatting."""
        # Test formatting for different model types
        prompt = "This is a test prompt"
        system_prompt = "You are a helpful assistant"
        
        # Test mistral formatting
        with patch("models.formatter.get_model_info", return_value={"family": "mistral"}):
            formatted = format_prompt("model_path", prompt, system_prompt)
            self.assertIn("[INST]", formatted)
            self.assertIn(prompt, formatted)
            self.assertIn(system_prompt, formatted)
        
        # Test llama formatting
        with patch("models.formatter.get_model_info", return_value={"family": "llama"}):
            formatted = format_prompt("model_path", prompt, system_prompt)
            self.assertIn("[INST]", formatted)
            self.assertIn("<<SYS>>", formatted)
            self.assertIn(prompt, formatted)
            self.assertIn(system_prompt, formatted)
        
        # Test unknown model formatting
        with patch("models.formatter.get_model_info", return_value=None):
            formatted = format_prompt("model_path", prompt, system_prompt)
            self.assertIn("### System:", formatted)
            self.assertIn("### User:", formatted)
            self.assertIn("### Assistant:", formatted)
            self.assertIn(prompt, formatted)
            self.assertIn(system_prompt, formatted)
    
    def test_format_conversation(self):
        """Test conversation formatting."""
        # Test conversation with multiple messages
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
            {"role": "user", "content": "How are you?"}
        ]
        system_prompt = "You are a helpful assistant"
        
        # Test mistral formatting
        with patch("models.formatter.get_model_info", return_value={"family": "mistral"}):
            formatted = format_conversation("model_path", messages, system_prompt)
            self.assertIn("[INST]", formatted)
            self.assertIn("Hello", formatted)
            self.assertIn("Hi there", formatted)
            self.assertIn("How are you?", formatted)
            self.assertIn(system_prompt, formatted)

class TestModelCaching(unittest.TestCase):
    """Test the models.caching module."""
    
    def test_get_cache_stats(self):
        """Test getting cache statistics."""
        # Get cache stats
        stats = get_cache_stats()
        
        # Check stats structure
        self.assertIn("enabled", stats)
        self.assertIn("max_models", stats)
        self.assertIn("current_size", stats)
        self.assertIn("models", stats)

if __name__ == "__main__":
    # Initialize core and models modules
    init_core()
    init_models()
    
    # Run the tests
    unittest.main()