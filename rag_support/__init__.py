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
    try:
        # Create required directories
        projects_dir = SCRIPT_DIR / "projects"
        utils_dir = SCRIPT_DIR / "utils"
        templates_dir = SCRIPT_DIR / "templates"

        # Create each directory if it doesn't exist
        for directory in [projects_dir, utils_dir, templates_dir]:
            directory.mkdir(exist_ok=True)

        # Ensure each directory has an __init__.py file
        for directory in [projects_dir, utils_dir, templates_dir]:
            init_file = directory / "__init__.py"
            if not init_file.exists():
                with open(init_file, "w") as f:
                    f.write(f"# Initialize {directory.name} module\n")

        return True
    except Exception as e:
        print(f"Error initializing directories: {e}")
        return False


# Initialize package on import
try:
    init_directories()
except Exception as e:
    print(f"Warning: RAG support initialization error: {e}")
    # Don't raise an exception - allow import to continue even if initialization fails

# Import key modules so they're available at package level
try:
    from . import api_extensions
except ImportError as e:
    print(f"Warning: Could not import api_extensions: {e}")

# Import hybrid_search module
try:
    from .utils.hybrid_search import hybrid_search
except ImportError as e:
    print(f"Warning: Could not import hybrid_search: {e}")
    hybrid_search = None

# Export BASE_DIR and key modules for other modules
__all__ = ["__version__", "BASE_DIR", "api_extensions", "hybrid_search"]
