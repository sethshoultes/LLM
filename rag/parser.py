#!/usr/bin/env python3
"""
Document parsing module for the LLM Platform.

Provides functionality for parsing different document formats and extracting content and metadata.
"""

import re
import json
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Union

from core.logging import get_logger
from core.utils import parse_frontmatter, format_with_frontmatter

# Get logger for this module
logger = get_logger("rag.parser")

class DocumentParser:
    """
    Base class for document parsers.
    
    Provides a common interface for parsing different document formats.
    """
    
    def parse(self, content: str) -> Tuple[Dict[str, Any], str]:
        """
        Parse document content into metadata and text.
        
        Args:
            content: Document content to parse
            
        Returns:
            Tuple of (metadata, content)
        """
        raise NotImplementedError("parse method must be implemented by subclasses")
    
    def format(self, metadata: Dict[str, Any], content: str) -> str:
        """
        Format metadata and content into a document.
        
        Args:
            metadata: Document metadata
            content: Document content
            
        Returns:
            Formatted document
        """
        raise NotImplementedError("format method must be implemented by subclasses")

class MarkdownParser(DocumentParser):
    """
    Parser for markdown documents with YAML frontmatter.
    
    Handles the standard format used by the RAG system.
    """
    
    def parse(self, content: str) -> Tuple[Dict[str, Any], str]:
        """
        Parse markdown content with YAML frontmatter.
        
        Args:
            content: Markdown content to parse
            
        Returns:
            Tuple of (metadata, content)
        """
        # Use the utility function from core.utils
        metadata, text = parse_frontmatter(content)
        return metadata, text
    
    def format(self, metadata: Dict[str, Any], content: str) -> str:
        """
        Format metadata and content into a markdown document with YAML frontmatter.
        
        Args:
            metadata: Document metadata
            content: Document content
            
        Returns:
            Formatted document
        """
        # Use the utility function from core.utils
        return format_with_frontmatter(metadata, content)

class TextParser(DocumentParser):
    """
    Parser for plain text documents.
    
    Extracts minimal metadata from plain text.
    """
    
    def parse(self, content: str) -> Tuple[Dict[str, Any], str]:
        """
        Parse plain text content.
        
        Args:
            content: Plain text content to parse
            
        Returns:
            Tuple of (metadata, content)
        """
        # Extract a title from the first line if possible
        title = content.split('\n', 1)[0].strip() if content else ""
        
        # Truncate title if too long
        if len(title) > 100:
            title = title[:97] + "..."
        
        # Basic metadata
        metadata = {
            "title": title,
            "format": "plain"
        }
        
        return metadata, content
    
    def format(self, metadata: Dict[str, Any], content: str) -> str:
        """
        Format metadata and content into a plain text document.
        
        Args:
            metadata: Document metadata
            content: Document content
            
        Returns:
            Formatted document
        """
        # For plain text, we just return the content
        return content

class JSONParser(DocumentParser):
    """
    Parser for JSON documents.
    
    Handles documents stored in JSON format.
    """
    
    def parse(self, content: str) -> Tuple[Dict[str, Any], str]:
        """
        Parse JSON content.
        
        Args:
            content: JSON content to parse
            
        Returns:
            Tuple of (metadata, content)
            
        Raises:
            ValueError: If the content is not valid JSON
        """
        try:
            data = json.loads(content)
            
            # If it's a simple string, treat it as content
            if isinstance(data, str):
                return {"format": "json"}, data
            
            # If it's a dict, extract content and use the rest as metadata
            if isinstance(data, dict):
                metadata = {k: v for k, v in data.items() if k != "content"}
                metadata["format"] = "json"
                
                # Extract content or use an empty string
                content = data.get("content", "")
                
                return metadata, content
            
            # Otherwise, serialize the entire object as content
            return {"format": "json"}, json.dumps(data, indent=2)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON content: {e}")
    
    def format(self, metadata: Dict[str, Any], content: str) -> str:
        """
        Format metadata and content into a JSON document.
        
        Args:
            metadata: Document metadata
            content: Document content
            
        Returns:
            Formatted document
        """
        # Combine metadata and content
        data = metadata.copy()
        data["content"] = content
        
        # Serialize to JSON
        return json.dumps(data, indent=2)

