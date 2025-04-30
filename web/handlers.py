#!/usr/bin/env python3
"""
HTTP handlers module for the LLM Platform web server.

Provides standardized handler functions for common web server operations,
including serving static files, rendering templates, and API requests.
"""

import os
import json
import logging
import traceback
import mimetypes
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple, Callable

# Import core modules
try:
    from core.logging import get_logger
    from core.paths import get_base_dir
except ImportError:
    # Fallback if core modules are not available
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    get_logger = lambda name: logging.getLogger(name)
    get_base_dir = lambda: Path(__file__).resolve().parent.parent

# Import template engine
try:
    from web.templates.engine import render_template
except ImportError:
    # Mock template rendering if not available
    def render_template(template_name, **context):
        return f"<p>Template {template_name} (mock rendering)</p>"

# Get logger for this module
logger = get_logger("web.handlers")

# Get base directory
BASE_DIR = get_base_dir()


class StaticFileHandler:
    """
    Handler for serving static files.
    
    Serves static files from a specified directory with proper MIME types
    and caching headers.
    """
    
    def __init__(self, static_dir=None, url_prefix="/static"):
        """
        Initialize static file handler.
        
        Args:
            static_dir: Directory containing static files
            url_prefix: URL prefix for static files
        """
        # Set static directory
        if static_dir is None:
            static_dir = BASE_DIR / "templates" / "assets"
            
        self.static_dir = Path(static_dir)
        self.url_prefix = url_prefix
        
        # Enable caching by default
        self.enable_caching = True
        self.max_age = 86400  # 1 day in seconds
    
    def handle(self, request, response):
        """
        Handle static file request.
        
        Args:
            request: Request object
            response: Response object
        """
        # Extract file path
        if not request.base_path.startswith(self.url_prefix):
            response.error(404, "File not found")
            return
            
        file_path = request.base_path[len(self.url_prefix):].lstrip('/')
        full_path = self.static_dir / file_path
        
        # Normalize path to prevent directory traversal attacks
        try:
            full_path = full_path.resolve()
            if not str(full_path).startswith(str(self.static_dir.resolve())):
                # Path is outside static directory
                response.error(403, "Access denied")
                return
        except Exception:
            response.error(400, "Invalid path")
            return
            
        # Check if file exists
        if not full_path.is_file():
            response.error(404, "File not found")
            return
            
        # Get file info
        file_size = full_path.stat().st_size
        file_mtime = full_path.stat().st_mtime
        
        # Get content type
        content_type, encoding = mimetypes.guess_type(str(full_path))
        if content_type is None:
            content_type = "application/octet-stream"
            
        # Set content type and encoding
        response.set_header("Content-Type", content_type)
        if encoding:
            response.set_header("Content-Encoding", encoding)
            
        # Set content length
        response.set_header("Content-Length", str(file_size))
        
        # Set caching headers if enabled
        if self.enable_caching:
            response.set_header("Cache-Control", f"max-age={self.max_age}, public")
            
        # Read and send file
        try:
            with open(full_path, "rb") as f:
                file_content = f.read()
                
            response.status_code = 200
            response.body = file_content
        except Exception as e:
            logger.error(f"Error reading file {full_path}: {e}")
            response.error(500, "Internal server error")


class TemplateHandler:
    """
    Handler for rendering templates.
    
    Renders templates using the template engine with context data and
    standardized error handling.
    """
    
    def __init__(self, templates_dir=None):
        """
        Initialize template handler.
        
        Args:
            templates_dir: Directory containing templates
        """
        # Set templates directory
        if templates_dir is None:
            templates_dir = BASE_DIR / "templates"
            
        self.templates_dir = Path(templates_dir)
    
    def render(self, template_name, context=None, status=200):
        """
        Render a template with context data.
        
        Args:
            template_name: Name of the template file
            context: Context data for template rendering
            status: HTTP status code
            
        Returns:
            Function that handles the request and response
        """
        context = context or {}
        
        def handler(request, response):
            try:
                # Add request data to context
                full_context = {
                    "request": request,
                    **context
                }
                
                # Render template
                html = render_template(template_name, **full_context)
                
                # Set response
                response.status_code = status
                response.html(html)
            except Exception as e:
                logger.error(f"Error rendering template {template_name}: {e}")
                response.error(500, f"Template error: {str(e)}")
        
        return handler


