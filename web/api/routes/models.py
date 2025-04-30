#!/usr/bin/env python3
"""
API routes for models in the LLM Platform.

Provides routes for listing, getting, and managing models.
"""

from typing import Dict, List, Any, Optional, Union

# Import from parent package
from web.api import logger

# Import from web server modules
from web.router import Router

# Import schemas and controllers
from web.api.controllers.models import ModelsController
from web.api.responses import success_response, error_response, not_found_response

# Import inference module
try:
    import minimal_inference_quiet as inference
    HAS_INFERENCE = True
except ImportError:
    logger.warning("minimal_inference_quiet.py not found. Model routes will have limited functionality.")
    HAS_INFERENCE = False


def register_model_routes(router: Router) -> Router:
    """
    Register model-related API routes.
    
    Args:
        router: Router to register routes with
        
    Returns:
        Router with routes registered
    """
    # Create controller
    controller = ModelsController()
    
    # GET /api/models - List all models
    @router.get("/models")
    def list_models(request, response):
        """List all available models."""
        try:
            if not HAS_INFERENCE:
                status, data = error_response(
                    "Inference module not available",
                    "The minimal_inference_quiet.py module could not be imported",
                    "inference_module_missing",
                    500
                )
                response.status_code = status
                response.json(data)
                return
            
            # Get models from inference module
            models = inference.list_models()
            
            # Return response
            status, data = success_response(
                data={"models": models},
                message="Models retrieved successfully",
                meta={
                    "count": len(models),
                    "filters": request.query_params
                }
            )
            response.status_code = status
            response.json(data)
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            status, data = error_response(
                error=e,
                detail="Failed to list models",
                code="model_list_error",
                status=500
            )
            response.status_code = status
            response.json(data)
    
    # GET /api/models/{model_id} - Get a specific model
    @router.get("/models/{model_id}")
    def get_model(request, response):
        """Get a specific model by ID."""
        try:
            if not HAS_INFERENCE:
                status, data = error_response(
                    "Inference module not available",
                    "The minimal_inference_quiet.py module could not be imported",
                    "inference_module_missing",
                    500
                )
                response.status_code = status
                response.json(data)
                return
            
            # Get model ID from path parameters
            model_id = request.path_params.get("model_id")
            
            # Get models from inference module
            models = inference.list_models()
            
            # Find the requested model
            model = next((m for m in models if m.get("id") == model_id), None)
            
            if not model:
                status, data = not_found_response("model", model_id)
                response.status_code = status
                response.json(data)
                return
            
            # Return response
            status, data = success_response(
                data=model,
                message="Model retrieved successfully"
            )
            response.status_code = status
            response.json(data)
        except Exception as e:
            logger.error(f"Error getting model: {e}")
            status, data = error_response(
                error=e,
                detail=f"Failed to get model with ID '{model_id}'",
                code="model_retrieval_error",
                status=500
            )
            response.status_code = status
            response.json(data)
    
    # Return router
    return router