#!/usr/bin/env python3
"""
Core module for the LLM Platform.

This module provides core functionality and utilities used across the platform:
- Configuration management
- Path resolution
- Logging
- Error handling
- Common utilities
"""

__version__ = "0.1.0"

# Import core components for easier access
from core.paths import (
    path_manager, get_path, resolve_path, ensure_dir, list_models
)
from core.config import (
    config, get, set_value, is_debug, is_rag_enabled, parse_args, save_config
)
from core.logging import (
    log_manager, get_logger, initialize as initialize_logging, 
    set_debug, log_exception
)
from core.errors import (
    LLMError, ConfigError, PathError, ModelError, RAGError, APIError,
    BadRequestError, NotFoundError, ServerError,
    format_error, log_error, handle_api_error
)
from core.utils import (
    timer, memoize, load_json_file, save_json_file, merge_dicts,
    create_unique_id, estimate_tokens, parse_frontmatter, format_with_frontmatter
)

# Initialize core systems
def initialize():
    """Initialize all core systems."""
    # Initialize logging first
    initialize_logging()
    
    # Get logger for initialization
    logger = get_logger("core.init")
    logger.info(f"Initializing LLM Platform Core v{__version__}")
    
    # Ensure base directories exist
    try:
        for dir_name in ["config", "logs"]:
            dir_path = get_path("base") / dir_name
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {dir_path}")
    except Exception as e:
        logger.error(f"Error ensuring directories: {e}")
        
    logger.info("Core initialization complete")