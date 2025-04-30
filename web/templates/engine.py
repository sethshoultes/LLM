#!/usr/bin/env python3
"""
Template engine for the LLM Platform web server.

Provides functions for loading and rendering templates from files,
with support for template inheritance, partials, and context variables.
"""

import os
import re
import logging
import json
import hashlib
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple

# Import jinja2 for modern template handling
from jinja2 import Environment, FileSystemLoader, select_autoescape, Template
from jinja2.exceptions import TemplateNotFound

# Import core modules
from core.paths import get_app_path

# Get logger for this module
logger = logging.getLogger(__name__)


class TemplateEngine:
    """
    Template rendering engine.
    
    Loads templates from files and renders them with context variables,
    supporting template inheritance, partials, and component-based UI.
    """
    
    def __init__(self, template_dir: Optional[Union[str, Path]] = None):
        """Initialize the template engine.
        
        Args:
            template_dir: Optional custom template directory.
                          If not provided, defaults to app_path/templates
        """
        self.template_dir = Path(template_dir) if template_dir else get_app_path() / "templates"
        self.components_dir = self.template_dir / "components"
        self.layouts_dir = self.template_dir / "layouts"
        
        # Check if directories exist
        if not self.template_dir.exists():
            logger.warning(f"Template directory {self.template_dir} does not exist")
            
        if not self.components_dir.exists():
            logger.warning(f"Components directory {self.components_dir} does not exist")
            
        if not self.layouts_dir.exists():
            logger.warning(f"Layouts directory {self.layouts_dir} does not exist")
        
        # Initialize Jinja environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(['html', 'xml']),
            cache_size=100,
            auto_reload=True
        )
        
        # Template cache with timestamps
        self._template_cache: Dict[str, Dict[str, Any]] = {}
        
        # Register custom filters
        self.register_filters()
        
        # Register global functions
        self.register_globals()
    
    def register_filters(self):
        """Register custom template filters."""
        # Add JSON filter
        self.env.filters['json'] = lambda obj: json.dumps(obj)
        
        # Add date formatting filter
        self.env.filters['format_date'] = lambda d, fmt='%Y-%m-%d': d.strftime(fmt) if d else ''
        
        # Add truncate filter with ellipsis
        def truncate(s, length=50, end='...'):
            if not s:
                return ''
            if len(s) <= length:
                return s
            return s[:length].rstrip() + end
            
        self.env.filters['truncate'] = truncate
    
    def register_globals(self):
        """Register global functions and variables for templates."""
        # Add include_component function
        self.env.globals['include_component'] = self.include_component
        
        # Add asset_url function
        self.env.globals['asset_url'] = self.get_asset_url
        
        # Add static variables
        self.env.globals['app_name'] = "LLM Platform"
        self.env.globals['version'] = "1.0.0"
    
    def include_component(self, name: str, **kwargs) -> str:
        """Include a component in a template.
        
        Args:
            name: Component name (without extension)
            **kwargs: Component context variables
            
        Returns:
            Rendered component HTML
        """
        try:
            return self.render_component(name, **kwargs)
        except Exception as e:
            logger.error(f"Error including component {name}: {str(e)}")
            return f"<!-- Error including component {name}: {str(e)} -->"
    
    def get_asset_url(self, path: str) -> str:
        """Get the URL for an asset.
        
        Args:
            path: Asset path relative to assets directory
            
        Returns:
            Asset URL with cache-busting parameter if applicable
        """
        # Construct file path
        asset_path = self.template_dir / "assets" / path
        
        # If file doesn't exist, return the path as-is
        if not asset_path.exists():
            return f"/assets/{path}"
        
        # Get file modification time for cache busting
        mtime = asset_path.stat().st_mtime
        mtime_hash = hashlib.md5(str(mtime).encode()).hexdigest()[:8]
        
        # Return URL with cache-busting parameter
        return f"/assets/{path}?v={mtime_hash}"
    
    def render_template(self, template_name: str, context: Dict[str, Any] = None) -> str:
        """Render a template with the given context.
        
        Args:
            template_name: Template name (with or without extension)
            context: Template variables
            
        Returns:
            Rendered template as string
            
        Raises:
            TemplateNotFound: If the template could not be found
        """
        if context is None:
            context = {}
            
        # Add .html extension if not present
        if not template_name.endswith('.html'):
            template_name = f"{template_name}.html"
        
        try:
            # Get template
            template = self.env.get_template(template_name)
            
            # Render template with context
            return template.render(**context)
        except TemplateNotFound:
            logger.error(f"Template not found: {template_name}")
            raise
        except Exception as e:
            logger.error(f"Error rendering template {template_name}: {str(e)}")
            raise
    
    def render_component(self, component_name: str, **kwargs) -> str:
        """Render a component with the given context.
        
        Args:
            component_name: Component name (without extension)
            **kwargs: Component context variables
            
        Returns:
            Rendered component as string
            
        Raises:
            TemplateNotFound: If the component could not be found
        """
        # Add .html extension if not present
        if not component_name.endswith('.html'):
            component_name = f"{component_name}.html"
        
        # Construct component path
        component_path = f"components/{component_name}"
        
        try:
            # Get component template
            template = self.env.get_template(component_path)
            
            # Render component with context
            return template.render(**kwargs)
        except TemplateNotFound:
            logger.error(f"Component not found: {component_name}")
            raise
        except Exception as e:
            logger.error(f"Error rendering component {component_name}: {str(e)}")
            raise
    
    def render_string(self, template_string: str, context: Dict[str, Any] = None) -> str:
        """Render a template string with the given context.
        
        Args:
            template_string: Template string
            context: Template variables
            
        Returns:
            Rendered template as string
        """
        if context is None:
            context = {}
            
        try:
            # Create template from string
            template = self.env.from_string(template_string)
            
            # Render template with context
            return template.render(**context)
        except Exception as e:
            logger.error(f"Error rendering template string: {str(e)}")
            raise
    
    def render_error(self, error_code: int, message: str = None, **kwargs) -> str:
        """Render an error page.
        
        Args:
            error_code: HTTP error code (e.g., 404, 500)
            message: Optional error message
            **kwargs: Additional context variables
            
        Returns:
            Rendered error page as string
        """
        # Set up error context
        context = {
            "error_code": error_code,
            "error_message": message,
            **kwargs
        }
        
        try:
            # Render error template
            return self.render_template("layouts/error", context)
        except Exception as e:
            logger.error(f"Error rendering error page: {str(e)}")
            # Fallback to simple error page
            return f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Error {error_code}</title>
            </head>
            <body>
                <h1>Error {error_code}</h1>
                <p>{message or 'An error occurred'}</p>
            </body>
            </html>
            """


# Create default template engine instance
template_engine = TemplateEngine()


# Module-level functions for easy access
def render_template(template_name: str, context: Dict[str, Any] = None) -> str:
    """Render a template with the given context.
    
    Args:
        template_name: Template name (with or without extension)
        context: Template variables
        
    Returns:
        Rendered template as string
    """
    return template_engine.render_template(template_name, context or {})


def render_component(component_name: str, **kwargs) -> str:
    """Render a component with the given context.
    
    Args:
        component_name: Component name (without extension)
        **kwargs: Component context variables
        
    Returns:
        Rendered component as string
    """
    return template_engine.render_component(component_name, **kwargs)


def render_string(template_string: str, context: Dict[str, Any] = None) -> str:
    """Render a template string with the given context.
    
    Args:
        template_string: Template string
        context: Template variables
        
    Returns:
        Rendered template as string
    """
    return template_engine.render_string(template_string, context or {})


def render_error(error_code: int, message: str = None, **kwargs) -> str:
    """Render an error page.
    
    Args:
        error_code: HTTP error code (e.g., 404, 500)
        message: Optional error message
        **kwargs: Additional context variables
        
    Returns:
        Rendered error page as string
    """
    return template_engine.render_error(error_code, message, **kwargs)


def get_asset_url(path: str) -> str:
    """Get the URL for an asset.
    
    Args:
        path: Asset path relative to assets directory
        
    Returns:
        Asset URL with cache-busting parameter
    """
    return template_engine.get_asset_url(path)


# For testing
if __name__ == "__main__":
    # Example template string
    example_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>{{ page_title }}</title>
        <link rel="stylesheet" href="{{ asset_url('css/main.css') }}">
    </head>
    <body>
        <header>
            {{ include_component('header', title=page_title) }}
        </header>
        
        <main>
            <h1>{{ page_title }}</h1>
            
            <ul>
            {% for item in items %}
                <li>{{ item.name }}: {{ item.value }}</li>
            {% endfor %}
            </ul>
            
            {% if show_extra %}
                <p>Extra content here!</p>
            {% else %}
                <p>No extra content.</p>
            {% endif %}
        </main>
        
        <footer>
            {{ include_component('footer') }}
        </footer>
        
        <script src="{{ asset_url('js/main.js') }}"></script>
    </body>
    </html>
    """
    
    # Test context
    context = {
        "page_title": "Test Page",
        "items": [
            {"name": "Item 1", "value": 100},
            {"name": "Item 2", "value": 200},
            {"name": "Item 3", "value": 300}
        ],
        "show_extra": True
    }
    
    # Mock file system for testing
    template_engine.env.loader = None  # Disable file loader
    
    # Render template string
    try:
        result = render_string(example_template, context)
        print(result)
    except Exception as e:
        print(f"Error: {e}")