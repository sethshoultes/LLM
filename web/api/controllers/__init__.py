#!/usr/bin/env python3
"""
API controllers for the LLM Platform.

Provides controller classes for handling API business logic,
separating it from the route handling code.
"""

from typing import Dict, List, Any, Optional, Union, Tuple

# Import from parent package

# Base controller class
class Controller:
    """
    Base controller for API endpoints.
    
    Provides common methods for handling API requests and generating responses.
    """
    
    def __init__(self):
        """Initialize controller."""
        pass
    
    def handle_request(self, request: Any) -> Dict[str, Any]:
        """
        Handle an API request.
        
        Args:
            request: Request object
            
        Returns:
            Response data dictionary
            
        Raises:
            NotImplementedError: This method must be implemented by subclasses
        """
        raise NotImplementedError("Controller.handle_request must be implemented by subclasses")
    
    def validate_request(self, request: Any, schema: Any) -> Tuple[bool, List[str]]:
        """
        Validate a request against a schema.
        
        Args:
            request: Request object
            schema: Schema to validate against
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        if hasattr(schema, 'validate'):
            return schema.validate(request.body if hasattr(request, 'body') else {})
        return True, []
    
    def format_success_response(
        self, 
        data: Any, 
        message: Optional[str] = None, 
        meta: Optional[Dict[str, Any]] = None,
        status_code: int = 200
    ) -> Tuple[int, Dict[str, Any]]:
        """Format a successful API response.
        
        Args:
            data: The response data
            message: Optional message
            meta: Optional metadata
            status_code: HTTP status code (default: 200)
            
        Returns:
            Tuple containing status code and response dict
        """
        response = {
            "status": "success",
            "data": data,
        }
        
        if message:
            response["message"] = message
            
        if meta:
            response["meta"] = meta
        
        return status_code, response
    
    def format_error_response(
        self, 
        error: str, 
        detail: Optional[str] = None, 
        code: Optional[str] = None,
        status_code: int = 400
    ) -> Tuple[int, Dict[str, Any]]:
        """Format an error API response.
        
        Args:
            error: Error message
            detail: Optional error details
            code: Optional error code
            status_code: HTTP status code (default: 400)
            
        Returns:
            Tuple containing status code and response dict
        """
        response = {
            "status": "error",
            "error": error
        }
        
        if detail:
            response["detail"] = detail
            
        if code:
            response["code"] = code
        
        return status_code, response


# Import specific controllers