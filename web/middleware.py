#!/usr/bin/env python3
"""
Middleware module for the LLM Platform web server.

Provides a middleware system for processing requests and responses,
with support for preprocessing, postprocessing, and error handling.
"""

import time
import logging
import traceback
from functools import wraps
from typing import Dict, List, Any, Optional, Union, Tuple, Callable

# Import core modules
try:
    from core.logging import get_logger
except ImportError:
    # Fallback if core module is not available
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    get_logger = lambda name: logging.getLogger(name)

# Get logger for this module
logger = get_logger("web.middleware")


class MiddlewareManager:
    """
    Manager for middleware functions.
    
    Allows registration and execution of middleware functions for
    preprocessing requests, postprocessing responses, and error handling.
    """
    
    def __init__(self):
        """Initialize middleware manager."""
        self.middleware = []
    
    def add(self, middleware_func):
        """
        Add a middleware function.
        
        Args:
            middleware_func: Middleware function to add
            
        Returns:
            Self for chaining
        """
        self.middleware.append(middleware_func)
        return self
    
    def get_middleware(self):
        """Get the list of middleware functions."""
        return self.middleware


# Built-in middleware functions

def request_logger(request, response):
    """
    Log incoming requests.
    
    Args:
        request: Request object
        response: Response object
    """
    start_time = time.time()
    
    # Store start time for later calculation of processing time
    request.start_time = start_time
    
    # Log request
    logger.info(f"{request.method} {request.path}")
    logger.debug(f"Headers: {request.headers}")
    
    # This middleware doesn't modify the request or response


def response_logger(request, response):
    """
    Log outgoing responses.
    
    Args:
        request: Request object
        response: Response object
    """
    # Calculate processing time
    if hasattr(request, 'start_time'):
        processing_time = (time.time() - request.start_time) * 1000  # Convert to ms
        logger.info(f"{request.method} {request.path} - {response.status_code} ({processing_time:.2f}ms)")
    else:
        logger.info(f"{request.method} {request.path} - {response.status_code}")


def cors_headers(allow_origin='*', allow_methods=None, allow_headers=None, allow_credentials=False):
    """
    Add CORS headers to responses.
    
    Args:
        allow_origin: Allowed origin(s)
        allow_methods: Allowed HTTP methods
        allow_headers: Allowed HTTP headers
        allow_credentials: Whether to allow credentials
    
    Returns:
        Middleware function
    """
    if allow_methods is None:
        allow_methods = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
        
    if allow_headers is None:
        allow_headers = ['Content-Type', 'Authorization']
    
    def middleware(request, response):
        # Add CORS headers
        response.set_header('Access-Control-Allow-Origin', allow_origin)
        response.set_header('Access-Control-Allow-Methods', ', '.join(allow_methods))
        response.set_header('Access-Control-Allow-Headers', ', '.join(allow_headers))
        
        if allow_credentials:
            response.set_header('Access-Control-Allow-Credentials', 'true')
        
        # Handle OPTIONS preflight requests
        if request.method == 'OPTIONS':
            response.status_code = 204  # No content
            response.body = ''
    
    return middleware


def json_body_parser(request, response):
    """
    Parse JSON request bodies.
    
    Args:
        request: Request object
        response: Response object
    """
    content_type = request.get_header('Content-Type', '')
    
    if 'application/json' in content_type and request.body:
        # Body should already be parsed by Request class
        if not isinstance(request.body, dict) and not isinstance(request.body, list):
            logger.warning("Failed to parse JSON body")
            response.status_code = 400
            response.set_content_type('application/json')
            response.body = '{"error": "Invalid JSON"}'


def error_handler(request, response):
    """
    Handle errors during request processing.
    
    Args:
        request: Request object
        response: Response object
    """
    # This middleware doesn't do anything at the preprocessing stage
    # It's designed to catch exceptions, but that's handled by the server
    pass


