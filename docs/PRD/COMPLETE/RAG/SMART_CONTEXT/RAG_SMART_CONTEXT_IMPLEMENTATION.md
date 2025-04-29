# RAG Smart Context Implementation Summary

## Overview

The RAG Smart Context system improves context management for different models when using Retrieval-Augmented Generation. It dynamically adjusts document inclusion based on conversation length, model capabilities, and relevance.

## Key Features

1. **Adaptive Token Management**
   - Adjusts context allocation based on conversation history length
   - Reserves appropriate tokens for system prompts and model responses
   - Adapts to different model context window sizes (small vs. large models)

2. **Intelligent Document Selection**
   - Prioritizes documents by relevance to the query
   - Truncates documents intelligently at sentence/paragraph boundaries
   - Ensures most important information is included even with limited context

3. **Dynamic Context Formatting**
   - Structures document context for optimal comprehension
   - Maintains document header and attribution information
   - Formats context in a way that preserves knowledge organization

## Implementation

The implementation consists of:

1. **Smart Context Manager Module**
   - Located at `rag_support/utils/context_manager.py`
   - Responsible for all context management logic
   - Provides a consistent API for the main interface

2. **CLI Integration**
   - Added `--no-smart-context` flag to disable the feature
   - Default behavior is to enable smart context management
   - Environment variable `LLM_RAG_SMART_CONTEXT` controls the setting

3. **UI Feedback**
   - Shows Smart Context status in the interface when RAG is enabled
   - Provides clear log information about context decisions

## Usage

Smart Context management is enabled by default when using RAG. To disable it:

```bash
./llm.sh --rag --no-smart-context
```

This will fall back to the legacy context handling with fixed allocation.

## Benefits

1. **Error Prevention**
   - Eliminates "token limit exceeded" errors that occurred with fixed context allocation
   - Prevents model degeneration from excess context overload

2. **Improved Response Quality**
   - More relevant information is prioritized in limited context
   - Ensures small models can still benefit from RAG

3. **Adaptive Experience**
   - Works with both small models (2K context) and large models (8K+ context)
   - Dynamically shifts context allocation as conversation grows

## Technical Details

- **Token Estimation**: Uses character-based heuristics (4 chars ≈ 1 token) for quick estimation
- **Context Window Detection**: Automatically determines model size from path and name
- **Relevance Scoring**: Uses simple TF-IDF scoring from search engine to prioritize documents
- **Breaking Point Selection**: Truncates text at natural boundaries (sentences, paragraphs)

## Future Extensions

Planned future improvements include:

1. Document summarization using a separate model
2. Semantic chunking for more precise excerpts
3. Full-text indexing for better document selection
4. Cross-document context synthesis

The current implementation successfully addresses immediate issues while providing a foundation for these future enhancements.