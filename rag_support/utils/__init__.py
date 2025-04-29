#!/usr/bin/env python3
# Initialize the rag_support utils package

# Import our utilities for easy access
from .project_manager import ProjectManager, project_manager
from .search import SimpleSearch, search_engine

# Provide singleton instances
__all__ = ['ProjectManager', 'project_manager', 'SimpleSearch', 'search_engine']