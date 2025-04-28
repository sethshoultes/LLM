#!/usr/bin/env python3
# Initialize the rag_support package

# Import utilities for easy access
from pathlib import Path

# Base directory - use absolute path
BASE_DIR = Path("/Volumes/LLM")

# Version information
__version__ = "0.1.0"

# Initialize directories if needed
def init_directories():
    """Initialize required directories if they don't exist"""
    (BASE_DIR / "rag_support" / "projects").mkdir(exist_ok=True)
    (BASE_DIR / "rag_support" / "utils").mkdir(exist_ok=True)
    (BASE_DIR / "rag_support" / "templates").mkdir(exist_ok=True)
    
    return True

# Initialize package
init_directories()

# Main package exports
__all__ = ['__version__']