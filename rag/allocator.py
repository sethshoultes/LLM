#!/usr/bin/env python3
"""
Token allocation module for the LLM Platform.

Provides specialized token budget allocation strategies for different
use cases, optimizing context usage based on conversation dynamics
and document characteristics.
"""

from typing import Dict, List, Any, Optional, Union, Tuple, Set

# Import core modules
from core.logging import get_logger
from core.utils import timer

# Import from tokens module
from rag.tokens import token_manager

# Configure logger
logger = get_logger("rag.allocator")

# Allocation strategy constants
ALLOCATION_STRATEGY_EQUAL = "equal"  # Allocate tokens equally among documents
ALLOCATION_STRATEGY_PROPORTIONAL = "proportional"  # Allocate tokens proportionally to relevance
ALLOCATION_STRATEGY_PRIORITIZED = "prioritized"  # Prioritize most relevant documents
ALLOCATION_STRATEGY_ADAPTIVE = "adaptive"  # Adapt allocation based on conversation

# Default allocation parameters
DEFAULT_MIN_DOCUMENT_TOKENS = 100  # Minimum tokens to allocate to any included document
DEFAULT_DOCUMENT_HEADER_TOKENS = 20  # Tokens reserved for document headers


class TokenAllocator:
    """
    Token budget allocator for RAG systems.
    
    Provides different strategies for allocating token budget to documents
    based on relevance, conversation context, and other factors.
    """
    
    def __init__(self):
        """Initialize the token allocator."""
        # Default allocation strategy
        self.default_strategy = ALLOCATION_STRATEGY_PRIORITIZED
    
    @timer
    def allocate_tokens(self,
                      documents: List[Dict[str, Any]],
                      available_tokens: int,
                      strategy: str = None,
                      query: str = None) -> List[Dict[str, Any]]:
        """
        Allocate available tokens to documents based on strategy.
        
        Args:
            documents: List of documents with relevance scores
            available_tokens: Maximum tokens available for context
            strategy: Allocation strategy to use
            query: Optional user query for relevance considerations
            
        Returns:
            Documents with token allocations
        """
        if not documents or available_tokens <= 0:
            return []
        
        # Use default strategy if none specified
        strategy = strategy or self.default_strategy
        
        # Apply allocation strategy
        if strategy == ALLOCATION_STRATEGY_EQUAL:
            return self._allocate_equal(documents, available_tokens)
        elif strategy == ALLOCATION_STRATEGY_PROPORTIONAL:
            return self._allocate_proportional(documents, available_tokens)
        elif strategy == ALLOCATION_STRATEGY_PRIORITIZED:
            return self._allocate_prioritized(documents, available_tokens)
        elif strategy == ALLOCATION_STRATEGY_ADAPTIVE:
            return self._allocate_adaptive(documents, available_tokens, query)
        else:
            logger.warning(f"Unknown allocation strategy: {strategy}. Using prioritized.")
            return self._allocate_prioritized(documents, available_tokens)
    
    def _allocate_equal(self,
                      documents: List[Dict[str, Any]],
                      available_tokens: int) -> List[Dict[str, Any]]:
        """
        Allocate tokens equally among documents.
        
        Args:
            documents: List of documents
            available_tokens: Maximum tokens available for context
            
        Returns:
            Documents with token allocations
        """
        # Calculate header tokens
        header_tokens_per_doc = DEFAULT_DOCUMENT_HEADER_TOKENS
        total_header_tokens = len(documents) * header_tokens_per_doc
        
        # Calculate content tokens
        content_tokens = max(0, available_tokens - total_header_tokens)
        
        # Calculate tokens per document
        if len(documents) > 0:
            content_tokens_per_doc = content_tokens // len(documents)
        else:
            content_tokens_per_doc = 0
        
        # Apply allocations
        allocated_docs = []
        
        for doc in documents:
            # Ensure minimum token allocation
            doc_allocation = max(DEFAULT_MIN_DOCUMENT_TOKENS, content_tokens_per_doc)
            
            # Check if we have enough tokens for this document
            if doc_allocation + header_tokens_per_doc <= available_tokens:
                # Add document with allocation
                allocated_doc = doc.copy()
                allocated_doc["allocated_tokens"] = doc_allocation
                allocated_doc["header_tokens"] = header_tokens_per_doc
                allocated_doc["total_allocated"] = doc_allocation + header_tokens_per_doc
                
                allocated_docs.append(allocated_doc)
                
                # Update available tokens
                available_tokens -= (doc_allocation + header_tokens_per_doc)
            else:
                # Not enough tokens left
                break
        
        return allocated_docs
    
    def _allocate_proportional(self,
                            documents: List[Dict[str, Any]],
                            available_tokens: int) -> List[Dict[str, Any]]:
        """
        Allocate tokens proportionally to document relevance scores.
        
        Args:
            documents: List of documents with relevance scores
            available_tokens: Maximum tokens available for context
            
        Returns:
            Documents with token allocations
        """
        if not documents:
            return []
        
        # Ensure documents have scores
        if "score" not in documents[0]:
            logger.warning("No relevance scores found. Using equal allocation.")
            return self._allocate_equal(documents, available_tokens)
        
        # Calculate total score for normalization
        total_score = sum(doc.get("score", 0) for doc in documents)
        
        if total_score <= 0:
            logger.warning("Total relevance score is zero. Using equal allocation.")
            return self._allocate_equal(documents, available_tokens)
        
        # Calculate header tokens
        header_tokens_per_doc = DEFAULT_DOCUMENT_HEADER_TOKENS
        total_header_tokens = len(documents) * header_tokens_per_doc
        
        # Calculate content tokens
        content_tokens = max(0, available_tokens - total_header_tokens)
        
        # Allocate tokens proportionally to score
        allocated_docs = []
        remaining_tokens = content_tokens
        
        for doc in documents:
            score = doc.get("score", 0)
            proportion = score / total_score
            
            # Calculate token allocation
            doc_allocation = max(
                DEFAULT_MIN_DOCUMENT_TOKENS,
                int(content_tokens * proportion)
            )
            
            # Ensure we don't exceed remaining tokens
            doc_allocation = min(doc_allocation, remaining_tokens)
            
            # Check if we have enough tokens
            if doc_allocation + header_tokens_per_doc <= available_tokens:
                # Add document with allocation
                allocated_doc = doc.copy()
                allocated_doc["allocated_tokens"] = doc_allocation
                allocated_doc["header_tokens"] = header_tokens_per_doc
                allocated_doc["total_allocated"] = doc_allocation + header_tokens_per_doc
                allocated_doc["allocation_proportion"] = proportion
                
                allocated_docs.append(allocated_doc)
                
                # Update available and remaining tokens
                available_tokens -= (doc_allocation + header_tokens_per_doc)
                remaining_tokens -= doc_allocation
            else:
                # Not enough tokens left
                break
        
        return allocated_docs
    
    def _allocate_prioritized(self,
                           documents: List[Dict[str, Any]],
                           available_tokens: int) -> List[Dict[str, Any]]:
        """
        Allocate tokens prioritizing most relevant documents.
        
        Args:
            documents: List of documents with relevance scores
            available_tokens: Maximum tokens available for context
            
        Returns:
            Documents with token allocations
        """
        if not documents:
            return []
        
        # Sort by relevance if scores available
        if "score" in documents[0]:
            sorted_docs = sorted(documents, key=lambda d: d.get("score", 0), reverse=True)
        else:
            sorted_docs = documents
        
        # Calculate header tokens
        header_tokens_per_doc = DEFAULT_DOCUMENT_HEADER_TOKENS
        
        # Allocated documents
        allocated_docs = []
        remaining_tokens = available_tokens
        
        for doc in sorted_docs:
            # Calculate token need for this document
            doc_tokens = doc.get("total_tokens", token_manager.estimate_tokens(doc.get("content", "")))
            header_tokens = header_tokens_per_doc
            total_need = doc_tokens + header_tokens
            
            # If we can fit the entire document
            if total_need <= remaining_tokens:
                # Add document with allocation
                allocated_doc = doc.copy()
                allocated_doc["allocated_tokens"] = doc_tokens
                allocated_doc["header_tokens"] = header_tokens
                allocated_doc["total_allocated"] = total_need
                allocated_doc["truncated"] = False
                
                allocated_docs.append(allocated_doc)
                
                # Update remaining tokens
                remaining_tokens -= total_need
            else:
                # If we can fit at least part of the document
                if remaining_tokens > header_tokens + DEFAULT_MIN_DOCUMENT_TOKENS:
                    # Allocate remaining tokens (minus header)
                    content_tokens = remaining_tokens - header_tokens
                    
                    # Add truncated document
                    allocated_doc = doc.copy()
                    allocated_doc["allocated_tokens"] = content_tokens
                    allocated_doc["header_tokens"] = header_tokens
                    allocated_doc["total_allocated"] = content_tokens + header_tokens
                    allocated_doc["truncated"] = True
                    
                    allocated_docs.append(allocated_doc)
                    
                    # All tokens are now allocated
                    remaining_tokens = 0
                
                # Stop allocating
                break
        
        return allocated_docs
    
    def _allocate_adaptive(self,
                        documents: List[Dict[str, Any]],
                        available_tokens: int,
                        query: str = None) -> List[Dict[str, Any]]:
        """
        Adaptively allocate tokens based on query and document characteristics.
        
        Args:
            documents: List of documents with relevance scores
            available_tokens: Maximum tokens available for context
            query: User query for additional relevance considerations
            
        Returns:
            Documents with token allocations
        """
        if not documents:
            return []
        
        # Default to prioritized if no query provided
        if not query:
            return self._allocate_prioritized(documents, available_tokens)
        
        # Sort by relevance if scores available
        if "score" in documents[0]:
            sorted_docs = sorted(documents, key=lambda d: d.get("score", 0), reverse=True)
        else:
            sorted_docs = documents
        
        # Calculate header tokens
        header_tokens_per_doc = DEFAULT_DOCUMENT_HEADER_TOKENS
        
        # For adaptive allocation, we'll reserve tokens for most relevant document
        # and distribute remaining tokens among others based on relevance
        if len(sorted_docs) > 1 and "score" in sorted_docs[0]:
            # Get top document
            top_doc = sorted_docs[0]
            other_docs = sorted_docs[1:]
            
            # Allocate at least 40% of tokens to top document
            top_doc_tokens = min(
                top_doc.get("total_tokens", token_manager.estimate_tokens(top_doc.get("content", ""))),
                max(int(available_tokens * 0.4), DEFAULT_MIN_DOCUMENT_TOKENS)
            )
            
            # Reserve header tokens
            top_doc_total = top_doc_tokens + header_tokens_per_doc
            
            # Allocate remaining tokens to other documents using proportional strategy
            remaining_tokens = available_tokens - top_doc_total
            
            # Create combined result
            if remaining_tokens > header_tokens_per_doc + DEFAULT_MIN_DOCUMENT_TOKENS:
                # Allocate other documents proportionally
                other_allocated = self._allocate_proportional(other_docs, remaining_tokens)
                
                # Add top document
                top_allocated = top_doc.copy()
                top_allocated["allocated_tokens"] = top_doc_tokens
                top_allocated["header_tokens"] = header_tokens_per_doc
                top_allocated["total_allocated"] = top_doc_total
                top_allocated["truncated"] = top_doc_tokens < token_manager.estimate_tokens(top_doc.get("content", ""))
                
                # Combine results
                return [top_allocated] + other_allocated
            else:
                # Only include top document
                top_allocated = top_doc.copy()
                top_allocated["allocated_tokens"] = top_doc_tokens
                top_allocated["header_tokens"] = header_tokens_per_doc
                top_allocated["total_allocated"] = top_doc_total
                top_allocated["truncated"] = top_doc_tokens < token_manager.estimate_tokens(top_doc.get("content", ""))
                
                return [top_allocated]
        else:
            # Fall back to prioritized for single document or no scores
            return self._allocate_prioritized(documents, available_tokens)


# Create singleton instance for global use
token_allocator = TokenAllocator()