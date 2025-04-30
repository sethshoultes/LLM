#!/usr/bin/env python3
"""
API schemas for models in the LLM Platform.

Provides schemas for model-related requests and responses.
"""

from typing import Dict, List, Any, Optional, Union

# Import from parent package
from web.api.schemas import Schema


class ModelSchema(Schema):
    """Schema for a model object."""
    
    def __init__(self):
        """Initialize schema."""
        super().__init__(
            id=str,
            name=str,
            path=str,
            type=str,
            parameters=dict,
            description=lambda x: isinstance(x, str) if x is not None else True,
            context_window=lambda x: isinstance(x, int) if x is not None else True,
            format=lambda x: isinstance(x, str) if x is not None else True
        )


class ModelListSchema(Schema):
    """Schema for a list of models."""
    
    def __init__(self):
        """Initialize schema."""
        super().__init__(
            models=list
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
        
        if is_valid and "models" in data:
            # Validate each model
            model_schema = ModelSchema()
            for i, model in enumerate(data["models"]):
                model_valid, model_errors = model_schema.validate(model)
                if not model_valid:
                    errors.append(f"Invalid model at index {i}: {', '.join(model_errors)}")
            
            is_valid = len(errors) == 0
        
        return is_valid, errors