#!/usr/bin/env python3
"""
API responses for the LLM Platform.

Provides standardized response formatting for API endpoints.
"""

import logging
import time
from typing import Dict, List, Any, Optional, Union, Tuple

# Import from parent package
from web.api import logger

# HTTP status codes
HTTP_OK = 200
HTTP_CREATED = 201
HTTP_ACCEPTED = 202
HTTP_NO_CONTENT = 204
HTTP_BAD_REQUEST = 400
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_METHOD_NOT_ALLOWED = 405
HTTP_CONFLICT = 409
HTTP_INTERNAL_SERVER_ERROR = 500
HTTP_SERVICE_UNAVAILABLE = 503


def success_response(data: Any = None, message: str = None, 
                  meta: Dict[str, Any] = None, status: int = HTTP_OK) -> Tuple[int, Dict[str, Any]]:
    """
    Create a success response.
    
    Args:
        data: Response data
        message: Optional success message
        meta: Optional metadata
        status: HTTP status code
        
    Returns:
        Tuple of (status_code, response_dict)
    """
    response = {
        "success": True,
        "status": status
    }
    
    if data is not None:
        response["data"] = data
        
    if message:
        response["message"] = message
        
    if meta:
        response["meta"] = meta
    else:
        response["meta"] = {
            "timestamp": time.time(),
            "response_id": f"res_{int(time.time() * 1000)}"
        }
        
    return status, response


def error_response(error: Union[str, Exception], detail: str = None, 
                code: str = None, status: int = HTTP_BAD_REQUEST) -> Tuple[int, Dict[str, Any]]:
    """
    Create an error response.
    
    Args:
        error: Error message or exception
        detail: Detailed error explanation
        code: Error code for client handling
        status: HTTP status code
        
    Returns:
        Tuple of (status_code, response_dict)
    """
    # Format error from exception if needed
    error_message = str(error)
    error_type = error.__class__.__name__ if isinstance(error, Exception) else None
    
    response = {
        "success": False,
        "status": status,
        "error": error_message
    }
    
    if detail:
        response["detail"] = detail
        
    if code:
        response["code"] = code
    
    if error_type:
        response["error_type"] = error_type
        
    response["meta"] = {
        "timestamp": time.time(),
        "response_id": f"err_{int(time.time() * 1000)}"
    }
        
    return status, response


def not_found_response(resource_type: str, resource_id: str) -> Tuple[int, Dict[str, Any]]:
    """
    Create a not found response.
    
    Args:
        resource_type: Type of resource not found (e.g., "model", "document")
        resource_id: ID of the resource not found
        
    Returns:
        Tuple of (status_code, response_dict)
    """
    return error_response(
        error=f"{resource_type.capitalize()} not found",
        detail=f"The requested {resource_type} with ID '{resource_id}' could not be found",
        code="resource_not_found",
        status=HTTP_NOT_FOUND
    )