#!/usr/bin/env python3
"""
Unit tests for the web server modules.

Tests the functionality of the server, router, middleware, and handlers
components of the web server system.
"""

import sys
import json
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the modules to test
from web.server import Request, Response, Server, create_server
from web.middleware import request_logger, json_body_parser, cors_headers
from web.handlers import StaticFileHandler, TemplateHandler, ApiHandler


class TestRequest(unittest.TestCase):
    """Tests for the Request class."""
    
    def setUp(self):
        """Set up test environment."""
        # Mock HTTP handler
        self.handler = Mock()
        self.handler.command = "GET"
        self.handler.path = "/test?param1=value1&param2=value2"
        self.handler.headers = {
            "Content-Type": "application/json",
            "User-Agent": "Test Agent",
            "Cookie": "token=abc123; session=xyz789"
        }
    
    def test_request_init(self):
        """Test request initialization."""
        request = Request(self.handler)
        
        self.assertEqual(request.method, "GET")
        self.assertEqual(request.path, "/test?param1=value1&param2=value2")
        self.assertEqual(request.base_path, "/test")
        self.assertEqual(request.query_params, {"param1": "value1", "param2": "value2"})
        self.assertEqual(request.headers, self.handler.headers)
    
    def test_parse_cookies(self):
        """Test cookie parsing."""
        request = Request(self.handler)
        
        self.assertEqual(request.cookies, {"token": "abc123", "session": "xyz789"})
        self.assertEqual(request.get_cookie("token"), "abc123")
        self.assertEqual(request.get_cookie("session"), "xyz789")
        self.assertIsNone(request.get_cookie("non_existent"))
        self.assertEqual(request.get_cookie("non_existent", "default"), "default")
    
    def test_get_header(self):
        """Test header retrieval."""
        request = Request(self.handler)
        
        self.assertEqual(request.get_header("Content-Type"), "application/json")
        self.assertEqual(request.get_header("User-Agent"), "Test Agent")
        self.assertIsNone(request.get_header("Non-Existent"))
        self.assertEqual(request.get_header("Non-Existent", "default"), "default")
    
    def test_json_body_parsing(self):
        """Test JSON body parsing."""
        # Setup handler with JSON body
        self.handler.rfile = MagicMock()
        self.handler.rfile.read.return_value = b'{"key":"value"}'
        self.handler.headers = {"Content-Type": "application/json", "Content-Length": "15"}
        
        request = Request(self.handler)
        
        self.assertEqual(request.body, {"key": "value"})


class TestResponse(unittest.TestCase):
    """Tests for the Response class."""
    
    def setUp(self):
        """Set up test environment."""
        self.response = Response()
    
    def test_response_init(self):
        """Test response initialization."""
        self.assertEqual(self.response.status_code, 200)
        self.assertEqual(self.response.headers, {"Content-Type": "text/html"})
        self.assertEqual(self.response.cookies, [])
        self.assertEqual(self.response.body, "")
    
    def test_set_status(self):
        """Test setting status code."""
        self.response.set_status(404)
        self.assertEqual(self.response.status_code, 404)
    
    def test_set_header(self):
        """Test setting headers."""
        self.response.set_header("X-Test", "test_value")
        self.assertEqual(self.response.headers["X-Test"], "test_value")
    
    def test_set_cookie(self):
        """Test setting cookies."""
        self.response.set_cookie("token", "abc123", path="/", secure=True)
        self.assertEqual(len(self.response.cookies), 1)
        self.assertIn("token=abc123", self.response.cookies[0])
        self.assertIn("Path=/", self.response.cookies[0])
        self.assertIn("Secure", self.response.cookies[0])
    
    def test_json_response(self):
        """Test JSON response."""
        data = {"key": "value"}
        self.response.json(data)
        self.assertEqual(self.response.headers["Content-Type"], "application/json")
        self.assertEqual(self.response.body, json.dumps(data))
    
    def test_html_response(self):
        """Test HTML response."""
        html = "<html><body>Test</body></html>"
        self.response.html(html)
        self.assertEqual(self.response.headers["Content-Type"], "text/html")
        self.assertEqual(self.response.body, html)
    
    def test_redirect(self):
        """Test redirect response."""
        self.response.redirect("/new/location")
        self.assertEqual(self.response.status_code, 302)
        self.assertEqual(self.response.headers["Location"], "/new/location")
        
        # Test permanent redirect
        self.response.redirect("/permanent", permanent=True)
        self.assertEqual(self.response.status_code, 301)
        self.assertEqual(self.response.headers["Location"], "/permanent")
    
    def test_error(self):
        """Test error response."""
        self.response.error(404, "Not Found")
        self.assertEqual(self.response.status_code, 404)
        self.assertEqual(self.response.body, "Not Found")
        
        # Test JSON error
        self.response.set_content_type("application/json")
        self.response.error(500, "Server Error")
        self.assertEqual(self.response.status_code, 500)
        self.assertEqual(self.response.body, json.dumps({"error": "Server Error"}))


