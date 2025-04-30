#!/usr/bin/env python3
"""
Asset management system.

This module provides functionality for managing web assets like CSS, JS, and images,
with support for bundling, minification, and cache busting.
"""

import os
import logging
from typing import Dict, List, Any, Set, Optional, Tuple
from pathlib import Path
import hashlib
import json
import re
import mimetypes

from core.paths import get_app_path

logger = logging.getLogger(__name__)


class AssetManager:
    """Asset management system."""
    
    def __init__(self, assets_dir: Optional[Path] = None, cache_bust: bool = True):
        """Initialize the asset manager.
        
        Args:
            assets_dir: Optional custom assets directory.
                        If not provided, defaults to app_path/templates/assets
            cache_bust: Whether to add cache-busting query parameters to asset URLs
        """
        self.assets_dir = assets_dir or get_app_path() / "templates" / "assets"
        self.css_dir = self.assets_dir / "css"
        self.js_dir = self.assets_dir / "js"
        self.img_dir = self.assets_dir / "img"
        
        self.cache_bust = cache_bust
        self._cache: Dict[str, Dict[str, Any]] = {}
        
        # Set up mime types
        mimetypes.init()
        mimetypes.add_type('text/css', '.css')
        mimetypes.add_type('application/javascript', '.js')
        mimetypes.add_type('image/svg+xml', '.svg')
        
        # Check if directories exist
        if not self.assets_dir.exists():
            logger.warning(f"Assets directory {self.assets_dir} does not exist")
        
        if not self.css_dir.exists():
            logger.warning(f"CSS directory {self.css_dir} does not exist")
        
        if not self.js_dir.exists():
            logger.warning(f"JS directory {self.js_dir} does not exist")
        
        if not self.img_dir.exists():
            logger.warning(f"Image directory {self.img_dir} does not exist")
    
    def get_url(self, path: str) -> str:
        """Get the URL for an asset.
        
        Args:
            path: Asset path relative to assets directory
            
        Returns:
            Asset URL with cache-busting parameter if applicable
        """
        # Normalize path
        path = path.lstrip('/')
        
        # Construct file path
        asset_path = self.assets_dir / path
        
        # If file doesn't exist, return the path as-is
        if not asset_path.exists():
            logger.warning(f"Asset not found: {path}")
            return f"/assets/{path}"
        
        # If cache busting is disabled, return the path as-is
        if not self.cache_bust:
            return f"/assets/{path}"
        
        # Get file modification time for cache busting
        mtime = asset_path.stat().st_mtime
        mtime_hash = hashlib.md5(str(mtime).encode()).hexdigest()[:8]
        
        # Return URL with cache-busting parameter
        return f"/assets/{path}?v={mtime_hash}"
    
    def get_urls(self, pattern: str, recursive: bool = False) -> List[str]:
        """Get URLs for assets matching a pattern.
        
        Args:
            pattern: Asset pattern relative to assets directory (e.g., "css/*.css")
            recursive: Whether to search recursively
            
        Returns:
            List of asset URLs
        """
        # Split pattern into directory and file pattern
        parts = pattern.split('/')
        dir_parts = parts[:-1]
        file_pattern = parts[-1]
        
        # Construct directory path
        dir_path = self.assets_dir.joinpath(*dir_parts)
        
        # Get matching files
        urls = []
        
        if recursive:
            for root, _, files in os.walk(dir_path):
                root_path = Path(root)
                rel_path = root_path.relative_to(self.assets_dir)
                
                for file in files:
                    if self._match_pattern(file, file_pattern):
                        file_path = rel_path / file
                        urls.append(self.get_url(str(file_path)))
        else:
            if dir_path.exists():
                for file in dir_path.iterdir():
                    if file.is_file() and self._match_pattern(file.name, file_pattern):
                        file_path = Path(*dir_parts) / file.name
                        urls.append(self.get_url(str(file_path)))
        
        return urls
    
    def get_asset(self, path: str) -> Tuple[Optional[bytes], Optional[str]]:
        """Get an asset's content and mime type.
        
        Args:
            path: Asset path relative to assets directory
            
        Returns:
            Tuple of (content, mime_type), or (None, None) if not found
        """
        # Normalize path
        path = path.lstrip('/')
        
        # Construct file path
        asset_path = self.assets_dir / path
        
        # If file doesn't exist, return None
        if not asset_path.exists():
            logger.warning(f"Asset not found: {path}")
            return None, None
        
        # Get mime type based on file extension
        mime_type, _ = mimetypes.guess_type(str(asset_path))
        
        if mime_type is None:
            # Default to octet-stream if mime type can't be determined
            mime_type = 'application/octet-stream'
        
        # Read file content
        try:
            with open(asset_path, 'rb') as f:
                content = f.read()
            
            return content, mime_type
        except Exception as e:
            logger.error(f"Error reading asset {path}: {str(e)}")
            return None, None
    
    def get_css_bundles(self) -> Dict[str, List[str]]:
        """Get CSS bundles defined in bundles.json.
        
        Returns:
            Dictionary mapping bundle names to lists of CSS file paths
        """
        return self._get_bundles("css")
    
    def get_js_bundles(self) -> Dict[str, List[str]]:
        """Get JavaScript bundles defined in bundles.json.
        
        Returns:
            Dictionary mapping bundle names to lists of JS file paths
        """
        return self._get_bundles("js")
    
    def get_bundle_url(self, bundle_name: str, bundle_type: str) -> str:
        """Get the URL for a bundle.
        
        Args:
            bundle_name: Bundle name
            bundle_type: Bundle type ("css" or "js")
            
        Returns:
            Bundle URL with cache-busting parameter if applicable
        """
        # Get bundle files
        bundles = self._get_bundles(bundle_type)
        
        if bundle_name not in bundles:
            logger.warning(f"Bundle not found: {bundle_name} ({bundle_type})")
            return ""
        
        # Get URLs for bundle files
        urls = []
        for file_path in bundles[bundle_name]:
            urls.append(self.get_url(f"{bundle_type}/{file_path}"))
        
        return urls
    
    def _get_bundles(self, bundle_type: str) -> Dict[str, List[str]]:
        """Get bundles of a specific type.
        
        Args:
            bundle_type: Bundle type ("css" or "js")
            
        Returns:
            Dictionary mapping bundle names to lists of file paths
        """
        # Check cache
        cache_key = f"bundles_{bundle_type}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Load bundles from bundles.json
        bundles_path = self.assets_dir / "bundles.json"
        
        if not bundles_path.exists():
            logger.warning(f"Bundles file not found: {bundles_path}")
            return {}
        
        try:
            with open(bundles_path, 'r') as f:
                bundles_data = json.load(f)
            
            # Get bundles of the specified type
            bundles = bundles_data.get(bundle_type, {})
            
            # Cache bundles
            self._cache[cache_key] = bundles
            
            return bundles
        except Exception as e:
            logger.error(f"Error loading bundles: {str(e)}")
            return {}
    
    def _match_pattern(self, filename: str, pattern: str) -> bool:
        """Check if a filename matches a pattern.
        
        Args:
            filename: Filename to check
            pattern: Pattern to match against (supports * and ? wildcards)
            
        Returns:
            True if the filename matches the pattern, False otherwise
        """
        # Convert pattern to regex
        regex_pattern = pattern.replace('.', '\\.')
        regex_pattern = regex_pattern.replace('*', '.*')
        regex_pattern = regex_pattern.replace('?', '.')
        regex_pattern = f"^{regex_pattern}$"
        
        # Match filename against regex
        return bool(re.match(regex_pattern, filename))


