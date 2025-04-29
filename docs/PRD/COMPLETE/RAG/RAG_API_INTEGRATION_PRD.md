# RAG API Integration PRD

## Overview
This document outlines the requirements for connecting the HTML interface to the backend API for the RAG (Retrieval-Augmented Generation) system, replacing the current mock data implementation with real data integrations.

## Goals
- Replace all mock data in the frontend with real API calls
- Ensure proper error handling for API failures
- Validate token counting and context selection with real data
- Test the RAG functionality with actual documents and projects
- Implement proper loading states and feedback for asynchronous operations

## Background
The current implementation uses mock data to demonstrate RAG functionality. The interface components are complete but not connected to the real backend. The API client (`api.js`) has placeholder methods that need to be updated to make real HTTP requests.

## Core Principles

The implementation must strictly adhere to these non-negotiable principles, as established in previous PRDs:

1. **DRY (Don't Repeat Yourself)**
   - Zero code duplication will be tolerated
   - Each functionality must exist in exactly one place
   - No duplicate files or alternative implementations allowed

2. **KISS (Keep It Simple, Stupid)**
   - Implement the simplest solution that works
   - No over-engineering or unnecessary complexity
   - Straightforward, maintainable code patterns

3. **Clean File System**
   - All existing files must be either used or removed
   - No orphaned, redundant, or unused files
   - Clear, logical organization of the file structure

4. **Transparent Error Handling**
   - No error hiding or fallback mechanisms that mask issues
   - All errors must be properly displayed to the user
   - Errors must be clear, actionable, and honest

## Success Criteria

In accordance with the established principles and previous PRDs, the implementation will be successful if:

1. **Zero Duplication**: No duplicate code or files exist in the codebase
2. **Single Implementation**: Each feature has exactly one implementation
3. **Complete API Integration**: All mock data is replaced with real API calls
4. **No Fallbacks**: No fallback systems that hide or mask errors
5. **Transparent Errors**: All errors are properly displayed to users
6. **External Assets**: All CSS and JavaScript is in external files
7. **Component Architecture**: UI is built from reusable, modular components
8. **Consistent Standards**: Implementation follows UI_INTEGRATION_STANDARDS.md
9. **Full Functionality**: All features work correctly with real backend data
10. **Complete Documentation**: Implementation details are properly documented

## Requirements

### 1. API Client Implementation

#### 1.1 Core API Methods
- Update `API.getModels()` to fetch actual models from the backend
- Implement `API.sendMessage()` to send messages with document context
- Add proper error handling and response validation

#### 1.2 RAG API Methods
- Implement `API.RAG.getProjects()` to retrieve user projects
- Implement `API.RAG.createProject(name)` for project creation
- Implement `API.RAG.getDocuments(projectId)` to fetch project documents
- Implement `API.RAG.uploadDocument(projectId, file, metadata)` for document uploads
- Implement `API.RAG.getDocumentPreview(documentId)` for document previews
- Implement `API.RAG.deleteDocument(documentId)` for document deletion
- Implement `API.RAG.searchDocuments(query, projectId)` for document search

#### 1.3 Authentication & Headers
- Add proper authentication headers to all requests if required
- Implement content-type and accept headers for API calls
- Handle API rate limiting and retries appropriately

### 2. Component Integration

#### 2.1 Project Management
- Connect project listing to real API data
- Implement project creation with error handling
- Add project deletion functionality with confirmation

#### 2.2 Document Management
- Connect document browser to real document API
- Implement document upload with progress indication
- Support multi-document selection for context
- Display accurate document metadata from API

#### 2.3 Document Preview
- Load actual document content from API
- Display accurate token counts from backend
- Implement chunk selection for partial document inclusion

#### 2.4 Search Integration
- Connect search functionality to actual backend search
- Display search results with relevance indicators
- Implement search filters (date, type, etc.)

### 3. Context & Token Management

#### 3.1 Token Counting
- Replace mock token counting with actual token counts from API
- Implement token budget visualization with document selections
- Add warnings when token limits are approached
- Provide token usage breakdown by document

#### 3.2 Context Selection
- Implement context prioritization based on token budget
- Allow manual selection/deselection of document chunks
- Provide visual feedback on included/excluded context

#### 3.3 Context Persistence
- Save and restore document context between sessions
- Implement context history for conversation continuity
- Allow saving specific context configurations

### 4. Error Handling & Feedback

#### 4.1 Loading States
- Add loading indicators for all asynchronous operations
- Implement skeleton loaders for document and project lists
- Show progress for long-running operations (uploads, indexing)

#### 4.2 Error Handling
- Display user-friendly error messages for API failures
- Implement proper retry mechanisms for transient errors
- Support offline detection and recovery

#### 4.3 Validation Feedback
- Implement input validation before API submissions
- Provide immediate feedback on invalid inputs
- Show success confirmations for completed operations

## Technical Specifications

### API Endpoints
- GET `/api/models` - Retrieve available models
- POST `/api/chat` - Send a chat message with context
- GET `/api/rag/projects` - List all projects
- POST `/api/rag/projects` - Create a new project
- GET `/api/rag/projects/{id}/documents` - List documents in project
- POST `/api/rag/projects/{id}/documents` - Upload document to project
- GET `/api/rag/documents/{id}` - Get document details/preview
- DELETE `/api/rag/documents/{id}` - Delete a document
- GET `/api/rag/search` - Search across documents

### Data Formats

#### Project Object
```json
{
  "id": "string",
  "name": "string",
  "description": "string",
  "created_at": "ISO-8601 timestamp",
  "document_count": "number"
}
```

#### Document Object
```json
{
  "id": "string",
  "filename": "string",
  "file_type": "string",
  "project_id": "string",
  "size_bytes": "number",
  "token_count": "number",
  "chunk_count": "number",
  "created_at": "ISO-8601 timestamp",
  "metadata": {
    "title": "string",
    "author": "string",
    "custom_fields": "object"
  }
}
```

#### Document Chunk
```json
{
  "id": "string",
  "document_id": "string",
  "content": "string",
  "token_count": "number",
  "position": "number"
}
```

## Implementation Plan

### Phase 1: API Client Implementation (2 days)
- Update API client with actual endpoints
- Implement authentication (if needed)
- Add error handling and retry logic
- Test all API methods with backend

### Phase 2: Project & Document Management (3 days)
- Connect project listing and creation
- Implement document upload and listing
- Add document metadata display
- Test project and document workflows

### Phase 3: Context & Token Management (2 days)
- Implement accurate token counting
- Add context selection with real documents
- Implement token budget visualization
- Test context integration with chat

### Phase 4: Search & Advanced Features (2 days)
- Connect search functionality
- Implement relevance sorting
- Add document filtering
- Test search performance

### Phase 5: Testing & Refinement (1 day)
- Comprehensive testing with real data
- Performance optimization
- Error handling improvements
- Final user experience refinements

## Testing Requirements
- Test all API endpoints with valid and invalid inputs
- Verify proper error handling for offline and server error states
- Test with large documents to validate token counting
- Test search with various query types
- Validate all user flows from project creation to chat with context

## Dependencies
- Backend API implementation must be complete and accessible
- Document processing pipeline must be functional
- Token counting API must be available
- Search indexing must be implemented on backend

## Implementation Tasklist

The following tasks must be completed to successfully implement the RAG API integration:

### Phase 1: API Client Implementation
- [x] Review existing API client structure in api.js
- [x] Identify all mock data implementations to be replaced
- [x] Implement proper fetch/XMLHttpRequest with error handling
- [x] Update API.getModels() to fetch real models
- [x] Implement API.sendMessage() with document context support
- [x] Implement all RAG.* API methods (getProjects, createProject, etc.)
- [x] Add proper authentication and headers to all requests
- [x] Create comprehensive error handling for all API calls
- [x] Test all API methods with backend services

### Phase 2: Project Management Integration
- [x] Replace mock project data with real API calls
- [x] Connect project listing component to real API
- [x] Implement project creation functionality
- [x] Add project deletion with confirmation
- [x] Implement project selection and state management
- [x] Add proper loading states for all project operations
- [x] Implement error handling for project API failures

### Phase 3: Document Management Integration
- [x] Connect document browser to real document API
- [x] Implement document upload with progress indication
- [x] Replace mock document metadata with real data
- [x] Connect document preview to actual document content
- [x] Implement chunk selection UI with real chunks
- [x] Add document deletion with confirmation
- [x] Ensure proper loading states for all document operations

### Phase 4: Context & Token Management
- [x] Replace mock token counting with real API data
- [x] Implement token budget visualization with actual counts
- [x] Connect context selection UI to real document chunks
- [x] Implement warning system for token limit approaches
- [x] Add context persistence between sessions
- [x] Ensure context is properly passed to chat messages
- [x] Test token counting accuracy with various document types

### Phase 5: Search Integration
- [x] Connect search functionality to backend search API
- [x] Implement proper display of search results with metadata
- [x] Add relevance indicators from real search results
- [x] Implement search filters if supported by backend
- [x] Add proper loading states for search operations
- [x] Test search with various query types and document sets

### Phase 6: Testing & Validation
- [ ] Test all API endpoints with valid inputs
- [ ] Test error handling with invalid inputs and error conditions
- [ ] Verify token counting accuracy with various documents
- [ ] Test end-to-end workflows from project creation to chat
- [ ] Validate all loading states and progress indicators
- [ ] Test offline scenarios and recovery
- [ ] Ensure all success criteria are met

### Phase 7: Cleanup & Documentation
- [x] Remove all unused mock data implementations
- [x] Ensure code adheres to DRY principle (no duplication)
- [x] Verify KISS principle is followed (simplest implementation)
- [ ] Document API client implementation details
- [ ] Update user documentation for real data workflows
- [ ] Perform final code review against success criteria

## Future Considerations
- Implementing advanced search features (semantic search)
- Adding document editing capabilities
- Supporting more document formats
- Implementing collaborative RAG features