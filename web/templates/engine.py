#!/usr/bin/env python3
"""
Template engine for the LLM Platform web server.

Provides functions for loading and rendering templates from files,
with support for template inheritance, partials, and context variables.
"""

import os
import re
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple

# Import core modules
try:
    from core.logging import get_logger
    from core.paths import get_base_dir
except ImportError:
    # Fallback if core modules are not available
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    get_logger = lambda name: logging.getLogger(name)
    get_base_dir = lambda: Path(__file__).resolve().parent.parent.parent

# Get logger for this module
logger = get_logger("web.templates.engine")

# Get base directory
BASE_DIR = get_base_dir()

# Template directories
TEMPLATES_DIR = BASE_DIR / "templates"
LAYOUTS_DIR = TEMPLATES_DIR / "layouts"
COMPONENTS_DIR = TEMPLATES_DIR / "components"

# Template cache
template_cache = {}
cache_enabled = True


class TemplateEngine:
    """
    Template rendering engine.
    
    Loads templates from files and renders them with context variables,
    supporting template inheritance, partials, and simple expressions.
    """
    
    def __init__(self, templates_dir=None, layouts_dir=None, components_dir=None):
        """
        Initialize template engine.
        
        Args:
            templates_dir: Base directory for templates
            layouts_dir: Directory for layout templates
            components_dir: Directory for component templates
        """
        # Set template directories
        self.templates_dir = Path(templates_dir) if templates_dir else TEMPLATES_DIR
        self.layouts_dir = Path(layouts_dir) if layouts_dir else LAYOUTS_DIR
        self.components_dir = Path(components_dir) if components_dir else COMPONENTS_DIR
        
        # Template cache
        self.cache = {}
        self.cache_enabled = cache_enabled
    
    def render_template(self, template_name, **context):
        """
        Render a template with context variables.
        
        Args:
            template_name: Name of the template file
            **context: Context variables for template rendering
            
        Returns:
            Rendered template string
        """
        # Load template
        template_content = self.load_template(template_name)
        
        # Check if template extends a layout
        layout_match = re.search(r'{%\s*extends\s+[\'"]([^\'"]+)[\'"].*?%}', template_content)
        
        if layout_match:
            # Template extends a layout
            layout_name = layout_match.group(1)
            layout_content = self.load_template(layout_name, is_layout=True)
            
            # Extract template blocks
            blocks = self._extract_blocks(template_content)
            
            # Replace block placeholders in layout
            rendered = layout_content
            for block_name, block_content in blocks.items():
                block_pattern = r'{%\s*block\s+' + re.escape(block_name) + r'\s*%}.*?{%\s*endblock\s*%}'
                rendered = re.sub(block_pattern, block_content, rendered, flags=re.DOTALL)
            
            # Remove any remaining block placeholders
            rendered = re.sub(r'{%\s*block\s+(\w+)\s*%}.*?{%\s*endblock\s*%}', '', rendered, flags=re.DOTALL)
        else:
            # Template doesn't extend a layout
            rendered = template_content
        
        # Process includes
        rendered = self._process_includes(rendered)
        
        # Render variables
        rendered = self._render_variables(rendered, context)
        
        # Render conditionals
        rendered = self._render_conditionals(rendered, context)
        
        # Render loops
        rendered = self._render_loops(rendered, context)
        
        return rendered
    
    def load_template(self, template_name, is_layout=False, is_component=False):
        """
        Load a template from file.
        
        Args:
            template_name: Name of the template file
            is_layout: Whether the template is a layout
            is_component: Whether the template is a component
            
        Returns:
            Template content as string
        """
        # Check cache first
        cache_key = f"{'layout' if is_layout else 'component' if is_component else 'template'}:{template_name}"
        if self.cache_enabled and cache_key in self.cache:
            return self.cache[cache_key]
        
        # Determine template directory
        if is_layout:
            template_dir = self.layouts_dir
        elif is_component:
            template_dir = self.components_dir
        else:
            template_dir = self.templates_dir
        
        # Add .html extension if not present
        if not template_name.endswith('.html'):
            template_name += '.html'
        
        # Load template from file
        try:
            template_path = template_dir / template_name
            with open(template_path, 'r') as f:
                content = f.read()
            
            # Cache template
            if self.cache_enabled:
                self.cache[cache_key] = content
            
            return content
        except Exception as e:
            logger.error(f"Error loading template {template_name}: {e}")
            return f"<!-- Error loading template {template_name}: {e} -->"
    
    def _extract_blocks(self, template_content):
        """
        Extract blocks from a template.
        
        Args:
            template_content: Template content string
            
        Returns:
            Dictionary mapping block names to block content
        """
        blocks = {}
        
        # Find all blocks
        block_pattern = r'{%\s*block\s+(\w+)\s*%}(.*?){%\s*endblock\s*%}'
        for match in re.finditer(block_pattern, template_content, re.DOTALL):
            block_name = match.group(1)
            block_content = match.group(2)
            blocks[block_name] = block_content
        
        return blocks
    
    def _process_includes(self, template_content):
        """
        Process include statements in a template.
        
        Args:
            template_content: Template content string
            
        Returns:
            Template with includes processed
        """
        include_pattern = r'{%\s*include\s+[\'"]([^\'"]+)[\'"].*?%}'
        
        # Find all includes
        def replace_include(match):
            include_name = match.group(1)
            include_content = self.load_template(include_name, is_component=True)
            return include_content
        
        # Replace includes
        rendered = re.sub(include_pattern, replace_include, template_content)
        
        return rendered
    
    def _render_variables(self, template_content, context):
        """
        Render variables in a template.
        
        Args:
            template_content: Template content string
            context: Context variables
            
        Returns:
            Template with variables rendered
        """
        # Simple variable pattern: {{ variable }}
        var_pattern = r'{{(.*?)}}'
        
        def replace_var(match):
            var_expr = match.group(1).strip()
            
            try:
                # Evaluate variable expression
                result = self._eval_expression(var_expr, context)
                
                # Convert to string
                if result is None:
                    return ''
                return str(result)
            except Exception as e:
                logger.error(f"Error rendering variable '{var_expr}': {e}")
                return f"<!-- Error: {e} -->"
        
        # Replace variables
        rendered = re.sub(var_pattern, replace_var, template_content)
        
        return rendered
    
    def _render_conditionals(self, template_content, context):
        """
        Render conditional statements in a template.
        
        Args:
            template_content: Template content string
            context: Context variables
            
        Returns:
            Template with conditionals rendered
        """
        # If-Else pattern
        if_pattern = r'{%\s*if\s+(.*?)\s*%}(.*?)(?:{%\s*else\s*%}(.*?))?{%\s*endif\s*%}'
        
        def replace_if(match):
            condition = match.group(1).strip()
            if_block = match.group(2)
            else_block = match.group(3) if match.group(3) else ''
            
            try:
                # Evaluate condition
                result = self._eval_expression(condition, context)
                
                # Return appropriate block
                if result:
                    return if_block
                else:
                    return else_block
            except Exception as e:
                logger.error(f"Error evaluating condition '{condition}': {e}")
                return f"<!-- Error in condition: {e} -->"
        
        # Process all conditionals
        rendered = template_content
        while re.search(if_pattern, rendered, re.DOTALL):
            rendered = re.sub(if_pattern, replace_if, rendered, flags=re.DOTALL)
        
        return rendered
    
    def _render_loops(self, template_content, context):
        """
        Render loop statements in a template.
        
        Args:
            template_content: Template content string
            context: Context variables
            
        Returns:
            Template with loops rendered
        """
        # For loop pattern
        for_pattern = r'{%\s*for\s+(\w+)\s+in\s+(.*?)\s*%}(.*?){%\s*endfor\s*%}'
        
        def replace_for(match):
            item_name = match.group(1)
            collection_expr = match.group(2).strip()
            loop_block = match.group(3)
            
            try:
                # Evaluate collection expression
                collection = self._eval_expression(collection_expr, context)
                
                # Iterate over collection
                result = []
                loop_index = 0
                
                if collection:
                    for item in collection:
                        # Create loop context
                        loop_context = context.copy()
                        loop_context[item_name] = item
                        loop_context['loop'] = {
                            'index': loop_index,
                            'index1': loop_index + 1,
                            'first': loop_index == 0,
                            'last': loop_index == len(collection) - 1
                        }
                        
                        # Render loop block with loop context
                        rendered_block = loop_block
                        rendered_block = self._render_variables(rendered_block, loop_context)
                        rendered_block = self._render_conditionals(rendered_block, loop_context)
                        
                        result.append(rendered_block)
                        loop_index += 1
                
                return ''.join(result)
            except Exception as e:
                logger.error(f"Error in loop '{item_name} in {collection_expr}': {e}")
                return f"<!-- Error in loop: {e} -->"
        
        # Process all loops
        rendered = template_content
        while re.search(for_pattern, rendered, re.DOTALL):
            rendered = re.sub(for_pattern, replace_for, rendered, flags=re.DOTALL)
        
        return rendered
    
    def _eval_expression(self, expr, context):
        """
        Evaluate a simple expression in template context.
        
        Args:
            expr: Expression string
            context: Context variables
            
        Returns:
            Evaluated expression result
        """
        # Simple implementation - handles variable access and basic methods
        expr = expr.strip()
        
        # Handle literals
        if expr.lower() == 'true':
            return True
        elif expr.lower() == 'false':
            return False
        elif expr.lower() == 'none':
            return None
        elif expr.isdigit():
            return int(expr)
        elif expr.startswith("'") and expr.endswith("'"):
            return expr[1:-1]
        elif expr.startswith('"') and expr.endswith('"'):
            return expr[1:-1]
        
        # Handle attribute access (obj.attr)
        if '.' in expr:
            obj_name, attr_name = expr.split('.', 1)
            obj = context.get(obj_name)
            
            if obj is None:
                return None
            
            # Handle nested attributes
            for part in attr_name.split('.'):
                if hasattr(obj, part):
                    obj = getattr(obj, part)
                elif isinstance(obj, dict) and part in obj:
                    obj = obj[part]
                else:
                    return None
            
            return obj
        
        # Handle variable lookup
        return context.get(expr)


