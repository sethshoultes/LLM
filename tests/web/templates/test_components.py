#!/usr/bin/env python3
"""
Unit tests for component-based UI system.

Tests the functionality of the component classes, ensuring proper rendering,
attributes handling, and component composition.
"""

import unittest
from unittest.mock import patch, MagicMock
import tempfile
import shutil
import os
from pathlib import Path

from web.templates.components import (
    Component,
    Container,
    TextBlock,
    Button,
    Form,
    Input,
    Select,
    NavBar,
    Card,
    Modal,
    Table
)


class TestComponents(unittest.TestCase):
    """Test component-based UI system functionality."""
    
    def setUp(self):
        """Set up test environment."""
        # Create patch for render_component
        self.render_patch = patch('web.templates.components.render_component')
        self.mock_render = self.render_patch.start()
        
        # Make render_component return the component name and context
        self.mock_render.side_effect = lambda name, **kwargs: f"Rendered {name} with {kwargs}"
    
    def tearDown(self):
        """Clean up after tests."""
        self.render_patch.stop()
    
    def test_base_component(self):
        """Test the base Component class."""
        # Create component
        component = Component(id="test-id", classes=["test-class"], attributes={"data-test": "value"})
        
        # Test attribute methods
        component.add_class("new-class")
        component.set_attribute("data-new", "new-value")
        
        # Check component state
        self.assertEqual(component.id, "test-id")
        self.assertIn("test-class", component.classes)
        self.assertIn("new-class", component.classes)
        self.assertEqual(component.attributes["data-test"], "value")
        self.assertEqual(component.attributes["data-new"], "new-value")
        
        # Test removing attributes
        component.remove_class("test-class")
        component.remove_attribute("data-test")
        
        self.assertNotIn("test-class", component.classes)
        self.assertNotIn("data-test", component.attributes)
    
    def test_component_nesting(self):
        """Test component nesting."""
        # Create parent and child components
        parent = Container(id="parent")
        child1 = TextBlock("Child 1", id="child1")
        child2 = TextBlock("Child 2", id="child2")
        
        # Add children to parent
        parent.add_child(child1)
        parent.add_child(child2)
        
        # Check parent-child relationships
        self.assertEqual(len(parent.children), 2)
        self.assertEqual(parent.children[0], child1)
        self.assertEqual(parent.children[1], child2)
        self.assertEqual(child1.parent, parent)
        self.assertEqual(child2.parent, parent)
        
        # Test removing a child
        parent.remove_child(child1)
        
        self.assertEqual(len(parent.children), 1)
        self.assertEqual(parent.children[0], child2)
        self.assertIsNone(child1.parent)
    
    def test_component_rendering(self):
        """Test component rendering."""
        # Create component with template
        component = Component(id="test-id")
        component.template = "test_component"
        
        # Test rendering
        result = component.render(test_var="test_value")
        
        # Check that render_component was called correctly
        self.mock_render.assert_called_once_with(
            "test_component", 
            id="test-id",
            classes="",
            attributes={},
            children=[],
            events={},
            test_var="test_value"
        )
    
    def test_text_block(self):
        """Test TextBlock component."""
        # Create TextBlock
        text_block = TextBlock("Test text", tag="h1", id="text-id", classes=["text-class"])
        
        # Check component state
        self.assertEqual(text_block.text, "Test text")
        self.assertEqual(text_block.tag, "h1")
        self.assertEqual(text_block.id, "text-id")
        self.assertIn("text-class", text_block.classes)
        
        # Test rendering
        text_block.render()
        
        # Check that render_component was called with correct context
        context = self.mock_render.call_args[1]
        self.assertEqual(context["text"], "Test text")
        self.assertEqual(context["tag"], "h1")
    
    def test_button(self):
        """Test Button component."""
        # Create Button
        button = Button("Click me", button_type="submit", id="button-id")
        
        # Check component state
        self.assertEqual(button.text, "Click me")
        self.assertEqual(button.button_type, "submit")
        self.assertEqual(button.id, "button-id")
        
        # Add event handler
        button.on("click", lambda: print("Clicked"))
        
        # Test rendering
        button.render()
        
        # Check that render_component was called with correct context
        context = self.mock_render.call_args[1]
        self.assertEqual(context["text"], "Click me")
        self.assertEqual(context["button_type"], "submit")
        self.assertIn("click", context["events"])
    
    def test_form(self):
        """Test Form component."""
        # Create Form
        form = Form(action="/submit", method="post", id="form-id")
        
        # Check component state
        self.assertEqual(form.action, "/submit")
        self.assertEqual(form.method, "post")
        self.assertEqual(form.id, "form-id")
        
        # Add form fields
        form.add_child(Input("username", label="Username"))
        form.add_child(Input("password", input_type="password", label="Password"))
        form.add_child(Button("Submit", button_type="submit"))
        
        # Test rendering
        form.render()
        
        # Check that render_component was called with correct context
        context = self.mock_render.call_args[1]
        self.assertEqual(context["action"], "/submit")
        self.assertEqual(context["method"], "post")
        self.assertEqual(len(context["children"]), 3)
    
    def test_select(self):
        """Test Select component."""
        # Create Select
        options = [
            {"value": "1", "text": "Option 1"},
            {"value": "2", "text": "Option 2"},
            {"value": "3", "text": "Option 3"}
        ]
        select = Select("test-select", options, selected="2", label="Test Select")
        
        # Check component state
        self.assertEqual(select.name, "test-select")
        self.assertEqual(select.options, options)
        self.assertEqual(select.selected, "2")
        self.assertEqual(select.label, "Test Select")
        
        # Test rendering
        select.render()
        
        # Check that render_component was called with correct context
        context = self.mock_render.call_args[1]
        self.assertEqual(context["name"], "test-select")
        self.assertEqual(context["options"], options)
        self.assertEqual(context["selected"], "2")
        self.assertEqual(context["label"], "Test Select")
    
    def test_complex_component(self):
        """Test a complex component composition."""
        # Create a card with nested components
        card = Card(title="Test Card", id="card-id")
        card.add_child(TextBlock("This is a test card with multiple components."))
        
        form = Form(action="/submit", method="post")
        form.add_child(Input("name", label="Name"))
        form.add_child(Input("email", label="Email"))
        form.add_child(Button("Submit", button_type="submit"))
        
        card.add_child(form)
        
        # Test rendering
        card.render()
        
        # Check that render_component was called with correct context
        context = self.mock_render.call_args[1]
        self.assertEqual(context["title"], "Test Card")
        self.assertEqual(context["id"], "card-id")
        self.assertEqual(len(context["children"]), 2)


if __name__ == "__main__":
    unittest.main()