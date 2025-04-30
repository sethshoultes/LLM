#!/usr/bin/env python3
"""
API controllers for inference in the LLM Platform.

Provides controllers for inference-related endpoints.
"""

import logging
import time
from typing import Dict, List, Any, Optional, Union

# Import from parent package
from web.api.controllers import Controller
from web.api import logger

# Import inference module
try:
    import minimal_inference_quiet as inference
    HAS_INFERENCE = True
except ImportError:
    logger.warning("minimal_inference_quiet.py not found. Inference controllers will have limited functionality.")
    HAS_INFERENCE = False


class InferenceController(Controller):
    """Controller for inference-related endpoints."""
    
    def __init__(self):
        """Initialize controller."""
        super().__init__()
    
    def generate_text(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate text using a model.
        
        Args:
            request_data: Dictionary with request data
            
        Returns:
            Dictionary with generated text and metadata
            
        Raises:
            RuntimeError: If inference module is not available
            ValueError: If required parameters are missing
        """
        if not HAS_INFERENCE:
            raise RuntimeError("Inference module not available")
        
        # Extract parameters
        model_path = request_data.get("model")
        prompt = request_data.get("prompt")
        system_prompt = request_data.get("system_prompt", "")
        temperature = float(request_data.get("temperature", 0.7))
        max_tokens = int(request_data.get("max_tokens", 500))
        top_p = float(request_data.get("top_p", 0.9))
        
        # Validate required parameters
        if not model_path:
            raise ValueError("Model path is required")
        
        if not prompt:
            raise ValueError("Prompt is required")
        
        # Add a timing measurement
        start_time = time.time()
        
        # Generate text
        result = inference.generate(
            model_path=model_path,
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p
        )
        
        # Calculate elapsed time
        elapsed_time = time.time() - start_time
        
        # Check for error
        if "error" in result:
            raise RuntimeError(result["error"])
        
        # Add extra metadata
        result["model"] = model_path
        result["elapsed_time"] = elapsed_time
        
        return result
    
    def chat(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Chat with a model.
        
        Args:
            request_data: Dictionary with request data
            
        Returns:
            Dictionary with chat response and metadata
            
        Raises:
            RuntimeError: If inference module is not available
            ValueError: If required parameters are missing
        """
        if not HAS_INFERENCE:
            raise RuntimeError("Inference module not available")
        
        # Extract parameters
        model_path = request_data.get("model")
        messages = request_data.get("messages", [])
        system_prompt = request_data.get("system_prompt", "")
        temperature = float(request_data.get("temperature", 0.7))
        max_tokens = int(request_data.get("max_tokens", 500))
        top_p = float(request_data.get("top_p", 0.9))
        
        # Validate required parameters
        if not model_path:
            raise ValueError("Model path is required")
        
        if not messages:
            raise ValueError("Messages are required")
        
        # Format prompt from messages
        last_user_message = next((m["content"] for m in reversed(messages) 
                                 if m.get("role") == "user"), None)
        
        if not last_user_message:
            raise ValueError("No user message found")
        
        # Add a timing measurement
        start_time = time.time()
        
        # Generate response
        result = inference.generate(
            model_path=model_path,
            prompt=last_user_message,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p
        )
        
        # Calculate elapsed time
        elapsed_time = time.time() - start_time
        
        # Check for error
        if "error" in result:
            raise RuntimeError(result["error"])
        
        # Add assistant response to messages
        messages.append({
            "role": "assistant",
            "content": result["response"]
        })
        
        # Return result
        return {
            "messages": messages,
            "response": result["response"],
            "model": model_path,
            "tokens_generated": result.get("tokens_generated", 0),
            "time_taken": result.get("time_taken", elapsed_time)
        }
    
    def handle_request(self, request) -> Dict[str, Any]:
        """
        Handle an inference-related API request.
        
        Args:
            request: Request object
            
        Returns:
            Response data dictionary
        """
        # Get path to determine action
        path = request.path if hasattr(request, "path") else ""
        
        if path.endswith("/chat"):
            # Chat endpoint
            return self.chat(request.body)
        else:
            # Generate endpoint
            return self.generate_text(request.body)