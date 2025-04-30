#!/usr/bin/env python3
"""
Model caching module for the LLM Platform.

Provides intelligent model caching to optimize memory usage and performance.
"""

import time
from typing import Dict, List, Optional, Any, Union, Set

from core.logging import get_logger
from core.config import get
from core.utils import timer

from models.registry import model_registry
from models.loader import model_loader

# Get logger for this module
logger = get_logger("models.caching")

class ModelCache:
    """
    Intelligent model cache manager.
    
    Manages loaded models with LRU (Least Recently Used) strategy
    to optimize memory usage while maintaining performance.
    """
    
    def __init__(self, max_models: int = 2, ttl: int = 3600):
        """
        Initialize the model cache manager.
        
        Args:
            max_models: Maximum number of models to keep in memory simultaneously
            ttl: Time to live in seconds for cached models
        """
        self.max_models = max_models
        self.ttl = ttl  # Time to live in seconds
        self.enabled = True
        
        # Cache stats
        self.hits = 0
        self.misses = 0
        self.evictions = 0
    
    def set_max_models(self, max_models: int) -> None:
        """
        Set the maximum number of models to keep in memory.
        
        Args:
            max_models: Maximum number of models
        """
        self.max_models = max_models
        
        # If the new limit is lower than the current cache size, evict models
        self._enforce_cache_limit()
    
    def set_ttl(self, ttl: int) -> None:
        """
        Set the time to live for cached models.
        
        Args:
            ttl: Time to live in seconds
        """
        self.ttl = ttl
        
        # Check for expired models
        self._remove_expired_models()
    
    def enable(self) -> None:
        """Enable model caching."""
        self.enabled = True
        logger.info("Model caching enabled")
    
    def disable(self) -> None:
        """Disable model caching and unload all models."""
        self.enabled = False
        self.clear()
        logger.info("Model caching disabled")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary of cache statistics
        """
        # Get current cache size
        loaded_models = model_registry.loaded_models
        current_size = len(loaded_models)
        
        # Calculate hit rate
        total_requests = self.hits + self.misses
        hit_rate = round((self.hits / total_requests) * 100, 2) if total_requests > 0 else 0
        
        stats = {
            "enabled": self.enabled,
            "max_models": self.max_models,
            "ttl_seconds": self.ttl,
            "current_size": current_size,
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "hit_rate_percent": hit_rate,
            "models": []
        }
        
        # Add information about each cached model
        for model_path, model_data in loaded_models.items():
            if not isinstance(model_data, dict):
                continue
            
            loaded_at = model_data.get("loaded_at", 0)
            last_used = model_data.get("last_used", 0)
            
            stats["models"].append({
                "path": model_path,
                "type": model_data.get("type", "unknown"),
                "format": model_data.get("model_format", "unknown"),
                "loaded_at": loaded_at,
                "last_used": last_used,
                "age_seconds": round(time.time() - loaded_at, 2),
                "idle_seconds": round(time.time() - last_used, 2)
            })
        
        return stats
    
    def touch(self, model_path: str) -> None:
        """
        Update the last used time for a model.
        
        Args:
            model_path: Path to the model
        """
        if model_path in model_registry.loaded_models:
            # Update last used time
            if isinstance(model_registry.loaded_models[model_path], dict):
                model_registry.loaded_models[model_path]["last_used"] = time.time()
    
    def preload(self, model_paths: List[str]) -> None:
        """
        Preload models into the cache.
        
        Args:
            model_paths: List of model paths to preload
        """
        if not self.enabled:
            logger.warning("Model caching is disabled, preload request ignored")
            return
            
        for model_path in model_paths:
            self.ensure_loaded(model_path)
    
    @timer
    def ensure_loaded(self, model_path: str) -> bool:
        """
        Ensure a model is loaded, loading it if necessary.
        
        Args:
            model_path: Path to the model
            
        Returns:
            True if the model is now loaded, False on error
        """
        if not self.enabled:
            return model_registry.is_model_loaded(model_path)
            
        # Check if the model is already loaded
        if model_registry.is_model_loaded(model_path):
            # Update last used time
            self.touch(model_path)
            self.hits += 1
            logger.debug(f"Cache hit for model: {model_path}")
            return True
            
        self.misses += 1
        logger.debug(f"Cache miss for model: {model_path}")
        
        # Remove expired models
        self._remove_expired_models()
        
        # Ensure we don't exceed the maximum number of models
        self._enforce_cache_limit()
        
        # Load the model
        try:
            model_loader.load_model(model_path)
            return True
        except Exception as e:
            logger.error(f"Error loading model {model_path}: {e}")
            return False
    
    def _remove_expired_models(self) -> None:
        """Remove models that have exceeded their TTL."""
        if not self.enabled or self.ttl <= 0:
            return
            
        current_time = time.time()
        models_to_unload = []
        
        for model_path, model_data in model_registry.loaded_models.items():
            if not isinstance(model_data, dict):
                continue
                
            last_used = model_data.get("last_used", 0)
            if current_time - last_used > self.ttl:
                models_to_unload.append(model_path)
        
        for model_path in models_to_unload:
            logger.info(f"Unloading expired model: {model_path}")
            model_loader.unload_model(model_path)
            self.evictions += 1
    
    def _enforce_cache_limit(self) -> None:
        """Ensure the number of loaded models doesn't exceed the maximum."""
        if not self.enabled or self.max_models <= 0:
            return
            
        # Get all loaded models
        loaded_models = list(model_registry.loaded_models.keys())
        
        # Check if we need to unload any models
        if len(loaded_models) <= self.max_models:
            return
            
        # Sort models by last used time (oldest first)
        models_with_time = []
        for model_path in loaded_models:
            model_data = model_registry.loaded_models.get(model_path, {})
            if isinstance(model_data, dict):
                last_used = model_data.get("last_used", 0)
                models_with_time.append((model_path, last_used))
        
        models_with_time.sort(key=lambda x: x[1])
        
        # Unload oldest models until we're within the limit
        models_to_unload = len(loaded_models) - self.max_models
        for i in range(models_to_unload):
            if i < len(models_with_time):
                model_path = models_with_time[i][0]
                logger.info(f"Unloading model to enforce cache limit: {model_path}")
                model_loader.unload_model(model_path)
                self.evictions += 1
    
    def clear(self) -> None:
        """Clear all models from the cache."""
        model_loader.unload_all_models()
        
        # Reset cache stats
        self.evictions += len(model_registry.loaded_models)
        logger.info("Model cache cleared")

# Create a global instance
model_cache = ModelCache()

# Initialize cache settings from config
def initialize_cache():
    """Initialize cache settings from configuration."""
    max_models = get("max_cached_models", 2)
    ttl = get("model_cache_ttl", 3600)
    enabled = get("model_cache_enabled", True)
    
    model_cache.set_max_models(max_models)
    model_cache.set_ttl(ttl)
    
    if enabled:
        model_cache.enable()
    else:
        model_cache.disable()
    
    logger.info(f"Model cache initialized: max_models={max_models}, ttl={ttl}s, enabled={enabled}")

# Convenience functions
def ensure_model_loaded(model_path: str) -> bool:
    """Ensure a model is loaded, loading it if necessary."""
    return model_cache.ensure_loaded(model_path)

def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics."""
    return model_cache.get_stats()

def preload_models(model_paths: List[str]) -> None:
    """Preload models into the cache."""
    model_cache.preload(model_paths)

def clear_cache() -> None:
    """Clear all models from the cache."""
    model_cache.clear()