# Create default asset manager
asset_manager = AssetManager()


# Module-level functions for easy access
def get_url(path: str) -> str:
    """Get the URL for an asset.
    
    Args:
        path: Asset path relative to assets directory
        
    Returns:
        Asset URL with cache-busting parameter if applicable
    """
    return asset_manager.get_url(path)


def get_urls(pattern: str, recursive: bool = False) -> List[str]:
    """Get URLs for assets matching a pattern.
    
    Args:
        pattern: Asset pattern relative to assets directory (e.g., "css/*.css")
        recursive: Whether to search recursively
        
    Returns:
        List of asset URLs
    """
    return asset_manager.get_urls(pattern, recursive)


def get_asset(path: str) -> Tuple[Optional[bytes], Optional[str]]:
    """Get an asset's content and mime type.
    
    Args:
        path: Asset path relative to assets directory
        
    Returns:
        Tuple of (content, mime_type), or (None, None) if not found
    """
    return asset_manager.get_asset(path)


def get_css_urls(bundle_name: str) -> List[str]:
    """Get URLs for CSS files in a bundle.
    
    Args:
        bundle_name: Bundle name
        
    Returns:
        List of CSS file URLs
    """
    return asset_manager.get_bundle_url(bundle_name, "css")


def get_js_urls(bundle_name: str) -> List[str]:
    """Get URLs for JavaScript files in a bundle.
    
    Args:
        bundle_name: Bundle name
        
    Returns:
        List of JavaScript file URLs
    """
    return asset_manager.get_bundle_url(bundle_name, "js")