class HTMLParser(DocumentParser):
    """
    Parser for HTML documents.
    
    Extracts content and metadata from HTML documents.
    """
    
    def parse(self, content: str) -> Tuple[Dict[str, Any], str]:
        """
        Parse HTML content.
        
        Args:
            content: HTML content to parse
            
        Returns:
            Tuple of (metadata, content)
        """
        # Extract title
        title_match = re.search(r"<title>(.*?)</title>", content, re.IGNORECASE | re.DOTALL)
        title = title_match.group(1).strip() if title_match else ""
        
        # Extract metadata from meta tags
        metadata = {
            "title": title,
            "format": "html"
        }
        
        # Extract meta tags
        meta_tags = re.findall(r"<meta\s+([^>]+)>", content, re.IGNORECASE)
        for meta in meta_tags:
            name_match = re.search(r'name=["\'](.*?)["\']', meta, re.IGNORECASE)
            content_match = re.search(r'content=["\'](.*?)["\']', meta, re.IGNORECASE)
            
            if name_match and content_match:
                metadata[name_match.group(1).lower()] = content_match.group(1)
        
        # Extract body content
        body_match = re.search(r"<body[^>]*>(.*?)</body>", content, re.IGNORECASE | re.DOTALL)
        body = body_match.group(1).strip() if body_match else content
        
        # Remove HTML tags to get plain text
        text = re.sub(r"<[^>]+>", "", body)
        text = re.sub(r"\s+", " ", text).strip()
        
        return metadata, text
    
    def format(self, metadata: Dict[str, Any], content: str) -> str:
        """
        Format metadata and content into an HTML document.
        
        Args:
            metadata: Document metadata
            content: Document content
            
        Returns:
            Formatted document
        """
        # Create HTML document
        html = "<!DOCTYPE html>\n<html>\n<head>\n"
        
        # Add title
        title = metadata.get("title", "Document")
        html += f"<title>{title}</title>\n"
        
        # Add meta tags
        for key, value in metadata.items():
            if key not in ["title", "format"]:
                html += f'<meta name="{key}" content="{value}">\n'
        
        # Add body
        html += "</head>\n<body>\n"
        
        # Add content
        if content:
            html += content + "\n"
        
        # Close tags
        html += "</body>\n</html>"
        
        return html

# Factory function to get a parser for a specific format
def get_parser(format_type: str) -> DocumentParser:
    """
    Get a parser for a specific document format.
    
    Args:
        format_type: Format type to get a parser for
        
    Returns:
        DocumentParser instance
        
    Raises:
        ValueError: If the format type is not supported
    """
    if format_type.lower() in ["md", "markdown"]:
        return MarkdownParser()
    elif format_type.lower() in ["txt", "text", "plain"]:
        return TextParser()
    elif format_type.lower() in ["json"]:
        return JSONParser()
    elif format_type.lower() in ["html", "htm"]:
        return HTMLParser()
    else:
        raise ValueError(f"Unsupported document format: {format_type}")

def parse_document(content: str, format_type: str) -> Tuple[Dict[str, Any], str]:
    """
    Parse document content based on its format.
    
    Args:
        content: Document content to parse
        format_type: Format of the document
        
    Returns:
        Tuple of (metadata, content)
        
    Raises:
        ValueError: If the format type is not supported
    """
    parser = get_parser(format_type)
    return parser.parse(content)

def format_document(metadata: Dict[str, Any], content: str, format_type: str) -> str:
    """
    Format metadata and content into a document of the specified format.
    
    Args:
        metadata: Document metadata
        content: Document content
        format_type: Format to use
        
    Returns:
        Formatted document
        
    Raises:
        ValueError: If the format type is not supported
    """
    parser = get_parser(format_type)
    return parser.format(metadata, content)

def detect_format(content: str) -> str:
    """
    Detect the format of a document based on its content.
    
    Args:
        content: Document content to analyze
        
    Returns:
        Detected format type
    """
    # Check for YAML frontmatter (markdown)
    if content.startswith("---"):
        return "markdown"
    
    # Check for HTML
    if re.search(r"<!DOCTYPE html>|<html>|<body>", content, re.IGNORECASE):
        return "html"
    
    # Check for JSON
    try:
        json.loads(content)
        return "json"
    except:
        pass
    
    # Default to plain text
    return "plain"