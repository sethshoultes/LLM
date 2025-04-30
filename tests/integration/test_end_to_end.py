#!/usr/bin/env python3
"""
End-to-end system tests for the LLM Platform.

Tests the complete system from model loading to inference and RAG,
ensuring all components work together correctly in a real-world scenario.
"""

import unittest
import os
import tempfile
import shutil
import json
import threading
import time
import requests
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import core modules
from core.paths import get_app_path, resolve_path
from core.config import get_config, load_config

# Import models modules
from models.registry import get_model_info, get_available_models
from models.loader import load_model, unload_model, is_model_loaded
from models.generation import generate_text

# Import RAG modules
from rag_support.utils.project_manager import ProjectManager
from rag_support.utils.search import SearchEngine
from rag_support.utils.context_manager import ContextManager

# Import web modules
from web.server import Server, RequestHandler
from web.router import Router
from web.middleware import apply_middleware
from web.handlers_new import json_api, render_view, static_handler


class EndToEndTest(unittest.TestCase):
    """End-to-end system tests for the LLM Platform."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment for all tests."""
        # Create temporary test directory
        cls.temp_dir = Path(tempfile.mkdtemp())
        
        # Create test directories
        cls.models_dir = cls.temp_dir / "models"
        cls.config_dir = cls.temp_dir / "config"
        cls.logs_dir = cls.temp_dir / "logs"
        cls.projects_dir = cls.temp_dir / "projects"
        cls.templates_dir = cls.temp_dir / "templates"
        cls.assets_dir = cls.templates_dir / "assets"
        cls.components_dir = cls.templates_dir / "components"
        cls.layouts_dir = cls.templates_dir / "layouts"
        
        os.makedirs(cls.models_dir)
        os.makedirs(cls.config_dir)
        os.makedirs(cls.logs_dir)
        os.makedirs(cls.projects_dir)
        os.makedirs(cls.templates_dir)
        os.makedirs(cls.assets_dir)
        os.makedirs(cls.components_dir)
        os.makedirs(cls.layouts_dir)
        
        # Create test model info
        cls.test_model = {
            "name": "Test Model 7B",
            "path": str(cls.models_dir / "test-model-7b"),
            "type": "llama",
            "context_length": 4096,
            "parameters": "7B"
        }
        
        # Create test model directory
        os.makedirs(cls.models_dir / "test-model-7b")
        with open(cls.models_dir / "test-model-7b" / "config.json", "w") as f:
            json.dump(cls.test_model, f, indent=2)
        
        # Create test config
        cls.test_config = {
            "paths": {
                "models_dir": str(cls.models_dir),
                "logs_dir": str(cls.logs_dir),
                "projects_dir": str(cls.projects_dir)
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
            },
            "server": {
                "host": "localhost",
                "port": 0,
                "open_browser": False
            }
        }
        
        # Write config to file
        with open(cls.config_dir / "config.json", "w") as f:
            json.dump(cls.test_config, f, indent=2)
        
        # Create test templates
        with open(cls.layouts_dir / "main.html", "w") as f:
            f.write("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>{% block title %}Default Title{% endblock %}</title>
            </head>
            <body>
                <header>
                    <h1>LLM Platform</h1>
                </header>
                <main>
                    {% block content %}
                    <p>Default content</p>
                    {% endblock %}
                </main>
                <footer>
                    <p>Footer</p>
                </footer>
            </body>
            </html>
            """)
        
        # Set up patchers for external dependencies
        cls.get_app_path_patcher = patch('core.paths.get_app_path')
        cls.mock_get_app_path = cls.get_app_path_patcher.start()
        cls.mock_get_app_path.return_value = cls.temp_dir
        
        cls.get_config_path_patcher = patch('core.config.get_config_path')
        cls.mock_get_config_path = cls.get_config_path_patcher.start()
        cls.mock_get_config_path.return_value = cls.config_dir / "config.json"
        
        # Mock model loading and inference
        cls.mock_llama_model = MagicMock()
        cls.mock_llama_model.generate.return_value = "This is a test response with RAG context."
        
        cls.load_llama_model_patcher = patch('models.loader._load_llama_model')
        cls.mock_load_llama_model = cls.load_llama_model_patcher.start()
        cls.mock_load_llama_model.return_value = cls.mock_llama_model
        
        # Mock embeddings functionality
        cls.mock_embeddings = MagicMock()
        cls.mock_embeddings.embed.return_value = [0.1, 0.2, 0.3, 0.4, 0.5]
        
        cls.get_embeddings_patcher = patch('rag_support.utils.search.get_embeddings')
        cls.mock_get_embeddings = cls.get_embeddings_patcher.start()
        cls.mock_get_embeddings.return_value = cls.mock_embeddings
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests."""
        # Stop patchers
        cls.get_app_path_patcher.stop()
        cls.get_config_path_patcher.stop()
        cls.load_llama_model_patcher.stop()
        cls.get_embeddings_patcher.stop()
        
        # Remove temporary directory
        shutil.rmtree(cls.temp_dir)
    
    def setUp(self):
        """Set up test environment for each test."""
        # Create instances of key components
        self.project_manager = ProjectManager(self.projects_dir)
        self.search_engine = SearchEngine()
        self.context_manager = ContextManager()
        
        # Create a test project with documents
        self.test_project = self.project_manager.create_project(
            "Test Project",
            "A test project for end-to-end testing"
        )
        self.test_project_id = self.test_project["id"]
        
        # Create test documents
        self.test_documents = []
        for i in range(3):
            doc = self.project_manager.add_document(
                self.test_project_id,
                f"Test Document {i}",
                f"This is test document {i} with information about the LLM platform. "
                f"The platform supports RAG (Retrieval Augmented Generation) "
                f"and various model types. This document provides context for testing.",
                ["test", "rag", f"doc{i}"]
            )
            self.test_documents.append(doc)
        
        # Load model
        self.model = load_model("test-model-7b")
        
        # Create router for web server
        self.router = Router()
        
        # Define routes
        self._define_routes()
        
        # Create server
        self.server = Server(host="localhost", port=0, router=self.router)
        
        # Start server in separate thread
        self.server_thread = threading.Thread(target=self._start_server)
        self.server_thread.daemon = True
        self.server_thread.start()
        
        # Wait for server to start
        time.sleep(0.5)
        
        # Get server port
        self.server_port = self.server.port
        self.base_url = f"http://localhost:{self.server_port}"
    
    def tearDown(self):
        """Clean up after each test."""
        # Stop server
        self.server.stop()
        
        # Wait for server to stop
        self.server_thread.join(timeout=1.0)
        
        # Unload model
        unload_model("test-model-7b")
        
        # Remove test project
        for project in self.project_manager.get_projects():
            self.project_manager.delete_project(project["id"])
    
    def _start_server(self):
        """Start the server."""
        self.server.start(block=True)
    
    def _define_routes(self):
        """Define routes for the test server."""
        # API routes
        @self.router.post("/api/completion")
        def completion(request, response):
            # Get request data
            data = request.body
            if not data:
                response.status_code = 400
                response.json({"status": "error", "error": "Invalid request"})
                return
            
            # Extract parameters
            prompt = data.get("prompt", "")
            model_id = data.get("model_id", "test-model-7b")
            params = data.get("params", {})
            use_rag = data.get("use_rag", False)
            project_id = data.get("project_id", self.test_project_id)
            
            # Generate context if RAG is enabled
            context = ""
            if use_rag:
                context_text, _, _ = self.context_manager.generate_context(
                    project_id,
                    prompt,
                    max_tokens=1000
                )
                context = context_text
            
            # Generate completion
            if use_rag:
                full_prompt = f"Context: {context}\n\nQuestion: {prompt}"
            else:
                full_prompt = prompt
            
            result = generate_text(self.model, full_prompt, params)
            
            # Return response
            response.status_code = 200
            response.json({
                "status": "success",
                "data": {
                    "completion": result,
                    "model": model_id,
                    "used_rag": use_rag
                }
            })
        
        @self.router.get("/api/projects")
        def list_projects(request, response):
            projects = self.project_manager.get_projects()
            response.status_code = 200
            response.json({
                "status": "success",
                "data": projects,
                "meta": {"count": len(projects)}
            })
        
        @self.router.get("/api/projects/{project_id}/documents")
        def list_documents(request, response):
            project_id = request.path_params.get("project_id")
            documents = self.project_manager.get_documents(project_id)
            response.status_code = 200
            response.json({
                "status": "success",
                "data": documents,
                "meta": {"count": len(documents), "project_id": project_id}
            })
        
        # Web routes
        @self.router.get("/")
        def home(request, response):
            response.status_code = 200
            response.html("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>LLM Platform</title>
            </head>
            <body>
                <h1>LLM Platform</h1>
                <p>Welcome to the LLM Platform test interface.</p>
                <p>Run tests by submitting a POST request to /api/completion.</p>
            </body>
            </html>
            """)
    
    def test_full_inference_without_rag(self):
        """Test complete inference flow without RAG."""
        # Make request to completion API
        response = requests.post(
            f"{self.base_url}/api/completion",
            json={
                "prompt": "What is Retrieval Augmented Generation?",
                "model_id": "test-model-7b",
                "params": {
                    "temperature": 0.5,
                    "top_p": 0.9,
                    "max_tokens": 100
                },
                "use_rag": False
            }
        )
        
        # Check status code
        self.assertEqual(response.status_code, 200)
        
        # Check response format
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["data"]["model"], "test-model-7b")
        self.assertEqual(data["data"]["used_rag"], False)
        self.assertEqual(data["data"]["completion"], "This is a test response with RAG context.")
        
        # Check that model.generate was called with correct parameters
        self.mock_llama_model.generate.assert_called_once()
        call_args, call_kwargs = self.mock_llama_model.generate.call_args
        self.assertEqual(call_args[0], "What is Retrieval Augmented Generation?")
        self.assertEqual(call_kwargs["temperature"], 0.5)
        self.assertEqual(call_kwargs["top_p"], 0.9)
        self.assertEqual(call_kwargs["max_tokens"], 100)
    
    def test_full_inference_with_rag(self):
        """Test complete inference flow with RAG."""
        # Make request to completion API
        response = requests.post(
            f"{self.base_url}/api/completion",
            json={
                "prompt": "What is Retrieval Augmented Generation?",
                "model_id": "test-model-7b",
                "params": {
                    "temperature": 0.5,
                    "top_p": 0.9,
                    "max_tokens": 100
                },
                "use_rag": True,
                "project_id": self.test_project_id
            }
        )
        
        # Check status code
        self.assertEqual(response.status_code, 200)
        
        # Check response format
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["data"]["model"], "test-model-7b")
        self.assertEqual(data["data"]["used_rag"], True)
        self.assertEqual(data["data"]["completion"], "This is a test response with RAG context.")
        
        # Check that model.generate was called with correct parameters
        self.mock_llama_model.generate.assert_called_once()
        call_args, call_kwargs = self.mock_llama_model.generate.call_args
        
        # The prompt should include context and the question
        self.assertIn("Context:", call_args[0])
        self.assertIn("Question: What is Retrieval Augmented Generation?", call_args[0])
        
        # Check that generation parameters were passed
        self.assertEqual(call_kwargs["temperature"], 0.5)
        self.assertEqual(call_kwargs["top_p"], 0.9)
        self.assertEqual(call_kwargs["max_tokens"], 100)
    
    def test_project_and_document_listing(self):
        """Test project and document listing APIs."""
        # Test project listing
        response = requests.get(f"{self.base_url}/api/projects")
        
        # Check status code and response format
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(len(data["data"]), 1)
        self.assertEqual(data["data"][0]["id"], self.test_project_id)
        
        # Test document listing
        response = requests.get(f"{self.base_url}/api/projects/{self.test_project_id}/documents")
        
        # Check status code and response format
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(len(data["data"]), 3)
        self.assertEqual(data["data"][0]["project_id"], self.test_project_id)
    
    def test_home_page(self):
        """Test the home page."""
        # Make request to home page
        response = requests.get(self.base_url)
        
        # Check status code and content
        self.assertEqual(response.status_code, 200)
        self.assertIn("<title>LLM Platform</title>", response.text)
        self.assertIn("Welcome to the LLM Platform test interface", response.text)


if __name__ == "__main__":
    unittest.main()