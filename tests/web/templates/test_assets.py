#!/usr/bin/env python3
"""
Unit tests for asset management system.

Tests the functionality of the asset manager, ensuring proper URL generation,
content retrieval, and cache busting.
"""

import unittest
import tempfile
import shutil
import os
from pathlib import Path
import json

from web.templates.assets import (
    AssetManager,
    get_url,
    get_urls,
    get_asset
)


class TestAssetManager(unittest.TestCase):
    """Test asset management system functionality."""
    
    def setUp(self):
        """Set up test environment."""
        # Create temporary test directory
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Create asset directories
        self.assets_dir = self.temp_dir / "assets"
        self.css_dir = self.assets_dir / "css"
        self.js_dir = self.assets_dir / "js"
        self.img_dir = self.assets_dir / "img"
        
        os.makedirs(self.assets_dir)
        os.makedirs(self.css_dir)
        os.makedirs(self.js_dir)
        os.makedirs(self.img_dir)
        
        # Create test assets
        with open(self.css_dir / "main.css", "w") as f:
            f.write("body { font-family: sans-serif; }")
            
        with open(self.css_dir / "theme.css", "w") as f:
            f.write(".theme { color: blue; }")
            
        with open(self.js_dir / "main.js", "w") as f:
            f.write("console.log('Hello');")
            
        with open(self.js_dir / "app.js", "w") as f:
            f.write("class App { constructor() {} }")
            
        with open(self.img_dir / "logo.png", "wb") as f:
            f.write(b"fake-png-data")
        
        # Create bundles.json
        with open(self.assets_dir / "bundles.json", "w") as f:
            json.dump({
                "css": {
                    "main": ["main.css", "theme.css"]
                },
                "js": {
                    "main": ["main.js", "app.js"]
                }
            }, f)
        
        # Create asset manager
        self.asset_manager = AssetManager(self.assets_dir)
    
    def tearDown(self):
        """Clean up after tests."""
        shutil.rmtree(self.temp_dir)
    
    def test_get_url(self):
        """Test getting asset URL."""
        # Get URL for existing asset
        url = self.asset_manager.get_url("css/main.css")
        
        # Check that URL includes cache busting parameter
        self.assertTrue(url.startswith("/assets/css/main.css?v="))
        
        # Get URL for non-existent asset
        url = self.asset_manager.get_url("css/nonexistent.css")
        
        # Check that URL is returned as-is
        self.assertEqual(url, "/assets/css/nonexistent.css")
    
    def test_get_urls(self):
        """Test getting multiple asset URLs with pattern matching."""
        # Get URLs for all CSS files
        urls = self.asset_manager.get_urls("css/*.css")
        
        # Check that all CSS files are included
        self.assertEqual(len(urls), 2)
        self.assertTrue(any(u.startswith("/assets/css/main.css?v=") for u in urls))
        self.assertTrue(any(u.startswith("/assets/css/theme.css?v=") for u in urls))
        
        # Get URLs for specific pattern
        urls = self.asset_manager.get_urls("js/main.js")
        
        # Check that only the matching file is included
        self.assertEqual(len(urls), 1)
        self.assertTrue(urls[0].startswith("/assets/js/main.js?v="))
    
    def test_get_asset(self):
        """Test getting asset content and mime type."""
        # Get existing asset
        content, mime_type = self.asset_manager.get_asset("css/main.css")
        
        # Check that content and mime type are correct
        self.assertEqual(content, b"body { font-family: sans-serif; }")
        self.assertEqual(mime_type, "text/css")
        
        # Get non-existent asset
        content, mime_type = self.asset_manager.get_asset("css/nonexistent.css")
        
        # Check that None is returned for both
        self.assertIsNone(content)
        self.assertIsNone(mime_type)
        
        # Get image asset
        content, mime_type = self.asset_manager.get_asset("img/logo.png")
        
        # Check that content and mime type are correct
        self.assertEqual(content, b"fake-png-data")
        self.assertEqual(mime_type, "image/png")
    
    def test_get_bundles(self):
        """Test getting bundle configurations."""
        # Get CSS bundles
        css_bundles = self.asset_manager.get_css_bundles()
        
        # Check that bundles are loaded correctly
        self.assertIn("main", css_bundles)
        self.assertEqual(css_bundles["main"], ["main.css", "theme.css"])
        
        # Get JS bundles
        js_bundles = self.asset_manager.get_js_bundles()
        
        # Check that bundles are loaded correctly
        self.assertIn("main", js_bundles)
        self.assertEqual(js_bundles["main"], ["main.js", "app.js"])
    
    def test_get_bundle_url(self):
        """Test getting URLs for bundled assets."""
        # Get URLs for CSS bundle
        urls = self.asset_manager.get_bundle_url("main", "css")
        
        # Check that URLs include both CSS files
        self.assertEqual(len(urls), 2)
        
        # Get URLs for non-existent bundle
        urls = self.asset_manager.get_bundle_url("nonexistent", "css")
        
        # Check that empty list is returned
        self.assertEqual(urls, "")
    
    def test_cache_busting_disabled(self):
        """Test asset URL generation with cache busting disabled."""
        # Create manager with cache busting disabled
        manager = AssetManager(self.assets_dir, cache_bust=False)
        
        # Get URL for existing asset
        url = manager.get_url("css/main.css")
        
        # Check that URL does not include cache busting parameter
        self.assertEqual(url, "/assets/css/main.css")
    
    @patch('web.templates.assets.get_app_path')
    def test_module_level_functions(self, mock_get_app_path):
        """Test module-level asset functions."""
        # Mock app path to point to our temp directory
        mock_get_app_path.return_value = self.temp_dir
        
        # Test module-level functions
        url = get_url("css/main.css")
        urls = get_urls("css/*.css")
        content, mime_type = get_asset("css/main.css")
        
        # Check that functions work
        self.assertTrue(url.startswith("/assets/css/main.css?v="))
        self.assertEqual(len(urls), 2)
        self.assertEqual(content, b"body { font-family: sans-serif; }")
        self.assertEqual(mime_type, "text/css")


if __name__ == "__main__":
    unittest.main()