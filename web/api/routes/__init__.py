#!/usr/bin/env python3
"""
API routes for the LLM Platform.

Provides RESTful API endpoint registration and routing logic.
"""

import logging
from typing import Dict, List, Any, Optional, Union, Tuple

# Import from parent package
from web.api import logger

# Import from web server modules
from web.router import Router

# Import route modules
from web.api.routes.models import register_model_routes
from web.api.routes.inference import register_inference_routes
from web.api.routes.rag import register_rag_routes


def register_api_routes(router: Router, api_prefix: str = "/api") -> Router:
    """
    Register all API routes with the given router.
    
    Args:
        router: Router instance to register routes with
        api_prefix: Prefix for all API routes
        
    Returns:
        Router instance with API routes registered
    """
    # Create API route group
    api_group = router.group(api_prefix)
    
    # Register API routes
    register_model_routes(api_group)
    register_inference_routes(api_group)
    register_rag_routes(api_group)
    
    # Register API version info endpoint
    @api_group.get("/version")
    def api_version(request, response):
        """Get API version information."""
        response.json({
            "version": "1.0.0",
            "name": "LLM Platform API",
            "environment": "development"
        })
    
    # Merge routes back to main router
    api_group.merge()
    
    return router