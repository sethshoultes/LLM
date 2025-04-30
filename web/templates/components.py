#!/usr/bin/env python3
"""
Component-based UI system.

This module provides functionality for creating and managing UI components
with standardized interfaces, properties, and events.
"""

import logging
from typing import Dict, List, Any, Optional, Union, Callable
from pathlib import Path
import json
import re

from web.templates.engine import render_component

logger = logging.getLogger(__name__)


class Component:
    """Base class for UI components."""
    
    def __init__(self, id: str = None, classes: List[str] = None, attributes: Dict[str, str] = None):
        """Initialize a component.
        
        Args:
            id: Optional HTML ID for the component
            classes: Optional list of CSS classes
            attributes: Optional HTML attributes
        """
        self.id = id
        self.classes = classes or []
        self.attributes = attributes or {}
        self.children = []
        self.parent = None
        self.template = None
        self.events = {}
    
    def add_class(self, class_name: str) -> 'Component':
        """Add a CSS class to the component.
        
        Args:
            class_name: CSS class name to add
            
        Returns:
            Self for method chaining
        """
        if class_name not in self.classes:
            self.classes.append(class_name)
        return self
    
    def remove_class(self, class_name: str) -> 'Component':
        """Remove a CSS class from the component.
        
        Args:
            class_name: CSS class name to remove
            
        Returns:
            Self for method chaining
        """
        if class_name in self.classes:
            self.classes.remove(class_name)
        return self
    
    def set_attribute(self, name: str, value: str) -> 'Component':
        """Set an HTML attribute on the component.
        
        Args:
            name: Attribute name
            value: Attribute value
            
        Returns:
            Self for method chaining
        """
        self.attributes[name] = value
        return self
    
    def remove_attribute(self, name: str) -> 'Component':
        """Remove an HTML attribute from the component.
        
        Args:
            name: Attribute name
            
        Returns:
            Self for method chaining
        """
        if name in self.attributes:
            del self.attributes[name]
        return self
    
    def add_child(self, child: 'Component') -> 'Component':
        """Add a child component.
        
        Args:
            child: Child component to add
            
        Returns:
            Self for method chaining
        """
        self.children.append(child)
        child.parent = self
        return self
    
    def remove_child(self, child: 'Component') -> 'Component':
        """Remove a child component.
        
        Args:
            child: Child component to remove
            
        Returns:
            Self for method chaining
        """
        if child in self.children:
            self.children.remove(child)
            child.parent = None
        return self
    
    def on(self, event: str, handler: Callable) -> 'Component':
        """Register an event handler.
        
        Args:
            event: Event name (e.g., 'click', 'change')
            handler: Event handler function
            
        Returns:
            Self for method chaining
        """
        self.events[event] = handler
        return self
    
    def render(self, **kwargs) -> str:
        """Render the component.
        
        Args:
            **kwargs: Additional context variables
            
        Returns:
            Rendered component HTML
        """
        context = self.get_context()
        context.update(kwargs)
        
        if not self.template:
            logger.warning(f"Component {self.__class__.__name__} has no template")
            return ""
        
        return render_component(self.template, **context)
    
    def get_context(self) -> Dict[str, Any]:
        """Get the component's context for rendering.
        
        Returns:
            Component context
        """
        return {
            "id": self.id,
            "classes": " ".join(self.classes),
            "attributes": self.attributes,
            "children": [child.render() for child in self.children],
            "events": self._format_events(),
        }
    
    def _format_events(self) -> Dict[str, str]:
        """Format event handlers as JavaScript code.
        
        Returns:
            Dictionary mapping event names to JavaScript event handler code
        """
        # Simple implementation - real implementation would generate proper event handlers
        return {
            event: f'data-event-{event}="{event}"'
            for event in self.events
        }


class Container(Component):
    """A container component that holds other components."""
    
    def __init__(self, id: str = None, classes: List[str] = None, attributes: Dict[str, str] = None):
        """Initialize a container component.
        
        Args:
            id: Optional HTML ID for the component
            classes: Optional list of CSS classes
            attributes: Optional HTML attributes
        """
        super().__init__(id, classes, attributes)
        self.template = "container"


