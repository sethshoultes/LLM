#!/usr/bin/env python3
"""
Smart context handling module for the LLM Platform.

Provides intelligent context management for RAG systems, handling
the selection, formatting, and optimization of document contexts
for inclusion in LLM prompts.
"""

from typing import Dict, List, Any, Tuple

# Import core modules
from core.logging import get_logger
from core.utils import timer

# Import from tokens module
from rag.tokens import token_manager

# Import types but defer actual import to avoid circular imports
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass  # Will be used for type annotations in future

# Configure logger
logger = get_logger("rag.context")

# Constants
MAX_DOCUMENT_PREVIEW_LENGTH = 200  # Maximum length of document previews in tokens
DEFAULT_MAX_DOCUMENTS = 5  # Default maximum number of documents to include


class ContextManager:
    """
    Smart context manager for RAG systems.

    Handles intelligent selection, prioritization, and formatting
    of document contexts based on query relevance and token constraints.
    """

    def __init__(self, model_id: str = None):
        """
        Initialize the context manager.

        Args:
            model_id: Optional model identifier to determine context window
        """
        self.model_id = model_id
        self.context_window = token_manager.get_context_window(model_id)

        # Feature flags
        self.smart_truncation = True  # Use smart truncation for documents
        self.preserve_document_boundaries = True  # Keep documents separate rather than merging

        logger.debug(f"Initialized ContextManager with context window: {self.context_window}")

    @timer
    def select_documents(
        self,
        documents: List[Dict[str, Any]],
        query: str,
        available_tokens: int,
        max_documents: int = DEFAULT_MAX_DOCUMENTS,
    ) -> List[Dict[str, Any]]:
        """
        Select and prioritize documents based on query relevance and token budget.

        Args:
            documents: List of documents with relevance scores
            query: User query for relevance determination
            available_tokens: Maximum tokens available for context
            max_documents: Maximum number of documents to include

        Returns:
            List of selected documents with token counts
        """
        if not documents or available_tokens <= 0:
            return []

        # Sort by relevance score (highest first) if available
        if "score" in documents[0]:
            documents = sorted(documents, key=lambda d: d.get("score", 0), reverse=True)

        # Limit to max_documents
        documents = documents[:max_documents]

        # Estimate tokens for each document
        for doc in documents:
            title = doc.get("title", "Document")
            content = doc.get("content", "")
            header = f"## {title}\n\n"

            # Calculate token counts
            header_tokens = token_manager.estimate_tokens(header)
            content_tokens = token_manager.estimate_tokens(content)

            # Add token information to document
            doc["header_tokens"] = header_tokens
            doc["content_tokens"] = content_tokens
            doc["total_tokens"] = header_tokens + content_tokens

        # Calculate how many documents we can include in full
        selected_docs = []
        remaining_tokens = available_tokens

        for doc in documents:
            doc_tokens = doc["total_tokens"]

            # Check if we can include the full document
            if doc_tokens <= remaining_tokens:
                # Include full document
                selected_docs.append(
                    {
                        "id": doc.get("id"),
                        "title": doc.get("title", "Document"),
                        "content": doc.get("content", ""),
                        "tokens": doc_tokens,
                        "truncated": False,
                        "header_tokens": doc.get("header_tokens", 0),
                        "content_tokens": doc.get("content_tokens", 0),
                        "score": doc.get("score", 0),
                    }
                )
                remaining_tokens -= doc_tokens
            else:
                # If we can't include the full document, check if we should include a truncated version
                if not selected_docs or remaining_tokens > doc.get("header_tokens", 0) + 50:
                    # We can include at least the header and some content
                    header_tokens = doc.get("header_tokens", 0)
                    content_tokens_available = remaining_tokens - header_tokens

                    if (
                        content_tokens_available > 50
                    ):  # Only truncate if we can include meaningful content
                        truncated_content = self._truncate_text(
                            doc.get("content", ""), content_tokens_available
                        )

                        truncated_tokens = token_manager.estimate_tokens(truncated_content)
                        total_tokens = header_tokens + truncated_tokens

                        selected_docs.append(
                            {
                                "id": doc.get("id"),
                                "title": doc.get("title", "Document"),
                                "content": truncated_content,
                                "tokens": total_tokens,
                                "truncated": True,
                                "header_tokens": header_tokens,
                                "content_tokens": truncated_tokens,
                                "score": doc.get("score", 0),
                            }
                        )
                        remaining_tokens -= total_tokens

                # Stop adding documents once we've added a truncated one
                break

        return selected_docs

    @timer
    def format_context(
        self, documents: List[Dict[str, Any]], query: str = "", add_prefix: bool = True
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Format documents into a context string for inclusion in a prompt.

        Args:
            documents: List of documents to format
            query: Optional user query for context
            add_prefix: Whether to add a system instruction prefix

        Returns:
            Tuple of (formatted context string, document metadata list)
        """
        if not documents:
            return "", []

        # Format each document
        context_parts = []
        context_metadata = []
        total_tokens = 0

        for doc in documents:
            doc_id = doc.get("id")
            title = doc.get("title", "Document")
            content = doc.get("content", "")

            # Create document header
            header = f"## {title}\n\n"

            # Format document
            doc_text = header + content

            # Add to context
            context_parts.append(doc_text)

            # Calculate token usage for metadata
            header_tokens = doc.get("header_tokens", token_manager.estimate_tokens(header))
            content_tokens = doc.get("content_tokens", token_manager.estimate_tokens(content))
            doc_tokens = header_tokens + content_tokens
            total_tokens += doc_tokens

            # Add metadata
            context_metadata.append(
                {
                    "id": doc_id,
                    "title": title,
                    "tokens": doc_tokens,
                    "truncated": doc.get("truncated", False),
                    "score": doc.get("score", 0),
                }
            )

        # Join document parts
        context_text = "\n\n".join(context_parts)

        # Add system instruction prefix if requested
        if add_prefix and context_text:
            prefix = "Use the following information to answer the user's question:\n\n"
            context_text = prefix + context_text

            # Add prefix tokens to total
            prefix_tokens = token_manager.estimate_tokens(prefix)
            total_tokens += prefix_tokens

        # Update token percentages in metadata
        if total_tokens > 0:
            for meta in context_metadata:
                meta["token_percentage"] = round((meta["tokens"] / total_tokens) * 100, 1)

        return context_text, context_metadata

    @timer
    def prepare_context_for_prompt(
        self,
        documents: List[Dict[str, Any]],
        query: str,
        system_message: str,
        messages: List[Dict[str, Any]],
        max_documents: int = DEFAULT_MAX_DOCUMENTS,
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Prepare context for inclusion in a prompt, respecting token limits.

        Args:
            documents: List of documents from search
            query: User query for relevance determination
            system_message: Base system message (without context)
            messages: Conversation history
            max_documents: Maximum number of documents to include

        Returns:
            Tuple of (system prompt with context, document metadata list)
        """
        # Determine context window and calculate available tokens
        allocation = token_manager.allocate_context_budget(
            context_window=self.context_window,
            system_message=system_message,
            messages=messages,
            model_id=self.model_id,
        )

        available_tokens = allocation["available_for_context"]
        logger.info(f"Available tokens for context: {available_tokens}")

        if available_tokens <= 0 or not documents:
            return system_message, []

        # Select documents based on relevance and token budget
        selected_docs = self.select_documents(
            documents=documents,
            query=query,
            available_tokens=available_tokens,
            max_documents=max_documents,
        )

        # Format selected documents into context
        context_text, context_metadata = self.format_context(
            documents=selected_docs, query=query, add_prefix=True
        )

        # Combine with base system message
        if context_text:
            if system_message:
                full_system_message = f"{system_message}\n\n{context_text}"
            else:
                full_system_message = context_text
        else:
            full_system_message = system_message

        return full_system_message, context_metadata

    def _truncate_text(self, text: str, max_tokens: int) -> str:
        """
        Truncate text to fit within token limit, preserving sentence boundaries.

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

        if self.smart_truncation:
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
                result = text[:max_chars] + "..."
            else:
                # Include the period/etc and the space
                result = text[: breakpoint + 1] + "..."

            # Add truncation indicator
            return result
        else:
            # Simple truncation without preserving structure
            char_ratio = 4  # Approximate characters per token
            max_chars = max_tokens * char_ratio
            return text[:max_chars] + "..."


# Create singleton instance for global use
context_manager = ContextManager()
