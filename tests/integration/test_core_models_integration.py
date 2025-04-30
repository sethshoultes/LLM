#!/usr/bin/env python3
"""
Integration tests for core and models components.

Tests the integration between core modules and model loading/inference,
ensuring these components work together correctly.
"""

import unittest
import os
import tempfile
import shutil
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import core modules
from core.paths import get_app_path, resolve_path
from core.config import get_config, load_config
from core.logging import get_logger

# Import models modules
from models.registry import get_model_info, get_available_models
from models.loader import load_model, unload_model, is_model_loaded
from models.generation import generate_text


class CoreModelsIntegrationTest(unittest.TestCase):
    """Integration tests for core and models components."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment for all tests."""
        # Create temporary test directory
        cls.temp_dir = Path(tempfile.mkdtemp())
        
        # Create test directories
        cls.models_dir = cls.temp_dir / "models"
        cls.config_dir = cls.temp_dir / "config"
        cls.logs_dir = cls.temp_dir / "logs"
        
        os.makedirs(cls.models_dir)
        os.makedirs(cls.config_dir)
        os.makedirs(cls.logs_dir)
        
        # Create test model info
        cls.test_models = {
            "test-model-7b": {
                "name": "Test Model 7B",
                "path": str(cls.models_dir / "test-model-7b"),
                "type": "llama",
                "context_length": 4096,
                "parameters": "7B"
            },
            "test-model-13b": {
                "name": "Test Model 13B",
                "path": str(cls.models_dir / "test-model-13b"),
                "type": "llama",
                "context_length": 4096,
                "parameters": "13B"
            }
        }
        
        # Create test config
        cls.test_config = {
            "paths": {
                "models_dir": str(cls.models_dir),
                "logs_dir": str(cls.logs_dir)
            },
            "models": {
                "default": "test-model-7b",
                "preload": []
            },
            "inference": {
                "default_params": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 1024
                }
            }
        }
        
        # Write config to file
        with open(cls.config_dir / "config.json", "w") as f:
            json.dump(cls.test_config, f, indent=2)
        
        # Create mock model files
        for model_id in cls.test_models:
            model_dir = cls.models_dir / model_id
            os.makedirs(model_dir)
            with open(model_dir / "config.json", "w") as f:
                json.dump(cls.test_models[model_id], f, indent=2)
        
        # Set up patchers for external dependencies
        cls.mock_llama_model = MagicMock()
        cls.mock_llama_model.generate.return_value = "This is a test response."
        
        cls.load_llama_model_patcher = patch('models.loader._load_llama_model')
        cls.mock_load_llama_model = cls.load_llama_model_patcher.start()
        cls.mock_load_llama_model.return_value = cls.mock_llama_model
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests."""
        # Stop patchers
        cls.load_llama_model_patcher.stop()
        
        # Remove temporary directory
        shutil.rmtree(cls.temp_dir)
    
    def setUp(self):
        """Set up test environment for each test."""
        # Set up config path patcher
        self.get_config_path_patcher = patch('core.config.get_config_path')
        self.mock_get_config_path = self.get_config_path_patcher.start()
        self.mock_get_config_path.return_value = self.config_dir / "config.json"
        
        # Set up app path patcher
        self.get_app_path_patcher = patch('core.paths.get_app_path')
        self.mock_get_app_path = self.get_app_path_patcher.start()
        self.mock_get_app_path.return_value = self.temp_dir
        
        # Clear model registry
        if hasattr(get_available_models, 'cache'):
            get_available_models.cache = {}
    
    def tearDown(self):
        """Clean up after each test."""
        # Stop patchers
        self.get_config_path_patcher.stop()
        self.get_app_path_patcher.stop()
    
    def test_path_resolution(self):
        """Test path resolution with config."""
        # Test resolving models directory
        models_path = resolve_path("models")
        self.assertEqual(models_path, self.models_dir)
        
        # Test resolving a file in models directory
        model_file_path = resolve_path("models/test-model-7b/config.json")
        self.assertEqual(model_file_path, self.models_dir / "test-model-7b" / "config.json")
    
    def test_config_loading(self):
        """Test loading configuration."""
        # Load config
        config = get_config()
        
        # Check config values
        self.assertEqual(config["paths"]["models_dir"], str(self.models_dir))
        self.assertEqual(config["models"]["default"], "test-model-7b")
        self.assertEqual(config["inference"]["default_params"]["temperature"], 0.7)
    
    def test_model_registry(self):
        """Test model registry functions."""
        # Get available models
        models = get_available_models()
        
        # Check that both test models are found
        self.assertEqual(len(models), 2)
        self.assertIn("test-model-7b", models)
        self.assertIn("test-model-13b", models)
        
        # Get model info
        model_info = get_model_info("test-model-7b")
        
        # Check model info
        self.assertEqual(model_info["name"], "Test Model 7B")
        self.assertEqual(model_info["type"], "llama")
        self.assertEqual(model_info["parameters"], "7B")
    
    def test_model_loading_and_generation(self):
        """Test model loading and text generation."""
        # Load model
        model = load_model("test-model-7b")
        
        # Check that model loading was called correctly
        self.mock_load_llama_model.assert_called_once()
        model_path = self.mock_load_llama_model.call_args[0][0]
        self.assertEqual(Path(model_path), self.models_dir / "test-model-7b")
        
        # Check that model is loaded
        self.assertTrue(is_model_loaded("test-model-7b"))
        
        # Generate text
        response = generate_text(model, "This is a test prompt.")
        
        # Check response
        self.assertEqual(response, "This is a test response.")
        
        # Check that generate was called on the model
        self.mock_llama_model.generate.assert_called_once()
        
        # Unload model
        unload_model("test-model-7b")
        
        # Check that model is unloaded
        self.assertFalse(is_model_loaded("test-model-7b"))
    
    def test_inference_with_custom_parameters(self):
        """Test text generation with custom parameters."""
        # Load model
        model = load_model("test-model-7b")
        
        # Generate text with custom parameters
        params = {
            "temperature": 0.8,
            "top_p": 0.95,
            "max_tokens": 2048
        }
        _ = generate_text(model, "This is a test prompt.", params)
        
        # Check that generate was called with custom parameters
        call_kwargs = self.mock_llama_model.generate.call_args[1]
        self.assertEqual(call_kwargs["temperature"], 0.8)
        self.assertEqual(call_kwargs["top_p"], 0.95)
        self.assertEqual(call_kwargs["max_tokens"], 2048)
    
    def test_logging_integration(self):
        """Test logging integration."""
        # Get logger
        logger = get_logger("test")
        
        # Test info logging
        with self.assertLogs(logger, level='INFO') as cm:
            logger.info("Test info message")
            self.assertIn("Test info message", cm.output[0])
        
        # Test error logging
        with self.assertLogs(logger, level='ERROR') as cm:
            logger.error("Test error message")
            self.assertIn("Test error message", cm.output[0])


if __name__ == "__main__":
    unittest.main()