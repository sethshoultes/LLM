#!/usr/bin/env python3
"""
Model registry module for the LLM Platform.

Provides a registry for available models with metadata and capabilities.
"""

import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple

from core.logging import get_logger
from core.utils import timer
from core.paths import path_manager

# Get logger for this module
logger = get_logger("models.registry")

class ModelRegistry:
    """
    Registry for LLM models with metadata and capabilities.
    
    Tracks available models, their formats, capabilities, and related metadata.
    """
    
    def __init__(self):
        """Initialize the model registry."""
        self.refresh_interval = 300  # 5 minutes
        self.last_refresh = 0
        self.models = {}
        self.loaded_models = {}
        self.refresh()
    
    @timer
    def refresh(self, force: bool = False) -> None:
        """
        Refresh the model registry by scanning available models.
        
        Args:
            force: Force refresh even if cache is still valid
        """
        current_time = time.time()
        
        # Check if we need to refresh
        if not force and current_time - self.last_refresh < self.refresh_interval:
            logger.debug("Using cached model list (use force=True to refresh)")
            return
            
        logger.info("Refreshing model registry...")
        
        # Clear existing model list
        self.models = {}
        
        # Get model paths from path manager
        model_paths = path_manager.list_models()
        
        # Process each model file
        for rel_path, full_path in model_paths.items():
            try:
                # Extract model metadata
                model_info = self._extract_model_metadata(rel_path, full_path)
                
                # Add to registry
                self.models[rel_path] = model_info
                logger.debug(f"Added model to registry: {rel_path}")
            except Exception as e:
                logger.error(f"Error processing model {rel_path}: {e}")
        
        self.last_refresh = current_time
        logger.info(f"Model registry refreshed - found {len(self.models)} models")
    
    def _extract_model_metadata(self, rel_path: str, full_path: Path) -> Dict[str, Any]:
        """
        Extract metadata for a model.
        
        Args:
            rel_path: Relative path to the model
            full_path: Full path to the model file
            
        Returns:
            Dictionary of model metadata
        """
        # Basic metadata
        model_info = {
            "path": rel_path,
            "full_path": str(full_path),
            "size_mb": round(full_path.stat().st_size / (1024 * 1024), 2),
            "last_modified": full_path.stat().st_mtime,
        }
        
        # Extract file extension
        file_ext = full_path.suffix.lower()
        model_info["file_ext"] = file_ext
        
        # Determine model format
        if file_ext == '.gguf':
            model_info["format"] = "gguf"
            model_info["loader_type"] = "llama.cpp"
        elif file_ext == '.bin' and 'ggml' in full_path.name.lower():
            model_info["format"] = "ggml"
            model_info["loader_type"] = "llama.cpp"
        elif file_ext in ['.safetensors', '.pt', '.bin'] and 'ggml' not in full_path.name.lower():
            model_info["format"] = "pytorch"
            model_info["loader_type"] = "transformers"
        else:
            model_info["format"] = "unknown"
            model_info["loader_type"] = "unknown"
        
        # Try to determine model family from path
        model_family = "unknown"
        for family in ["llama", "mistral", "tinyllama", "phi", "mixtral", "gemma", "gpt"]:
            if family in str(full_path).lower():
                model_family = family
                break
        model_info["family"] = model_family
        
        # Determine model size (e.g., 7B, 13B) if available
        model_size = None
        size_patterns = ["7b", "13b", "70b", "1.1b", "1b", "2b", "8x7b"]
        path_lower = str(full_path).lower()
        for pattern in size_patterns:
            if pattern in path_lower:
                model_size = pattern.upper()
                break
        model_info["size"] = model_size
        
        # Determine if it's a quantized model
        if "quantized" in str(full_path):
            model_info["quantized"] = True
            
            # Try to determine quantization level
            quant_patterns = ["q4_k_m", "q5_k_m", "q6_k", "q8_0", "q2_k", "q3_k_l", "q4_0"]
            for pattern in quant_patterns:
                if pattern in str(full_path).lower():
                    model_info["quantization"] = pattern.upper()
                    break
        else:
            model_info["quantized"] = False
        
        # Guess context window size based on model family and size
        context_window = self._guess_context_window(model_family, model_size)
        model_info["context_window"] = context_window
        
        # Is it an instruction-tuned model?
        model_info["instruct"] = any(kw in str(full_path).lower() 
                                    for kw in ["instruct", "chat", "orca", "wizard"])
        
        return model_info
    
    def _guess_context_window(self, model_family: str, model_size: Optional[str]) -> int:
        """
        Guess the context window size based on model family and size.
        
        Args:
            model_family: Model family (e.g., "llama", "mistral")
            model_size: Model size (e.g., "7B", "13B")
            
        Returns:
            Estimated context window size in tokens
        """
        # Default window size
        default_window = 2048
        
        # Model-specific window sizes
        if model_family == "llama" and model_size in ["70B"]:
            return 4096
        elif model_family == "mistral":
            return 8192  # Mistral models typically have 8K context
        elif model_family == "mixtral":
            return 32768  # Mixtral has a very large context
        elif model_family == "phi" and model_size in ["2B"]:
            return 2048
        elif model_family == "tinyllama":
            return 2048
        elif model_family == "gemma":
            return 8192
        
        # Default case
        return default_window
    
    def get_models(self, refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Get a list of all available models.
        
        Args:
            refresh: Whether to force a refresh of the model list
            
        Returns:
            List of model metadata dictionaries
        """
        if refresh or not self.models:
            self.refresh(force=refresh)
            
        return list(self.models.values())
    
    def get_model_info(self, model_path: str, refresh: bool = False) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a specific model.
        
        Args:
            model_path: Path to the model (relative to BASE_DIR)
            refresh: Whether to force a refresh of the model list
            
        Returns:
            Model metadata dictionary or None if not found
        """
        if refresh or not self.models:
            self.refresh(force=refresh)
            
        return self.models.get(model_path)
    
    def find_models_by_family(self, family: str, instruct_only: bool = False) -> List[Dict[str, Any]]:
        """
        Find models by family.
        
        Args:
            family: Model family to search for
            instruct_only: Whether to only return instruction-tuned models
            
        Returns:
            List of matching model metadata dictionaries
        """
        results = []
        
        for model_info in self.models.values():
            if model_info["family"].lower() == family.lower():
                if not instruct_only or model_info.get("instruct", False):
                    results.append(model_info)
        
        # Sort by size (smallest first)
        results.sort(key=lambda m: m.get("size_mb", 0))
        
        return results
    
    def find_models_by_format(self, format_type: str) -> List[Dict[str, Any]]:
        """
        Find models by format.
        
        Args:
            format_type: Model format to search for (e.g., "gguf", "pytorch")
            
        Returns:
            List of matching model metadata dictionaries
        """
        results = []
        
        for model_info in self.models.values():
            if model_info["format"].lower() == format_type.lower():
                results.append(model_info)
        
        # Sort by size (smallest first)
        results.sort(key=lambda m: m.get("size_mb", 0))
        
        return results
    
    def get_best_model(self, family: Optional[str] = None, 
                     instruct: bool = True,
                     max_size_mb: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Get the best available model matching the criteria.
        
        Args:
            family: Preferred model family (optional)
            instruct: Whether to prefer instruction-tuned models
            max_size_mb: Maximum model size in MB
            
        Returns:
            Model metadata dictionary or None if no suitable model found
        """
        candidates = []
        
        for model_info in self.models.values():
            # Filter by family if specified
            if family and model_info["family"].lower() != family.lower():
                continue
                
            # Filter by instruction tuning if required
            if instruct and not model_info.get("instruct", False):
                continue
                
            # Filter by maximum size if specified
            if max_size_mb and model_info.get("size_mb", 0) > max_size_mb:
                continue
                
            candidates.append(model_info)
        
        if not candidates:
            return None
            
        # Sort by preference criteria
        # 1. Quantized models first (they're faster)
        # 2. Then by size (smaller = faster)
        candidates.sort(key=lambda m: (not m.get("quantized", False), m.get("size_mb", 0)))
        
        return candidates[0]
    
    def register_loaded_model(self, model_path: str, model_instance: Any) -> None:
        """
        Register a loaded model instance.
        
        Args:
            model_path: Path to the model (relative to BASE_DIR)
            model_instance: Loaded model instance
        """
        self.loaded_models[model_path] = {
            "instance": model_instance,
            "loaded_at": time.time(),
            "last_used": time.time()
        }
        logger.info(f"Registered loaded model: {model_path}")
    
    def unregister_loaded_model(self, model_path: str) -> bool:
        """
        Unregister a loaded model instance.
        
        Args:
            model_path: Path to the model (relative to BASE_DIR)
            
        Returns:
            True if model was unregistered, False if not found
        """
        if model_path in self.loaded_models:
            del self.loaded_models[model_path]
            logger.info(f"Unregistered loaded model: {model_path}")
            return True
        return False
    
    def is_model_loaded(self, model_path: str) -> bool:
        """
        Check if a model is currently loaded.
        
        Args:
            model_path: Path to the model (relative to BASE_DIR)
            
        Returns:
            True if model is loaded, False otherwise
        """
        return model_path in self.loaded_models
    
    def get_loaded_model(self, model_path: str) -> Optional[Any]:
        """
        Get a loaded model instance.
        
        Args:
            model_path: Path to the model (relative to BASE_DIR)
            
        Returns:
            Model instance or None if not loaded
        """
        if model_path in self.loaded_models:
            # Update last used time
            self.loaded_models[model_path]["last_used"] = time.time()
            return self.loaded_models[model_path]["instance"]
        return None
    
    def clear_loaded_models(self) -> None:
        """Clear all loaded models from the registry."""
        self.loaded_models.clear()
        logger.info("Cleared all loaded models from registry")

# Create a global instance
model_registry = ModelRegistry()

# Convenience functions
def get_models(refresh: bool = False) -> List[Dict[str, Any]]:
    """Get a list of all available models."""
    return model_registry.get_models(refresh)

def get_model_info(model_path: str, refresh: bool = False) -> Optional[Dict[str, Any]]:
    """Get metadata for a specific model."""
    return model_registry.get_model_info(model_path, refresh)

def find_models_by_family(family: str, instruct_only: bool = False) -> List[Dict[str, Any]]:
    """Find models by family."""
    return model_registry.find_models_by_family(family, instruct_only)

def find_models_by_format(format_type: str) -> List[Dict[str, Any]]:
    """Find models by format."""
    return model_registry.find_models_by_format(format_type)

def get_best_model(family: Optional[str] = None, instruct: bool = True, max_size_mb: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Get the best available model matching the criteria."""
    return model_registry.get_best_model(family, instruct, max_size_mb)

def refresh_registry(force: bool = False) -> None:
    """Refresh the model registry."""
    model_registry.refresh(force)