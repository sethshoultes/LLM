#!/usr/bin/env python3
"""
Unit tests for template engine.

Tests the functionality of the template engine, ensuring proper rendering,
component inclusion, and error handling.
"""

import unittest
import tempfile
import shutil
import os
from pathlib import Path

    TemplateEngine, 
    render_template, 
    render_component, 
    render_string, 
    render_error
)


class TestTemplateEngine(unittest.TestCase):
    """Test template engine functionality."""
    
    def setUp(self):
        """Set up test environment."""
        # Create temporary test directory
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Create template directories
        self.templates_dir = self.temp_dir / "templates"
        self.components_dir = self.templates_dir / "components"
        self.layouts_dir = self.templates_dir / "layouts"
        
        os.makedirs(self.templates_dir)
        os.makedirs(self.components_dir)
        os.makedirs(self.layouts_dir)
        
        # Create test templates
        self.test_layout = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>{% block title %}Default Title{% endblock %}</title>
        </head>
        <body>
            <header>
                {{ include_component('header') }}
            </header>
            <main>
                {% block content %}
                <p>Default content</p>
                {% endblock %}
            </main>
            <footer>
                {{ include_component('footer') }}
            </footer>
        </body>
        </html>
        """
        
        self.test_template = """
        {% extends "main.html" %}
        
        {% block title %}Test Page{% endblock %}
        
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
        
        self.test_header = "<nav>Navigation</nav>"
        self.test_footer = "<p>Footer content</p>"
        
        # Write templates to files
        with open(self.layouts_dir / "main.html", "w") as f:
            f.write(self.test_layout)
            
        with open(self.templates_dir / "test.html", "w") as f:
            f.write(self.test_template)
            
        with open(self.components_dir / "header.html", "w") as f:
            f.write(self.test_header)
            
        with open(self.components_dir / "footer.html", "w") as f:
            f.write(self.test_footer)
        
        # Create test engine
        self.engine = TemplateEngine(self.templates_dir)
        
        # Test context
        self.test_context = {
            "page_title": "Test Page",
            "items": [
                {"name": "Item 1", "value": 100},
                {"name": "Item 2", "value": 200},
                {"name": "Item 3", "value": 300}
            ],
            "show_extra": True
        }
    
    def tearDown(self):
        """Clean up after tests."""
        shutil.rmtree(self.temp_dir)
    
    def test_render_template(self):
        """Test rendering a template with context."""
        # Render template
        result = self.engine.render_template("test.html", self.test_context)
        
        # Check that template was rendered correctly
        self.assertIn("<title>Test Page</title>", result)
        self.assertIn("<h1>Test Page</h1>", result)
        self.assertIn("<li>Item 1: 100</li>", result)
        self.assertIn("<li>Item 2: 200</li>", result)
        self.assertIn("<li>Item 3: 300</li>", result)
        self.assertIn("<p>Extra content here!</p>", result)
        self.assertIn("<nav>Navigation</nav>", result)
        self.assertIn("<p>Footer content</p>", result)
    
    def test_render_component(self):
        """Test rendering a component with context."""
        # Render component
        result = self.engine.render_component("header.html")
        
        # Check that component was rendered correctly
        self.assertEqual(result, self.test_header)
    
    def test_render_string(self):
        """Test rendering a template string with context."""
        # Template string
        template_string = """
        <h1>{{ page_title }}</h1>
        <p>{{ items|length }} items</p>
        """
        
        # Render string
        result = self.engine.render_string(template_string, self.test_context)
        
        # Check that string was rendered correctly
        self.assertIn("<h1>Test Page</h1>", result)
        self.assertIn("<p>3 items</p>", result)
    
    def test_render_error(self):
        """Test rendering an error page."""
        # Render error
        result = self.engine.render_error(404, "Page not found")
        
        # Check that error was rendered correctly
        self.assertIn("Error 404", result)
        self.assertIn("Page not found", result)
    
    def test_template_not_found(self):
        """Test handling of template not found errors."""
        # Try to render non-existent template
        with self.assertRaises(Exception):
            self.engine.render_template("nonexistent.html")
    
    def test_component_not_found(self):
        """Test handling of component not found errors."""
        # Try to render non-existent component
        with self.assertRaises(Exception):
            self.engine.render_component("nonexistent.html")
    
    def test_custom_filters(self):
        """Test custom Jinja2 filters."""
        # Template string with custom filters
        template_string = """
        <p>{{ items|json }}</p>
        <p>{{ page_title|truncate(8) }}</p>
        """
        
        # Render string
        result = self.engine.render_string(template_string, self.test_context)
        
        # Check that custom filters work
        self.assertIn("[{\"name\": \"Item 1\", \"value\": 100},", result)
        self.assertIn("<p>Test Pag...</p>", result)
    
    @patch('web.templates.engine.get_app_path')
    def test_module_level_functions(self, mock_get_app_path):
        """Test module-level rendering functions."""
        # Mock app path to point to our temp directory
        mock_get_app_path.return_value = self.temp_dir
        
        # Create a template string to test with
        template_string = "<p>{{ test_var }}</p>"
        
        # Test module-level functions
        result1 = render_string(template_string, {"test_var": "Test value"})
        result2 = render_error(500, "Test error")
        
        # Check that functions work
        self.assertEqual(result1, "<p>Test value</p>")
        self.assertIn("Error 500", result2)
        self.assertIn("Test error", result2)


if __name__ == "__main__":
    unittest.main()