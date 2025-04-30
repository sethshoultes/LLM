#!/usr/bin/env python3
"""
API request/response schemas for the LLM Platform.

Provides schemas for validating API requests and standardizing responses.
"""

import logging
from typing import Dict, List, Any, Optional, Union, Tuple, Callable, Type

# Import from parent package
from web.api import logger

# Schema validation class
class Schema:
    """
    Base schema for request/response validation.
    
    Provides methods for validating data against a schema definition.
    """
    
    def __init__(self, **schema):
        """
        Initialize schema with field definitions.
        
        Args:
            **schema: Field definitions, where keys are field names and
                     values are either types or validation functions
        """
        self.schema = schema
    
    def validate(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate data against the schema.
        
        Args:
            data: Dictionary of data to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        if not isinstance(data, dict):
            return False, ["Data must be a dictionary"]
        
        errors = []
        
        # Check required fields and types
        for field_name, field_type in self.schema.items():
            # Skip optional fields
            if field_name.endswith('?'):
                required_field = field_name[:-1]
                required = False
            else:
                required_field = field_name
                required = True
            
            # Check if field exists
            if required_field not in data:
                if required:
                    errors.append(f"Field '{required_field}' is required")
                continue
            
            value = data[required_field]
            
            # Check type or custom validation
            if callable(field_type):
                # Custom validation function
                try:
                    result = field_type(value)
                    if result is not True:
                        errors.append(result)
                except Exception as e:
                    errors.append(f"Validation error for field '{required_field}': {str(e)}")
            elif isinstance(field_type, type):
                # Type validation
                if not isinstance(value, field_type):
                    errors.append(f"Field '{required_field}' must be of type {field_type.__name__}")
        
        return len(errors) == 0, errors


# Import specific schemas
from web.api.schemas.models import ModelListSchema, ModelSchema
from web.api.schemas.inference import GenerateRequestSchema, GenerateResponseSchema