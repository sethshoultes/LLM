#!/usr/bin/env python3
"""
Asset bundling system.

This module provides functionality for bundling, minifying, and optimizing
CSS and JavaScript assets for production use.
"""

import os
import logging
from typing import Dict, List, Any, Optional, Union, Tuple
from pathlib import Path
import hashlib
import json
import re
import time

from core.paths import get_app_path

logger = logging.getLogger(__name__)


class Bundler:
    """Asset bundling system."""
    
    def __init__(self, assets_dir: Optional[Path] = None, output_dir: Optional[Path] = None):
        """Initialize the bundler.
        
        Args:
            assets_dir: Optional custom assets directory.
                        If not provided, defaults to app_path/templates/assets
            output_dir: Optional custom output directory.
                        If not provided, defaults to app_path/templates/assets/dist
        """
        self.assets_dir = assets_dir or get_app_path() / "templates" / "assets"
        self.output_dir = output_dir or self.assets_dir / "dist"
        
        self.css_dir = self.assets_dir / "css"
        self.js_dir = self.assets_dir / "js"
        
        # Check if directories exist
        if not self.assets_dir.exists():
            logger.warning(f"Assets directory {self.assets_dir} does not exist")
        
        if not self.css_dir.exists():
            logger.warning(f"CSS directory {self.css_dir} does not exist")
        
        if not self.js_dir.exists():
            logger.warning(f"JS directory {self.js_dir} does not exist")
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Load bundle configuration
        self.bundles = self._load_bundles()
    
    def _load_bundles(self) -> Dict[str, Any]:
        """Load bundle configuration from bundles.json.
        
        Returns:
            Bundle configuration as a dictionary
        """
        bundles_path = self.assets_dir / "bundles.json"
        
        if not bundles_path.exists():
            logger.warning(f"Bundles file not found: {bundles_path}")
            return {"css": {}, "js": {}}
        
        try:
            with open(bundles_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading bundles: {str(e)}")
            return {"css": {}, "js": {}}
    
    def bundle_css(self, bundle_name: str = None) -> bool:
        """Bundle CSS files.
        
        Args:
            bundle_name: Optional bundle name.
                        If provided, only this bundle will be processed.
                        Otherwise, all CSS bundles will be processed.
        
        Returns:
            True if successful, False otherwise
        """
        if bundle_name:
            if bundle_name not in self.bundles.get("css", {}):
                logger.error(f"CSS bundle not found: {bundle_name}")
                return False
            
            bundles = {bundle_name: self.bundles["css"][bundle_name]}
        else:
            bundles = self.bundles.get("css", {})
        
        for name, files in bundles.items():
            try:
                # Concatenate CSS files
                css_content = self._concatenate_files(files, self.css_dir)
                
                # Minify CSS
                css_content = self._minify_css(css_content)
                
                # Write bundle file
                bundle_path = self.output_dir / f"{name}.min.css"
                with open(bundle_path, 'w') as f:
                    f.write(css_content)
                
                logger.info(f"Created CSS bundle: {bundle_path}")
            except Exception as e:
                logger.error(f"Error bundling CSS for {name}: {str(e)}")
                return False
        
        return True
    
    def bundle_js(self, bundle_name: str = None) -> bool:
        """Bundle JavaScript files.
        
        Args:
            bundle_name: Optional bundle name.
                        If provided, only this bundle will be processed.
                        Otherwise, all JS bundles will be processed.
        
        Returns:
            True if successful, False otherwise
        """
        if bundle_name:
            if bundle_name not in self.bundles.get("js", {}):
                logger.error(f"JS bundle not found: {bundle_name}")
                return False
            
            bundles = {bundle_name: self.bundles["js"][bundle_name]}
        else:
            bundles = self.bundles.get("js", {})
        
        for name, files in bundles.items():
            try:
                # Concatenate JS files
                js_content = self._concatenate_files(files, self.js_dir)
                
                # Minify JS
                js_content = self._minify_js(js_content)
                
                # Write bundle file
                bundle_path = self.output_dir / f"{name}.min.js"
                with open(bundle_path, 'w') as f:
                    f.write(js_content)
                
                logger.info(f"Created JS bundle: {bundle_path}")
            except Exception as e:
                logger.error(f"Error bundling JS for {name}: {str(e)}")
                return False
        
        return True
    
    def bundle_all(self) -> bool:
        """Bundle all CSS and JavaScript files.
        
        Returns:
            True if successful, False otherwise
        """
        css_success = self.bundle_css()
        js_success = self.bundle_js()
        
        return css_success and js_success
    
    def update_manifest(self) -> bool:
        """Update the asset manifest file.
        
        Creates a manifest.json file in the output directory with information
        about all bundled assets, including file paths and hashes.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            manifest = {
                "css": {},
                "js": {},
                "generated_at": time.time()
            }
            
            # Add CSS bundles to manifest
            for name in self.bundles.get("css", {}):
                file_path = f"{name}.min.css"
                bundle_path = self.output_dir / file_path
                
                if bundle_path.exists():
                    # Get file hash
                    with open(bundle_path, 'rb') as f:
                        file_hash = hashlib.md5(f.read()).hexdigest()
                    
                    manifest["css"][name] = {
                        "path": file_path,
                        "hash": file_hash,
                        "size": bundle_path.stat().st_size
                    }
            
            # Add JS bundles to manifest
            for name in self.bundles.get("js", {}):
                file_path = f"{name}.min.js"
                bundle_path = self.output_dir / file_path
                
                if bundle_path.exists():
                    # Get file hash
                    with open(bundle_path, 'rb') as f:
                        file_hash = hashlib.md5(f.read()).hexdigest()
                    
                    manifest["js"][name] = {
                        "path": file_path,
                        "hash": file_hash,
                        "size": bundle_path.stat().st_size
                    }
            
            # Write manifest file
            manifest_path = self.output_dir / "manifest.json"
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2)
            
            logger.info(f"Updated asset manifest: {manifest_path}")
            return True
        except Exception as e:
            logger.error(f"Error updating asset manifest: {str(e)}")
            return False
    
    def clean(self) -> bool:
        """Clean the output directory.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete all files in the output directory
            for file in self.output_dir.glob("*"):
                if file.is_file():
                    file.unlink()
            
            logger.info(f"Cleaned output directory: {self.output_dir}")
            return True
        except Exception as e:
            logger.error(f"Error cleaning output directory: {str(e)}")
            return False
    
    def _concatenate_files(self, files: List[str], base_dir: Path) -> str:
        """Concatenate files into a single string.
        
        Args:
            files: List of file paths relative to base_dir
            base_dir: Base directory for file paths
            
        Returns:
            Concatenated file content
            
        Raises:
            FileNotFoundError: If a file is not found
            IOError: If there is an error reading a file
        """
        content = []
        
        for file_path in files:
            # Normalize file path
            file_path = file_path.lstrip('/')
            
            # Construct full path
            full_path = base_dir / file_path
            
            # Read file content
            if not full_path.exists():
                raise FileNotFoundError(f"File not found: {full_path}")
            
            with open(full_path, 'r') as f:
                file_content = f.read()
            
            # Add file content with separator
            content.append(f"/* {file_path} */")
            content.append(file_content)
            content.append("")
        
        return "\n".join(content)
    
    def _minify_css(self, css_content: str) -> str:
        """Minify CSS content.
        
        Args:
            css_content: CSS content to minify
            
        Returns:
            Minified CSS content
        """
        try:
            # Simple CSS minification - for production, consider using a proper CSS minifier
            # Remove comments
            css_content = re.sub(r'/\*[\s\S]*?\*/', '', css_content)
            
            # Remove whitespace
            css_content = re.sub(r'\s+', ' ', css_content)
            css_content = re.sub(r'([,:;{}])\s+', r'\1', css_content)
            css_content = re.sub(r'\s+([,:;{}])', r'\1', css_content)
            
            # Remove semicolons before closing brace
            css_content = re.sub(r';\s*}', '}', css_content)
            
            # Remove leading/trailing whitespace
            css_content = css_content.strip()
            
            return css_content
        except Exception as e:
            logger.error(f"Error minifying CSS: {str(e)}")
            return css_content
    
    def _minify_js(self, js_content: str) -> str:
        """Minify JavaScript content.
        
        Args:
            js_content: JavaScript content to minify
            
        Returns:
            Minified JavaScript content
        """
        try:
            # Simple JS minification - for production, consider using a proper JS minifier
            # like UglifyJS or Terser
            
            # Remove comments
            js_content = re.sub(r'//.*$', '', js_content, flags=re.MULTILINE)
            js_content = re.sub(r'/\*[\s\S]*?\*/', '', js_content)
            
            # Remove whitespace
            js_content = re.sub(r'\s+', ' ', js_content)
            
            # Remove whitespace around operators
            js_content = re.sub(r'\s*([=+\-*/<>!&|:?;,{}()])\s*', r'\1', js_content)
            
            # Fix double operators
            js_content = re.sub(r'([=+\-*/<>!&|:?;,{}()])\1', r'\1\1', js_content)
            
            # Remove semicolons before closing brace
            js_content = re.sub(r';\s*}', '}', js_content)
            
            # Remove leading/trailing whitespace
            js_content = js_content.strip()
            
            return js_content
        except Exception as e:
            logger.error(f"Error minifying JavaScript: {str(e)}")
            return js_content


# Create default bundler
bundler = Bundler()


# Module-level functions for easy access
def bundle_css(bundle_name: str = None) -> bool:
    """Bundle CSS files.
    
    Args:
        bundle_name: Optional bundle name.
                    If provided, only this bundle will be processed.
                    Otherwise, all CSS bundles will be processed.
    
    Returns:
        True if successful, False otherwise
    """
    return bundler.bundle_css(bundle_name)


def bundle_js(bundle_name: str = None) -> bool:
    """Bundle JavaScript files.
    
    Args:
        bundle_name: Optional bundle name.
                    If provided, only this bundle will be processed.
                    Otherwise, all JS bundles will be processed.
    
    Returns:
        True if successful, False otherwise
    """
    return bundler.bundle_js(bundle_name)


def bundle_all() -> bool:
    """Bundle all CSS and JavaScript files.
    
    Returns:
        True if successful, False otherwise
    """
    return bundler.bundle_all()


def update_manifest() -> bool:
    """Update the asset manifest file.
    
    Creates a manifest.json file in the output directory with information
    about all bundled assets, including file paths and hashes.
    
    Returns:
        True if successful, False otherwise
    """
    return bundler.update_manifest()


def clean() -> bool:
    """Clean the output directory.
    
    Returns:
        True if successful, False otherwise
    """
    return bundler.clean()