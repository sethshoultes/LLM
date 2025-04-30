#!/usr/bin/env python3
"""
Integration tests for web and API components.

Tests the integration between web server, API controllers, and template system,
ensuring all components work together correctly.
"""

import unittest
import os
import tempfile
import shutil
import threading
import time
import requests
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import server components
from web.router import Router
from web.middleware import apply_middleware
from web.middleware.template_middleware import template_middleware

# Import API controllers
from web.api.controllers.rag import RagController


class WebApiIntegrationTest(unittest.TestCase):
    """Integration tests for web and API components."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment for all tests."""
        # Create temporary test directory
        cls.temp_dir = Path(tempfile.mkdtemp())
        
        # Create test directories
        cls.templates_dir = cls.temp_dir / "templates"
        cls.assets_dir = cls.templates_dir / "assets"
        cls.components_dir = cls.templates_dir / "components"
        cls.layouts_dir = cls.templates_dir / "layouts"
        
        os.makedirs(cls.templates_dir)
        os.makedirs(cls.assets_dir)
        os.makedirs(cls.components_dir)
        os.makedirs(cls.layouts_dir)
        
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
            
        with open(cls.templates_dir / "test.html", "w") as f:
            f.write("""
            {% extends "layouts/main.html" %}
            
            {% block title %}Test Page{% endblock %}
            
            {% block content %}
            <h1>{{ page_title }}</h1>
            <p>{{ page_content }}</p>
            {% endblock %}
            """)
            
        with open(cls.components_dir / "test_component.html", "w") as f:
            f.write("""
            <div class="component">
                <h2>{{ title }}</h2>
                <p>{{ content }}</p>
            </div>
            """)
            
        # Create test asset
        with open(cls.assets_dir / "test.css", "w") as f:
            f.write("""
            body { font-family: sans-serif; }
            """)
        
        # Set up mocks for project_manager and search_engine
        cls.mock_project_manager = MagicMock()
        cls.mock_search_engine = MagicMock()
        
        # Define test data
        cls.test_project_id = "test_project_id"
        cls.test_document_id = "test_document_id"
        
        cls.test_project = {
            "id": cls.test_project_id,
            "name": "Test Project",
            "description": "Test project description"
        }
        
        cls.test_document = {
            "id": cls.test_document_id,
            "project_id": cls.test_project_id,
            "title": "Test Document",
            "content": "Test document content"
        }
        
        # Configure mocks
        cls.mock_project_manager.get_project.return_value = cls.test_project
        cls.mock_project_manager.get_projects.return_value = [cls.test_project]
        cls.mock_project_manager.get_document.return_value = cls.test_document
        cls.mock_project_manager.get_documents.return_value = [cls.test_document]
        
        # Start patcher for project_manager and search_engine
        cls.project_manager_patcher = patch('web.api.controllers.rag.project_manager', cls.mock_project_manager)
        cls.search_engine_patcher = patch('web.api.controllers.rag.search_engine', cls.mock_search_engine)
        
        cls.project_manager_patcher.start()
        cls.search_engine_patcher.start()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests."""
        # Stop patchers
        cls.project_manager_patcher.stop()
        cls.search_engine_patcher.stop()
        
        # Remove temporary directory
        shutil.rmtree(cls.temp_dir)
    
    def setUp(self):
        """Set up test environment for each test."""
        # Create router
        self.router = Router()
        
        # Create controllers
        self.rag_controller = RagController()
        
        # Create template middleware
        self.template_middleware = template_middleware
        
        # Define middleware stack
        middleware_stack = [self.template_middleware]
        
        # Apply middleware to router
        apply_middleware(self.router, middleware_stack)
        
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
    
    def _start_server(self):
        """Start the server."""
        self.server.start(block=True)
    
    def _define_routes(self):
        """Define routes for the test server."""
        # API routes
        @self.router.get("/api/projects")
        def list_projects(request, response):
            status, data = self.rag_controller.list_projects()
            response.status_code = status
            response.json(data)
        
        @self.router.get("/api/projects/{project_id}")
        def get_project(request, response):
            project_id = request.path_params.get("project_id")
            status, data = self.rag_controller.get_project(project_id)
            response.status_code = status
            response.json(data)
        
        @self.router.get("/api/projects/{project_id}/documents")
        def list_documents(request, response):
            project_id = request.path_params.get("project_id")
            status, data = self.rag_controller.list_documents(project_id)
            response.status_code = status
            response.json(data)
        
        @self.router.get("/api/projects/{project_id}/documents/{document_id}")
        def get_document(request, response):
            project_id = request.path_params.get("project_id")
            document_id = request.path_params.get("document_id")
            status, data = self.rag_controller.get_document(project_id, document_id)
            response.status_code = status
            response.json(data)
        
        # Web routes
        @self.router.get("/")
        def home(request, response):
            render_view("test.html", {
                "page_title": "Home Page",
                "page_content": "Welcome to the home page."
            })(request, response)
        
        @self.router.get("/test")
        def test_page(request, response):
            render_view("test.html", {
                "page_title": "Test Page",
                "page_content": "This is a test page."
            })(request, response)
        
        # Static assets route
        @self.router.get("/assets{path:.*}")
        def assets(request, response):
            static_handler.static_dir = self.assets_dir.parent
            static_handler.handle(request, response)
    
    def test_api_list_projects(self):
        """Test API route for listing projects."""
        # Make request
        response = requests.get(f"{self.base_url}/api/projects")
        
        # Check status code
        self.assertEqual(response.status_code, 200)
        
        # Check response format
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(len(data["data"]), 1)
        self.assertEqual(data["data"][0]["id"], self.test_project_id)
    
    def test_api_get_project(self):
        """Test API route for getting a project."""
        # Make request
        response = requests.get(f"{self.base_url}/api/projects/{self.test_project_id}")
        
        # Check status code
        self.assertEqual(response.status_code, 200)
        
        # Check response format
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["data"]["id"], self.test_project_id)
    
    def test_api_list_documents(self):
        """Test API route for listing documents."""
        # Make request
        response = requests.get(f"{self.base_url}/api/projects/{self.test_project_id}/documents")
        
        # Check status code
        self.assertEqual(response.status_code, 200)
        
        # Check response format
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(len(data["data"]), 1)
        self.assertEqual(data["data"][0]["id"], self.test_document_id)
    
    def test_api_get_document(self):
        """Test API route for getting a document."""
        # Make request
        response = requests.get(f"{self.base_url}/api/projects/{self.test_project_id}/documents/{self.test_document_id}")
        
        # Check status code
        self.assertEqual(response.status_code, 200)
        
        # Check response format
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["data"]["id"], self.test_document_id)
    
    def test_web_home_page(self):
        """Test web route for home page."""
        # Make request
        response = requests.get(f"{self.base_url}/")
        
        # Check status code
        self.assertEqual(response.status_code, 200)
        
        # Check content
        self.assertIn("<title>Test Page</title>", response.text)
        self.assertIn("<h1>Home Page</h1>", response.text)
        self.assertIn("<p>Welcome to the home page.</p>", response.text)
    
    def test_web_test_page(self):
        """Test web route for test page."""
        # Make request
        response = requests.get(f"{self.base_url}/test")
        
        # Check status code
        self.assertEqual(response.status_code, 200)
        
        # Check content
        self.assertIn("<title>Test Page</title>", response.text)
        self.assertIn("<h1>Test Page</h1>", response.text)
        self.assertIn("<p>This is a test page.</p>", response.text)
    
    def test_static_asset(self):
        """Test serving static assets."""
        # Make request
        response = requests.get(f"{self.base_url}/assets/test.css")
        
        # Check status code
        self.assertEqual(response.status_code, 200)
        
        # Check content type
        self.assertEqual(response.headers["Content-Type"], "text/css")
        
        # Check content
        self.assertIn("body { font-family: sans-serif; }", response.text)
    
    def test_404_handling(self):
        """Test handling of 404 errors."""
        # Make request
        response = requests.get(f"{self.base_url}/nonexistent", allow_redirects=False)
        
        # Check status code
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()