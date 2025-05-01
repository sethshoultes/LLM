#!/usr/bin/env python3
"""
Prompt formatting module for the LLM Platform.

Provides standardized prompt formatting for different model types and families.
"""

from typing import Dict, List, Optional, Any, Union

from core.logging import get_logger
from models.registry import get_model_info

# Get logger for this module
logger = get_logger("models.formatter")

class PromptFormatter:
    """
    Prompt formatter for different model types.
    
    Handles formatting of prompts, system messages, and conversation history
    according to the requirements of different model families.
    """
    
    def format_prompt(self, model_path: str, prompt: str, system_prompt: str = "") -> str:
        """
        Format a prompt for a specific model.
        
        Args:
            model_path: Path to the model
            prompt: User prompt
            system_prompt: Optional system prompt/instructions
            
        Returns:
            Formatted prompt string
        """
        # Get model info from registry
        model_info = get_model_info(model_path)
        if not model_info:
            # Fallback to generic format if model not found
            logger.warning(f"Model info not found for {model_path}, using generic format")
            return self._format_generic(prompt, system_prompt)
        
        # Get model family
        model_family = model_info.get("family", "unknown").lower()
        
        # Format based on model family
        if model_family == "mistral":
            return self._format_mistral(prompt, system_prompt)
        elif model_family == "llama":
            return self._format_llama(prompt, system_prompt)
        elif model_family == "tinyllama":
            return self._format_tinyllama(prompt, system_prompt)
        elif model_family == "phi":
            return self._format_phi(prompt, system_prompt)
        elif model_family == "mixtral":
            return self._format_mistral(prompt, system_prompt)  # Mixtral uses mistral format
        elif model_family == "gemma":
            return self._format_gemma(prompt, system_prompt)
        else:
            # Generic format for unknown models
            return self._format_generic(prompt, system_prompt)
    
    def _format_mistral(self, prompt: str, system_prompt: str = "") -> str:
        """Format prompt for Mistral models."""
        # Don't explicitly add <s> token - the model's chat template will add it
        if system_prompt:
            return f"[INST] {system_prompt}\n\n{prompt} [/INST]"
        else:
            return f"[INST] {prompt} [/INST]"
    
    def _format_llama(self, prompt: str, system_prompt: str = "") -> str:
        """Format prompt for Llama models."""
        if system_prompt:
            return f"<s>[INST] <<SYS>>\n{system_prompt}\n<</SYS>>\n\n{prompt} [/INST]"
        else:
            return f"<s>[INST] {prompt} [/INST]"
    
    def _format_tinyllama(self, prompt: str, system_prompt: str = "") -> str:
        """Format prompt for TinyLlama models."""
        if system_prompt:
            return f"<|system|>\n{system_prompt}</s>\n<|user|>\n{prompt}</s>\n<|assistant|>\n"
        else:
            return f"<|user|>\n{prompt}</s>\n<|assistant|>\n"
    
    def _format_phi(self, prompt: str, system_prompt: str = "") -> str:
        """Format prompt for Phi models."""
        if system_prompt:
            return f"<|system|>\n{system_prompt}\n<|user|>\n{prompt}\n<|assistant|>\n"
        else:
            return f"<|user|>\n{prompt}\n<|assistant|>\n"
    
    def _format_gemma(self, prompt: str, system_prompt: str = "") -> str:
        """Format prompt for Gemma models."""
        if system_prompt:
            return f"<start_of_turn>user\n{system_prompt}\n\n{prompt}<end_of_turn>\n<start_of_turn>model\n"
        else:
            return f"<start_of_turn>user\n{prompt}<end_of_turn>\n<start_of_turn>model\n"
    
    def _format_generic(self, prompt: str, system_prompt: str = "") -> str:
        """Generic format for unknown models."""
        if system_prompt:
            return f"### System:\n{system_prompt}\n\n### User:\n{prompt}\n\n### Assistant:\n"
        else:
            return f"### User:\n{prompt}\n\n### Assistant:\n"
    
    def format_conversation(self, model_path: str, messages: List[Dict[str, str]], 
                           system_prompt: str = "") -> str:
        """
        Format a conversation history for a specific model.
        
        Args:
            model_path: Path to the model
            messages: List of conversation messages with 'role' and 'content'
            system_prompt: Optional system prompt/instructions
            
        Returns:
            Formatted conversation string
        """
        if not messages:
            return ""
        
        # Get model info from registry
        model_info = get_model_info(model_path)
        if not model_info:
            # Fallback to generic format if model not found
            logger.warning(f"Model info not found for {model_path}, using generic format")
            return self._format_conversation_generic(messages, system_prompt)
        
        # Get model family
        model_family = model_info.get("family", "unknown").lower()
        
        # Format based on model family
        if model_family == "mistral":
            return self._format_conversation_mistral(messages, system_prompt)
        elif model_family == "llama":
            return self._format_conversation_llama(messages, system_prompt)
        elif model_family == "tinyllama":
            return self._format_conversation_tinyllama(messages, system_prompt)
        elif model_family == "phi":
            return self._format_conversation_phi(messages, system_prompt)
        elif model_family == "mixtral":
            return self._format_conversation_mistral(messages, system_prompt)  # Mixtral uses mistral format
        elif model_family == "gemma":
            return self._format_conversation_gemma(messages, system_prompt)
        else:
            # Generic format for unknown models
            return self._format_conversation_generic(messages, system_prompt)
    
    def _format_conversation_mistral(self, messages: List[Dict[str, str]], system_prompt: str = "") -> str:
        """Format conversation for Mistral models."""
        formatted_content = ""
        
        # Remove explicit start token - model's chat template will add it
        # This prevents the "duplicate leading <s>" warning
        
        # Process messages in pairs (user + assistant)
        for i in range(0, len(messages), 2):
            user_msg = messages[i] if i < len(messages) else None
            assistant_msg = messages[i+1] if i+1 < len(messages) else None
            
            # Add system prompt before the first user message if available
            if i == 0 and system_prompt:
                # For the first pair with system prompt
                if user_msg and user_msg.get('role') == 'user':
                    formatted_content += f"[INST] {system_prompt}\n\n{user_msg.get('content')} [/INST] "
                    
                    # Add assistant response if available
                    if assistant_msg and assistant_msg.get('role') == 'assistant':
                        formatted_content += f"{assistant_msg.get('content')} "
                continue
            
            # Handle regular message pairs
            if user_msg and user_msg.get('role') == 'user':
                formatted_content += f"[INST] {user_msg.get('content')} [/INST] "
                
                # Add assistant response if available
                if assistant_msg and assistant_msg.get('role') == 'assistant':
                    formatted_content += f"{assistant_msg.get('content')} "
        
        # If the last message is from a user and wasn't handled in the loop
        if messages[-1].get('role') == 'user' and (len(messages) % 2 == 1):
            # Make sure we don't repeat the prompt if it was the only message
            if len(messages) > 1 or not system_prompt:
                formatted_content += f"[INST] {messages[-1].get('content')} [/INST]"
                
        return formatted_content
    
    def _format_conversation_llama(self, messages: List[Dict[str, str]], system_prompt: str = "") -> str:
        """Format conversation for Llama models."""
        if system_prompt:
            current_content = f"<s>[INST] <<SYS>>\n{system_prompt}\n<</SYS>>\n\n"
        else:
            current_content = "<s>[INST] "
            
        # Track if we need to start a new instruction
        need_inst_tag = False
        
        for i, msg in enumerate(messages):
            role = msg.get('role', '').lower()
            content = msg.get('content', '')
            
            if role == 'user':
                if need_inst_tag:
                    current_content += " [INST] "
                current_content += content
                if i == len(messages) - 1:  # If this is the last message
                    current_content += " [/INST]"
                else:
                    current_content += " [/INST] "
                need_inst_tag = False
            elif role == 'assistant':
                current_content += content + " "
                need_inst_tag = True
        
        return current_content
    
    def _format_conversation_tinyllama(self, messages: List[Dict[str, str]], system_prompt: str = "") -> str:
        """Format conversation for TinyLlama models."""
        formatted_messages = []
        
        if system_prompt:
            formatted_messages.append(f"<|system|>\n{system_prompt}</s>")
        
        for msg in messages:
            role = msg.get('role', '').lower()
            content = msg.get('content', '')
            
            if role == 'user':
                formatted_messages.append(f"<|user|>\n{content}</s>")
            elif role == 'assistant':
                formatted_messages.append(f"<|assistant|>\n{content}</s>")
        
        # Add final assistant prompt
        formatted_messages.append("<|assistant|>")
        
        return "\n".join(formatted_messages)
    
    def _format_conversation_phi(self, messages: List[Dict[str, str]], system_prompt: str = "") -> str:
        """Format conversation for Phi models."""
        formatted_messages = []
        
        if system_prompt:
            formatted_messages.append(f"<|system|>\n{system_prompt}")
        
        for msg in messages:
            role = msg.get('role', '').lower()
            content = msg.get('content', '')
            
            if role == 'user':
                formatted_messages.append(f"<|user|>\n{content}")
            elif role == 'assistant':
                formatted_messages.append(f"<|assistant|>\n{content}")
        
        # Add final assistant prompt if last message was from user
        if messages and messages[-1].get('role', '') == 'user':
            formatted_messages.append("<|assistant|>")
        
        return "\n".join(formatted_messages)
    
    def _format_conversation_gemma(self, messages: List[Dict[str, str]], system_prompt: str = "") -> str:
        """Format conversation for Gemma models."""
        formatted_content = ""
        
        # Add system prompt to the first user message if available
        first_user_msg = None
        for msg in messages:
            if msg.get('role') == 'user':
                first_user_msg = msg
                break
        
        # Process all messages
        for i, msg in enumerate(messages):
            role = msg.get('role', '').lower()
            content = msg.get('content', '')
            
            if role == 'user':
                # For first user message, include system prompt if available
                if msg == first_user_msg and system_prompt:
                    formatted_content += f"<start_of_turn>user\n{system_prompt}\n\n{content}<end_of_turn>\n"
                else:
                    formatted_content += f"<start_of_turn>user\n{content}<end_of_turn>\n"
            elif role == 'assistant':
                formatted_content += f"<start_of_turn>model\n{content}<end_of_turn>\n"
        
        # Add final model turn if last message was from user
        if messages and messages[-1].get('role', '') == 'user':
            formatted_content += "<start_of_turn>model\n"
        
        return formatted_content
    
    def _format_conversation_generic(self, messages: List[Dict[str, str]], system_prompt: str = "") -> str:
        """Generic conversation format for unknown models."""
        formatted_messages = []
        
        if system_prompt:
            formatted_messages.append(f"### System:\n{system_prompt}\n")
        
        for msg in messages:
            role = msg.get('role', '').lower()
            content = msg.get('content', '')
            
            if role == 'user':
                formatted_messages.append(f"### User:\n{content}\n")
            elif role == 'assistant':
                formatted_messages.append(f"### Assistant:\n{content}\n")
        
        # Add final assistant prompt if last message was from user
        if messages and messages[-1].get('role', '') == 'user':
            formatted_messages.append("### Assistant:\n")
        
        return "\n".join(formatted_messages)

# Create a global instance
prompt_formatter = PromptFormatter()

# Convenience functions
def format_prompt(model_path: str, prompt: str, system_prompt: str = "") -> str:
    """Format a prompt for a specific model."""
    return prompt_formatter.format_prompt(model_path, prompt, system_prompt)

def format_conversation(model_path: str, messages: List[Dict[str, str]], system_prompt: str = "") -> str:
    """Format a conversation history for a specific model."""
    return prompt_formatter.format_conversation(model_path, messages, system_prompt)