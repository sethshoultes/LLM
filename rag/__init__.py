#!/usr/bin/env python3
"""
RAG (Retrieval-Augmented Generation) module for the LLM Platform.

This module provides RAG functionality:
- Document management
- Project organization
- Search capabilities
- Context management
- Retrieval strategies
"""

__version__ = "0.1.0"

# Import BASE_DIR from environment if set
import os
from pathlib import Path

# Set up base directory
SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
BASE_DIR = Path(os.environ.get("LLM_BASE_DIR", str(BASE_DIR)))

# Standard RAG directories
RAG_DIR = BASE_DIR / "rag_support"
PROJECTS_DIR = RAG_DIR / "projects"


def init_directories() -> bool:
    """
    Initialize RAG directories.

    Returns:
        True if initialization was successful, False otherwise
    """
    try:
        # Ensure RAG directories exist
        RAG_DIR.mkdir(exist_ok=True)
        PROJECTS_DIR.mkdir(exist_ok=True)

        # Add __init__.py if needed
        init_file = PROJECTS_DIR / "__init__.py"
        if not init_file.exists():
            with open(init_file, "w") as f:
                f.write('"""Projects directory for RAG system."""\n')

        return True
    except Exception as e:
        print(f"Error initializing RAG directories: {e}")
        return False


# Initialize on import
try:
    init_directories()
except Exception as e:
    print(f"Warning: RAG initialization error: {e}")

# Import key components for easier access
try:
    from .documents import Document
    from .indexer import DocumentIndexer
    from .storage import FileSystemStorage as DocumentStore
    from .search import SearchEngine, SearchResult
    from .parser import DocumentParser, MarkdownParser, TextParser, HTMLParser

    # Export key components
    __all__ = [
        "Document",
        "DocumentIndexer",
        "DocumentStore",
        "DocumentParser",
        "MarkdownParser",
        "TextParser",
        "HTMLParser",
        "SearchEngine",
        "SearchResult",
        "BASE_DIR",
        "RAG_DIR",
        "PROJECTS_DIR",
        "__version__",
    ]
except ImportError as e:
    print(f"Warning: Some RAG components could not be imported: {e}")
    # Define minimal exports
    __all__ = ["BASE_DIR", "RAG_DIR", "PROJECTS_DIR", "__version__"]
