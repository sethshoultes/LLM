#!/usr/bin/env python3
"""
Modern HTTP server for the LLM Platform.

Provides a lightweight HTTP server with support for routing, middleware,
and standardized request/response handling.
"""

import os
import sys
import http.server
import socketserver
import json
import urllib.parse
import threading
import webbrowser
import time
import logging
import traceback
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple, Callable

# Import core modules
try:
    from core.logging import get_logger
    from core.config import get_config
    from core.paths import get_base_dir
except ImportError:
    # Fallback if core modules are not available
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    get_logger = lambda name: logging.getLogger(name)
    get_config = lambda: {"server": {"port": 5100, "host": "localhost"}}
    get_base_dir = lambda: Path(__file__).resolve().parent.parent

# Get logger for this module
logger = get_logger("web.server")

# Server configuration
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 5100
DEFAULT_PORT_RANGE = (5100, 5110)
DEFAULT_OPEN_BROWSER = True

# HTTP status codes
HTTP_OK = 200
HTTP_CREATED = 201
HTTP_NO_CONTENT = 204
HTTP_BAD_REQUEST = 400
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_METHOD_NOT_ALLOWED = 405
HTTP_INTERNAL_SERVER_ERROR = 500

# MIME types
MIME_HTML = "text/html"
MIME_JSON = "application/json"
MIME_TEXT = "text/plain"
MIME_CSS = "text/css"
MIME_JS = "application/javascript"


class Request:
    """
    Represents an HTTP request with parsed parameters.
    
    Provides easy access to request data including path, query parameters,
    headers, cookies, and body content.
    """
    
    def __init__(self, handler):
        """
        Initialize request from handler.
        
        Args:
            handler: BaseHTTPRequestHandler instance
        """
        self.handler = handler
        self.method = handler.command
        self.path = handler.path
        self.headers = handler.headers
        
        # Parse URL components
        parsed_url = urllib.parse.urlparse(self.path)
        self.base_path = parsed_url.path
        
        # Parse query parameters
        self.query_params = {}
        for key, value in urllib.parse.parse_qsl(parsed_url.query):
            self.query_params[key] = value
            
        # Parse request body
        self.body = self._parse_body()
        
        # Parse cookies
        self.cookies = self._parse_cookies()
    
    def _parse_body(self):
        """Parse request body based on content type."""
        if not hasattr(self.handler, 'rfile'):
            return None
            
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length == 0:
            return None
            
        content_type = self.headers.get('Content-Type', '')
        
        # Read body content
        body_data = self.handler.rfile.read(content_length)
        
        # Parse based on content type
        if 'application/json' in content_type:
            try:
                return json.loads(body_data.decode('utf-8'))
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON body: {e}")
                return None
                
        elif 'application/x-www-form-urlencoded' in content_type:
            try:
                form_data = {}
                for key, value in urllib.parse.parse_qsl(body_data.decode('utf-8')):
                    form_data[key] = value
                return form_data
            except Exception as e:
                logger.error(f"Failed to parse form data: {e}")
                return None
                
        else:
            # Return raw body
            return body_data.decode('utf-8')
    
    def _parse_cookies(self):
        """Parse cookies from request headers."""
        cookies = {}
        cookie_string = self.headers.get('Cookie', '')
        
        if not cookie_string:
            return cookies
            
        for cookie in cookie_string.split(';'):
            if '=' in cookie:
                name, value = cookie.strip().split('=', 1)
                cookies[name] = value
                
        return cookies
    
    def get_header(self, name, default=None):
        """Get header value by name."""
        return self.headers.get(name, default)
    
    def get_query_param(self, name, default=None):
        """Get query parameter by name."""
        return self.query_params.get(name, default)
    
    def get_cookie(self, name, default=None):
        """Get cookie by name."""
        return self.cookies.get(name, default)


