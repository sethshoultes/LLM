#!/usr/bin/env python3
"""
HTTP handlers module for the LLM Platform web server.

Provides standardized handler functions for common web server operations,
including serving static files, rendering templates, and API requests.
"""

import traceback
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple, Callable

# Import core modules
from core.logging import get_logger
from core.paths import get_app_path

# Import template engine modules
from web.templates.components import Component

# Get logger for this module
logger = get_logger(__name__)


class StaticFileHandler:
    """
    Handler for serving static files.
    
    Serves static files from a specified directory with proper MIME types
    and caching headers.
    """
    
    def __init__(self, static_dir=None, url_prefix="/assets"):
        """
        Initialize static file handler.
        
        Args:
            static_dir: Directory containing static files
            url_prefix: URL prefix for static files
        """
        # Set static directory
        if static_dir is None:
            static_dir = get_app_path() / "templates" / "assets"
            
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
        
        # Get asset content and mime type
        content, mime_type = get_asset(file_path)
        
        if content is None:
            response.error(404, "File not found")
            return
        
        # Check for cache control via query parameters
        no_cache = request.get_query_param("no-cache")
        
        # Set content type
        response.set_header("Content-Type", mime_type)
        
        # Set content length
        response.set_header("Content-Length", str(len(content)))
        
        # Set caching headers if enabled
        if self.enable_caching and not no_cache:
            response.set_header("Cache-Control", f"max-age={self.max_age}, public")
        else:
            response.set_header("Cache-Control", "no-cache, no-store, must-revalidate")
            response.set_header("Pragma", "no-cache")
            response.set_header("Expires", "0")
        
        # Send content
        response.status_code = 200
        response.body = content