class TextBlock(Component):
    """A component for displaying text."""
    
    def __init__(
        self, 
        text: str, 
        tag: str = "p", 
        id: str = None, 
        classes: List[str] = None, 
        attributes: Dict[str, str] = None
    ):
        """Initialize a text block component.
        
        Args:
            text: Text content
            tag: HTML tag to use (default: p)
            id: Optional HTML ID for the component
            classes: Optional list of CSS classes
            attributes: Optional HTML attributes
        """
        super().__init__(id, classes, attributes)
        self.text = text
        self.tag = tag
        self.template = "text_block"
    
    def get_context(self) -> Dict[str, Any]:
        """Get the component's context for rendering.
        
        Returns:
            Component context
        """
        context = super().get_context()
        context.update({
            "text": self.text,
            "tag": self.tag
        })
        return context


class Button(Component):
    """A button component."""
    
    def __init__(
        self, 
        text: str, 
        button_type: str = "button", 
        id: str = None, 
        classes: List[str] = None, 
        attributes: Dict[str, str] = None
    ):
        """Initialize a button component.
        
        Args:
            text: Button text
            button_type: Button type (default: "button")
            id: Optional HTML ID for the component
            classes: Optional list of CSS classes
            attributes: Optional HTML attributes
        """
        super().__init__(id, classes, attributes)
        self.text = text
        self.button_type = button_type
        self.template = "button"
    
    def get_context(self) -> Dict[str, Any]:
        """Get the component's context for rendering.
        
        Returns:
            Component context
        """
        context = super().get_context()
        context.update({
            "text": self.text,
            "button_type": self.button_type
        })
        return context


class Form(Component):
    """A form component."""
    
    def __init__(
        self, 
        action: str = "", 
        method: str = "post", 
        id: str = None, 
        classes: List[str] = None, 
        attributes: Dict[str, str] = None
    ):
        """Initialize a form component.
        
        Args:
            action: Form action URL
            method: Form method (default: "post")
            id: Optional HTML ID for the component
            classes: Optional list of CSS classes
            attributes: Optional HTML attributes
        """
        super().__init__(id, classes, attributes)
        self.action = action
        self.method = method
        self.template = "form"
    
    def get_context(self) -> Dict[str, Any]:
        """Get the component's context for rendering.
        
        Returns:
            Component context
        """
        context = super().get_context()
        context.update({
            "action": self.action,
            "method": self.method
        })
        return context


class Input(Component):
    """An input component."""
    
    def __init__(
        self, 
        name: str, 
        input_type: str = "text", 
        value: str = "", 
        label: str = None, 
        placeholder: str = None, 
        required: bool = False, 
        id: str = None, 
        classes: List[str] = None, 
        attributes: Dict[str, str] = None
    ):
        """Initialize an input component.
        
        Args:
            name: Input name
            input_type: Input type (default: "text")
            value: Input value
            label: Input label
            placeholder: Input placeholder
            required: Whether the input is required
            id: Optional HTML ID for the component
            classes: Optional list of CSS classes
            attributes: Optional HTML attributes
        """
        super().__init__(id, classes, attributes)
        self.name = name
        self.input_type = input_type
        self.value = value
        self.label = label
        self.placeholder = placeholder
        self.required = required
        self.template = "input"
    
    def get_context(self) -> Dict[str, Any]:
        """Get the component's context for rendering.
        
        Returns:
            Component context
        """
        context = super().get_context()
        context.update({
            "name": self.name,
            "input_type": self.input_type,
            "value": self.value,
            "label": self.label,
            "placeholder": self.placeholder,
            "required": self.required
        })
        return context


class Select(Component):
    """A select component."""
    
    def __init__(
        self, 
        name: str, 
        options: List[Dict[str, str]], 
        selected: str = None, 
        label: str = None, 
        required: bool = False, 
        id: str = None, 
        classes: List[str] = None, 
        attributes: Dict[str, str] = None
    ):
        """Initialize a select component.
        
        Args:
            name: Select name
            options: List of option dicts with "value" and "text" keys
            selected: Selected option value
            label: Select label
            required: Whether the select is required
            id: Optional HTML ID for the component
            classes: Optional list of CSS classes
            attributes: Optional HTML attributes
        """
        super().__init__(id, classes, attributes)
        self.name = name
        self.options = options
        self.selected = selected
        self.label = label
        self.required = required
        self.template = "select"
    
    def get_context(self) -> Dict[str, Any]:
        """Get the component's context for rendering.
        
        Returns:
            Component context
        """
        context = super().get_context()
        context.update({
            "name": self.name,
            "options": self.options,
            "selected": self.selected,
            "label": self.label,
            "required": self.required
        })
        return context


