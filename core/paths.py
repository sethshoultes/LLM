#!/usr/bin/env python3
"""
Path management module for the LLM Platform.

Provides centralized path resolution and management to ensure consistent
path handling across the entire application.
"""

import os
import sys
from pathlib import Path
from typing import Union, Optional, Dict


class PathManager:
    """Centralized path management for the LLM Platform."""

    def __init__(self):
        """Initialize the path manager with base paths."""
        # Determine base directory
        if "LLM_BASE_DIR" in os.environ:
            self.base_dir = Path(os.environ["LLM_BASE_DIR"])
        else:
            # Use the directory where this module is located
            self.base_dir = Path(__file__).resolve().parent.parent

        # Ensure base_dir is absolute
        self.base_dir = self.base_dir.absolute()

        # Define standard paths
        self.paths = {
            "base": self.base_dir,
            "core": self.base_dir / "core",
            "models": self.base_dir / "models",
            "scripts": self.base_dir / "scripts",
            "templates": self.base_dir / "templates",
            "rag": self.base_dir / "rag_support",
            "llm_models": self.base_dir / "LLM-MODELS",
            "quantized": self.base_dir / "LLM-MODELS" / "quantized",
            "open_source": self.base_dir / "LLM-MODELS" / "open-source",
            "projects": self.base_dir / "rag_support" / "projects",
            "docs": self.base_dir / "docs",
            "config": self.base_dir / "config",
        }

        # Add paths to Python path if needed
        self._setup_python_path()

    def _setup_python_path(self) -> None:
        """Add necessary directories to Python path."""
        for path_name in ["base", "scripts"]:
            path_str = str(self.paths[path_name])
            if path_str not in sys.path:
                sys.path.insert(0, path_str)

    def get(self, name: str) -> Path:
        """
        Get a standard path by name.

        Args:
            name: Name of the path to retrieve

        Returns:
            Path object for the requested location

        Raises:
            KeyError: If the path name is not recognized
        """
        if name not in self.paths:
            raise KeyError(f"Unknown path name: {name}")
        return self.paths[name]

    def resolve(self, path: Union[str, Path], relative_to: Optional[str] = None) -> Path:
        """
        Resolve a path to an absolute path.

        Args:
            path: Path to resolve (can be relative or absolute)
            relative_to: Name of standard path to resolve relative to (if path is relative)

        Returns:
            Absolute Path object

        Raises:
            ValueError: If relative_to is not a recognized path name
        """
        # Convert to Path object if it's a string
        if isinstance(path, str):
            path = Path(path)

        # If path is absolute, return it directly
        if path.is_absolute():
            return path

        # If relative_to is specified, resolve relative to that path
        if relative_to:
            if relative_to not in self.paths:
                raise ValueError(f"Unknown relative path base: {relative_to}")
            return (self.paths[relative_to] / path).resolve()

        # Default to base directory
        return (self.base_dir / path).resolve()

    def ensure_dir(self, path: Union[str, Path], relative_to: Optional[str] = None) -> Path:
        """
        Ensure a directory exists and return its path.

        Args:
            path: Path to ensure (can be relative or absolute)
            relative_to: Name of standard path to resolve relative to (if path is relative)

        Returns:
            Absolute Path object to the ensured directory
        """
        dir_path = self.resolve(path, relative_to)
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path

    def list_models(self, format_filter: Optional[str] = None) -> Dict[str, Path]:
        """
        List available model paths in the LLM-MODELS directory.

        Args:
            format_filter: Optional filter for model format (e.g., 'gguf', 'safetensors')

        Returns:
            Dictionary mapping model names to their full paths
        """
        models = {}

        # Check quantized models
        quantized_dir = self.paths["quantized"]
        if quantized_dir.exists():
            for format_dir in quantized_dir.glob("*"):
                if format_dir.is_dir():
                    for model_file in format_dir.glob("*"):
                        if self._is_model_file(model_file, format_filter):
                            rel_path = model_file.relative_to(self.base_dir)
                            models[str(rel_path)] = model_file

        # Check open source models
        open_source_dir = self.paths["open_source"]
        if open_source_dir.exists():
            for family_dir in open_source_dir.glob("*"):
                if family_dir.is_dir():
                    for size_dir in family_dir.glob("*"):
                        if size_dir.is_dir():
                            for model_file in size_dir.glob("*"):
                                if self._is_model_file(model_file, format_filter):
                                    rel_path = model_file.relative_to(self.base_dir)
                                    models[str(rel_path)] = model_file

        return models

    def _is_model_file(self, path: Path, format_filter: Optional[str] = None) -> bool:
        """
        Check if a file is a model file.

        Args:
            path: Path to check
            format_filter: Optional filter for model format

        Returns:
            True if the file is a model file matching the format filter (if specified)
        """
        if not path.is_file():
            return False

        # Check if it has a valid model extension
        valid_extensions = [".bin", ".gguf", ".safetensors", ".pt"]
        if path.suffix.lower() not in valid_extensions:
            return False

        # If format filter is specified, check against it
        if format_filter:
            if format_filter.lower() == "gguf" and path.suffix.lower() == ".gguf":
                return True
            elif (
                format_filter.lower() == "ggml"
                and path.suffix.lower() == ".bin"
                and "ggml" in path.name.lower()
            ):
                return True
            elif (
                format_filter.lower() == "pytorch"
                and path.suffix.lower() in [".safetensors", ".pt", ".bin"]
                and "ggml" not in path.name.lower()
            ):
                return True
            # If filter is specified but doesn't match, return False
            return False

        # If no filter specified, it's a valid model file based on extension
        return True


# Create a global instance
path_manager = PathManager()


# Convenience functions
def get_path(name: str) -> Path:
    """Get a standard path by name."""
    return path_manager.get(name)


def resolve_path(path: Union[str, Path], relative_to: Optional[str] = None) -> Path:
    """Resolve a path to an absolute path."""
    return path_manager.resolve(path, relative_to)


def ensure_dir(path: Union[str, Path], relative_to: Optional[str] = None) -> Path:
    """Ensure a directory exists and return its path."""
    return path_manager.ensure_dir(path, relative_to)


def list_models(format_filter: Optional[str] = None) -> Dict[str, Path]:
    """List available model paths."""
    return path_manager.list_models(format_filter)


def get_app_path() -> Path:
    """Get the base application path."""
    return path_manager.base_dir
