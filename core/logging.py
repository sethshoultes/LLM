#!/usr/bin/env python3
"""
Logging module for the LLM Platform.

Provides a centralized logging system with structured logging capabilities
that can be configured based on the application's needs.
"""

import os
import sys
import logging
import traceback
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, Union

from core.config import is_debug
from core.paths import resolve_path, ensure_dir, get_path

class LogFormatter(logging.Formatter):
    """Custom log formatter with colors for console output."""
    
    COLORS = {
        'DEBUG': '\033[0;36m',  # Cyan
        'INFO': '\033[0;32m',   # Green
        'WARNING': '\033[0;33m', # Yellow
        'ERROR': '\033[0;31m',  # Red
        'CRITICAL': '\033[1;31m', # Bold Red
        'RESET': '\033[0m',     # Reset
    }
    
    def __init__(self, use_colors: bool = True, *args, **kwargs):
        """Initialize the formatter with color option."""
        super().__init__(*args, **kwargs)
        self.use_colors = use_colors
    
    def format(self, record):
        """Format log record with optional colors."""
        log_message = super().format(record)
        
        if self.use_colors and record.levelname in self.COLORS:
            return f"{self.COLORS[record.levelname]}{log_message}{self.COLORS['RESET']}"
        
        return log_message

class LogManager:
    """Centralized logging management for the LLM Platform."""
    
    def __init__(self):
        """Initialize the log manager."""
        self.loggers = {}
        self.log_dir = None
        self.console_handler = None
        self.file_handler = None
        self.initialized = False
    
    def initialize(self, log_dir: Optional[Union[str, Path]] = None):
        """
        Initialize logging system.
        
        Args:
            log_dir: Directory for log files (optional)
        """
        if self.initialized:
            return
        
        # Set up log directory
        if log_dir:
            self.log_dir = resolve_path(log_dir)
        else:
            # Default to logs directory within the base directory
            self.log_dir = get_path("base") / "logs"
        
        ensure_dir(self.log_dir)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG if is_debug() else logging.INFO)
        
        # Remove existing handlers to avoid duplicates if re-initialized
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Console handler
        self.console_handler = logging.StreamHandler(sys.stdout)
        self.console_handler.setLevel(logging.DEBUG if is_debug() else logging.INFO)
        
        # Determine if we should use colors based on terminal capabilities
        use_colors = sys.stdout.isatty() and os.name != 'nt'
        console_formatter = LogFormatter(
            use_colors=use_colors,
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.console_handler.setFormatter(console_formatter)
        root_logger.addHandler(self.console_handler)
        
        # File handler for all logs
        log_file = self.log_dir / f"llm_platform_{datetime.now().strftime('%Y%m%d')}.log"
        self.file_handler = logging.FileHandler(log_file)
        self.file_handler.setLevel(logging.DEBUG)  # Always log debug and above to file
        file_formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.file_handler.setFormatter(file_formatter)
        root_logger.addHandler(self.file_handler)
        
        self.initialized = True
        
        # Log initialization message
        root_logger.info(f"Logging initialized. Log file: {log_file}")
        if is_debug():
            root_logger.info("Debug mode enabled.")
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        Get a logger by name.
        
        Args:
            name: Logger name
            
        Returns:
            Logger instance
        """
        if not self.initialized:
            self.initialize()
            
        if name not in self.loggers:
            self.loggers[name] = logging.getLogger(name)
            
        return self.loggers[name]
    
    def set_debug(self, debug: bool = True) -> None:
        """
        Set debug mode for logging.
        
        Args:
            debug: Whether to enable debug logging
        """
        level = logging.DEBUG if debug else logging.INFO
        
        logging.getLogger().setLevel(level)
        if self.console_handler:
            self.console_handler.setLevel(level)
    
    def log_exception(self, exception: Exception, context: str = "", logger: Optional[logging.Logger] = None) -> None:
        """
        Log an exception with optional context.
        
        Args:
            exception: The exception to log
            context: Optional context information
            logger: Optional specific logger to use (defaults to root logger)
        """
        logger = logger or logging.getLogger()
        
        error_type = type(exception).__name__
        error_message = str(exception)
        
        if context:
            logger.error(f"Exception in {context}: {error_type} - {error_message}")
        else:
            logger.error(f"Exception: {error_type} - {error_message}")
            
        if is_debug():
            logger.debug(f"Traceback:\n{traceback.format_exc()}")

# Create a global instance
log_manager = LogManager()

# Convenience functions
def get_logger(name: str) -> logging.Logger:
    """Get a logger by name."""
    return log_manager.get_logger(name)

def initialize(log_dir: Optional[Union[str, Path]] = None) -> None:
    """Initialize logging system."""
    log_manager.initialize(log_dir)

def set_debug(debug: bool = True) -> None:
    """Set debug mode for logging."""
    log_manager.set_debug(debug)

def log_exception(exception: Exception, context: str = "", logger: Optional[logging.Logger] = None) -> None:
    """Log an exception with optional context."""
    log_manager.log_exception(exception, context, logger)

# Core logger for this module
logger = get_logger("core")