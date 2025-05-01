#!/usr/bin/env python3
"""
Model loader module for the LLM Platform.

Provides unified model loading functionality for different model types.
"""

import os
import gc
import time
from pathlib import Path
from typing import Dict, Any, Optional, Union, List, Tuple

from core.logging import get_logger
from core.utils import timer

from models.registry import model_registry, get_model_info

# Get logger for this module
logger = get_logger("models.loader")

class ModelLoader:
    """
    Unified model loader for different model types.
    
    Handles loading of different model formats (GGUF, GGML, PyTorch)
    with appropriate libraries and settings.
    """
    
    def __init__(self):
        """Initialize the model loader with default settings."""
        self.default_settings = {
            "llama.cpp": {
                "n_ctx": 2048,      # Context window size
                "n_batch": 512,      # Batch size for efficient inference
                "n_gpu_layers": -1,  # Auto-determine GPU layers
                "seed": 42,          # Random seed for reproducibility
                "use_mlock": True,   # Lock memory to prevent swapping
                "use_mmap": True,    # Use memory mapping for efficiency
                "verbose": False     # Verbose output from llama.cpp
            },
            "transformers": {
                "device_map": "auto",    # Automatically determine device mapping
                "torch_dtype": "auto",   # Automatically determine dtype
                "trust_remote_code": True, # Trust remote code for models
                "local_files_only": False, # Look for local files first
                "low_cpu_mem_usage": True, # Use low CPU memory when possible
                "revision": "main"      # Git revision to use
            }
        }
    
    def _check_dependencies(self, loader_type: str) -> bool:
        """
        Check if required dependencies are installed.
        
        Args:
            loader_type: Type of loader to check dependencies for
            
        Returns:
            True if dependencies are installed, False otherwise
        """
        if loader_type == "llama.cpp":
            try:
                import llama_cpp
                return True
            except ImportError:
                logger.warning("llama-cpp-python not installed. Please install with: pip install llama-cpp-python")
                return False
                
        elif loader_type == "transformers":
            try:
                import transformers
                return True
            except ImportError:
                logger.warning("Transformers or PyTorch not installed. Please install with: pip install transformers torch")
                return False
                
        return False
    
    @timer
    def load_model(self, model_path: str, **kwargs) -> Dict[str, Any]:
        """
        Load a model from the given path.
        
        Args:
            model_path: Path to the model (relative to BASE_DIR)
            **kwargs: Additional settings to override defaults
            
        Returns:
            Dictionary containing the loaded model and related objects
            
        Raises:
            ModelNotFoundError: If model not found
            ModelLoadError: If model loading fails
        """
        # Check if model is already loaded
        if model_registry.is_model_loaded(model_path):
            logger.info(f"Model already loaded: {model_path}")
            return model_registry.get_loaded_model(model_path)
        
        # Get model info from registry
        model_info = get_model_info(model_path)
        if not model_info:
            raise ModelNotFoundError(f"Model not found: {model_path}")
        
        # Get full path
        full_path = model_info["full_path"]
        if not Path(full_path).exists():
            raise ModelNotFoundError(f"Model file not found: {full_path}")
        
        # Get loader type
        loader_type = model_info["loader_type"]
        
        # Check dependencies
        if not self._check_dependencies(loader_type):
            raise ModelLoadError(f"Missing dependencies for loader type: {loader_type}")
        
        # Load based on loader type
        if loader_type == "llama.cpp":
            return self._load_llama_cpp_model(model_path, model_info, **kwargs)
        elif loader_type == "transformers":
            return self._load_transformers_model(model_path, model_info, **kwargs)
        else:
            raise ModelLoadError(f"Unsupported loader type: {loader_type}")
    
    def _load_llama_cpp_model(self, model_path: str, model_info: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Load a model using llama.cpp.
        
        Args:
            model_path: Path to the model (relative to BASE_DIR)
            model_info: Model metadata from registry
            **kwargs: Additional settings to override defaults
            
        Returns:
            Dictionary containing the loaded model and related objects
            
        Raises:
            ModelLoadError: If model loading fails
        """
        full_path = model_info["full_path"]
        logger.info(f"Loading llama.cpp model from {full_path}")
        
        try:
            import llama_cpp
            
            # Combine default settings with overrides
            settings = dict(self.default_settings["llama.cpp"])
            settings.update(kwargs)
            
            # Set GGML verbose logging based on settings
            os.environ["LLAMA_CPP_VERBOSE"] = "1" if settings.pop("verbose", False) else "0"
            
            # Check if this is a legacy GGML model
            is_legacy = model_info["format"] == "ggml"
            if is_legacy:
                settings["legacy"] = True
            
            # Load the model
            model = llama_cpp.Llama(
                model_path=full_path,
                **settings
            )
            
            # Create model instance dictionary
            model_instance = {
                "model": model,
                "type": "llama.cpp",
                "model_format": model_info["format"],
                "loaded_at": time.time(),
                "settings": settings
            }
            
            # Register with model registry
            model_registry.register_loaded_model(model_path, model_instance)
            
            logger.info(f"Successfully loaded {model_info['format'].upper()} model: {model_path}")
            return model_instance
            
        except Exception as e:
            raise ModelLoadError(f"Failed to load llama.cpp model: {str(e)}")
    
    def _load_transformers_model(self, model_path: str, model_info: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Load a model using transformers.
        
        Args:
            model_path: Path to the model (relative to BASE_DIR)
            model_info: Model metadata from registry
            **kwargs: Additional settings to override defaults
            
        Returns:
            Dictionary containing the loaded model and related objects
            
        Raises:
            ModelLoadError: If model loading fails
        """
        full_path = model_info["full_path"]
        logger.info(f"Loading transformers model from {full_path}")
        
        try:
            import transformers
            
            # Combine default settings with overrides
            settings = dict(self.default_settings["transformers"])
            settings.update(kwargs)
            
            # If it's a full path to a model file, use the parent directory as the model path
            model_dir = str(Path(full_path).parent) if Path(full_path).is_file() else full_path
            
            # Load tokenizer
            logger.debug(f"Loading tokenizer from {model_dir}")
            tokenizer = transformers.AutoTokenizer.from_pretrained(
                model_dir,
                trust_remote_code=settings.pop("trust_remote_code", True),
                local_files_only=settings.pop("local_files_only", False),
                revision=settings.pop("revision", "main")
            )
            
            # Load model
            logger.debug(f"Loading model from {model_dir}")
            model = transformers.AutoModelForCausalLM.from_pretrained(
                model_dir,
                **settings
            )
            
            # Create pipeline
            logger.debug("Creating pipeline")
            pipeline = transformers.pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer,
                do_sample=True
            )
            
            # Create model instance dictionary
            model_instance = {
                "model": model,
                "tokenizer": tokenizer,
                "pipeline": pipeline,
                "type": "transformers",
                "model_format": model_info["format"],
                "loaded_at": time.time(),
                "settings": settings
            }
            
            # Register with model registry
            model_registry.register_loaded_model(model_path, model_instance)
            
            logger.info(f"Successfully loaded PyTorch model: {model_path}")
            return model_instance
            
        except Exception as e:
            raise ModelLoadError(f"Failed to load transformers model: {str(e)}")
    
    def unload_model(self, model_path: str) -> bool:
        """
        Unload a model to free memory.
        
        Args:
            model_path: Path to the model (relative to BASE_DIR)
            
        Returns:
            True if model was unloaded, False if not found
        """
        if not model_registry.is_model_loaded(model_path):
            logger.debug(f"Model not loaded, nothing to unload: {model_path}")
            return False
        
        # Get model instance
        model_instance = model_registry.get_loaded_model(model_path)
        if not model_instance:
            return False
        
        # Different unloading procedures depending on model type
        try:
            if model_instance["type"] == "llama.cpp":
                # llama.cpp models free their memory when the object is deleted
                model_instance["model"] = None
            elif model_instance["type"] == "transformers":
                # Clear references to all transformers objects
                model_instance["model"] = None
                model_instance["tokenizer"] = None
                model_instance["pipeline"] = None
            
            # Remove from registry
            model_registry.unregister_loaded_model(model_path)
            
            # Run garbage collection to free memory
            gc.collect()
            
            logger.info(f"Unloaded model: {model_path}")
            return True
        except Exception as e:
            logger.error(f"Error unloading model {model_path}: {e}")
            return False
    
    def unload_all_models(self) -> None:
        """Unload all loaded models to free memory."""
        for model_path in list(model_registry.loaded_models.keys()):
            self.unload_model(model_path)
        
        # Run garbage collection to free memory
        gc.collect()
        logger.info("Unloaded all models")

# Create a global instance
model_loader = ModelLoader()

# Convenience functions
def load_model(model_path: str, **kwargs) -> Dict[str, Any]:
    """Load a model from the given path."""
    return model_loader.load_model(model_path, **kwargs)

def unload_model(model_path: str) -> bool:
    """Unload a model to free memory."""
    return model_loader.unload_model(model_path)

def unload_all_models() -> None:
    """Unload all loaded models to free memory."""
    model_loader.unload_all_models()

def is_model_loaded(model_path: str) -> bool:
    """Check if a model is currently loaded."""
    return model_registry.is_model_loaded(model_path)

def get_loaded_model(model_path: str) -> Optional[Dict[str, Any]]:
    """Get a loaded model instance."""
    return model_registry.get_loaded_model(model_path)