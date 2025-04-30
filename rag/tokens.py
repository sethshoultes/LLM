#!/usr/bin/env python3
"""
Unified token management module for the LLM Platform.

Provides centralized token counting, estimation, and budget allocation
for different types of language models. This module serves as the single
source of truth for all token-related operations across the system.
"""

import os
import re
import math
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple

# Import core modules
from core.logging import get_logger

# Configure logger
logger = get_logger("rag.tokens")

# Constants for token estimation
DEFAULT_TOKENS_PER_CHAR = 0.25  # Approximation of tokens per character (1 token ~= 4 chars)
MIN_TOKENS = 1  # Minimum token count for any non-empty text
DEFAULT_CONTEXT_WINDOW = 2048  # Default context window for small models
LARGE_CONTEXT_WINDOW = 4096  # Large context window for bigger models
VERY_LARGE_CONTEXT_WINDOW = 8192  # Very large context window for largest models

# Token reserve constants
TOKEN_RESERVE_RATIO = 0.15  # Percentage of tokens to reserve for the response
MIN_RESERVED_TOKENS = 256  # Minimum number of tokens to reserve for response

# Special token counts for different message components
ROLE_TOKEN_OVERHEAD = 4  # Approximate token overhead for role markers (e.g., "user:", "assistant:")
MESSAGE_SEPARATOR_TOKENS = 3  # Tokens used for message separation
COMPLETION_PREFIX_TOKENS = 2  # Tokens for completion marker


