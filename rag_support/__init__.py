#!/usr/bin/env python3
# Initialize the rag_support package

# Import utilities for easy access
import os
from pathlib import Path

# Use script-relative path instead of hardcoded path
SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent

# Use environment variable if available
BASE_DIR = Path(os.environ.get("LLM_BASE_DIR", str(BASE_DIR)))

# Version information
__version__ = "0.1.0"

# Initialize directories if needed
def init_directories():
    """Initialize required directories if they don't exist"""
    (SCRIPT_DIR / "projects").mkdir(exist_ok=True)
    (SCRIPT_DIR / "utils").mkdir(exist_ok=True)
    (SCRIPT_DIR / "templates").mkdir(exist_ok=True)
    
    return True

# Initialize package
init_directories()

# Export BASE_DIR for other modules
__all__ = ['__version__', 'BASE_DIR']