class TestRouter(unittest.TestCase):
    """Tests for the Router class."""
    
    def setUp(self):
        """Set up test environment."""
        self.router = Router()
        
        # Add test routes
        @self.router.get("/")
        def index(request, response):
            response.html("<h1>Home</h1>")
        
        @self.router.get("/users/{id}")
        def get_user(request, response):
            user_id = request.path_params["id"]
            response.json({"id": user_id, "name": f"User {user_id}"})
        
        @self.router.post("/users")
        def create_user(request, response):
            response.set_status(201)
            response.json({"id": "new", "name": "New User"})
    
    def test_route_matching(self):
        """Test route matching."""
        # Test exact match
        handler = self.router.find_handler("/", "GET")
        self.assertIsNotNone(handler)
        
        # Test with path parameter
        handler = self.router.find_handler("/users/123", "GET")
        self.assertIsNotNone(handler)
        
        # Test method mismatch
        handler = self.router.find_handler("/", "POST")
        self.assertIsNone(handler)
        
        # Test non-existent route
        handler = self.router.find_handler("/non-existent", "GET")
        self.assertIsNone(handler)
    
    def test_path_params(self):
        """Test path parameter extraction."""
        # Create mock request and response
        request = MagicMock()
        response = MagicMock()
        
        # Get handler with path parameters
        handler = self.router.find_handler("/users/123", "GET")
        self.assertIsNotNone(handler)
        
        # Call handler
        handler(request, response)
        
        # Check that path_params was set on request
        self.assertEqual(request.path_params, {"id": "123"})
    
    def test_route_group(self):
        """Test route grouping."""
        # Create a route group
        api = self.router.group("/api")
        
        @api.get("/items")
        def get_items(request, response):
            response.json({"items": []})
        
        # Merge group back to main router
        api.merge()
        
        # Test grouped route
        handler = self.router.find_handler("/api/items", "GET")
        self.assertIsNotNone(handler)


class TestMiddleware(unittest.TestCase):
    """Tests for middleware functions."""
    
    def setUp(self):
        """Set up test environment."""
        self.request = MagicMock()
        self.request.method = "GET"
        self.request.path = "/test"
        self.request.headers = {"Content-Type": "application/json"}
        
        self.response = MagicMock()
        self.response.status_code = 200
        self.response.headers = {}
        self.response.set_header = MagicMock()
    
    def test_request_logger(self):
        """Test request logger middleware."""
        with patch("web.middleware.logger") as mock_logger:
            request_logger(self.request, self.response)
            mock_logger.info.assert_called_once()
            self.assertTrue(hasattr(self.request, "start_time"))
    
    def test_cors_headers(self):
        """Test CORS headers middleware."""
        middleware = cors_headers(allow_origin="*", allow_methods=["GET", "POST"])
        middleware(self.request, self.response)
        
        self.response.set_header.assert_any_call("Access-Control-Allow-Origin", "*")
        self.response.set_header.assert_any_call("Access-Control-Allow-Methods", "GET, POST")
    
    def test_json_body_parser(self):
        """Test JSON body parser middleware."""
        # Test with valid JSON body
        self.request.get_header = MagicMock(return_value="application/json")
        self.request.body = '{"key":"value"}'
        
        with patch("web.middleware.logger"):
            json_body_parser(self.request, self.response)
            # No change to response since body is already parsed by Request class
        
        # Test with invalid JSON
        self.request.body = "not json"
        self.response.status_code = 200
        
        with patch("web.middleware.logger"):
            json_body_parser(self.request, self.response)
            # Should still be 200 since we're just logging the warning
            self.assertEqual(self.response.status_code, 200)