def static_files(static_dir, url_prefix='/static'):
    """
    Serve static files.
    
    Args:
        static_dir: Directory containing static files
        url_prefix: URL prefix for static files
    
    Returns:
        Middleware function
    """
    import os
    import mimetypes
    
    def middleware(request, response):
        # Check if path starts with url_prefix
        if request.base_path.startswith(url_prefix):
            # Extract file path
            file_path = request.base_path[len(url_prefix):].lstrip('/')
            full_path = os.path.join(static_dir, file_path)
            
            # Check if file exists
            if os.path.isfile(full_path):
                # Get content type
                content_type, _ = mimetypes.guess_type(full_path)
                if content_type is None:
                    content_type = 'application/octet-stream'
                
                # Read file
                try:
                    with open(full_path, 'rb') as f:
                        file_content = f.read()
                    
                    # Set response
                    response.status_code = 200
                    response.set_header('Content-Type', content_type)
                    response.body = file_content
                except Exception as e:
                    logger.error(f"Error reading static file {full_path}: {e}")
                    response.status_code = 500
                    response.body = 'Error reading file'
            else:
                # File not found
                response.status_code = 404
                response.body = 'File not found'
    
    return middleware


def rate_limiter(requests_per_minute=60, window_seconds=60):
    """
    Rate limit requests by IP address.
    
    Args:
        requests_per_minute: Maximum requests per minute
        window_seconds: Time window in seconds
    
    Returns:
        Middleware function
    """
    from collections import defaultdict
    import time
    
    # Store request counts per IP
    request_counts = defaultdict(list)
    
    def middleware(request, response):
        # Get client IP
        client_ip = request.handler.client_address[0]
        current_time = time.time()
        
        # Clean up old requests
        request_counts[client_ip] = [t for t in request_counts[client_ip] if current_time - t < window_seconds]
        
        # Check rate limit
        if len(request_counts[client_ip]) >= requests_per_minute:
            response.status_code = 429  # Too Many Requests
            response.set_content_type('application/json')
            response.body = '{"error": "Rate limit exceeded"}'
            return
        
        # Add current request
        request_counts[client_ip].append(current_time)
    
    return middleware


def compression(level=6):
    """
    Compress response bodies.
    
    Args:
        level: Compression level (1-9)
    
    Returns:
        Middleware function
    """
    import gzip
    import io
    
    def middleware(request, response):
        # Check if client supports gzip
        accept_encoding = request.get_header('Accept-Encoding', '')
        
        if 'gzip' in accept_encoding:
            # Get original response body
            body = response.body
            
            # Skip compression for small responses or binary data
            if not body or len(body) < 1000:
                return
                
            if isinstance(body, str):
                body = body.encode('utf-8')
                
            # Compress body
            try:
                compressed_body = io.BytesIO()
                with gzip.GzipFile(fileobj=compressed_body, mode='wb', compresslevel=level) as f:
                    f.write(body)
                    
                # Update response
                response.body = compressed_body.getvalue()
                response.set_header('Content-Encoding', 'gzip')
                response.set_header('Content-Length', str(len(response.body)))
            except Exception as e:
                logger.error(f"Compression error: {e}")
                # Keep original body
    
    return middleware


# Create global middleware manager
middleware_manager = MiddlewareManager()

# Add default middleware
middleware_manager.add(request_logger)
middleware_manager.add(response_logger)
middleware_manager.add(json_body_parser)
middleware_manager.add(error_handler)

# Function to create middleware stack
def create_middleware(*middleware_funcs):
    """
    Create a middleware stack from the given functions.
    
    Args:
        *middleware_funcs: Middleware functions to include
    
    Returns:
        List of middleware functions
    """
    return list(middleware_funcs)


# Create default middleware stack
default_middleware = middleware_manager.get_middleware()


# For testing
if __name__ == "__main__":
    # Define a simple mock Request and Response
    class MockRequest:
        def __init__(self):
            self.method = "GET"
            self.path = "/test"
            self.headers = {"Content-Type": "application/json"}
            self.body = '{"test": true}'
            
        def get_header(self, name, default=None):
            return self.headers.get(name, default)
            
    class MockResponse:
        def __init__(self):
            self.status_code = 200
            self.headers = {}
            self.body = ""
            
        def set_header(self, name, value):
            self.headers[name] = value
            
        def set_content_type(self, content_type):
            self.headers["Content-Type"] = content_type
            
    # Create middleware
    test_middleware = create_middleware(
        request_logger,
        cors_headers(),
        json_body_parser,
        response_logger
    )
    
    # Test middleware
    request = MockRequest()
    response = MockResponse()
    
    for middleware in test_middleware:
        middleware(request, response)
        
    print(f"Response headers: {response.headers}")
    print(f"Response status: {response.status_code}")