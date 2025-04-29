# RAG Feature Usage Guide

## Overview
This guide explains how to use the Retrieval-Augmented Generation (RAG) features in our LLM interface, which allows you to provide your models with additional context from documents.

## Getting Started

### Launching RAG-Enhanced Interface
To use the RAG features, launch the interface with the RAG-specific script:

```bash
./llm_rag.sh
```

This will start the familiar interface with additional RAG capabilities in a sidebar.

## Projects and Documents

### Creating a Project
1. In the sidebar, click "New Project"
2. Enter a project name and optional description
3. Click "Create Project"

Projects help organize your documents and chat history.

### Adding Documents
1. Select a project from the dropdown
2. Click "Add Document" in the sidebar
3. Enter a title, optional tags (comma-separated), and content (markdown supported)
4. Click "Save Document"

Documents are stored as markdown files and can be viewed by clicking on them in the sidebar.

## Using RAG in Chat

### Adding Context Manually
1. Click on a document in the sidebar to view it
2. Click "Use as Context" to add it to the current chat
3. Selected documents appear in the context bar above the chat
4. Type your message and send as usual

The model will use the document content to inform its response.

### Auto-Context Suggestion
1. Toggle "Auto-suggest context" in the context bar to ON
2. Type your message as usual
3. The system will automatically find relevant documents
4. Review the suggested documents in the context bar
5. Send your message

### Removing Context
Click the "×" next to any document in the context bar to remove it from the current context.

## Document Management

### Searching Documents
Use the search box in the sidebar to filter documents by title or tags.

### Viewing Document Content
Click on any document in the sidebar to view its full content and tags.

## Implementation Details
- Documents are stored as markdown files with YAML frontmatter for metadata
- No database is required; everything is file-based for portability
- Search uses a simple TF-IDF algorithm for lightweight relevance scoring
- The system extends the existing interface rather than replacing it

## Limitations
- Large document collections may experience slower search performance
- Search is based on keywords, not semantic meaning
- Context size is limited by your model's context window

## Troubleshooting
- If the sidebar isn't visible, click the menu icon (⋮) in the top corner
- If documents aren't appearing in search, try refreshing the document list
- If the model ignores context, try providing more specific questions that relate to the document content