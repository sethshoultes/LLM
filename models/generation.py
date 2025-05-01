#!/usr/bin/env python3
"""
Text generation module for the LLM Platform.

Provides unified text generation functionality for different model types.
"""

import time
import traceback
from typing import Dict, List, Optional, Any, Union, Tuple

from core.logging import get_logger
from core.utils import timer

from models.registry import get_model_info
from models.loader import load_model, is_model_loaded, get_loaded_model
from models.formatter import format_prompt, format_conversation

# Get logger for this module
logger = get_logger("models.generation")

class TextGenerator:
    """
    Unified text generation for different model types.
    
    Handles text generation with different model formats and types
    with consistent interfaces and outputs.
    """
    
    def __init__(self):
        """Initialize the text generator with default settings."""
        self.default_settings = {
            "max_tokens": 512,
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 40,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
            "stop": None
        }
    
    @timer
    def generate_text(self, model_path: str, prompt: str, system_prompt: str = "", **kwargs) -> Dict[str, Any]:
        """
        Generate text using the specified model.
        
        Args:
            model_path: Path to the model
            prompt: User prompt
            system_prompt: Optional system prompt/instructions
            **kwargs: Additional generation settings
            
        Returns:
            Dictionary containing the generated text and metadata
            
        Raises:
            ModelNotFoundError: If model not found
            ModelLoadError: If model loading fails
            ModelInferenceError: If text generation fails
        """
        # Check if model exists
        model_info = get_model_info(model_path)
        if not model_info:
            raise ModelNotFoundError(f"Model not found: {model_path}")
        
        # Load model if not already loaded
        if not is_model_loaded(model_path):
            try:
                load_model(model_path)
            except Exception as e:
                raise ModelLoadError(f"Failed to load model: {str(e)}")
        
        # Get model instance
        model_instance = get_loaded_model(model_path)
        if not model_instance:
            raise ModelLoadError(f"Failed to retrieve loaded model: {model_path}")
        
        # Format the prompt
        formatted_prompt = format_prompt(model_path, prompt, system_prompt)
        logger.debug(f"Formatted prompt: {formatted_prompt[:100]}...")
        
        # Combine default settings with overrides
        settings = dict(self.default_settings)
        settings.update(kwargs)
        
        # Generate based on model type
        model_type = model_instance.get("type")
        
        if model_type == "llama.cpp":
            return self._generate_with_llamacpp(model_instance, formatted_prompt, model_path, settings)
        elif model_type == "transformers":
            return self._generate_with_transformers(model_instance, formatted_prompt, model_path, settings)
        else:
            raise ModelInferenceError(f"Unsupported model type for generation: {model_type}")
    
    def _generate_with_llamacpp(self, model_instance: Dict[str, Any], 
                              formatted_prompt: str, model_path: str, 
                              settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate text using a llama.cpp model.
        
        Args:
            model_instance: Loaded model instance
            formatted_prompt: Formatted prompt string
            model_path: Path to the model
            settings: Generation settings
            
        Returns:
            Dictionary containing the generated text and metadata
            
        Raises:
            ModelInferenceError: If text generation fails
        """
        try:
            model = model_instance["model"]
            
            # Extract generation parameters
            max_tokens = settings.get("max_tokens", 512)
            temperature = settings.get("temperature", 0.7)
            top_p = settings.get("top_p", 0.95)
            top_k = settings.get("top_k", 40)
            frequency_penalty = settings.get("frequency_penalty", 0.0)
            presence_penalty = settings.get("presence_penalty", 0.0)
            stop = settings.get("stop")
            
            if stop is None:
                stop = ["</s>", "[/INST]", "### User:"]  # Common stop tokens
            
            # Build the parameters dictionary
            generation_params = {
                "prompt": formatted_prompt,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "top_k": top_k,
                "frequency_penalty": frequency_penalty,
                "presence_penalty": presence_penalty,
                "stop": stop,
            }
            
            # Generate response
            start_time = time.time()
            response = model.create_completion(**generation_params)
            end_time = time.time()
            
            # Extract the generated text
            generated_text = response["choices"][0]["text"].strip()
            
            # Return response with metadata
            result = {
                "response": generated_text,
                "model": model_path,
                "model_type": model_instance.get("type", "unknown"),
                "model_format": model_instance.get("model_format", "unknown"),
                "time_taken": round(end_time - start_time, 2),
                "tokens_generated": response["usage"]["completion_tokens"],
                "total_tokens": response["usage"]["total_tokens"],
                "settings": {k: v for k, v in settings.items() if k != "stop"}
            }
            
            return result
        except Exception as e:
            error_msg = f"Error generating text with llama.cpp: {str(e)}"
            logger.error(error_msg)
            logger.debug(traceback.format_exc())
            raise ModelInferenceError(error_msg)
    
    def _generate_with_transformers(self, model_instance: Dict[str, Any], 
                                 formatted_prompt: str, model_path: str, 
                                 settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate text using a transformers model.
        
        Args:
            model_instance: Loaded model instance
            formatted_prompt: Formatted prompt string
            model_path: Path to the model
            settings: Generation settings
            
        Returns:
            Dictionary containing the generated text and metadata
            
        Raises:
            ModelInferenceError: If text generation fails
        """
        try:
            pipeline = model_instance["pipeline"]
            tokenizer = model_instance["tokenizer"]
            
            # Extract generation parameters
            max_tokens = settings.get("max_tokens", 512)
            temperature = settings.get("temperature", 0.7)
            top_p = settings.get("top_p", 0.95)
            top_k = settings.get("top_k", 40)
            frequency_penalty = settings.get("frequency_penalty", 0.0)
            
            # Prepare generation parameters
            gen_kwargs = {
                "max_new_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "top_k": top_k,
                "repetition_penalty": 1.0 + frequency_penalty,  # Convert to repetition penalty format
                "do_sample": temperature > 0.0,
            }
            
            # Generate text
            start_time = time.time()
            response = pipeline(
                formatted_prompt,
                **gen_kwargs
            )
            end_time = time.time()
            
            # Extract the generated text
            if isinstance(response, list) and len(response) > 0:
                # Extracting the generated text and removing the prompt
                generated_text = response[0]["generated_text"]
                
                # Remove the prompt part from the response if possible
                if generated_text.startswith(formatted_prompt):
                    generated_text = generated_text[len(formatted_prompt):].strip()
                
                # Clean up common artifacts
                if generated_text.startswith(":") or generated_text.startswith("\n"):
                    generated_text = generated_text.lstrip(":\n ")
            else:
                generated_text = "No response generated"
            
            # Count tokens for stats
            try:
                input_tokens = len(tokenizer.encode(formatted_prompt))
                output_tokens = len(tokenizer.encode(generated_text))
            except:
                input_tokens = 0
                output_tokens = 0
            
            # Return response with metadata
            result = {
                "response": generated_text,
                "model": model_path,
                "model_type": model_instance.get("type", "unknown"),
                "model_format": model_instance.get("model_format", "unknown"),
                "time_taken": round(end_time - start_time, 2),
                "tokens_generated": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                "settings": {k: v for k, v in settings.items() if k != "stop"}
            }
            
            return result
        except Exception as e:
            error_msg = f"Error generating text with transformers: {str(e)}"
            logger.error(error_msg)
            logger.debug(traceback.format_exc())
            raise ModelInferenceError(error_msg)
    
    @timer
    def generate_with_history(self, model_path: str, messages: List[Dict[str, str]], 
                           system_prompt: str = "", **kwargs) -> Dict[str, Any]:
        """
        Generate text using conversation history.
        
        Args:
            model_path: Path to the model
            messages: List of conversation messages with 'role' and 'content'
            system_prompt: Optional system prompt/instructions
            **kwargs: Additional generation settings
            
        Returns:
            Dictionary containing the generated text and metadata
            
        Raises:
            ModelNotFoundError: If model not found
            ModelLoadError: If model loading fails
            ModelInferenceError: If text generation fails
        """
        # Check if model exists
        model_info = get_model_info(model_path)
        if not model_info:
            raise ModelNotFoundError(f"Model not found: {model_path}")
        
        # Load model if not already loaded
        if not is_model_loaded(model_path):
            try:
                load_model(model_path)
            except Exception as e:
                raise ModelLoadError(f"Failed to load model: {str(e)}")
        
        # Get model instance
        model_instance = get_loaded_model(model_path)
        if not model_instance:
            raise ModelLoadError(f"Failed to retrieve loaded model: {model_path}")
        
        # Format the conversation history
        formatted_prompt = format_conversation(model_path, messages, system_prompt)
        logger.debug(f"Formatted conversation history: {formatted_prompt[:100]}...")
        
        # Fix for duplicate <s> tokens in Mistral models
        if "mistral" in model_path.lower() and formatted_prompt.count("<s>") > 1:
            logger.warning("Detected duplicate <s> tokens in Mistral conversation history. Fixing...")
            # Keep only the first <s> token by removing all and adding one back at the beginning
            formatted_prompt = "<s>" + formatted_prompt.replace("<s>", "")
        
        # Combine default settings with overrides
        settings = dict(self.default_settings)
        settings.update(kwargs)
        
        # Generate based on model type
        model_type = model_instance.get("type")
        
        if model_type == "llama.cpp":
            return self._generate_with_llamacpp(model_instance, formatted_prompt, model_path, settings)
        elif model_type == "transformers":
            return self._generate_with_transformers(model_instance, formatted_prompt, model_path, settings)
        else:
            raise ModelInferenceError(f"Unsupported model type for generation: {model_type}")

# Create a global instance
text_generator = TextGenerator()

# Convenience functions
def generate_text(model_path: str, prompt: str, system_prompt: str = "", **kwargs) -> Dict[str, Any]:
    """Generate text using the specified model."""
    return text_generator.generate_text(model_path, prompt, system_prompt, **kwargs)

def generate_with_history(model_path: str, messages: List[Dict[str, str]], system_prompt: str = "", **kwargs) -> Dict[str, Any]:
    """Generate text using conversation history."""
    return text_generator.generate_with_history(model_path, messages, system_prompt, **kwargs)