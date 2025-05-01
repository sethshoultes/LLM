#!/usr/bin/env python3
"""
API schemas for inference in the LLM Platform.

Provides schemas for inference-related requests and responses.
"""

from typing import Dict, List, Any, Optional, Union

# Import from parent package
from web.api.schemas import Schema


class GenerateRequestSchema(Schema):
    """Schema for text generation request."""
    
    def __init__(self):
        """Initialize schema."""
        super().__init__(
            model=str,  # Required
            prompt=str,  # Required
            system_prompt=lambda x: isinstance(x, str) if x is not None else True,  # Optional
            temperature=lambda x: isinstance(x, (int, float)) and 0 <= x <= 2 if x is not None else True,  # Optional
            max_tokens=lambda x: isinstance(x, int) and x > 0 if x is not None else True,  # Optional
            top_p=lambda x: isinstance(x, (int, float)) and 0 <= x <= 1 if x is not None else True,  # Optional
            stop_sequences=lambda x: isinstance(x, list) if x is not None else True,  # Optional
            stream=lambda x: isinstance(x, bool) if x is not None else True  # Optional
        )
    
    def validate(self, data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate data against the schema.
        
        Args:
            data: Dictionary of data to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        is_valid, errors = super().validate(data)
        
        # Check required fields
        if "model" not in data or not data["model"]:
            errors.append("Field 'model' is required and must not be empty")
            is_valid = False
            
        if "prompt" not in data or not data["prompt"]:
            errors.append("Field 'prompt' is required and must not be empty")
            is_valid = False
        
        # Additional validation
        if "temperature" in data and (not isinstance(data["temperature"], (int, float)) or 
                                     data["temperature"] < 0 or 
                                     data["temperature"] > 2):
            errors.append("Field 'temperature' must be a number between 0 and 2")
            is_valid = False
            
        if "max_tokens" in data and (not isinstance(data["max_tokens"], int) or 
                                    data["max_tokens"] <= 0):
            errors.append("Field 'max_tokens' must be a positive integer")
            is_valid = False
            
        if "top_p" in data and (not isinstance(data["top_p"], (int, float)) or 
                               data["top_p"] < 0 or 
                               data["top_p"] > 1):
            errors.append("Field 'top_p' must be a number between 0 and 1")
            is_valid = False
        
        return is_valid, errors


class GenerateResponseSchema(Schema):
    """Schema for text generation response."""
    
    def __init__(self):
        """Initialize schema."""
        super().__init__(
            response=str,
            model=str,
            tokens_generated=int,
            time_taken=float,
            success=bool
        )


class ChatMessageSchema(Schema):
    """Schema for a chat message."""
    
    def __init__(self):
        """Initialize schema."""
        super().__init__(
            role=lambda x: x in ["system", "user", "assistant"],
            content=str
        )


class ChatRequestSchema(Schema):
    """Schema for chat request."""
    
    def __init__(self):
        """Initialize schema."""
        super().__init__(
            model=str,  # Required
            messages=list,  # Required
            system_prompt=lambda x: isinstance(x, str) if x is not None else True,  # Optional
            temperature=lambda x: isinstance(x, (int, float)) and 0 <= x <= 2 if x is not None else True,  # Optional
            max_tokens=lambda x: isinstance(x, int) and x > 0 if x is not None else True,  # Optional
            top_p=lambda x: isinstance(x, (int, float)) and 0 <= x <= 1 if x is not None else True,  # Optional
            stop_sequences=lambda x: isinstance(x, list) if x is not None else True,  # Optional
            stream=lambda x: isinstance(x, bool) if x is not None else True  # Optional
        )
    
    def validate(self, data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate data against the schema.
        
        Args:
            data: Dictionary of data to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        is_valid, errors = super().validate(data)
        
        # Check required fields
        if "model" not in data or not data["model"]:
            errors.append("Field 'model' is required and must not be empty")
            is_valid = False
            
        if "messages" not in data or not isinstance(data["messages"], list) or len(data["messages"]) == 0:
            errors.append("Field 'messages' is required and must be a non-empty array")
            is_valid = False
        else:
            # Validate each message
            message_schema = ChatMessageSchema()
            for i, message in enumerate(data["messages"]):
                if not isinstance(message, dict):
                    errors.append(f"Message at index {i} must be an object")
                    is_valid = False
                    continue
                    
                msg_valid, msg_errors = message_schema.validate(message)
                if not msg_valid:
                    errors.append(f"Invalid message at index {i}: {', '.join(msg_errors)}")
                    is_valid = False
        
        return is_valid, errors


class ChatResponseSchema(Schema):
    """Schema for chat response."""
    
    def __init__(self):
        """Initialize schema."""
        super().__init__(
            messages=list,
            model=str,
            tokens_generated=int,
            time_taken=float,
            success=bool
        )