#!/usr/bin/env python3
"""
Templates package for the LLM Platform web server.

Contains template handling and rendering logic for the web interface.
"""

from .engine import TemplateEngine
from .components import Component
from .assets import AssetManager
from .bundler import Bundler as AssetBundler