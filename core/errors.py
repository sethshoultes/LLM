#!/usr/bin/env python3
"""
Error handling module for the LLM Platform.

Provides standardized error handling, custom exception classes,
and utilities for error formatting and reporting.
"""

import traceback
import json
from typing import Dict, Any, Optional, Union, List, Tuple

from core.logging import get_logger
from core.config import is_debug

# Get logger for this module
logger = get_logger("errors")

class LLMError(Exception):
    """Base exception class for all LLM Platform errors."""
    
    def __init__(self, message: str, code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        """
        Initialize an LLM error.
        
        Args:
            message: Error message
            code: Error code for programmatic handling
            details: Additional error details
        """
        super().__init__(message)
        self.message = message
        self.code = code or self.__class__.__name__
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert error to a dictionary representation.
        
        Returns:
            Dictionary containing error information
        """
        error_dict = {
            "error": self.message,
            "error_type": self.__class__.__name__,
            "code": self.code
        }
        
        if self.details:
            error_dict["details"] = self.details
        
        if is_debug():
            error_dict["traceback"] = traceback.format_exc()
            
        return error_dict
    
    def to_json(self) -> str:
        """
        Convert error to JSON string.
        
        Returns:
            JSON string representation of the error
        """
        return json.dumps(self.to_dict(), indent=2)

class ConfigError(LLMError):
    """Error raised when there's a configuration issue."""
    pass

class PathError(LLMError):
    """Error raised when there's a path resolution issue."""
    pass

class ModelError(LLMError):
    """Base class for model-related errors."""
    pass

class ModelNotFoundError(ModelError):
    """Error raised when a model cannot be found."""
    pass

class ModelLoadError(ModelError):
    """Error raised when a model cannot be loaded."""
    pass

class ModelInferenceError(ModelError):
    """Error raised when model inference fails."""
    pass

class RAGError(LLMError):
    """Base class for RAG-related errors."""
    pass

class DocumentError(RAGError):
    """Error raised for document-related issues."""
    pass

class SearchError(RAGError):
    """Error raised when search operations fail."""
    pass

class APIError(LLMError):
    """Base class for API-related errors."""
    
    def __init__(self, message: str, status_code: int = 500, code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        """
        Initialize an API error.
        
        Args:
            message: Error message
            status_code: HTTP status code
            code: Error code for programmatic handling
            details: Additional error details
        """
        super().__init__(message, code, details)
        self.status_code = status_code
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert API error to a dictionary representation.
        
        Returns:
            Dictionary containing error information
        """
        error_dict = super().to_dict()
        error_dict["status"] = self.status_code
        return error_dict

class BadRequestError(APIError):
    """Error raised for invalid requests."""
    
    def __init__(self, message: str, code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        """Initialize a bad request error with status code 400."""
        super().__init__(message, 400, code, details)

class NotFoundError(APIError):
    """Error raised when a requested resource is not found."""
    
    def __init__(self, message: str, code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        """Initialize a not found error with status code 404."""
        super().__init__(message, 404, code, details)

class ServerError(APIError):
    """Error raised for server-side issues."""
    
    def __init__(self, message: str, code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        """Initialize a server error with status code 500."""
        super().__init__(message, 500, code, details)

class ErrorHandler:
    """Utility class for handling and formatting errors."""
    
    @staticmethod
    def format_error(error: Exception, include_traceback: bool = False) -> str:
        """
        Format an error message with optional traceback.
        
        Args:
            error: The exception to format
            include_traceback: Whether to include traceback
            
        Returns:
            Formatted error message
        """
        error_type = type(error).__name__
        error_message = str(error)
        
        formatted = f"Error: {error_type} - {error_message}"
        
        if include_traceback:
            tb = traceback.format_exc()
            formatted += f"\n\nTraceback:\n{tb}"
            
        return formatted
    
    @staticmethod
    def log_error(error: Exception, context: str = "", include_traceback: bool = True) -> None:
        """
        Log an error with consistent formatting.
        
        Args:
            error: The exception to log
            context: Optional context information
            include_traceback: Whether to include traceback in debug logs
        """
        error_type = type(error).__name__
        error_message = str(error)
        
        if context:
            logger.error(f"[{context}] {error_type}: {error_message}")
        else:
            logger.error(f"{error_type}: {error_message}")
        
        if include_traceback and is_debug():
            logger.debug(f"Traceback for error in {context or 'unknown context'}:\n{traceback.format_exc()}")
    
    @staticmethod
    def handle_api_error(error: Exception, context: str = "") -> Tuple[int, Dict[str, Any]]:
        """
        Handle an API error and return appropriate response.
        
        Args:
            error: The exception to handle
            context: Optional context information
            
        Returns:
            Tuple of (status_code, response_dict)
        """
        # Log the error
        ErrorHandler.log_error(error, context)
        
        # If it's an APIError, use its status and format
        if isinstance(error, APIError):
            return error.status_code, error.to_dict()
        
        # If it's an LLMError, use its format with 500 status
        if isinstance(error, LLMError):
            response = error.to_dict()
            return 500, response
        
        # For other exceptions, create a generic server error
        error_type = type(error).__name__
        error_message = str(error)
        
        response = {
            "error": error_message,
            "error_type": error_type,
            "status": 500,
            "context": context
        }
        
        if is_debug():
            response["traceback"] = traceback.format_exc()
        
        return 500, response
    
    @staticmethod
    def format_response_error(status_code: int, message: str, code: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Format an error response for API endpoints.
        
        Args:
            status_code: HTTP status code
            message: Error message
            code: Error code for programmatic handling
            details: Additional error details
            
        Returns:
            Formatted error response dictionary
        """
        response = {
            "error": message,
            "status": status_code,
            "code": code or "error"
        }
        
        if details:
            response["details"] = details
            
        if is_debug():
            response["debug_info"] = {
                "timestamp": traceback.format_stack()[-2].strip(),
            }
            
        return response

# Convenience functions
def format_error(error: Exception, include_traceback: bool = False) -> str:
    """Format an error message with optional traceback."""
    return ErrorHandler.format_error(error, include_traceback)

def log_error(error: Exception, context: str = "", include_traceback: bool = True) -> None:
    """Log an error with consistent formatting."""
    ErrorHandler.log_error(error, context, include_traceback)

def handle_api_error(error: Exception, context: str = "") -> Tuple[int, Dict[str, Any]]:
    """Handle an API error and return appropriate response."""
    return ErrorHandler.handle_api_error(error, context)

def format_response_error(status_code: int, message: str, code: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Format an error response for API endpoints."""
    return ErrorHandler.format_response_error(status_code, message, code, details)