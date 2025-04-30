# RAG (Retrieval-Augmented Generation) Usage Guide

This document provides information on how to use the RAG features in the Portable LLM Environment.

## Overview

RAG (Retrieval-Augmented Generation) is a technique that enhances LLM responses by providing relevant context from a knowledge base. This implementation includes:

- Project-based organization of documents
- Document management (create, read, update, delete)
- Document search and context suggestion
- Context-aware chat with token management
- Token visualization and optimization

## Getting Started

To use RAG features, launch the interface with the `--rag` flag:

```bash
./llm.sh --rag
```

## Interface Components

The interface includes:

1. **Project Manager** - Create and manage projects to organize your documents
2. **Document Manager** - Add, view, and organize documents within projects
3. **Context Bar** - Shows currently selected context documents and token usage
4. **Token Visualization** - Visual representation of token usage for context window

## API Endpoints

The RAG implementation provides the following API endpoints:

### Projects

- `GET /api/projects` - List all projects
- `POST /api/projects` - Create a new project
- `GET /api/projects/{id}` - Get project details
- `DELETE /api/projects/{id}` - Delete a project

### Documents

- `GET /api/projects/{id}/documents` - List all documents in a project
- `POST /api/projects/{id}/documents` - Create a new document
- `GET /api/projects/{id}/documents/{doc_id}` - Get a document
- `DELETE /api/projects/{id}/documents/{doc_id}` - Delete a document

### Search

- `GET /api/projects/{id}/search?q={query}` - Search documents in a project
- `GET /api/projects/{id}/search?q={query}&search_type=hybrid` - Search documents using hybrid search
- `GET /api/projects/{id}/search?q={query}&search_type=semantic` - Search documents using semantic search
- `GET /api/projects/{id}/suggest?q={query}` - Get document suggestions for a query

### Chat

- `GET /api/projects/{id}/chats` - List all chats in a project
- `POST /api/projects/{id}/chats` - Create a new chat
- `POST /api/projects/{id}/chats/{chat_id}/messages` - Add a message to a chat

### Token Management

- `POST /api/tokens` - Estimate token counts for text and context documents

## Usage Examples

### Create a Project

```javascript
// Create a new project
const result = await fetch('/api/projects', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        name: 'My Research Project',
        description: 'Research notes and reference materials'
    })
});
const project = await result.json();
```

### Add a Document

```javascript
// Add a document to a project
const result = await fetch(`/api/projects/${projectId}/documents`, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        title: 'Important Research Paper',
        content: '# Research Paper\n\nThis is the content of the paper...',
        tags: ['research', 'important', 'reference']
    })
});
const document = await result.json();
```

### Search Documents

```javascript
// Basic keyword search
const result = await fetch(`/api/projects/${projectId}/search?q=research+methodology`);
const searchResults = await result.json();

// Hybrid search (combining keyword and semantic search)
const hybridResult = await fetch(`/api/projects/${projectId}/search?q=research+methodology&search_type=hybrid`);
const hybridSearchResults = await hybridResult.json();

// Semantic search only (using embeddings for meaning-based search)
const semanticResult = await fetch(`/api/projects/${projectId}/search?q=research+methodology&search_type=semantic`);
const semanticSearchResults = await semanticResult.json();

// Hybrid search with custom weights
const customResult = await fetch(`/api/projects/${projectId}/search?q=research+methodology&search_type=hybrid&semantic_weight=0.7&keyword_weight=0.3`);
const customSearchResults = await customResult.json();
```

### Send Message with Context

```javascript
// Send a message with context documents
const result = await fetch(`/api/projects/${projectId}/chats/${chatId}/messages`, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        content: 'Summarize the key findings from these papers',
        context_docs: ['doc1_id', 'doc2_id'],
        model: '/path/to/model.gguf'
    })
});
const response = await result.json();
```

### Estimate Token Usage

```javascript
// Estimate token usage for a message with context
const result = await fetch('/api/tokens', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        project_id: projectId,
        text: 'My message text',
        context_docs: ['doc1_id', 'doc2_id']
    })
});
const tokenInfo = await result.json();
console.log(`Total tokens: ${tokenInfo.total_tokens}, Available: ${tokenInfo.available_tokens}`);
```

## Best Practices

1. **Organize by project** - Create separate projects for different domains or tasks
2. **Add descriptive tags** - Tags improve searchability of documents
3. **Monitor token usage** - Watch the token visualization to avoid context window overflow
4. **Use auto-suggest** - Enable auto-suggestion for relevant context documents
5. **Chunk large documents** - Break very large documents into smaller, focused pieces

## Implementation Details

The RAG implementation is built on a modular architecture:

- Documents are stored as markdown files with YAML frontmatter for metadata
- No database is required; everything is file-based for portability
- Multiple search options available:
  - TF-IDF algorithm for keyword-based search
  - Semantic embedding search using sentence-transformers
  - Hybrid search combining both approaches for better results
- Embeddings are cached to disk for performance
- The system extends the existing interface rather than replacing it

## Search Capabilities

Three search methods are available, each with different strengths:

- **Keyword Search**: Traditional TF-IDF search for exact term matching
  - Pros: Fast, lightweight, no additional dependencies
  - Cons: Might miss semantically related content, sensitive to vocabulary
  
- **Semantic Search**: Embedding-based search using sentence-transformers
  - Pros: Understands meaning beyond keywords, finds conceptually related content
  - Cons: Requires more RAM, initial embedding generation is slower
  
- **Hybrid Search**: Combines keyword and semantic approaches
  - Pros: Best overall results, balances precision with semantic understanding
  - Cons: Most resource-intensive option
  - Customizable weights: Adjust semantic_weight and keyword_weight parameters to fine-tune results

## Advanced Customization

The RAG implementation can be extended by:

1. Modifying `/Volumes/LLM/rag_support/api_extensions.py` for API customization
2. Updating `/Volumes/LLM/rag_support/ui_extensions.py` for UI changes
3. Enhancing `/Volumes/LLM/rag_support/utils/search.py` for keyword search algorithms
4. Customizing `/Volumes/LLM/rag_support/utils/hybrid_search.py` for semantic and hybrid search

## Limitations

- First-time embedding generation may be slow for large document collections
- Semantic search requires additional RAM for the embedding model
- Hybrid search combines strengths of both approaches but uses more resources
- Context size is limited by your model's context window
- Embedding model quality impacts semantic search results