# API Reference

## Overview

This document provides a comprehensive reference for the LLM Platform API. The API follows REST principles with standardized request and response formats, providing access to model inference, RAG capabilities, and document management.

## Base URL

All API endpoints are relative to the base URL of your LLM Platform instance:

```
http://localhost:5100
```

## Authentication

Authentication is not required for local usage. For production deployments, authentication methods should be implemented.

## Response Format

All API responses follow a standardized format:

### Success Response

```json
{
  "status": "success",
  "data": { ... },
  "message": "Optional success message",
  "meta": { ... }
}
```

- `status`: Always "success" for successful requests
- `data`: The response payload
- `message`: Optional message describing the result
- `meta`: Optional metadata about the response (pagination, counts, etc.)

### Error Response

```json
{
  "status": "error",
  "error": "Error message",
  "detail": "Optional detailed error information",
  "code": "Optional error code"
}
```

- `status`: Always "error" for error responses
- `error`: A concise error message
- `detail`: Optional detailed error information
- `code`: Optional error code for programmatic handling

## HTTP Status Codes

- `200 OK`: Request succeeded
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

## API Endpoints

### Model Inference

#### Get Available Models

```
GET /api/models
```

Returns a list of available models.

**Response**:

```json
{
  "status": "success",
  "data": [
    {
      "id": "llama-7b",
      "name": "LLaMa 7B",
      "type": "llama",
      "parameters": "7B",
      "context_length": 4096
    },
    ...
  ],
  "meta": {
    "count": 5
  }
}
```

#### Get Model Information

```
GET /api/models/{model_id}
```

Returns information about a specific model.

**Path Parameters**:
- `model_id`: ID of the model

**Response**:

```json
{
  "status": "success",
  "data": {
    "id": "llama-7b",
    "name": "LLaMa 7B",
    "type": "llama",
    "parameters": "7B",
    "context_length": 4096,
    "is_loaded": true
  }
}
```

#### Generate Completion

```
POST /api/completion
```

Generates text completion based on a prompt.

**Request Body**:

```json
{
  "prompt": "Hello, world!",
  "model_id": "llama-7b",
  "params": {
    "temperature": 0.7,
    "top_p": 0.9,
    "max_tokens": 100
  },
  "use_rag": false,
  "project_id": null
}
```

- `prompt`: The input prompt
- `model_id`: ID of the model to use
- `params`: Generation parameters
  - `temperature`: Randomness of generation (0.0-1.0)
  - `top_p`: Nucleus sampling parameter (0.0-1.0)
  - `max_tokens`: Maximum tokens to generate
- `use_rag`: Whether to use RAG for context
- `project_id`: Project ID for RAG (required if use_rag is true)

**Response**:

```json
{
  "status": "success",
  "data": {
    "completion": "Generated text response",
    "model": "llama-7b",
    "used_rag": false
  }
}
```

#### Stream Completion

```
POST /api/completion/stream
```

Streams text completion as it's generated.

**Request Body**: Same as `/api/completion`

**Response**: Server-sent events with the following format:

```
event: completion
data: {"text": "partial", "done": false}

event: completion
data: {"text": " response", "done": false}

event: completion
data: {"text": ".", "done": true}
```

### Project Management

#### List Projects

```
GET /api/projects
```

Returns a list of all projects.

**Response**:

```json
{
  "status": "success",
  "data": [
    {
      "id": "project-id-1",
      "name": "Project 1",
      "description": "Project description",
      "document_count": 5,
      "created_at": "2025-04-15T10:30:00Z"
    },
    ...
  ],
  "meta": {
    "count": 3
  }
}
```

#### Get Project

```
GET /api/projects/{project_id}
```

Returns information about a specific project.

**Path Parameters**:
- `project_id`: ID of the project

**Response**:

```json
{
  "status": "success",
  "data": {
    "id": "project-id-1",
    "name": "Project 1",
    "description": "Project description",
    "document_count": 5,
    "created_at": "2025-04-15T10:30:00Z"
  }
}
```

#### Create Project

```
POST /api/projects
```

Creates a new project.

**Request Body**:

```json
{
  "name": "New Project",
  "description": "Project description"
}
```

**Response**:

```json
{
  "status": "success",
  "data": {
    "id": "new-project-id",
    "name": "New Project",
    "description": "Project description",
    "document_count": 0,
    "created_at": "2025-04-30T12:00:00Z"
  },
  "message": "Project created successfully"
}
```

#### Delete Project

```
DELETE /api/projects/{project_id}
```

Deletes a project.

**Path Parameters**:
- `project_id`: ID of the project

