#!/usr/bin/env python3
"""
Cache clearing utility for the LLM Platform.

This script clears various caches used by the RAG system, including:
- Embedding caches
- Model caches
- Search index caches
- Temporary files

Use this when context is not properly refreshing or when old data
is affecting the system's responses.
"""

import os
import sys
import shutil
import time
from pathlib import Path
import argparse

# Add parent directory to path
parent_dir = Path(__file__).resolve().parent.parent
if str(parent_dir) not in sys.path:
    sys.path.append(str(parent_dir))

# Import necessary modules
try:
    from core.logging import get_logger
    logger = get_logger("cache_cleaner")
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    logger = logging.getLogger("cache_cleaner")

# Constants
BASE_DIR = parent_dir
CACHE_DIRS = [
    "rag_support/cache",
    "rag_support/cache/embeddings",
    "logs",
    "__pycache__",
]

def clear_python_caches():
    """Clear Python cache files (.pyc, __pycache__) recursively."""
    logger.info("Clearing Python cache files...")
    count = 0
    
    # Find and remove __pycache__ directories
    for root, dirs, files in os.walk(BASE_DIR):
        # Skip virtual environment directories
        if "LLM-MODELS/tools/python" in root:
            continue
            
        # Remove __pycache__ directories
        if "__pycache__" in dirs:
            cache_dir = os.path.join(root, "__pycache__")
            try:
                shutil.rmtree(cache_dir)
                count += 1
                logger.debug(f"Removed {cache_dir}")
            except Exception as e:
                logger.error(f"Error removing {cache_dir}: {e}")
                
        # Remove .pyc files
        for file in files:
            if file.endswith(".pyc"):
                pyc_file = os.path.join(root, file)
                try:
                    os.remove(pyc_file)
                    count += 1
                    logger.debug(f"Removed {pyc_file}")
                except Exception as e:
                    logger.error(f"Error removing {pyc_file}: {e}")
                    
    logger.info(f"Removed {count} Python cache files/directories")
    return count

def clear_embedding_caches():
    """Clear embedding cache files."""
    logger.info("Clearing embedding caches...")
    count = 0
    
    embedding_cache_dir = BASE_DIR / "rag_support" / "cache" / "embeddings"
    if embedding_cache_dir.exists():
        try:
            # Remove individual files rather than the directory
            for file in embedding_cache_dir.glob("*"):
                if file.is_file():
                    file.unlink()
                    count += 1
                    logger.debug(f"Removed {file}")
            
            logger.info(f"Cleared {count} embedding cache files")
        except Exception as e:
            logger.error(f"Error clearing embedding cache: {e}")
    else:
        logger.info(f"No embedding cache directory found at {embedding_cache_dir}")
        
    return count

def clear_model_caches():
    """Clear any model cache files."""
    logger.info("Clearing model caches...")
    count = 0
    
    # Try to use minimal_inference_quiet to unload models
    try:
        from scripts.minimal_inference_quiet import unload_all
        unload_all()
        logger.info("Unloaded all models")
    except ImportError:
        logger.warning("Could not import minimal_inference_quiet to unload models")
    except Exception as e:
        logger.error(f"Error unloading models: {e}")
        
    # Force garbage collection
    try:
        import gc
        gc.collect()
        logger.info("Forced garbage collection")
    except Exception as e:
        logger.error(f"Error forcing garbage collection: {e}")
        
    return count

def ensure_cache_dirs():
    """Ensure all cache directories exist."""
    logger.info("Ensuring cache directories exist...")
    
    for cache_dir in CACHE_DIRS:
        dir_path = BASE_DIR / cache_dir
        if not dir_path.exists():
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created cache directory: {dir_path}")
            except Exception as e:
                logger.error(f"Error creating cache directory {dir_path}: {e}")
                
    return True

def main():
    """Main function to clear caches."""
    parser = argparse.ArgumentParser(description="Clear RAG system caches")
    parser.add_argument("--all", action="store_true", help="Clear all caches")
    parser.add_argument("--python", action="store_true", help="Clear Python cache files")
    parser.add_argument("--embeddings", action="store_true", help="Clear embedding caches")
    parser.add_argument("--models", action="store_true", help="Clear model caches")
    
    args = parser.parse_args()
    
    # If no options specified, clear all caches
    if not (args.all or args.python or args.embeddings or args.models):
        args.all = True
    
    start_time = time.time()
    logger.info("Starting cache clearing...")
    
    # Clear specified caches
    if args.all or args.python:
        clear_python_caches()
        
    if args.all or args.embeddings:
        clear_embedding_caches()
        
    if args.all or args.models:
        clear_model_caches()
    
    # Ensure cache directories exist
    ensure_cache_dirs()
    
    elapsed = time.time() - start_time
    logger.info(f"Cache clearing completed in {elapsed:.2f} seconds")
    
    print("\n" + "=" * 60)
    print("Cache clearing completed successfully!")
    print(f"Time taken: {elapsed:.2f} seconds")
    print("=" * 60)
    print("\nRestart the LLM platform to apply changes.")
    
if __name__ == "__main__":
    main()