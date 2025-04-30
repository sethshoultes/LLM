#!/usr/bin/env python3
"""
Configuration management module for the LLM Platform.

Provides a centralized configuration system that loads settings from:
- Environment variables
- Configuration files
- Command-line arguments
- Default values

This ensures consistent configuration across the entire application.
"""

import os
import json
import argparse
from typing import Any, Dict, Optional, Union, List, Set
from pathlib import Path
from .paths import resolve_path


class Config:
    """Centralized configuration management for the LLM Platform."""
    
    # Default configuration values
    DEFAULTS = {
        # Server settings
        "port": 5100,
        "port_max": 5110,
        "host": "0.0.0.0",
        
        # Feature flags
        "debug": False,
        "rag_enabled": False,
        "smart_context": True,
        
        # Model settings
        "default_max_tokens": 1024,
        "default_temperature": 0.7,
        "default_top_p": 0.95,
        
        # Context window settings
        "default_context_window": 2048,
        "large_context_window": 4096,
        "token_reserve_ratio": 0.15,
        "min_reserved_tokens": 256,
        
        # Cache settings
        "model_cache_enabled": True,
        "document_cache_ttl": 300,  # 5 minutes
        
        # Paths (relative to base_dir)
        "config_file": "config/settings.json",
    }
    
    # Environment variable mapping
    ENV_VARS = {
        "LLM_DEBUG_MODE": ("debug", lambda x: x == "1"),
        "LLM_RAG_ENABLED": ("rag_enabled", lambda x: x == "1"),
        "LLM_RAG_SMART_CONTEXT": ("smart_context", lambda x: x == "1"),
        "LLM_PORT": ("port", int),
        "LLM_PORT_MAX": ("port_max", int),
        "LLM_HOST": ("host", str),
        "LLAMA_CPP_VERBOSE": ("llama_cpp_verbose", lambda x: x == "1"),
    }
    
    def __init__(self):
        """Initialize configuration with default values and load from sources."""
        # Start with default values
        self._config = self.DEFAULTS.copy()
        
        # Load configuration in order of precedence
        self._load_from_file()
        self._load_from_env()
        
        # Parse command line arguments (highest precedence)
        # Not done here because it needs to be called explicitly after instance creation
        
        # Set key OS environment variables based on our config
        self._update_env_vars()
    
    def _load_from_file(self) -> None:
        """Load configuration from settings file if available."""
        # Resolve the path to the config file
        config_file = resolve_path(self._config["config_file"])
        
        if config_file.exists():
            try:
                with open(config_file, "r") as f:
                    file_config = json.load(f)
                    self._config.update(file_config)
            except Exception as e:
                print(f"Error loading configuration file: {e}")
    
    def _load_from_env(self) -> None:
        """Load configuration from environment variables."""
        for env_var, (config_key, convert) in self.ENV_VARS.items():
            if env_var in os.environ:
                try:
                    self._config[config_key] = convert(os.environ[env_var])
                except Exception as e:
                    print(f"Error converting environment variable {env_var}: {e}")
    
    def parse_args(self, args: Optional[List[str]] = None) -> None:
        """
        Parse command-line arguments and update configuration.
        
        Args:
            args: Command-line arguments to parse (defaults to sys.argv[1:])
        """
        parser = argparse.ArgumentParser(description="LLM Platform")
        
        # Add arguments for common configuration options
        parser.add_argument("--debug", action="store_true", help="Enable debug mode")
        parser.add_argument("--rag", action="store_true", help="Enable RAG features")
        parser.add_argument("--no-smart-context", action="store_true", help="Disable smart context management")
        parser.add_argument("--port", type=int, help="Starting port for the server")
        parser.add_argument("--host", type=str, help="Host to bind the server to")
        
        # Parse arguments
        parsed_args = parser.parse_args(args)
        
        # Update configuration with parsed arguments (only if specified)
        if parsed_args.debug:
            self._config["debug"] = True
        if parsed_args.rag:
            self._config["rag_enabled"] = True
        if parsed_args.no_smart_context:
            self._config["smart_context"] = False
        if parsed_args.port is not None:
            self._config["port"] = parsed_args.port
        if parsed_args.host is not None:
            self._config["host"] = parsed_args.host
    
    def _update_env_vars(self) -> None:
        """Update environment variables based on current configuration."""
        # Update key environment variables that external libraries may depend on
        if self._config.get("debug", False):
            os.environ["LLM_DEBUG_MODE"] = "1"
        else:
            os.environ["LLM_DEBUG_MODE"] = "0"
        
        if self._config.get("rag_enabled", False):
            os.environ["LLM_RAG_ENABLED"] = "1"
        else:
            os.environ["LLM_RAG_ENABLED"] = "0"
        
        if self._config.get("smart_context", True):
            os.environ["LLM_RAG_SMART_CONTEXT"] = "1"
        else:
            os.environ["LLM_RAG_SMART_CONTEXT"] = "0"
        
        # Set llama.cpp verbosity
        os.environ["LLAMA_CPP_VERBOSE"] = "1" if self._config.get("llama_cpp_verbose", False) else "0"
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key.
        
        Args:
            key: Configuration key to retrieve
            default: Default value if the key is not found
            
        Returns:
            The configuration value or the default
        """
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.
        
        Args:
            key: Configuration key to set
            value: Value to set
        """
        self._config[key] = value
        
        # Update environment variables if this key affects them
        if key in {"debug", "rag_enabled", "smart_context", "llama_cpp_verbose"}:
            self._update_env_vars()
    
    def is_debug(self) -> bool:
        """Check if debug mode is enabled."""
        return self._config.get("debug", False)
    
    def is_rag_enabled(self) -> bool:
        """Check if RAG features are enabled."""
        return self._config.get("rag_enabled", False)
    
    def is_smart_context_enabled(self) -> bool:
        """Check if smart context management is enabled."""
        return self._config.get("smart_context", True)
    
    def get_port_range(self) -> tuple:
        """Get the port range for the server."""
        return (self._config.get("port", 5100), self._config.get("port_max", 5110))
    
    def get_host(self) -> str:
        """Get the host for the server."""
        return self._config.get("host", "0.0.0.0")
    
    def save(self) -> None:
        """Save the current configuration to the settings file."""
        # Get keys from DEFAULTS to determine which ones to save
        keys_to_save = set(self.DEFAULTS.keys())
        
        # Exclude keys that shouldn't be saved
        exclude_keys = {"config_file"}
        keys_to_save -= exclude_keys
        
        # Create a dictionary with only the keys to save
        config_to_save = {k: self._config[k] for k in keys_to_save if k in self._config}
        
        # Resolve the path to the config file
        config_file = resolve_path(self._config["config_file"])
        
        # Ensure the directory exists
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Save the configuration
        try:
            with open(config_file, "w") as f:
                json.dump(config_to_save, f, indent=2)
        except Exception as e:
            print(f"Error saving configuration file: {e}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Get a copy of the full configuration as a dictionary."""
        return self._config.copy()

# Create a global instance
config = Config()

# Convenience functions
def get(key: str, default: Any = None) -> Any:
    """Get a configuration value by key."""
    return config.get(key, default)

def set_value(key: str, value: Any) -> None:
    """Set a configuration value."""
    config.set(key, value)

def is_debug() -> bool:
    """Check if debug mode is enabled."""
    return config.is_debug()

def is_rag_enabled() -> bool:
    """Check if RAG features are enabled."""
    return config.is_rag_enabled()

def parse_args(args: Optional[List[str]] = None) -> None:
    """Parse command-line arguments and update configuration."""
    config.parse_args(args)

def save_config() -> None:
    """Save the current configuration to the settings file."""
    config.save()