class Response:
    """
    Represents an HTTP response to be sent to the client.
    
    Provides methods for setting response status, headers, and body,
    and for sending the response through the handler.
    """
    
    def __init__(self):
        """Initialize response with default values."""
        self.status_code = HTTP_OK
        self.headers = {'Content-Type': MIME_HTML}
        self.cookies = []
        self.body = ""
    
    def set_status(self, status_code):
        """Set response status code."""
        self.status_code = status_code
        return self
    
    def set_header(self, name, value):
        """Set response header."""
        self.headers[name] = value
        return self
    
    def set_content_type(self, content_type):
        """Set content type header."""
        self.headers['Content-Type'] = content_type
        return self
    
    def set_cookie(self, name, value, expires=None, path="/", domain=None, secure=False, http_only=False):
        """Set response cookie."""
        cookie = f"{name}={value}"
        
        if expires:
            cookie += f"; Expires={expires}"
        if path:
            cookie += f"; Path={path}"
        if domain:
            cookie += f"; Domain={domain}"
        if secure:
            cookie += "; Secure"
        if http_only:
            cookie += "; HttpOnly"
            
        self.cookies.append(cookie)
        return self
    
    def set_body(self, body):
        """Set response body."""
        self.body = body
        return self
    
    def json(self, data):
        """Set JSON response."""
        self.headers['Content-Type'] = MIME_JSON
        self.body = json.dumps(data)
        return self
    
    def text(self, content):
        """Set text response."""
        self.headers['Content-Type'] = MIME_TEXT
        self.body = content
        return self
    
    def html(self, content):
        """Set HTML response."""
        self.headers['Content-Type'] = MIME_HTML
        self.body = content
        return self
    
    def redirect(self, location, permanent=False):
        """Set redirect response."""
        self.status_code = 301 if permanent else 302
        self.headers['Location'] = location
        return self
    
    def error(self, status_code, message=None):
        """Set error response."""
        self.status_code = status_code
        
        if message:
            if self.headers.get('Content-Type') == MIME_JSON:
                self.body = json.dumps({"error": message})
            else:
                self.body = message
                
        return self
    
    def send(self, handler):
        """Send response through handler."""
        try:
            # Set status code
            handler.send_response(self.status_code)
            
            # Set headers
            for name, value in self.headers.items():
                handler.send_header(name, value)
                
            # Set cookies
            for cookie in self.cookies:
                handler.send_header('Set-Cookie', cookie)
                
            # End headers
            handler.end_headers()
            
            # Send body
            if self.body:
                # Convert to bytes if necessary
                if isinstance(self.body, str):
                    body_bytes = self.body.encode('utf-8')
                elif isinstance(self.body, dict) or isinstance(self.body, list):
                    body_bytes = json.dumps(self.body).encode('utf-8')
                else:
                    body_bytes = self.body
                    
                handler.wfile.write(body_bytes)
                
        except Exception as e:
            logger.error(f"Error sending response: {e}")
            raise


