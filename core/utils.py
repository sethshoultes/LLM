#!/usr/bin/env python3
"""
Utility module for the LLM Platform.

Provides common utility functions used across the application.
"""

import re
import json
import time
import hashlib
from pathlib import Path
from typing import Any, Dict, Union, Callable
from functools import wraps

from core.logging import get_logger
from core.config import is_debug

# Get logger for this module
logger = get_logger("utils")


def timer(func: Callable) -> Callable:
    """
    Decorator to measure and log function execution time.

    Args:
        func: Function to time

    Returns:
        Wrapped function that logs execution time
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time

        if is_debug():
            logger.debug(f"Function '{func.__name__}' executed in {execution_time:.4f} seconds")

        return result

    return wrapper


def memoize(ttl: int = 300) -> Callable:
    """
    Decorator to memoize function results with time-based expiration.

    Args:
        ttl: Time to live for cached results in seconds

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        cache = {}

        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create a cache key from the function arguments
            key_parts = [str(arg) for arg in args]
            key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
            key = hashlib.md5(":".join(key_parts).encode()).hexdigest()

            current_time = time.time()

            # Check if result is in cache and not expired
            if key in cache and current_time - cache[key]["time"] < ttl:
                return cache[key]["result"]

            # Call the function and cache the result
            result = func(*args, **kwargs)
            cache[key] = {"result": result, "time": current_time}

            return result

        # Add a function to clear the cache
        wrapper.clear_cache = lambda: cache.clear()

        return wrapper

    return decorator


def load_json_file(file_path: Union[str, Path], default: Any = None) -> Any:
    """
    Load JSON data from a file with error handling.

    Args:
        file_path: Path to the JSON file
        default: Default value to return if file doesn't exist or is invalid

    Returns:
        Parsed JSON data or default value
    """
    path = Path(file_path)

    if not path.exists():
        return default

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading JSON file '{path}': {e}")
        return default


def save_json_file(file_path: Union[str, Path], data: Any, indent: int = 2) -> bool:
    """
    Save data to a JSON file with error handling.

    Args:
        file_path: Path to the JSON file
        data: Data to save
        indent: JSON indentation level

    Returns:
        True if saving was successful, False otherwise
    """
    path = Path(file_path)

    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent)
        return True
    except Exception as e:
        logger.error(f"Error saving JSON file '{path}': {e}")
        return False


def merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively merge two dictionaries.

    Args:
        dict1: First dictionary
        dict2: Second dictionary (values from this take precedence)

    Returns:
        Merged dictionary
    """
    result = dict1.copy()

    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value

    return result


def create_unique_id(prefix: str = "") -> str:
    """
    Create a unique ID with an optional prefix.

    Args:
        prefix: Optional prefix for the ID

    Returns:
        Unique ID string
    """
    import uuid

    unique_id = str(uuid.uuid4())

    if prefix:
        return f"{prefix}_{unique_id}"

    return unique_id


def estimate_tokens(text: str) -> int:
    """
    Estimate the number of tokens in a text string.

    This is a simple approximation - 1 token is roughly 4 characters for English text.
    For more accurate counts, a proper tokenizer should be used.

    Args:
        text: Text to estimate tokens for

    Returns:
        Estimated token count
    """
    if not text:
        return 0

    # Simple approximation: 1 token is roughly 4 characters for English text
    char_count = len(text)
    token_estimate = char_count // 4

    # Account for whitespace and newlines which are typically tokenized differently
    whitespace_count = len([c for c in text if c.isspace()])
    whitespace_token_adjustment = whitespace_count // 8  # Adjust for whitespace

    return max(1, token_estimate + whitespace_token_adjustment)


def parse_frontmatter(content: str) -> tuple:
    """
    Parse YAML frontmatter from a markdown document.

    Args:
        content: Document content with optional frontmatter

    Returns:
        Tuple of (metadata_dict, content_without_frontmatter)
    """
    metadata = {}
    markdown_content = content

    # Check if the content starts with frontmatter delimiter
    if content.startswith("---"):
        try:
            # Extract frontmatter
            _, frontmatter, markdown = content.split("---", 2)

            # Parse frontmatter lines
            for line in frontmatter.strip().split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    key = key.strip()
                    value = value.strip()

                    # Try to parse as JSON if possible
                    try:
                        metadata[key] = json.loads(value)
                    except json.JSONDecodeError:
                        metadata[key] = value

            markdown_content = markdown.strip()
        except ValueError:
            # If splitting fails, assume no valid frontmatter
            pass

    return metadata, markdown_content


def format_with_frontmatter(data: Dict[str, Any], content: str) -> str:
    """
    Format content with YAML frontmatter.

    Args:
        data: Metadata to include in frontmatter
        content: Content to format

    Returns:
        Formatted string with frontmatter
    """
    frontmatter = "---\n"

    for key, value in data.items():
        if isinstance(value, (dict, list, tuple)):
            # Convert complex types to JSON string
            frontmatter += f"{key}: {json.dumps(value)}\n"
        else:
            # Simple types can be represented directly
            frontmatter += f"{key}: {value}\n"

    frontmatter += "---\n\n"

    return frontmatter + content


def safe_file_name(name: str) -> str:
    """
    Convert a string to a safe file name.

    Args:
        name: Original string

    Returns:
        Safe file name
    """
    # Replace spaces with underscores
    name = name.replace(" ", "_")

    # Remove unsafe characters
    name = re.sub(r"[^\w\-\.]", "", name)

    # Limit length
    if len(name) > 255:
        name = name[:255]

    return name
