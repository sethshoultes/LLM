#!/usr/bin/env python3
"""
Context formatting module for the LLM Platform.

Provides formatting utilities for preparing document content for inclusion
in prompts, with support for different model and interface requirements.
"""

from typing import Dict, List, Any, Optional, Union, Tuple

# Import core modules
from core.logging import get_logger
from core.utils import timer

# Import from tokens module
from rag.tokens import token_manager

# Configure logger
logger = get_logger("rag.formatter")

# Default formatting templates
DEFAULT_HEADER_TEMPLATE = "## {title}\n\n"
DEFAULT_SOURCE_TEMPLATE = "Source: {source}\n\n"
DEFAULT_CONTEXT_PREFIX = "Use the following information to answer the user's question:\n\n"
DEFAULT_CONTEXT_SUFFIX = "\n\nAnswer the user's question based on the information provided above."
DEFAULT_TRUNCATION_MARKER = "...[truncated]"


class ContextFormatter:
    """
    Context formatter for RAG systems.

    Provides methods for formatting document content into context strings
    suitable for inclusion in LLM prompts.
    """

    def __init__(self):
        """Initialize the context formatter."""
        # Configure templates
        self.header_template = DEFAULT_HEADER_TEMPLATE
        self.source_template = DEFAULT_SOURCE_TEMPLATE
        self.context_prefix = DEFAULT_CONTEXT_PREFIX
        self.context_suffix = DEFAULT_CONTEXT_SUFFIX
        self.truncation_marker = DEFAULT_TRUNCATION_MARKER

        # Configure formatting options
        self.include_sources = True  # Include source information in context
        self.include_prefix = True  # Include context prefix in final output
        self.include_suffix = False  # Include context suffix in final output
        self.use_markdown = True  # Use markdown formatting
        self.use_document_separators = True  # Add separators between documents

    def set_template(self, template_type: str, template: str):
        """
        Set a custom template.

        Args:
            template_type: Type of template to set ('header', 'source', 'prefix', 'suffix')
            template: Template string
        """
        if template_type == "header":
            self.header_template = template
        elif template_type == "source":
            self.source_template = template
        elif template_type == "prefix":
            self.context_prefix = template
        elif template_type == "suffix":
            self.context_suffix = template
        else:
            logger.warning(f"Unknown template type: {template_type}")

    @timer
    def format_document(
        self, document: Dict[str, Any], allocated_tokens: int = 0
    ) -> Tuple[str, int]:
        """
        Format a single document for inclusion in context.

        Args:
            document: Document to format
            allocated_tokens: Maximum tokens to use (0 for no limit)

        Returns:
            Tuple of (formatted document text, tokens used)
        """
        # Get document information
        title = document.get("title", "Document")
        content = document.get("content", "")
        source = document.get("source", "")

        # Format header
        header = self.header_template.format(title=title)
        header_tokens = token_manager.estimate_tokens(header)

        # Format source if available and enabled
        source_text = ""
        source_tokens = 0

        if source and self.include_sources:
            source_text = self.source_template.format(source=source)
            source_tokens = token_manager.estimate_tokens(source_text)

        # Calculate tokens available for content
        available_for_content = allocated_tokens
        if allocated_tokens > 0:
            available_for_content = max(0, allocated_tokens - header_tokens - source_tokens)

        # Format content
        if (
            available_for_content > 0
            and token_manager.estimate_tokens(content) > available_for_content
        ):
            # Need to truncate content
            content = self._truncate_text(content, available_for_content)
            truncated = True
        else:
            truncated = False

        content_tokens = token_manager.estimate_tokens(content)

        # Combine parts
        formatted_text = header + source_text + content

        if truncated:
            formatted_text += self.truncation_marker

        # Calculate total tokens
        total_tokens = header_tokens + source_tokens + content_tokens
        if truncated:
            total_tokens += token_manager.estimate_tokens(self.truncation_marker)

        return formatted_text, total_tokens

    @timer
    def format_documents(
        self, documents: List[Dict[str, Any]], allocated_tokens: Dict[str, int] = None
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Format multiple documents into a context string.

        Args:
            documents: List of documents to format
            allocated_tokens: Optional dictionary mapping document IDs to token allocations

        Returns:
            Tuple of (formatted context string, document metadata list)
        """
        if not documents:
            return "", []

        formatted_parts = []
        document_metadata = []

        # Prepare allocated tokens map
        token_allocations = {}
        if allocated_tokens:
            token_allocations = allocated_tokens

        # Format each document
        for doc in documents:
            doc_id = doc.get("id", "")

            # Get token allocation if available
            allocation = token_allocations.get(doc_id, 0)

            # Format document
            formatted_doc, tokens_used = self.format_document(doc, allocation)

            # Add to formatted parts
            formatted_parts.append(formatted_doc)

            # Add metadata
            document_metadata.append(
                {
                    "id": doc_id,
                    "title": doc.get("title", "Document"),
                    "tokens_used": tokens_used,
                    "truncated": tokens_used
                    < token_manager.estimate_tokens(doc.get("content", "")),
                }
            )

            # Add separator if enabled and not the last document
            if self.use_document_separators and doc != documents[-1]:
                formatted_parts.append("\n---\n")

        # Combine parts
        context_text = "\n\n".join(formatted_parts)

        # Add prefix/suffix if enabled
        if self.include_prefix and self.context_prefix:
            context_text = self.context_prefix + context_text

        if self.include_suffix and self.context_suffix:
            context_text = context_text + self.context_suffix

        return context_text, document_metadata

    @timer
    def create_system_prompt(
        self,
        base_prompt: str,
        documents: List[Dict[str, Any]],
        allocated_tokens: Dict[str, int] = None,
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Create a system prompt with document context.

        Args:
            base_prompt: Base system prompt
            documents: List of documents to include
            allocated_tokens: Optional dictionary mapping document IDs to token allocations

        Returns:
            Tuple of (system prompt with context, document metadata list)
        """
        if not documents:
            return base_prompt, []

        # Format documents
        context_text, document_metadata = self.format_documents(
            documents=documents, allocated_tokens=allocated_tokens
        )

        # Combine with base prompt
        if context_text:
            if base_prompt:
                system_prompt = f"{base_prompt}\n\n{context_text}"
            else:
                system_prompt = context_text
        else:
            system_prompt = base_prompt

        return system_prompt, document_metadata

    def _truncate_text(self, text: str, max_tokens: int) -> str:
        """
        Truncate text to fit within token limit.

        Args:
            text: Text to truncate
            max_tokens: Maximum tokens allowed

        Returns:
            Truncated text
        """
        if not text or max_tokens <= 0:
            return ""

        # If the text is already within the token limit, return it as is
        if token_manager.estimate_tokens(text) <= max_tokens:
            return text

        # Convert tokens to approximate character count
        char_ratio = 4  # Approximate characters per token
        max_chars = max_tokens * char_ratio

        # Find a good breaking point (end of sentence or paragraph)
        breakpoint = -1

        # Try to find end of sentence within the limit
        for pattern in ["\n\n", ". ", "! ", "? ", ".\n", "!\n", "?\n"]:
            pos = text[:max_chars].rfind(pattern)
            if pos > breakpoint:
                breakpoint = pos + len(pattern) - 1  # Include the period but not the space

        # If no good breakpoint found, just cut at the character limit
        if breakpoint == -1:
            return text[:max_chars]
        else:
            # Include the period/etc and the space
            return text[: breakpoint + 1]


# Create singleton instance for global use
context_formatter = ContextFormatter()
