#!/usr/bin/env python3
"""
Router module for the LLM Platform web server.

Provides clean routing with support for path parameters, route grouping,
and HTTP method handling.
"""

import re
import logging
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
logger = get_logger("web.router")


class Route:
    """
    Represents a route in the web application.
    
    Stores information about a route, including path pattern, HTTP method,
    handler function, and path parameter parsing.
    """
    
    def __init__(self, path: str, method: str, handler: Callable, name: str = None):
        """
        Initialize a route.
        
        Args:
            path: URL path pattern, may include parameters like /users/{id}
            method: HTTP method (GET, POST, etc.)
            handler: Function to handle the route
            name: Optional name for the route
        """
        self.path = path
        self.method = method.upper()
        self.handler = handler
        self.name = name or handler.__name__
        
        # Prepare path pattern for matching
        self.params = []
        self.pattern = self._create_pattern(path)
    
    def _create_pattern(self, path):
        """
        Create a regex pattern for path matching.
        
        Args:
            path: URL path pattern
            
        Returns:
            Compiled regex pattern for matching URLs
        """
        # Escape special regex characters
        pattern = re.escape(path)
        
        # Extract parameter names and build the pattern
        param_pattern = r'\\{([^}]+)\\}'
        matches = re.finditer(param_pattern, pattern)
        
        for match in matches:
            param_name = match.group(1)
            self.params.append(param_name)
            
            # Replace {param} with regex group
            pattern = pattern.replace(f'\\{{{param_name}\\}}', '([^/]+)')
            
        # Ensure pattern matches the entire path
        pattern = f'^{pattern}$'
        return re.compile(pattern)
    
    def match(self, path: str):
        """
        Check if the path matches this route.
        
        Args:
            path: URL path to match
            
        Returns:
            Dictionary of path parameters if match, None otherwise
        """
        match = self.pattern.match(path)
        if not match:
            return None
        
        # Extract path parameters
        params = {}
        if self.params:
            values = match.groups()
            for i, param in enumerate(self.params):
                params[param] = values[i]
        
        return params


class Router:
    """
    Router for handling HTTP requests.
    
    Maps URLs to handler functions with support for different HTTP methods,
    path parameters, and route groups.
    """
    
    def __init__(self):
        """Initialize the router."""
        self.routes = []
        self.prefix = ""
    
    def add_route(self, method: str, path: str, handler: Callable, name: str = None):
        """
        Add a route to the router.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            path: URL path, may include parameters like /users/{id}
            handler: Function to handle the route
            name: Optional name for the route
            
        Returns:
            Added route
        """
        # Apply prefix if set
        full_path = f"{self.prefix}{path}"
        
        # Create and add route
        route = Route(full_path, method, handler, name)
        self.routes.append(route)
        
        logger.debug(f"Added route: {method} {full_path} -> {handler.__name__}")
        return route
    
    def get(self, path: str, name: str = None):
        """Decorator for adding GET routes."""
        def decorator(handler):
            self.add_route('GET', path, handler, name)
            return handler
        return decorator
    
    def post(self, path: str, name: str = None):
        """Decorator for adding POST routes."""
        def decorator(handler):
            self.add_route('POST', path, handler, name)
            return handler
        return decorator
    
    def put(self, path: str, name: str = None):
        """Decorator for adding PUT routes."""
        def decorator(handler):
            self.add_route('PUT', path, handler, name)
            return handler
        return decorator
    
    def delete(self, path: str, name: str = None):
        """Decorator for adding DELETE routes."""
        def decorator(handler):
            self.add_route('DELETE', path, handler, name)
            return handler
        return decorator
    
    def options(self, path: str, name: str = None):
        """Decorator for adding OPTIONS routes."""
        def decorator(handler):
            self.add_route('OPTIONS', path, handler, name)
            return handler
        return decorator
    
    def all(self, path: str, name: str = None):
        """Decorator for adding routes for all HTTP methods."""
        def decorator(handler):
            for method in ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']:
                self.add_route(method, path, handler, name)
            return handler
        return decorator
    
    def group(self, prefix: str):
        """
        Create a route group with a common prefix.
        
        Args:
            prefix: Common prefix for all routes in the group
            
        Returns:
            New router instance with the prefix
        """
        # Create new router with combined prefix
        group_router = Router()
        group_router.prefix = f"{self.prefix}{prefix}"
        
        # Add a method to merge routes back to the parent
        def merge():
            self.routes.extend(group_router.routes)
            return self
        
        group_router.merge = merge
        return group_router
    
    def include(self, router):
        """
        Include routes from another router.
        
        Args:
            router: Router instance to include
            
        Returns:
            Self for chaining
        """
        self.routes.extend(router.routes)
        return self
    
    def find_handler(self, path: str, method: str):
        """
        Find a handler for the given path and method.
        
        Args:
            path: URL path
            method: HTTP method
            
        Returns:
            Handler function with path params injected, or None if not found
        """
        method = method.upper()
        
        for route in self.routes:
            if route.method != method:
                continue
                
            params = route.match(path)
            if params is not None:
                # Return a wrapper that injects path parameters
                original_handler = route.handler
                
                def handler_with_params(request, response):
                    # Add path parameters to request
                    request.path_params = params
                    # Call the actual handler
                    return original_handler(request, response)
                
                return handler_with_params
        
        return None
    
    def url_for(self, name: str, **params):
        """
        Generate URL for a named route.
        
        Args:
            name: Route name
            **params: Path parameters
            
        Returns:
            URL string, or None if route not found
        """
        for route in self.routes:
            if route.name == name:
                # Replace parameters in path
                url = route.path
                for param, value in params.items():
                    url = url.replace(f"{{{param}}}", str(value))
                return url
        
        return None


# For testing
if __name__ == "__main__":
    router = Router()
    
    # Add some test routes
    @router.get("/")
    def index(request, response):
        return "Index page"
    
    @router.get("/users/{id}")
    def get_user(request, response):
        user_id = request.path_params['id']
        return f"User {user_id}"
    
    # Test route group
    api = router.group("/api")
    
    @api.get("/items")
    def get_items(request, response):
        return "Items list"
    
    @api.post("/items")
    def create_item(request, response):
        return "Create item"
    
    # Merge api routes back to main router
    api.merge()
    
    # Test URL generation
    print(router.url_for("get_user", id=123))  # Should print "/users/123"
    
    # Test route matching
    handler = router.find_handler("/users/123", "GET")
    print(handler is not None)  # Should be True
    
    handler = router.find_handler("/api/items", "POST")
    print(handler is not None)  # Should be True
    
    handler = router.find_handler("/not-found", "GET")
    print(handler is None)  # Should be True