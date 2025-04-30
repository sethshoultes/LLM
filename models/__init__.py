#!/usr/bin/env python3
"""
Models module for the LLM Platform.

This module provides model management, loading, and generation capabilities:
- Model registry with metadata
- Unified model loading
- Standardized text generation
- Prompt formatting for different model types
- Intelligent model caching
"""

__version__ = "0.1.0"

# Import key components for easier access
from .registry import (
    get_models, get_model_info, 
    find_models_by_family, find_models_by_format,
    get_best_model, refresh_registry
)

from .loader import (
    load_model, unload_model, 
    unload_all_models, is_model_loaded, get_loaded_model
)

from .formatter import (
    format_prompt, format_conversation
)

from .generation import (
    generate_text, generate_with_history
)

from .caching import (
    initialize_cache, ensure_model_loaded,
    get_cache_stats, preload_models, clear_cache
)

# Initialize models module
def initialize():
    """Initialize the models module."""
    from core.logging import get_logger
    
    logger = get_logger("models.init")
    logger.info(f"Initializing LLM Platform Models v{__version__}")
    
    # Refresh the model registry
    refresh_registry(force=True)
    
    # Initialize cache settings
    initialize_cache()
    
    logger.info("Models initialization complete")