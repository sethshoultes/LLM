#!/usr/bin/env python3
"""
Web server package for the LLM Platform.

Provides a modern, modular web server implementation with clean
routing, middleware support, and standardized API endpoints.
"""

import os
import logging
from pathlib import Path

# Set up package-level variables
__version__ = "1.0.0"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Determine base directory
try:
    from core.paths import get_base_dir
    BASE_DIR = get_base_dir()
except ImportError:
    # Fallback if core module is not available
    BASE_DIR = Path(__file__).resolve().parent.parent

# Import key components to make them available at package level
from web.server import create_server, start_server
from web.router import Router