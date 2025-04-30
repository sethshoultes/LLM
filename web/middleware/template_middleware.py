#!/usr/bin/env python3
"""
Template middleware for the LLM Platform web server.

Provides middleware for injecting common template variables into responses
and handling template-related concerns.
"""

from typing import Dict, Any, Callable

from core.logging import get_logger
from web.templates.assets import get_url

# Get logger for this module
logger = get_logger(__name__)


class TemplateMiddleware:
    """
    Middleware for injecting common template variables into responses.
    
    Adds common variables like application name, version, and asset paths
    to template contexts.
    """
    
    def __init__(
        self, 
        app_name: str = "LLM Platform", 
        app_version: str = "1.0.0",
        global_context: Dict[str, Any] = None
    ):
        """
        Initialize template middleware.
        
        Args:
            app_name: Application name
            app_version: Application version
            global_context: Global context variables for all templates
        """
        self.app_name = app_name
        self.app_version = app_version
        self.global_context = global_context or {}
        
        # Add app info to global context
        self.global_context.update({
            "app_name": app_name,
            "app_version": app_version,
        })
        
        # Add asset helper functions
        self.global_context.update({
            "asset_url": get_url,
        })
        
        # The middleware function
        self.middleware_func = self._create_middleware()
    
    def _create_middleware(self) -> Callable:
        """
        Create the middleware function.
        
        Returns:
            Middleware function
        """
        def middleware(request, response):
            # Add request-specific data to context
            request_context = {
                "request_path": request.base_path,
                "query_params": request.query_params
            }
            
            # Store combined context in request for use in handlers
            request.template_context = {
                **self.global_context,
                **request_context
            }
            
            # Add utility methods to the request for template rendering
            request.get_template_context = lambda additional=None: {
                **request.template_context,
                **(additional or {})
            }
        
        return middleware
    
    def __call__(self, request, response):
        """
        Call the middleware function.
        
        Args:
            request: Request object
            response: Response object
        """
        return self.middleware_func(request, response)
    
    def add_global(self, key: str, value: Any) -> None:
        """
        Add a global context variable.
        
        Args:
            key: Variable name
            value: Variable value
        """
        self.global_context[key] = value
    
    def add_globals(self, context: Dict[str, Any]) -> None:
        """
        Add multiple global context variables.
        
        Args:
            context: Dictionary of context variables
        """
        self.global_context.update(context)


def create_template_middleware(
    app_name: str = "LLM Platform", 
    app_version: str = "1.0.0",
    global_context: Dict[str, Any] = None
) -> TemplateMiddleware:
    """
    Create a template middleware instance.
    
    Args:
        app_name: Application name
        app_version: Application version
        global_context: Global context variables for all templates
        
    Returns:
        Template middleware instance
    """
    return TemplateMiddleware(app_name, app_version, global_context)


# Default middleware instance
template_middleware = create_template_middleware()