class ApiHandler:
    """
    Handler for API endpoints.
    
    Provides standardized handling of API requests and responses,
    including JSON parsing, validation, and error handling.
    """
    
    def __init__(self):
        """Initialize API handler."""
        pass
    
    def json_response(self, data, status=200):
        """
        Create a JSON response handler.
        
        Args:
            data: Data to return as JSON
            status: HTTP status code
            
        Returns:
            Function that handles the request and response
        """
        def handler(request, response):
            response.status_code = status
            response.json(data)
        
        return handler
    
    def error_response(self, message, status=400):
        """
        Create an error response handler.
        
        Args:
            message: Error message
            status: HTTP status code
            
        Returns:
            Function that handles the request and response
        """
        def handler(request, response):
            response.status_code = status
            response.json({"error": message})
        
        return handler
    
    def create_handler(self, handler_func, validator=None):
        """
        Create an API request handler with validation.
        
        Args:
            handler_func: Function that processes the request and returns data
            validator: Optional function to validate request data
            
        Returns:
            Function that handles the request and response
        """
        def api_handler(request, response):
            try:
                # Validate request if validator provided
                if validator:
                    validation_errors = validator(request)
                    if validation_errors:
                        response.status_code = 400
                        response.json({"errors": validation_errors})
                        return
                
                # Process request
                result = handler_func(request)
                
                # Set response based on result
                if isinstance(result, tuple) and len(result) == 2:
                    # Result is (data, status_code)
                    data, status_code = result
                    response.status_code = status_code
                    response.json(data)
                else:
                    # Result is just data
                    response.json(result)
            except Exception as e:
                logger.error(f"API handler error: {e}\n{traceback.format_exc()}")
                response.status_code = 500
                response.json({
                    "error": "Internal server error",
                    "message": str(e)
                })
        
        return api_handler


# Create handler instances
static_handler = StaticFileHandler()
template_handler = TemplateHandler()
api_handler = ApiHandler()


# Helper functions for common handlers

def serve_static_file(file_path, request, response):
    """
    Serve a static file.
    
    Args:
        file_path: Path to the file
        request: Request object
        response: Response object
    """
    static_handler.static_dir = Path(file_path).parent
    static_handler.url_prefix = ""
    
    # Modify request path to match file name
    original_path = request.base_path
    request.base_path = "/" + Path(file_path).name
    
    # Handle request
    static_handler.handle(request, response)
    
    # Restore original path
    request.base_path = original_path


def render_view(template_name, context=None):
    """
    Render a template view.
    
    Args:
        template_name: Name of the template file
        context: Context data for template rendering
        
    Returns:
        Handler function for the request
    """
    return template_handler.render(template_name, context)


def json_api(handler_func, validator=None):
    """
    Create a JSON API endpoint.
    
    Args:
        handler_func: Function that processes the request and returns data
        validator: Optional function to validate request data
        
    Returns:
        Handler function for the request
    """
    return api_handler.create_handler(handler_func, validator)


def redirect(location, permanent=False):
    """
    Create a redirect handler.
    
    Args:
        location: URL to redirect to
        permanent: If True, use permanent redirect (301)
        
    Returns:
        Handler function for the request
    """
    def handler(request, response):
        response.redirect(location, permanent)
    
    return handler


# For testing
if __name__ == "__main__":
    # Test static file handler
    class MockRequest:
        def __init__(self, path):
            self.base_path = path
            
    class MockResponse:
        def __init__(self):
            self.status_code = 200
            self.headers = {}
            self.body = ""
            
        def set_header(self, name, value):
            self.headers[name] = value
            
        def error(self, status, message):
            self.status_code = status
            self.body = message
            
        def html(self, content):
            self.body = content
            
        def json(self, data):
            self.body = json.dumps(data)
    
    # Test serving a static file
    static_dir = BASE_DIR / "templates" / "assets"
    test_file = "css/main.css"
    
    req = MockRequest(f"/static/{test_file}")
    res = MockResponse()
    
    static_handler.static_dir = static_dir
    static_handler.handle(req, res)
    
    print(f"Status: {res.status_code}")
    print(f"Content-Type: {res.headers.get('Content-Type')}")
    print(f"Body length: {len(res.body) if isinstance(res.body, (str, bytes)) else 'N/A'}")