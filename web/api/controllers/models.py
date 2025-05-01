#!/usr/bin/env python3
"""
API controllers for models in the LLM Platform.

Provides controllers for model-related endpoints.
"""

from typing import Dict, List, Any, Optional, Union

# Import from parent package
from web.api.controllers import Controller
from web.api import logger

# Import inference module
try:
    import minimal_inference_quiet as inference
    HAS_INFERENCE = True
except ImportError:
    logger.warning("minimal_inference_quiet.py not found. Model controllers will have limited functionality.")
    HAS_INFERENCE = False


class ModelsController(Controller):
    """Controller for model-related endpoints."""
    
    def __init__(self):
        """Initialize controller."""
        super().__init__()
    
    def list_models(self) -> Dict[str, Any]:
        """
        List all available models.
        
        Returns:
            Dictionary with models information
        
        Raises:
            RuntimeError: If inference module is not available
        """
        if not HAS_INFERENCE:
            raise RuntimeError("Inference module not available")
        
        # Get models from inference module
        models = inference.list_models()
        
        return {
            "models": models,
            "count": len(models)
        }
    
    def get_model(self, model_id: str) -> Dict[str, Any]:
        """
        Get a specific model by ID.
        
        Args:
            model_id: ID of the model to get
            
        Returns:
            Dictionary with model information
            
        Raises:
            RuntimeError: If inference module is not available
            ValueError: If model is not found
        """
        if not HAS_INFERENCE:
            raise RuntimeError("Inference module not available")
        
        # Get models from inference module
        models = inference.list_models()
        
        # Find the requested model
        model = next((m for m in models if m.get("id") == model_id), None)
        
        if not model:
            raise ValueError(f"Model with ID '{model_id}' not found")
        
        return model
    
    def handle_request(self, request) -> Dict[str, Any]:
        """
        Handle a model-related API request.
        
        Args:
            request: Request object
            
        Returns:
            Response data dictionary
        """
        # Get model ID if provided
        model_id = request.path_params.get("model_id") if hasattr(request, "path_params") else None
        
        if model_id:
            # Get specific model
            return self.get_model(model_id)
        else:
            # List all models
            return self.list_models()