**Response**:

```json
{
  "status": "success",
  "data": {
    "id": "project-id-1"
  },
  "message": "Project deleted successfully"
}
```

### Document Management

#### List Documents

```
GET /api/projects/{project_id}/documents
```

Returns a list of documents in a project.

**Path Parameters**:
- `project_id`: ID of the project

**Response**:

```json
{
  "status": "success",
  "data": [
    {
      "id": "doc-id-1",
      "project_id": "project-id-1",
      "title": "Document 1",
      "content": "Document content...",
      "tags": ["tag1", "tag2"],
      "created_at": "2025-04-15T10:35:00Z"
    },
    ...
  ],
  "meta": {
    "count": 5,
    "project_id": "project-id-1"
  }
}
```

#### Get Document

```
GET /api/projects/{project_id}/documents/{document_id}
```

Returns a specific document.

**Path Parameters**:
- `project_id`: ID of the project
- `document_id`: ID of the document

**Response**:

```json
{
  "status": "success",
  "data": {
    "id": "doc-id-1",
    "project_id": "project-id-1",
    "title": "Document 1",
    "content": "Document content...",
    "tags": ["tag1", "tag2"],
    "created_at": "2025-04-15T10:35:00Z"
  }
}
```

#### Create Document

```
POST /api/projects/{project_id}/documents
```

Creates a new document in a project.

**Path Parameters**:
- `project_id`: ID of the project

**Request Body**:

```json
{
  "title": "New Document",
  "content": "Document content...",
  "tags": ["tag1", "tag2"]
}
```

**Response**:

```json
{
  "status": "success",
  "data": {
    "id": "new-doc-id",
    "project_id": "project-id-1",
    "title": "New Document",
    "content": "Document content...",
    "tags": ["tag1", "tag2"],
    "created_at": "2025-04-30T12:05:00Z"
  },
  "message": "Document created successfully"
}
```

#### Delete Document

```
DELETE /api/projects/{project_id}/documents/{document_id}
```

Deletes a document.

**Path Parameters**:
- `project_id`: ID of the project
- `document_id`: ID of the document

**Response**:

```json
{
  "status": "success",
  "data": {
    "id": "doc-id-1",
    "project_id": "project-id-1"
  },
  "message": "Document deleted successfully"
}
```

### Search and RAG

#### Search Documents

```
POST /api/projects/{project_id}/search
```

Searches for documents in a project.

**Path Parameters**:
- `project_id`: ID of the project

**Request Body**:

```json
{
  "query": "search query",
  "options": {
    "max_results": 10,
    "semantic_weight": 0.6,
    "keyword_weight": 0.4
  }
}
```

**Response**:

```json
{
  "status": "success",
  "data": [
    {
      "id": "doc-id-1",
      "project_id": "project-id-1",
      "title": "Document 1",
      "content": "Document content...",
      "tags": ["tag1", "tag2"],
      "score": 0.85
    },
    ...
  ],
  "meta": {
    "count": 3,
    "query": "search query",
    "search_type": "hybrid",
    "max_results": 10
  }
}
```

#### Generate Context

```
POST /api/projects/{project_id}/context
```

Generates context for a query from project documents.

**Path Parameters**:
- `project_id`: ID of the project

**Request Body**:

```json
{
  "query": "context query",
  "max_tokens": 2000,
  "document_ids": ["doc-id-1", "doc-id-2"]
}
```

- `document_ids`: Optional list of specific document IDs to use (if null, relevant documents will be searched for)

**Response**:

```json
{
  "status": "success",
  "data": {
    "context": "Generated context text...",
    "documents": ["doc-id-1", "doc-id-2"],
    "truncated": false
  },
  "meta": {
    "tokens": 1500,
    "document_count": 2
  }
}
```

## Error Examples

### Resource Not Found

```json
{
  "status": "error",
  "error": "Project not found",
  "detail": "No project found with ID: project-id-123",
  "code": "project_not_found"
}
```

### Invalid Request

```json
{
  "status": "error",
  "error": "Invalid request",
  "detail": "Request must include a 'query' field",
  "code": "invalid_request"
}
```

### Server Error

```json
{
  "status": "error",
  "error": "Internal server error",
  "detail": "Failed to process request: Database connection error",
  "code": "internal_error"
}
```

## Rate Limiting

The API does not implement rate limiting for local usage. For production deployments, appropriate rate limiting should be implemented.

## Versioning

The API is currently at version 1. The version is implicit in the paths and does not need to be specified.

## Client Libraries

No official client libraries are provided. The API follows REST principles and can be accessed using any HTTP client.