# Create global template engine
engine = TemplateEngine()


def render_template(template_name, **context):
    """
    Render a template with context variables.
    
    Args:
        template_name: Name of the template file
        **context: Context variables for template rendering
        
    Returns:
        Rendered template string
    """
    return engine.render_template(template_name, **context)


def set_template_dirs(templates_dir=None, layouts_dir=None, components_dir=None):
    """
    Set template directories.
    
    Args:
        templates_dir: Base directory for templates
        layouts_dir: Directory for layout templates
        components_dir: Directory for component templates
    """
    if templates_dir:
        engine.templates_dir = Path(templates_dir)
    
    if layouts_dir:
        engine.layouts_dir = Path(layouts_dir)
    
    if components_dir:
        engine.components_dir = Path(components_dir)


def enable_cache(enabled=True):
    """Enable or disable template caching."""
    engine.cache_enabled = enabled
    
    # Clear cache if disabling
    if not enabled:
        engine.cache = {}


def clear_cache():
    """Clear the template cache."""
    engine.cache = {}


# For testing
if __name__ == "__main__":
    # Example template
    example_template = """
    {% extends "main.html" %}
    
    {% block title %}Example Page{% endblock %}
    
    {% block content %}
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
    {% endblock %}
    """
    
    # Mock layout template
    mock_layout = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>{% block title %}Default Title{% endblock %}</title>
    </head>
    <body>
        <header>
            {% include "header.html" %}
        </header>
        
        <main>
            {% block content %}
            <p>Default content</p>
            {% endblock %}
        </main>
        
        <footer>
            {% include "footer.html" %}
        </footer>
    </body>
    </html>
    """
    
    # Mock includes
    mock_header = "<nav>Navigation</nav>"
    mock_footer = "<p>Footer content</p>"
    
    # Mock loading
    def mock_load_template(name, *args, **kwargs):
        if name == "main.html" or name == "main":
            return mock_layout
        elif name == "header.html" or name == "header":
            return mock_header
        elif name == "footer.html" or name == "footer":
            return mock_footer
        else:
            return f"<!-- Template {name} not found -->"
    
    # Modify engine for testing
    engine.load_template = mock_load_template
    
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
    
    # Render template
    result = render_template("example", **context)
    
    print(result)