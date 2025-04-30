#!/usr/bin/env python3
"""
Context management module for the LLM Platform.

Provides smart context management for RAG systems with token budgeting 
and adaptive document selection.
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union

# Import from core modules
from core.logging import get_logger
from core.utils import timer

# Import RAG types but defer actual import to avoid circular imports
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from rag.documents import Document, DocumentCollection
    from rag.search import SearchEngine, SearchResult

# Get logger for this module
logger = get_logger("rag_support.context_manager")

# Import BASE_DIR from rag_support
try:
    from rag_support import BASE_DIR
except ImportError:
    # Fallback if the import fails
    import os
    SCRIPT_DIR = Path(__file__).resolve().parent
    BASE_DIR = SCRIPT_DIR.parent.parent
    # Use environment variable if available
    BASE_DIR = Path(os.environ.get("LLM_BASE_DIR", str(BASE_DIR)))

# Import project manager for document access
try:
    from rag_support.utils.project_manager import project_manager
except ImportError:
    logger.error("Failed to import project_manager - context functionality will be limited")
    project_manager = None

# Constants
DEFAULT_TOKENS_PER_CHAR = 0.25  # Approximation of tokens per character (1 token ~= 4 chars)
DEFAULT_CONTEXT_WINDOW = 2048   # Default context window for small models
LARGE_CONTEXT_WINDOW = 4096     # Large context window for bigger models
TOKEN_RESERVE_RATIO = 0.15      # Percentage of tokens to reserve for the response
MIN_RESERVED_TOKENS = 256       # Minimum number of tokens to reserve for response

class SmartContextManager:
    """
    Manages context for RAG systems with adaptive token allocation.
    
    Handles intelligent document selection, token budgeting, and
    context formatting for optimal RAG performance.
    """
    
    def __init__(self, model_path: str = None):
        """
        Initialize the context manager.
        
        Args:
            model_path: Path to the model (used to determine model size and capabilities)
        """
        self.model_path = model_path
        self.model_context_window = self._determine_context_window(model_path)
        self.use_smart_context = os.environ.get("LLM_RAG_SMART_CONTEXT") == "1"
        
        logger.debug(f"Initialized SmartContextManager with context window: {self.model_context_window}")
    
    def _determine_context_window(self, model_path: str) -> int:
        """
        Determine the context window size based on model path.
        
        Args:
            model_path: Path to the model file
            
        Returns:
            Context window size in tokens
        """
        # Default to smaller context size
        context_window = DEFAULT_CONTEXT_WINDOW
        
        if model_path:
            model_path_lower = str(model_path).lower()
            
            # Large models
            if any(marker in model_path_lower for marker in ["70b", "claude"]):
                context_window = 8192  # Very large models
                
            # Medium-sized models
            elif any(marker in model_path_lower for marker in ["13b", "mistral", "7b", "llama2"]):
                context_window = LARGE_CONTEXT_WINDOW  # 4096 tokens
            
            # Small models
            elif any(marker in model_path_lower for marker in ["tiny", "small", "1.1b", "1b"]):
                context_window = DEFAULT_CONTEXT_WINDOW  # 2048 tokens
        
        return context_window
    
    @timer
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate the number of tokens in a text string.
        
        Args:
            text: The text to estimate tokens for
            
        Returns:
            Estimated token count
        """
        if not text:
            return 0
        
        # Import tokenization utilities if available
        try:
            from core.utils import estimate_tokens
            return estimate_tokens(text)
        except ImportError:
            # Simple char-based approximation as fallback
            return max(1, int(len(text) * DEFAULT_TOKENS_PER_CHAR))
    
    @timer
    def estimate_history_tokens(self, message_history: List[Dict[str, Any]]) -> int:
        """
        Estimate tokens used by conversation history.
        
        Args:
            message_history: List of conversation messages
            
        Returns:
            Estimated token count for conversation history
        """
        if not message_history:
            return 0
        
        total_tokens = 0
        for message in message_history:
            content = message.get('content', '')
            role = message.get('role', '')
            
            # Allow for role prefix in token estimation (e.g., "user: ", "assistant: ")
            role_prefix = len(role) + 2 if role else 0
            
            total_tokens += self.estimate_tokens(content) + role_prefix
        
        # Add overhead for formatting (message separators, etc.)
        total_tokens += len(message_history) * 5
        
        return total_tokens
    
    @timer
    def calculate_available_context_tokens(self, 
                                          message_history: List[Dict[str, Any]], 
                                          system_message: str = "") -> int:
        """
        Calculate tokens available for RAG context.
        
        Args:
            message_history: Conversation history
            system_message: System message (excluding RAG context)
            
        Returns:
            Number of tokens available for RAG context
        """
        # Calculate tokens used by history and system message
        history_tokens = self.estimate_history_tokens(message_history)
        system_tokens = self.estimate_tokens(system_message)
        
        # Reserve tokens for response
        # Either use a percentage of context window or a minimum value, whichever is larger
        reserve_tokens = max(
            MIN_RESERVED_TOKENS,
            int(self.model_context_window * TOKEN_RESERVE_RATIO)
        )
        
        # Calculate available tokens
        available_tokens = max(0, self.model_context_window - history_tokens - system_tokens - reserve_tokens)
        
        # Log token allocation
        logger.info(f"Token allocation: {available_tokens} available for RAG context")
        logger.debug(f"  Context window: {self.model_context_window}")
        logger.debug(f"  History: {history_tokens}")
        logger.debug(f"  System: {system_tokens}")
        logger.debug(f"  Reserved: {reserve_tokens}")
        
        return available_tokens
    
    @timer
    def select_and_format_documents(self, 
                                  project_id: str, 
                                  document_ids: List[str], 
                                  query: str,
                                  available_tokens: int) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Select and format documents to fit within token constraints.
        
        Args:
            project_id: Project ID
            document_ids: List of document IDs to include
            query: The user query for relevance determination
            available_tokens: Maximum tokens available for context
            
        Returns:
            Tuple of (formatted context string, list of document info dicts)
        """
        if not document_ids or not project_manager or available_tokens <= 0:
            return "", []
        
        # Get the full documents
        documents = []
        for doc_id in document_ids:
            doc = project_manager.get_document(project_id, doc_id)
            if doc:
                documents.append(doc)
        
        if not documents:
            return "", []
        
        # Smart document selection - if we have more docs than we can fit,
        # we'll use the search to prioritize the most relevant ones
        if len(documents) > 1 and query and query.strip():
            # Get search results to determine document relevance
            search_results = project_manager.search_documents(project_id, query)
            
            # Create a mapping of doc_id to search score
            relevance_scores = {result['id']: result.get('score', 0) for result in search_results}
            
            # Sort documents by relevance score (highest first)
            documents.sort(
                key=lambda doc: relevance_scores.get(doc['id'], 0), 
                reverse=True
            )
        
        # Calculate tokens for each document
        for doc in documents:
            doc_content = doc.get('content', '')
            doc['token_estimate'] = self.estimate_tokens(doc_content)
        
        # Determine how many documents we can include fully
        context_content = ""
        context_docs_info = []
        current_tokens = 0
        
        for doc in documents:
            doc_tokens = doc['token_estimate']
            doc_title = doc.get('title', 'Document')
            
            # Calculate tokens for the header (document title)
            header = f"## {doc_title}\n\n"
            header_tokens = self.estimate_tokens(header)
            
            # Check if this document would exceed our token limit
            if current_tokens + doc_tokens + header_tokens > available_tokens:
                # If this is the first document, we need to include at least part of it
                if not context_docs_info:
                    # Calculate how many tokens we can use for content
                    content_tokens = available_tokens - current_tokens - header_tokens
                    
                    # Get the content and limit it
                    content = doc.get('content', '')
                    
                    # Estimate characters based on token ratio
                    max_chars = int(content_tokens / DEFAULT_TOKENS_PER_CHAR)
                    
                    # Find a good breaking point (end of sentence or paragraph)
                    # Look for the last period, question mark, or exclamation mark followed by whitespace
                    # within the allowed character limit
                    breakpoint = max(
                        content[:max_chars].rfind('. '),
                        content[:max_chars].rfind('! '),
                        content[:max_chars].rfind('? '),
                        content[:max_chars].rfind('\n\n')
                    )
                    
                    # If no good breakpoint found, just cut at the character limit
                    if breakpoint == -1:
                        breakpoint = max_chars
                    else:
                        # Include the period/etc and the space
                        breakpoint += 2
                    
                    truncated_content = content[:breakpoint] + "...[truncated]"
                    
                    # Add to context
                    context_content += header + truncated_content + "\n\n"
                    truncated_tokens = self.estimate_tokens(truncated_content)
                    
                    context_docs_info.append({
                        'id': doc['id'],
                        'title': doc_title,
                        'tokens': truncated_tokens + header_tokens,
                        'truncated': True
                    })
                    
                    current_tokens += truncated_tokens + header_tokens
                
                # Stop processing more documents
                break
            
            # Add document to context
            content = doc.get('content', '')
            context_content += header + content + "\n\n"
            
            context_docs_info.append({
                'id': doc['id'],
                'title': doc_title,
                'tokens': doc_tokens + header_tokens,
                'truncated': False
            })
            
            current_tokens += doc_tokens + header_tokens
        
        return context_content, context_docs_info
    
    @timer
    def prepare_system_prompt_with_context(self,
                                         project_id: str,
                                         document_ids: List[str],
                                         query: str,
                                         base_system_prompt: str = "",
                                         message_history: List[Dict[str, Any]] = None) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Prepare a system prompt with context from documents.
        
        Args:
            project_id: Project ID
            document_ids: List of document IDs to include
            query: The user query
            base_system_prompt: Base system prompt (without RAG context)
            message_history: Conversation history
            
        Returns:
            Tuple of (system prompt with context, list of document info dicts)
        """
        if not document_ids:
            return base_system_prompt, []
        
        message_history = message_history or []
        
        # Calculate available tokens for context
        available_tokens = self.calculate_available_context_tokens(
            message_history=message_history,
            system_message=base_system_prompt
        )
        
        # Select and format documents to fit in available tokens
        context_content, context_docs_info = self.select_and_format_documents(
            project_id=project_id,
            document_ids=document_ids,
            query=query,
            available_tokens=available_tokens
        )
        
        # Combine with base system prompt
        if context_content:
            system_prompt = base_system_prompt
            if system_prompt:
                system_prompt += "\n\n"
            system_prompt += "Use the following information to answer the user's question:\n\n" + context_content
        else:
            system_prompt = base_system_prompt
        
        return system_prompt, context_docs_info
    
    @timer
    def estimate_document_tokens(self, document: Dict[str, Any]) -> int:
        """
        Estimate tokens for a document.
        
        Args:
            document: Document dictionary
            
        Returns:
            Estimated token count
        """
        content = document.get('content', '')
        return self.estimate_tokens(content)
    
    @timer
    def format_documents_for_context(self, 
                                  documents: List[Dict[str, Any]], 
                                  max_tokens: int) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Format a list of documents for context, fitting within max_tokens.
        
        Args:
            documents: List of document dictionaries
            max_tokens: Maximum tokens to use
            
        Returns:
            Tuple of (formatted context, document info list)
        """
        if not documents or max_tokens <= 0:
            return "", []
        
        # Calculate tokens for each document
        for doc in documents:
            if 'token_estimate' not in doc:
                doc['token_estimate'] = self.estimate_document_tokens(doc)
        
        # Sort by relevance if score is available
        if 'score' in documents[0]:
            documents.sort(key=lambda doc: doc.get('score', 0), reverse=True)
        
        # Format documents to fit within token limit
        formatted_context = ""
        docs_info = []
        current_tokens = 0
        
        for doc in documents:
            doc_title = doc.get('title', 'Document')
            doc_content = doc.get('content', '')
            doc_tokens = doc.get('token_estimate', self.estimate_tokens(doc_content))
            
            # Calculate tokens for the header
            header = f"## {doc_title}\n\n"
            header_tokens = self.estimate_tokens(header)
            
            # Check if adding this document would exceed the token limit
            if current_tokens + doc_tokens + header_tokens > max_tokens:
                # If this is the first document, include a truncated version
                if not docs_info:
                    available_content_tokens = max_tokens - current_tokens - header_tokens
                    truncated_content = self._truncate_text(doc_content, available_content_tokens)
                    
                    formatted_context += header + truncated_content + "\n\n"
                    truncated_tokens = self.estimate_tokens(truncated_content)
                    
                    docs_info.append({
                        'id': doc.get('id'),
                        'title': doc_title,
                        'tokens': truncated_tokens + header_tokens,
                        'truncated': True
                    })
                    
                    current_tokens += truncated_tokens + header_tokens
                
                # Stop processing more documents
                break
            
            # Add full document
            formatted_context += header + doc_content + "\n\n"
            docs_info.append({
                'id': doc.get('id'),
                'title': doc_title,
                'tokens': doc_tokens + header_tokens,
                'truncated': False
            })
            
            current_tokens += doc_tokens + header_tokens
        
        return formatted_context, docs_info
    
    def _truncate_text(self, text: str, max_tokens: int) -> str:
        """
        Truncate text to fit within max_tokens in a smart way.
        
        Args:
            text: Text to truncate
            max_tokens: Maximum tokens allowed
            
        Returns:
            Truncated text
        """
        if not text:
            return ""
        
        # Convert tokens to approximate character count
        max_chars = int(max_tokens / DEFAULT_TOKENS_PER_CHAR)
        
        # If text is already short enough, return it as is
        if len(text) <= max_chars:
            return text
        
        # Find a good breaking point (end of sentence or paragraph)
        breakpoint = max(
            text[:max_chars].rfind('. '),
            text[:max_chars].rfind('! '),
            text[:max_chars].rfind('? '),
            text[:max_chars].rfind('\n\n')
        )
        
        # If no good breakpoint found, just cut at the character limit
        if breakpoint == -1:
            return text[:max_chars] + "...[truncated]"
        else:
            # Include the period/etc and the space
            return text[:breakpoint + 2] + "...[truncated]"

# Create default instance
context_manager = SmartContextManager()