class TokenManager:
    """
    Unified token manager for the LLM Platform.
    
    Provides token counting, estimation, and budget allocation services
    for different model types and sizes.
    """
    
    def __init__(self, model_registry=None):
        """
        Initialize the token manager.
        
        Args:
            model_registry: Optional model registry for accessing tokenizers
        """
        self.model_registry = model_registry
        self.tokenizer_cache = {}  # Cache for loaded tokenizers
    
    def estimate_tokens(self, text: str, model_id: str = None) -> int:
        """
        Estimate the number of tokens in a text string.
        
        Args:
            text: Text to estimate tokens for
            model_id: Optional model identifier for model-specific estimation
            
        Returns:
            Estimated token count
        """
        if not text:
            return 0
        
        # Try to use model-specific tokenizer if available
        if model_id and self.model_registry:
            try:
                return self._count_with_model_tokenizer(text, model_id)
            except Exception as e:
                logger.debug(f"Error using model tokenizer: {e}. Falling back to approximation.")
        
        # Fall back to character-based approximation
        return self._estimate_from_characters(text)
    
    def _count_with_model_tokenizer(self, text: str, model_id: str) -> int:
        """
        Count tokens using a model-specific tokenizer.
        
        Args:
            text: Text to count tokens for
            model_id: Model identifier
            
        Returns:
            Token count from model tokenizer
        """
        # Get model info from registry
        model_info = self.model_registry.get_model_info(model_id)
        if not model_info:
            raise ValueError(f"Model {model_id} not found in registry")
        
        # Use cached tokenizer if available
        if model_id in self.tokenizer_cache:
            tokenizer = self.tokenizer_cache[model_id]
            if hasattr(tokenizer, 'encode'):
                return len(tokenizer.encode(text))
            else:
                raise ValueError(f"Tokenizer for {model_id} doesn't have encode method")
        
        # Handle different model types
        model_path = model_info.get('path')
        model_type = model_info.get('type', '').lower()
        
        if 'llama' in model_type or model_path.endswith('.gguf'):
            # Llama models via llama-cpp-python
            try:
                from llama_cpp import Llama
                llm = Llama(model_path=model_path, n_ctx=0, verbose=False)
                result = len(llm.tokenize(text.encode('utf-8')))
                # Don't cache the full model to save memory
                return result
            except Exception as e:
                logger.warning(f"Failed to use llama tokenizer: {e}")
                raise
                
        elif 'gpt' in model_type or 'chatgpt' in model_type:
            # OpenAI models
            try:
                import tiktoken
                encoder_name = "cl100k_base"  # Default for gpt-4, gpt-3.5-turbo
                # Could be refined based on specific model
                if model_info.get('name') in ('gpt-3', 'text-davinci-003'):
                    encoder_name = "p50k_base"
                
                tokenizer = tiktoken.get_encoding(encoder_name)
                self.tokenizer_cache[model_id] = tokenizer
                return len(tokenizer.encode(text))
            except Exception as e:
                logger.warning(f"Failed to use OpenAI tokenizer: {e}")
                raise
                
        elif 'bert' in model_type or 'roberta' in model_type:
            # Hugging Face transformer models
            try:
                from transformers import AutoTokenizer
                tokenizer = AutoTokenizer.from_pretrained(model_path)
                self.tokenizer_cache[model_id] = tokenizer
                return len(tokenizer.encode(text))
            except Exception as e:
                logger.warning(f"Failed to use transformer tokenizer: {e}")
                raise
        
        # If no specific tokenizer is available
        raise ValueError(f"No tokenizer available for model type {model_type}")
    
    def _estimate_from_characters(self, text: str) -> int:
        """
        Estimate token count based on character count and patterns.
        
        Args:
            text: Text to estimate tokens for
            
        Returns:
            Estimated token count
        """
        if not text:
            return 0
        
        # Count characters
        char_count = len(text)
        
        # Count spaces and newlines which typically tokenize differently
        space_count = text.count(' ')
        newline_count = text.count('\n')
        
        # Count numbers which often get tokenized differently
        number_count = sum(c.isdigit() for c in text)
        
        # Count special characters which often get their own tokens
        special_char_count = sum(not (c.isalnum() or c.isspace()) for c in text)
        
        # Basic approximation: 1 token is roughly 4 characters for English text
        token_estimate = int(char_count * DEFAULT_TOKENS_PER_CHAR)
        
        # Adjust for spaces (often cause token breaks)
        token_estimate += space_count // 8
        
        # Adjust for newlines (often treated as special tokens)
        token_estimate += newline_count // 2
        
        # Adjust for numbers and special characters (often tokenized separately)
        token_estimate += (number_count + special_char_count) // 6
        
        # Ensure minimum token count
        return max(MIN_TOKENS, token_estimate)
    
    def estimate_prompt_tokens(self, 
                             messages: List[Dict[str, Any]], 
                             system_message: str = "", 
                             model_id: str = None) -> Dict[str, int]:
        """
        Estimate tokens used by a complete prompt (messages + system).
        
        Args:
            messages: List of messages in the conversation
            system_message: System message or instructions
            model_id: Optional model identifier
            
        Returns:
            Dictionary with token counts for different components and total
        """
        # Initialize counts
        system_tokens = self.estimate_tokens(system_message, model_id) if system_message else 0
        message_tokens = 0
        
        # Count tokens for each message
        for message in messages:
            role = message.get('role', '')
            content = message.get('content', '')
            
            # Count content tokens
            content_tokens = self.estimate_tokens(content, model_id)
            
            # Add role overhead
            message_tokens += content_tokens + ROLE_TOKEN_OVERHEAD
        
        # Add separator tokens between messages
        if messages:
            message_tokens += (len(messages) - 1) * MESSAGE_SEPARATOR_TOKENS
        
        # Add completion prefix tokens
        message_tokens += COMPLETION_PREFIX_TOKENS
        
        # Calculate total
        total_tokens = system_tokens + message_tokens
        
        # Return detailed breakdown
        return {
            'total': total_tokens,
            'system': system_tokens,
            'messages': message_tokens,
            'message_count': len(messages)
        }
    
    def get_context_window(self, model_id: str = None, model_path: str = None) -> int:
        """
        Determine the context window size for a model.
        
        Args:
            model_id: Optional model identifier
            model_path: Optional model path for heuristic detection
            
        Returns:
            Context window size in tokens
        """
        # Try to get from model registry first
        if model_id and self.model_registry:
            model_info = self.model_registry.get_model_info(model_id)
            if model_info and 'context_window' in model_info:
                return model_info['context_window']
        
        # Fall back to heuristic detection from path
        if model_path:
            model_path_lower = str(model_path).lower()
            
            # Very large models
            if any(marker in model_path_lower for marker in ["70b", "claude", "gpt-4"]):
                return VERY_LARGE_CONTEXT_WINDOW  # 8192 tokens
                
            # Medium-sized models
            elif any(marker in model_path_lower for marker in ["13b", "mistral", "7b", "llama2"]):
                return LARGE_CONTEXT_WINDOW  # 4096 tokens
            
            # Small models
            elif any(marker in model_path_lower for marker in ["tiny", "small", "1.1b", "1b"]):
                return DEFAULT_CONTEXT_WINDOW  # 2048 tokens
        
        # Default context window
        return DEFAULT_CONTEXT_WINDOW
    
    def allocate_tokens(self, 
                      context_window: int,
                      system_tokens: int = 0,
                      message_tokens: int = 0,
                      completion_tokens: int = 0) -> Dict[str, int]:
        """
        Allocate token budget for different components of the conversation.
        
        Args:
            context_window: Total context window size
            system_tokens: Tokens used by system message
            message_tokens: Tokens used by conversation history
            completion_tokens: Desired tokens for completion (0 for auto)
            
        Returns:
            Dictionary with token allocation for different components
        """
        # Calculate reserved tokens (for response)
        reserved_tokens = max(
            completion_tokens if completion_tokens > 0 else MIN_RESERVED_TOKENS,
            int(context_window * TOKEN_RESERVE_RATIO)
        )
        
        # Calculate available tokens for RAG context
        available_for_context = max(0, context_window - system_tokens - message_tokens - reserved_tokens)
        
        # Calculate percentages
        total_used = system_tokens + message_tokens + reserved_tokens
        system_pct = round((system_tokens / context_window) * 100, 1) if context_window > 0 else 0
        message_pct = round((message_tokens / context_window) * 100, 1) if context_window > 0 else 0
        reserved_pct = round((reserved_tokens / context_window) * 100, 1) if context_window > 0 else 0
        available_pct = round((available_for_context / context_window) * 100, 1) if context_window > 0 else 0
        
        # Return allocation
        return {
            'context_window': context_window,
            'system_tokens': system_tokens,
            'system_pct': system_pct,
            'message_tokens': message_tokens,
            'message_pct': message_pct,
            'reserved_tokens': reserved_tokens,
            'reserved_pct': reserved_pct,
            'available_for_context': available_for_context,
            'available_pct': available_pct,
            'total_used': total_used,
            'total_used_pct': round((total_used / context_window) * 100, 1) if context_window > 0 else 0,
            'is_over_limit': total_used > context_window
        }
    
    def allocate_context_budget(self,
                             context_window: int,
                             system_message: str,
                             messages: List[Dict[str, Any]],
                             model_id: str = None,
                             completion_tokens: int = 0) -> Dict[str, Any]:
        """
        Calculate token budget for RAG context.
        
        Args:
            context_window: Total context window size
            system_message: System message (without RAG context)
            messages: Conversation history
            model_id: Optional model identifier
            completion_tokens: Desired tokens for completion (0 for auto)
            
        Returns:
            Token allocation with detailed breakdown
        """
        # Estimate tokens for system and messages
        system_tokens = self.estimate_tokens(system_message, model_id) if system_message else 0
        
        # Get message tokens
        prompt_tokens = self.estimate_prompt_tokens(messages, '', model_id)
        message_tokens = prompt_tokens['messages']
        
        # Allocate tokens
        allocation = self.allocate_tokens(
            context_window=context_window,
            system_tokens=system_tokens,
            message_tokens=message_tokens,
            completion_tokens=completion_tokens
        )
        
        # Add additional metadata
        allocation['model_id'] = model_id
        allocation['message_count'] = len(messages)
        
        return allocation
    
    def get_token_limit_warnings(self, allocation: Dict[str, Any]) -> List[str]:
        """
        Generate warnings based on token allocation.
        
        Args:
            allocation: Token allocation dictionary
            
        Returns:
            List of warning messages if any thresholds are exceeded
        """
        warnings = []
        
        # Check if over limit
        if allocation.get('is_over_limit', False):
            warnings.append(
                f"Token limit exceeded: Using {allocation.get('total_used', 0)} tokens, "
                f"but context window is only {allocation.get('context_window', 0)} tokens"
            )
        
        # Check if close to limit (>90%)
        elif allocation.get('total_used_pct', 0) > 90:
            warnings.append(
                f"Token usage high: Using {allocation.get('total_used_pct', 0)}% of "
                f"available context window ({allocation.get('total_used', 0)} tokens)"
            )
        
        # Check if response tokens are below minimum
        if allocation.get('reserved_tokens', 0) < MIN_RESERVED_TOKENS:
            warnings.append(
                f"Low response token allowance: Only {allocation.get('reserved_tokens', 0)} "
                f"tokens available for response (minimum recommended is {MIN_RESERVED_TOKENS})"
            )
        
        return warnings


# Create singleton instance for global use
token_manager = TokenManager()