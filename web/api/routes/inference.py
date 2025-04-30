#!/usr/bin/env python3
"""
API routes for inference in the LLM Platform.

Provides routes for text generation and inference using LLM models.
"""

import sys
import logging
from typing import Dict, List, Any, Optional, Union

# Import from parent package
from web.api import logger

# Import from web server modules
from web.router import Router

# Import schemas and controllers
from web.api.schemas.inference import GenerateRequestSchema, GenerateResponseSchema
from web.api.controllers.inference import InferenceController
from web.api.responses import success_response, error_response, not_found_response

# Import inference module
try:
    import minimal_inference_quiet as inference
    HAS_INFERENCE = True
except ImportError:
    logger.warning("minimal_inference_quiet.py not found. Inference routes will have limited functionality.")
    HAS_INFERENCE = False


def register_inference_routes(router: Router) -> Router:
    """
    Register inference-related API routes.
    
    Args:
        router: Router to register routes with
        
    Returns:
        Router with routes registered
    """
    # Create controller
    controller = InferenceController()
    
    # POST /api/generate - Generate text with a model
    @router.post("/generate")
    def generate_text(request, response):
        """Generate text using a model."""
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
            
            # Get request data
            request_data = request.body
            
            # Validate request
            schema = GenerateRequestSchema()
            is_valid, errors = schema.validate(request_data)
            
            if not is_valid:
                status, data = error_response(
                    error="Invalid request data",
                    detail="The request data is invalid",
                    code="invalid_request",
                    status=400
                )
                # Add validation errors
                data["errors"] = errors
                response.status_code = status
                response.json(data)
                return
            
            # Extract parameters
            model_path = request_data.get("model")
            prompt = request_data.get("prompt")
            system_prompt = request_data.get("system_prompt", "")
            temperature = float(request_data.get("temperature", 0.7))
            max_tokens = int(request_data.get("max_tokens", 500))
            top_p = float(request_data.get("top_p", 0.9))
            
            # Generate text
            result = inference.generate(
                model_path=model_path,
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p
            )
            
            # Check for error
            if "error" in result:
                status, data = error_response(
                    error=result["error"],
                    detail="Failed to generate text",
                    code="generation_error",
                    status=500
                )
                response.status_code = status
                response.json(data)
                return
            
            # Return result
            status, data = success_response(
                data={
                    "response": result["response"],
                    "model": model_path,
                    "tokens_generated": result.get("tokens_generated", 0),
                    "time_taken": result.get("time_taken", 0)
                },
                message="Text generated successfully"
            )
            response.status_code = status
            response.json(data)
        except Exception as e:
            logger.error(f"Error generating text: {e}")
            status, data = error_response(
                error=e,
                detail="Failed to generate text",
                code="generation_error",
                status=500
            )
            response.status_code = status
            response.json(data)
    
    # POST /api/chat - Chat with a model
    @router.post("/chat")
    def chat(request, response):
        """Chat with a model."""
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
            
            # Get request data
            request_data = request.body
            
            # Extract parameters
            model_path = request_data.get("model")
            messages = request_data.get("messages", [])
            system_prompt = request_data.get("system_prompt", "")
            temperature = float(request_data.get("temperature", 0.7))
            max_tokens = int(request_data.get("max_tokens", 500))
            top_p = float(request_data.get("top_p", 0.9))
            
            # Validate required parameters
            if not model_path:
                status, data = error_response(
                    error="Model path is required",
                    detail="The 'model' field is required",
                    code="missing_model",
                    status=400
                )
                response.status_code = status
                response.json(data)
                return
            
            if not messages:
                status, data = error_response(
                    error="Messages are required",
                    detail="The 'messages' field is required and must be a non-empty array",
                    code="missing_messages",
                    status=400
                )
                response.status_code = status
                response.json(data)
                return
            
            # Format prompt from messages
            last_user_message = next((m["content"] for m in reversed(messages) 
                                     if m.get("role") == "user"), None)
            
            if not last_user_message:
                status, data = error_response(
                    error="No user message found",
                    detail="At least one message with role 'user' is required",
                    code="missing_user_message",
                    status=400
                )
                response.status_code = status
                response.json(data)
                return
            
            # Generate response
            result = inference.generate(
                model_path=model_path,
                prompt=last_user_message,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p
            )
            
            # Check for error
            if "error" in result:
                status, data = error_response(
                    error=result["error"],
                    detail="Failed to generate chat response",
                    code="chat_error",
                    status=500
                )
                response.status_code = status
                response.json(data)
                return
            
            # Add assistant response to messages
            messages.append({
                "role": "assistant",
                "content": result["response"]
            })
            
            # Return result
            status, data = success_response(
                data={
                    "messages": messages,
                    "model": model_path,
                    "tokens_generated": result.get("tokens_generated", 0),
                    "time_taken": result.get("time_taken", 0)
                },
                message="Chat response generated successfully"
            )
            response.status_code = status
            response.json(data)
        except Exception as e:
            logger.error(f"Error in chat: {e}")
            status, data = error_response(
                error=e,
                detail="Failed to generate chat response",
                code="chat_error",
                status=500
            )
            response.status_code = status
            response.json(data)
    
    # Return router
    return router