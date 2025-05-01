#!/usr/bin/env python3
"""
API subpackage for the LLM Platform web server.

Provides standardized REST API endpoints, request/response schemas,
controllers for business logic, and consistent response formatting.
"""

import logging
from typing import Dict, List, Any, Optional, Union, Tuple

# Import core modules
try:
    from core.logging import get_logger
except ImportError:
    # Fallback if core module is not available
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    get_logger = lambda name: logging.getLogger(name)

# Get logger for this module
logger = get_logger("web.api")

# Import key components to make them available at package level
from .responses import (
    success_response, 
    error_response, 
    not_found_response
)

from .versioning import APIVersion, get_current_version