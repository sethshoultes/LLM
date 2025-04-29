# RAG Smart Context Management PRD

## Issue Summary

The RAG implementation encounters issues with context window management:

1. **Token Limit Errors**: When using RAG with TinyLlama and other small models, users experience errors when the combined token count of conversation history and RAG documents exceeds the model's context window (2048 tokens):
   ```
   Error: Error generating text with history: Requested tokens (2136) exceed context window of 2048
   ```

2. **Degeneration with Large Contexts**: When attempting to increase the context window, small models like TinyLlama produce gibberish/degeneration with outputs like:
   ```
   <<umsumsumsumsumsumsationsumsencesumsumsumsumsppersumsumsumsationsumsumsumsumsatory...
   ```

These issues indicate the need for smart context management that adjusts to model capabilities and preserves the most relevant information.

## Root Cause Analysis

1. **Fixed Context Allocation**: The current implementation allocates a fixed amount of tokens (1200) for RAG context, which doesn't adapt to conversation length or model capabilities.

2. **Raw Document Inclusion**: Documents are included in their raw form without summarization or prioritization, creating information overload for smaller models.

3. **Lack of Adaptive Mechanisms**: There's no mechanism to dynamically adjust context based on model size or to use a separate (potentially larger) model for preprocessing documents.

## Solution Requirements

1. **Smart Context Management**: Implement an adaptive context allocation system that:
   - Dynamically adjusts context size based on conversation length
   - Adapts to different model capabilities
   - Prioritizes most relevant document sections

2. **Document Summarization Option**: Add the ability to use a separate (potentially larger) model to summarize documents before including them in the context.

3. **Graceful Fallback**: Ensure the system gracefully handles context limitations without errors, even with limited context space.

4. **Configuration Options**: Allow users to enable/disable these features via command line flags.

## Implementation Approach

The solution will implement a "RAG Smart Context" feature with three core components:

1. **Adaptive Token Management**:
   - Calculate available tokens based on conversation history
   - Allocate context tokens based on model size
   - Reserve sufficient tokens for system prompt and response

2. **Document Preprocessing**:
   - Add optional document summarization using a larger model
   - Implement chunk extraction for targeted context
   - Extract most relevant sections when full documents won't fit

3. **Command-Line Options**:
   - Add `--rag-summaries` flag to enable document summarization
   - Add model selection for summarization

## Success Criteria

1. **Error Elimination**: No more "token limit exceeded" errors when using RAG
2. **Quality Preservation**: No degeneration/gibberish when using small models with RAG
3. **Informative Context**: Despite token limitations, contexts remain informative and useful for query answering
4. **User Control**: Features can be easily enabled/disabled per user preference

## Implementation Plan and Tasklist

### Phase 1: Adaptive Token Management ✓ COMPLETED

1. [x] Modify `quiet_interface.py` to dynamically calculate available context tokens based on:
   - Conversation history length
   - Model context window size
   - Reserved tokens for response

2. [x] Implement smarter document selection and truncation:
   - Prioritize most relevant documents
   - Extract most relevant sections from documents
   - Truncate in a way that preserves document structure

### Phase 2: Document Preprocessing ⏳ PARTIALLY IMPLEMENTED

3. [ ] Create a document summarization module in `rag_support/utils/`:
   - Implement function to summarize documents with a model
   - Add document chunking capability to isolate relevant sections
   - Create utility to extract key information from documents

4. [x] Modify the context inclusion logic:
   - Add decision tree for document selection and truncation
   - Implement metadata to track truncation status
   - Add fallback to legacy context handling when smart context is disabled

### Phase 3: Command Line and UI Integration ✓ COMPLETED

5. [x] Update `llm.sh`:
   - Add `--no-smart-context` flag to control the feature
   - Add environment variable for smart context settings (`LLM_RAG_SMART_CONTEXT`)

6. [x] Update UI:
   - Show smart context status in the interface
   - Add token allocation information to logs
   - Show truncation status for documents

### Phase 4: Testing and Optimization ⏳ PENDING

7. [ ] Test with various models:
   - Test with small models like TinyLlama
   - Test with mid-sized models
   - Test with large documents and long conversations

8. [ ] Optimize performance:
   - Add caching for document selection
   - Implement parallel processing where applicable
   - Fine-tune token allocation for different model sizes

## Current Status

The RAG Smart Context system has been partially implemented with the following status:

- **COMPLETED**: Core adaptive token management system
- **COMPLETED**: Command line interface integration with `--no-smart-context` flag
- **COMPLETED**: Basic UI and logging feedback
- **PENDING**: Document summarization with a separate model
- **PENDING**: Comprehensive testing with various model sizes
- **PENDING**: Performance optimization

For implementation details, see `/Volumes/LLM/docs/PRD/COMPLETE/RAG/RAG_SMART_CONTEXT_IMPLEMENTATION.md`.

## Compatibility

This change is backwards compatible and won't affect users who don't enable the new features. It expands functionality while preserving existing behavior when new flags aren't used.

## Future Extensions

- Implement semantic chunking of documents for more targeted context
- Add custom prompts for document summarization
- Support for hybrid approaches (some documents summarized, others included raw)
- Implement automatic model selection based on available models