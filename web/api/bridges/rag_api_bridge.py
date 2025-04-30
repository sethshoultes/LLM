#!/usr/bin/env python3
"""
Bridge between original api_extensions.py and new rag_controller.py.

This module provides a compatibility layer between the original RAG API handler
and the new controller-based implementation, allowing for a smooth transition.
"""

import logging
from typing import Dict, Any, Tuple, Optional, List

from web.api.controllers.rag import rag_controller

logger = logging.getLogger(__name__)


class RagApiBridge:
    """Bridge between original API handler and new controller implementation."""
    
    def __init__(self):
        """Initialize the bridge."""
        self.controller = rag_controller
    
    def handle_request(
        self,
        path: str,
        method: str,
        query_params: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None
    ) -> Tuple[int, Dict[str, Any]]:
        """Handle a RAG API request by delegating to the controller.
        
        Args:
            path: Request path
            method: HTTP method
            query_params: Optional query parameters
            body: Optional request body
            
        Returns:
            Tuple containing status code and response dict
        """
        try:
            # Delegate to controller
            return self.controller.handle_request(
                path=path,
                method=method,
                query_params=query_params,
                body=body
            )
        except Exception as e:
            logger.error(f"Error handling request: {str(e)}")
            return self.controller.format_error_response(
                "Internal server error",
                str(e),
                "internal_error",
                status_code=500
            )


# Create bridge instance to match original API handler
api_handler = RagApiBridge()