class RequestHandler(http.server.BaseHTTPRequestHandler):
    """
    Custom HTTP request handler for the LLM Platform server.
    
    Processes incoming HTTP requests, routes them to the appropriate
    handler functions, and sends responses to clients.
    """
    
    # Will be set by the Server class
    router = None
    middleware = []
    
    def log_message(self, format, *args):
        """Override default logging to use our logger."""
        logger.debug(f"{self.address_string()} - {format % args}")
    
    def handle_error(self, status_code, message=None):
        """Handle errors consistently."""
        response = Response().error(status_code, message)
        response.send(self)
    
    def process_request(self, method):
        """Process an incoming request of any method."""
        if not self.router:
            self.handle_error(HTTP_INTERNAL_SERVER_ERROR, "Router not configured")
            return
            
        try:
            # Create request and response objects
            request = Request(self)
            response = Response()
            
            # Run request through middleware
            for middleware_func in self.middleware:
                try:
                    middleware_func(request, response)
                    
                    # If middleware has already set a status code other than 200, stop processing
                    if response.status_code != HTTP_OK:
                        response.send(self)
                        return
                except Exception as e:
                    logger.error(f"Middleware error: {e}")
                    self.handle_error(HTTP_INTERNAL_SERVER_ERROR, f"Middleware error: {str(e)}")
                    return
            
            # Route the request
            handler_func = self.router.find_handler(request.base_path, method)
            
            if handler_func:
                # Call the handler
                try:
                    handler_func(request, response)
                    response.send(self)
                except Exception as e:
                    logger.error(f"Handler error: {e}\n{traceback.format_exc()}")
                    self.handle_error(HTTP_INTERNAL_SERVER_ERROR, f"Handler error: {str(e)}")
            else:
                # No route found
                self.handle_error(HTTP_NOT_FOUND, f"No handler found for {method} {request.base_path}")
                
        except Exception as e:
            logger.error(f"Request processing error: {e}\n{traceback.format_exc()}")
            self.handle_error(HTTP_INTERNAL_SERVER_ERROR, f"Request processing error: {str(e)}")
    
    # Handle different HTTP methods
    def do_GET(self):
        """Handle GET requests."""
        self.process_request('GET')
    
    def do_POST(self):
        """Handle POST requests."""
        self.process_request('POST')
    
    def do_PUT(self):
        """Handle PUT requests."""
        self.process_request('PUT')
    
    def do_DELETE(self):
        """Handle DELETE requests."""
        self.process_request('DELETE')
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests."""
        self.process_request('OPTIONS')


class Server:
    """
    HTTP server for the LLM Platform.
    
    Manages the HTTP server, including configuration, startup, shutdown,
    and integration with routers and middleware.
    """
    
    def __init__(self, host=None, port=None, router=None, middleware=None):
        """
        Initialize the server.
        
        Args:
            host: Server hostname (default: localhost)
            port: Server port (default: from config or 5100)
            router: Router instance for request routing
            middleware: List of middleware functions
        """
        # Get configuration
        config = get_config()
        server_config = config.get("server", {})
        
        # Set server properties
        self.host = host or server_config.get("host", DEFAULT_HOST)
        self.port = port or server_config.get("port", DEFAULT_PORT)
        self.port_range = server_config.get("port_range", DEFAULT_PORT_RANGE)
        self.open_browser = server_config.get("open_browser", DEFAULT_OPEN_BROWSER)
        
        # Set router and middleware
        self.router = router
        self.middleware = middleware or []
        
        # Initialize server variables
        self.httpd = None
        self.server_thread = None
        self.is_running = False
    
    def configure_handler(self):
        """Configure the request handler with router and middleware."""
        # Set class variables on RequestHandler
        RequestHandler.router = self.router
        RequestHandler.middleware = self.middleware
    
    def find_available_port(self):
        """Find an available port in the configured range."""
        # Try the specified port first
        try:
            with socketserver.TCPServer((self.host, self.port), None) as test_server:
                # Port is available
                return self.port
        except OSError:
            logger.info(f"Port {self.port} is in use, trying others in range {self.port_range}")
            
        # Try other ports in the range
        start_port, end_port = self.port_range
        for port in range(start_port, end_port + 1):
            if port == self.port:
                continue  # Already tried this one
                
            try:
                with socketserver.TCPServer((self.host, port), None) as test_server:
                    # Port is available
                    return port
            except OSError:
                continue
                
        # No ports available
        raise RuntimeError(f"No available ports in range {start_port}-{end_port}")
    
    def start(self, block=False):
        """
        Start the server.
        
        Args:
            block: If True, block until server is stopped
        
        Returns:
            (host, port) tuple for the running server
        """
        if self.is_running:
            logger.warning("Server is already running")
            return (self.host, self.port)
            
        # Find available port
        try:
            self.port = self.find_available_port()
        except RuntimeError as e:
            logger.error(str(e))
            raise
            
        # Configure handler
        self.configure_handler()
        
        # Create server
        try:
            self.httpd = socketserver.ThreadingTCPServer((self.host, self.port), RequestHandler)
            self.httpd.daemon_threads = True  # Exit quickly on shutdown
        except Exception as e:
            logger.error(f"Failed to create server: {e}")
            raise
            
        # Start server thread if not blocking
        if not block:
            self.server_thread = threading.Thread(target=self.httpd.serve_forever)
            self.server_thread.daemon = True
            self.server_thread.start()
            self.is_running = True
            
            logger.info(f"Server started on http://{self.host}:{self.port}")
            
            # Open browser if configured
            if self.open_browser:
                threading.Thread(
                    target=lambda: self._open_browser_delayed(f"http://{self.host}:{self.port}")
                ).start()
                
            return (self.host, self.port)
        else:
            # Block until Ctrl+C
            self.is_running = True
            logger.info(f"Server started on http://{self.host}:{self.port}")
            
            # Open browser if configured
            if self.open_browser:
                threading.Thread(
                    target=lambda: self._open_browser_delayed(f"http://{self.host}:{self.port}")
                ).start()
                
            try:
                self.httpd.serve_forever()
            except KeyboardInterrupt:
                logger.info("Server stopped by user")
                self.stop()
                
            return (self.host, self.port)
    
    def stop(self):
        """Stop the server."""
        if not self.is_running:
            logger.warning("Server is not running")
            return
            
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
            self.is_running = False
            logger.info("Server stopped")
    
    def _open_browser_delayed(self, url, delay=1.0):
        """Open browser with delay to ensure server is ready."""
        time.sleep(delay)
        webbrowser.open(url)


def create_server(host=None, port=None, router=None, middleware=None):
    """
    Create a server instance.
    
    Args:
        host: Server hostname
        port: Server port
        router: Router instance
        middleware: List of middleware functions
        
    Returns:
        Server instance
    """
    return Server(host, port, router, middleware)


def start_server(host=None, port=None, router=None, middleware=None, block=True):
    """
    Create and start a server.
    
    Args:
        host: Server hostname
        port: Server port
        router: Router instance
        middleware: List of middleware functions
        block: If True, block until server is stopped
        
    Returns:
        (host, port) tuple for the running server
    """
    server = create_server(host, port, router, middleware)
    return server.start(block)


# For testing
if __name__ == "__main__":
    from web.router import Router
    
    # Create router
    router = Router()
    
    # Add test routes
    @router.get("/")
    def home(request, response):
        response.html("<h1>Hello from LLM Platform!</h1>")
    
    @router.get("/api/test")
    def api_test(request, response):
        response.json({"message": "API is working!"})
    
    # Start server
    start_server(router=router, block=True)