class TestHandlers(unittest.TestCase):
    """Tests for the handler classes."""
    
    def setUp(self):
        """Set up test environment."""
        self.request = MagicMock()
        self.request.method = "GET"
        self.request.base_path = "/assets/test.css"
        
        self.response = MagicMock()
        self.response.status_code = 200
        self.response.headers = {}
        self.response.set_header = MagicMock()
        self.response.error = MagicMock()
    
    def test_static_file_handler(self):
        """Test static file handler."""
        with patch("web.handlers.Path") as mock_path:
            # Mock file operations
            mock_file = mock_path.return_value.__truediv__.return_value
            mock_file.is_file.return_value = True
            mock_file.stat.return_value.st_size = 100
            mock_file.stat.return_value.st_mtime = 123456789
            
            # Mock open
            mock_open = MagicMock()
            mock_open.return_value.__enter__.return_value.read.return_value = b"file content"
            
            with patch("builtins.open", mock_open):
                # Create handler
                handler = StaticFileHandler()
                
                # Test handler
                handler.handle(self.request, self.response)
                
                # Verify response
                self.response.set_header.assert_any_call("Content-Type", "text/css")
                self.assertEqual(self.response.body, b"file content")
    
    def test_template_handler(self):
        """Test template handler."""
        with patch("web.handlers.render_template") as mock_render:
            mock_render.return_value = "<html>Test</html>"
            
            # Create handler
            handler = TemplateHandler()
            
            # Create template renderer
            renderer = handler.render("test.html", {"key": "value"})
            
            # Execute renderer
            renderer(self.request, self.response)
            
            # Verify response
            self.response.html.assert_called_once_with("<html>Test</html>")
    
    def test_api_handler(self):
        """Test API handler."""
        # Create handler
        handler = ApiHandler()
        
        # Test JSON response
        json_handler = handler.json_response({"key": "value"})
        json_handler(self.request, self.response)
        self.response.json.assert_called_once_with({"key": "value"})
        
        # Test error response
        error_handler = handler.error_response("Error message", 400)
        error_handler(self.request, self.response)
        self.response.json.assert_called_with({"error": "Error message"})
        
        # Test API handler
        def test_func(request):
            return {"result": "success"}
        
        api_handler = handler.create_handler(test_func)
        api_handler(self.request, self.response)
        self.response.json.assert_called_with({"result": "success"})


class TestServer(unittest.TestCase):
    """Tests for the Server class."""
    
    def setUp(self):
        """Set up test environment."""
        self.router = Router()
        
        @self.router.get("/")
        def index(request, response):
            response.html("<h1>Home</h1>")
    
    @patch("web.server.socketserver.TCPServer")
    def test_server_init(self, mock_server):
        """Test server initialization."""
        server = Server(host="localhost", port=5000, router=self.router)
        
        self.assertEqual(server.host, "localhost")
        self.assertEqual(server.port, 5000)
        self.assertEqual(server.router, self.router)
    
    @patch("web.server.socketserver.TCPServer")
    def test_server_start(self, mock_server):
        """Test server start."""
        # Mock find_available_port
        with patch.object(Server, "find_available_port", return_value=5000):
            server = Server(host="localhost", port=5000, router=self.router)
            server.start(block=False)
            
            self.assertTrue(server.is_running)
            self.assertIsNotNone(server.server_thread)
            
            # Cleanup
            server.stop()
    
    @patch("web.server.socketserver.TCPServer")
    def test_create_server(self, mock_server):
        """Test create_server function."""
        with patch("web.server.get_config", return_value={}):
            server = create_server(host="localhost", port=5000, router=self.router)
            
            self.assertEqual(server.host, "localhost")
            self.assertEqual(server.port, 5000)
            self.assertEqual(server.router, self.router)


if __name__ == "__main__":
    unittest.main()