class TemplateHandler:
    """
    Handler for rendering templates.
    
    Renders templates using the template engine with context data and
    standardized error handling.
    """
    
    def __init__(self):
        """Initialize template handler."""
        pass
    
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
                    "query": request.query_params,
                    "path": request.base_path,
                    **context
                }
                
                # Render template
                html = render_template(template_name, full_context)
                
                # Set response
                response.status_code = status
                response.html(html)
            except Exception as e:
                logger.error(f"Error rendering template {template_name}: {e}")
                error_html = render_error(500, f"Template error: {str(e)}")
                response.status_code = 500
                response.html(error_html)
        
        return handler
    
    def render_component(self, component_name, context=None, status=200):
        """
        Render a component with context data.
        
        Args:
            component_name: Name of the component
            context: Context data for component rendering
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
                    "query": request.query_params,
                    "path": request.base_path,
                    **context
                }
                
                # Render component
                html = render_component(component_name, **full_context)
                
                # Set response
                response.status_code = status
                response.html(html)
            except Exception as e:
                logger.error(f"Error rendering component {component_name}: {e}")
                error_html = render_error(500, f"Component error: {str(e)}")
                response.status_code = 500
                response.html(error_html)
        
        return handler
    
    def render_component_object(self, component: Component, status=200):
        """
        Render a component object.
        
        Args:
            component: Component object to render
            status: HTTP status code
            
        Returns:
            Function that handles the request and response
        """
        def handler(request, response):
            try:
                # Add request to component context
                component_html = component.render(request=request)
                
                # Set response
                response.status_code = status
                response.html(component_html)
            except Exception as e:
                logger.error(f"Error rendering component object: {e}")
                error_html = render_error(500, f"Component error: {str(e)}")
                response.status_code = 500
                response.html(error_html)
        
        return handler
    
    def render_error(self, error_code, message=None):
        """
        Render an error page.
        
        Args:
            error_code: HTTP error code
            message: Optional error message
            
        Returns:
            Function that handles the request and response
        """
        def handler(request, response):
            try:
                # Render error page
                html = render_error(error_code, message)
                
                # Set response
                response.status_code = error_code
                response.html(html)
            except Exception as e:
                logger.error(f"Error rendering error page: {e}")
                response.status_code = 500
                response.html("<h1>Error 500</h1><p>Internal server error</p>")
        
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
    
    def success_response(self, data, message=None, meta=None, status=200):
        """
        Create a standardized success response.
        
        Args:
            data: Response data
            message: Optional success message
            meta: Optional metadata
            status: HTTP status code
            
        Returns:
            Response data dictionary
        """
        response = {
            "status": "success",
            "data": data
        }
        
        if message:
            response["message"] = message
            
        if meta:
            response["meta"] = meta
            
        return response, status
    
    def error_response(self, error, detail=None, code=None, status=400):
        """
        Create a standardized error response.
        
        Args:
            error: Error message
            detail: Optional error details
            code: Optional error code
            status: HTTP status code
            
        Returns:
            Response data dictionary
        """
        response = {
            "status": "error",
            "error": error
        }
        
        if detail:
            response["detail"] = detail
            
        if code:
            response["code"] = code
            
        return response, status
    
    def json_handler(self, handler_func, validator=None):
        """
        Create a JSON API handler.
        
        Args:
            handler_func: Function that processes the request and returns (data, status)
            validator: Optional function to validate request data
            
        Returns:
            Function that handles the request and response
        """
        def api_handler(request, response):
            try:
                # Validate request if validator provided
                if validator and request.body:
                    validation_errors = validator(request.body)
                    if validation_errors:
                        error_data, error_status = self.error_response(
                            "Validation failed",
                            validation_errors,
                            "validation_error",
                            400
                        )
                        response.status_code = error_status
                        response.json(error_data)
                        return
                
                # Process request
                result = handler_func(request)
                
                # Set response based on result
                if isinstance(result, tuple) and len(result) == 2:
                    # Result is already in (data, status) format
                    data, status_code = result
                    response.status_code = status_code
                    response.json(data)
                else:
                    # Wrap result in success response
                    data, status_code = self.success_response(result)
                    response.status_code = status_code
                    response.json(data)
            except Exception as e:
                logger.error(f"API handler error: {e}\n{traceback.format_exc()}")
                error_data, error_status = self.error_response(
                    "Internal server error",
                    str(e),
                    "internal_error",
                    500
                )
                response.status_code = error_status
                response.json(error_data)
        
        return api_handler


# Create handler instances
static_handler = StaticFileHandler()
template_handler = TemplateHandler()
api_handler = ApiHandler()


# Helper functions for common handlers

def serve_static_file(request, response):
    """
    Serve a static file.
    
    Args:
        request: Request object
        response: Response object
    """
    static_handler.handle(request, response)


def render_view(template_name, context=None, status=200):
    """
    Render a template view.
    
    Args:
        template_name: Name of the template file
        context: Context data for template rendering
        status: HTTP status code
        
    Returns:
        Handler function for the request
    """
    return template_handler.render(template_name, context, status)


def render_ui_component(component_name, context=None, status=200):
    """
    Render a UI component.
    
    Args:
        component_name: Name of the component
        context: Context data for component rendering
        status: HTTP status code
        
    Returns:
        Handler function for the request
    """
    return template_handler.render_component(component_name, context, status)


def render_component_object(component, status=200):
    """
    Render a component object.
    
    Args:
        component: Component object to render
        status: HTTP status code
        
    Returns:
        Handler function for the request
    """
    return template_handler.render_component_object(component, status)


def json_api(handler_func, validator=None):
    """
    Create a JSON API endpoint.
    
    Args:
        handler_func: Function that processes the request and returns (data, status)
        validator: Optional function to validate request data
        
    Returns:
        Handler function for the request
    """
    return api_handler.json_handler(handler_func, validator)


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


def error_page(error_code, message=None):
    """
    Create an error page handler.
    
    Args:
        error_code: HTTP error code
        message: Optional error message
        
    Returns:
        Handler function for the request
    """
    return template_handler.render_error(error_code, message)