class NavBar(Component):
    """A navigation bar component."""
    
    def __init__(
        self, 
        brand: str, 
        items: List[Dict[str, str]], 
        id: str = None, 
        classes: List[str] = None, 
        attributes: Dict[str, str] = None
    ):
        """Initialize a navigation bar component.
        
        Args:
            brand: Brand text
            items: List of item dicts with "text" and "href" keys
            id: Optional HTML ID for the component
            classes: Optional list of CSS classes
            attributes: Optional HTML attributes
        """
        super().__init__(id, classes, attributes)
        self.brand = brand
        self.items = items
        self.template = "navbar"
    
    def get_context(self) -> Dict[str, Any]:
        """Get the component's context for rendering.
        
        Returns:
            Component context
        """
        context = super().get_context()
        context.update({
            "brand": self.brand,
            "items": self.items
        })
        return context


class Card(Component):
    """A card component."""
    
    def __init__(
        self, 
        title: str = None, 
        content: str = None, 
        footer: str = None, 
        image: str = None, 
        id: str = None, 
        classes: List[str] = None, 
        attributes: Dict[str, str] = None
    ):
        """Initialize a card component.
        
        Args:
            title: Card title
            content: Card content
            footer: Card footer
            image: Card image URL
            id: Optional HTML ID for the component
            classes: Optional list of CSS classes
            attributes: Optional HTML attributes
        """
        super().__init__(id, classes, attributes)
        self.title = title
        self.content = content
        self.footer = footer
        self.image = image
        self.template = "card"
    
    def get_context(self) -> Dict[str, Any]:
        """Get the component's context for rendering.
        
        Returns:
            Component context
        """
        context = super().get_context()
        context.update({
            "title": self.title,
            "content": self.content,
            "footer": self.footer,
            "image": self.image
        })
        return context


class Modal(Component):
    """A modal component."""
    
    def __init__(
        self, 
        title: str, 
        content: str = None, 
        footer: str = None,
        id: str = None, 
        classes: List[str] = None, 
        attributes: Dict[str, str] = None
    ):
        """Initialize a modal component.
        
        Args:
            title: Modal title
            content: Modal content
            footer: Modal footer
            id: Optional HTML ID for the component
            classes: Optional list of CSS classes
            attributes: Optional HTML attributes
        """
        super().__init__(id, classes, attributes)
        self.title = title
        self.content = content
        self.footer = footer
        self.template = "modal"
    
    def get_context(self) -> Dict[str, Any]:
        """Get the component's context for rendering.
        
        Returns:
            Component context
        """
        context = super().get_context()
        context.update({
            "title": self.title,
            "content": self.content,
            "footer": self.footer
        })
        return context


class Table(Component):
    """A table component."""
    
    def __init__(
        self, 
        headers: List[str], 
        rows: List[List[Any]], 
        id: str = None, 
        classes: List[str] = None, 
        attributes: Dict[str, str] = None
    ):
        """Initialize a table component.
        
        Args:
            headers: Table headers
            rows: Table rows
            id: Optional HTML ID for the component
            classes: Optional list of CSS classes
            attributes: Optional HTML attributes
        """
        super().__init__(id, classes, attributes)
        self.headers = headers
        self.rows = rows
        self.template = "table"
    
    def get_context(self) -> Dict[str, Any]:
        """Get the component's context for rendering.
        
        Returns:
            Component context
        """
        context = super().get_context()
        context.update({
            "headers": self.headers,
            "rows": self.rows
        })
        return context


class Pagination(Component):
    """A pagination component."""
    
    def __init__(
        self, 
        total_pages: int, 
        current_page: int, 
        base_url: str, 
        id: str = None, 
        classes: List[str] = None, 
        attributes: Dict[str, str] = None
    ):
        """Initialize a pagination component.
        
        Args:
            total_pages: Total number of pages
            current_page: Current page number
            base_url: Base URL for page links
            id: Optional HTML ID for the component
            classes: Optional list of CSS classes
            attributes: Optional HTML attributes
        """
        super().__init__(id, classes, attributes)
        self.total_pages = total_pages
        self.current_page = current_page
        self.base_url = base_url
        self.template = "pagination"
    
    def get_context(self) -> Dict[str, Any]:
        """Get the component's context for rendering.
        
        Returns:
            Component context
        """
        context = super().get_context()
        context.update({
            "total_pages": self.total_pages,
            "current_page": self.current_page,
            "base_url": self.base_url
        })
        return context