# RAG API Reference

This document provides detailed information about the RAG (Retrieval-Augmented Generation) API endpoints, request formats, and response structures.

## API Overview

The RAG API provides endpoints for:

1. Project Management
2. Document Management
3. Search and Query
4. Chat Conversations
5. Token Estimation
6. Artifact Management

All endpoints follow RESTful design principles and use a standardized response format.

## Base URL

All API endpoints are prefixed with `/api`.

## Authentication

Authentication is not required for the current implementation as it's designed for local use.

## Response Format

### Success Response

All successful API responses follow this format:

```json
{
  "status": "success",
  "data": { ... },
  "message": "Description of the successful operation",
  "meta": { ... }
}
```

- `status`: Always "success" for successful operations
- `data`: The primary data returned by the endpoint
- `message`: A human-readable description of the operation
- `meta`: Additional metadata about the response

### Error Response

All error responses follow this format:

```json
{
  "error": "Short error message",
  "status": 400,
  "detail": "Detailed explanation of the error",
  "code": "error_code"
}
```

- `error`: A short error message
- `status`: The HTTP status code
- `detail`: A detailed explanation of the error (optional)
- `code`: A machine-readable error code for client handling (optional)

## Project Endpoints

### List Projects

Retrieves a list of all projects.

**Endpoint:** `GET /api/projects`

**Response:**

```json
{
  "status": "success",
  "data": [
    {
      "id": "project-uuid",
      "name": "Project Name",
      "description": "Project description",
      "created_at": "2023-01-01T00:00:00.000Z",
      "updated_at": "2023-01-01T00:00:00.000Z",
      "document_count": 10,
      "chat_count": 2,
      "artifact_count": 3
    },
    ...
  ],
  "message": "Projects retrieved successfully",
  "meta": {
    "count": 5,
    "timestamp": "2023-01-01T00:00:00.000Z"
  }
}
```

### Create Project

Creates a new project.

**Endpoint:** `POST /api/projects`

**Request Body:**

```json
{
  "name": "My Project",
  "description": "A description of my project"
}
```

**Response:**

```json
{
  "status": "success",
  "message": "Project created successfully",
  "data": {
    "id": "project-uuid",
    "name": "My Project",
    "description": "A description of my project",
    "created_at": "2023-01-01T00:00:00.000Z",
    "updated_at": "2023-01-01T00:00:00.000Z",
    "document_count": 0,
    "chat_count": 0,
    "artifact_count": 0
  }
}
```

### Get Project

Retrieves a specific project by ID.

**Endpoint:** `GET /api/projects/{project_id}`

**Response:**

```json
{
  "status": "success",
  "data": {
    "id": "project-uuid",
    "name": "Project Name",
    "description": "Project description",
    "created_at": "2023-01-01T00:00:00.000Z",
    "updated_at": "2023-01-01T00:00:00.000Z",
    "document_count": 10,
    "chat_count": 2,
    "artifact_count": 3
  },
  "message": "Project retrieved successfully",
  "meta": {
    "retrieved_at": "2023-01-01T00:00:00.000Z",
    "document_count": 10,
    "chat_count": 2,
    "artifact_count": 3
  }
}
```

### Delete Project

Deletes a specific project by ID.

**Endpoint:** `DELETE /api/projects/{project_id}`

**Response:**

```json
{
  "status": "success",
  "message": "Project deleted successfully",
  "data": {
    "id": "project-uuid",
    "name": "Project Name"
  }
}
```

## Document Endpoints

### List Documents

Lists all documents in a project.

**Endpoint:** `GET /api/projects/{project_id}/documents`

**Response:**

```json
{
  "status": "success",
  "data": [
    {
      "id": "document-uuid",
      "title": "Document Title",
      "created_at": "2023-01-01T00:00:00.000Z",
      "updated_at": "2023-01-01T00:00:00.000Z",
      "tags": ["tag1", "tag2"]
    },
    ...
  ],
  "message": "Documents retrieved successfully",
  "meta": {
    "count": 10,
    "project_id": "project-uuid",
    "project_name": "Project Name"
  }
}
```

### Create Document

Creates a new document in a project.

**Endpoint:** `POST /api/projects/{project_id}/documents`

**Request Body:**

```json
{
  "title": "Document Title",
  "content": "# Document Content\n\nThis is the content of the document...",
  "tags": ["tag1", "tag2"]
}
```

**Response:**

```json
{
  "status": "success",
  "message": "Document created successfully",
  "data": {
    "id": "document-uuid",
    "title": "Document Title",
    "tags": ["tag1", "tag2"]
  },
  "meta": {
    "token_count": 123,
    "created_at": "2023-01-01T00:00:00.000Z",
    "project_id": "project-uuid"
  }
}
```

### Get Document

Retrieves a specific document by ID.

**Endpoint:** `GET /api/projects/{project_id}/documents/{document_id}`

**Response:**

```json
{
  "status": "success",
  "data": {
    "id": "document-uuid",
    "title": "Document Title",
    "content": "# Document Content\n\nThis is the content of the document...",
    "tags": ["tag1", "tag2"],
    "created_at": "2023-01-01T00:00:00.000Z",
    "updated_at": "2023-01-01T00:00:00.000Z"
  },
  "message": "Document retrieved successfully",
  "meta": {
    "token_count": 123,
    "project_id": "project-uuid",
    "project_name": "Project Name"
  }
}
```

### Delete Document

Deletes a specific document by ID.

**Endpoint:** `DELETE /api/projects/{project_id}/documents/{document_id}`

**Response:**

```json
{
  "status": "success",
  "message": "Document deleted successfully",
  "data": {
    "id": "document-uuid",
    "title": "Document Title"
  }
}
```

## Search Endpoints

### Search Documents

Searches for documents in a project based on a query.

**Endpoint:** `GET /api/projects/{project_id}/search?q={query}`

**Response:**

```json
{
  "status": "success",
  "data": [
    {
      "id": "document-uuid",
      "title": "Document Title",
      "preview": "...matching content preview...",
      "score": 0.85,
      "tags": ["tag1", "tag2"],
      "updated_at": "2023-01-01T00:00:00.000Z"
    },
    ...
  ],
  "message": "Found 3 documents matching query",
  "meta": {
    "count": 3,
    "query": "search term",
    "project_id": "project-uuid",
    "project_name": "Project Name",
    "search_time_ms": 125.5
  }
}
```

### Suggest Documents

Suggests relevant documents for a query (for auto-suggest functionality).

**Endpoint:** `GET /api/projects/{project_id}/suggest?q={query}`

**Response:**

```json
{
  "status": "success",
  "data": [
    {
      "id": "document-uuid",
      "title": "Document Title",
      "preview": "...matching content preview...",
      "score": 0.92,
      "tags": ["tag1", "tag2"]
    },
    ...
  ],
  "message": "Found 3 document suggestions",
  "meta": {
    "count": 3,
    "query": "search term",
    "max_results": 3,
    "search_time_ms": 95.2
  }
}
```

## Chat Endpoints

### List Chats

Lists all chats in a project.

**Endpoint:** `GET /api/projects/{project_id}/chats`

**Response:**

```json
{
  "status": "success",
  "data": [
    {
      "id": "chat-uuid",
      "title": "Chat Title",
      "created_at": "2023-01-01T00:00:00.000Z",
      "updated_at": "2023-01-01T00:00:00.000Z",
      "message_count": 10
    },
    ...
  ],
  "message": "Chats retrieved successfully",
  "meta": {
    "count": 5,
    "project_id": "project-uuid",
    "project_name": "Project Name"
  }
}
```

### Create Chat

Creates a new chat in a project.

**Endpoint:** `POST /api/projects/{project_id}/chats`

**Request Body:**

```json
{
  "title": "Chat Title"
}
```

**Response:**

```json
{
  "status": "success",
  "message": "Chat created successfully",
  "data": {
    "id": "chat-uuid",
    "title": "Chat Title",
    "created_at": "2023-01-01T00:00:00.000Z"
  }
}
```

### Add Message

Adds a message to a chat and gets an AI response.

**Endpoint:** `POST /api/projects/{project_id}/chats/{chat_id}/messages`

**Request Body:**

```json
{
  "content": "User message content",
  "context_docs": ["document-uuid1", "document-uuid2"],
  "model": "/path/to/model.gguf",
  "temperature": 0.7,
  "max_tokens": 1024,
  "top_p": 0.95
}
```

**Response:**

```json
{
  "status": "success",
  "data": {
    "response": "AI response text",
    "chat_id": "chat-uuid",
    "message_id": null
  },
  "message": "LLM response generated successfully",
  "meta": {
    "chat_id": "chat-uuid",
    "project_id": "project-uuid",
    "model_path": "/path/to/model.gguf",
    "model_type": "llama",
    "model_format": "gguf",
    "tokens_generated": 256,
    "generation_time_s": 2.5,
    "total_time_s": 3.1,
    "context_documents": {
      "count": 2,
      "tokens": 512,
      "sources": [
        {
          "id": "document-uuid1",
          "title": "Document Title",
          "tokens": 256
        },
        {
          "id": "document-uuid2",
          "title": "Another Document",
          "tokens": 256
        }
      ]
    },
    "parameters": {
      "temperature": 0.7,
      "max_tokens": 1024,
      "top_p": 0.95
    }
  }
}
```

## Token Estimation Endpoint

### Estimate Tokens

Estimates token counts for text and context documents.

**Endpoint:** `POST /api/tokens`

**Request Body:**

```json
{
  "text": "User message text",
  "context_docs": ["document-uuid1", "document-uuid2"],
  "project_id": "project-uuid",
  "model": "/path/to/model.gguf"
}
```

**Response:**

```json
{
  "status": "success",
  "data": {
    "total_tokens": 768,
    "text_tokens": 256,
    "context_tokens": 512,
    "contexts": [
      {
        "id": "document-uuid1",
        "title": "Document Title",
        "tokens": 256,
        "percentage": 50.0
      },
      {
        "id": "document-uuid2",
        "title": "Another Document",
        "tokens": 256,
        "percentage": 50.0
      }
    ],
    "model_context_window": 4096,
    "available_tokens": 2304,
    "available_percentage": 56.3,
    "usage_percentage": 18.8,
    "is_over_limit": false,
    "reserved_tokens": 1024
  },
  "message": "Token estimation completed successfully",
  "meta": {
    "timestamp": "2023-01-01T00:00:00.000Z",
    "model_path": "/path/to/model.gguf",
    "context_count": 2,
    "estimation_method": "character-based-approximation"
  }
}
```

## Artifact Endpoints

### List Artifacts

Lists all artifacts in a project.

**Endpoint:** `GET /api/projects/{project_id}/artifacts`

**Response:**

```json
{
  "status": "success",
  "data": [
    {
      "id": "artifact-uuid",
      "title": "Artifact Title",
      "created_at": "2023-01-01T00:00:00.000Z",
      "file_type": "md"
    },
    ...
  ],
  "message": "Artifacts retrieved successfully",
  "meta": {
    "count": 3,
    "project_id": "project-uuid",
    "project_name": "Project Name"
  }
}
```

### Create Artifact

Creates a new artifact in a project.

**Endpoint:** `POST /api/projects/{project_id}/artifacts`

**Request Body:**

```json
{
  "title": "Artifact Title",
  "content": "Artifact content",
  "file_ext": "md"
}
```

**Response:**

```json
{
  "status": "success",
  "message": "Artifact created successfully",
  "data": {
    "id": "artifact-uuid",
    "title": "Artifact Title",
    "file_type": "md"
  }
}
```

### Get Artifact

Retrieves a specific artifact by ID.

**Endpoint:** `GET /api/projects/{project_id}/artifacts/{artifact_id}`

**Response:**

```json
{
  "status": "success",
  "data": {
    "id": "artifact-uuid",
    "title": "Artifact Title",
    "content": "Artifact content",
    "created_at": "2023-01-01T00:00:00.000Z",
    "file_type": "md",
    "path": "/path/to/artifact.md"
  },
  "message": "Artifact retrieved successfully"
}
```

### Delete Artifact

Deletes a specific artifact by ID.

**Endpoint:** `DELETE /api/projects/{project_id}/artifacts/{artifact_id}`

**Response:**

```json
{
  "status": "success",
  "message": "Artifact deleted successfully",
  "data": {
    "id": "artifact-uuid",
    "title": "Artifact Title"
  }
}
```

## Error Codes

The API uses the following error codes:

| Code | Description |
|------|-------------|
| `missing_required_field` | A required field is missing from the request |
| `missing_project_id` | Project ID is missing from the request |
| `missing_chat_id` | Chat ID is missing from the request |
| `missing_message_content` | Message content is missing from the request |
| `missing_parameters` | Required parameters are missing from the request |
| `project_not_found` | The requested project was not found |
| `chat_not_found` | The requested chat was not found |
| `document_not_found` | The requested document was not found |
| `artifact_not_found` | The requested artifact was not found |
| `project_creation_error` | An error occurred while creating a project |
| `message_save_error` | An error occurred while saving a message |
| `search_error` | An error occurred during search |
| `llm_generation_error` | An error occurred during LLM response generation |
| `inference_module_error` | The inference module could not be loaded |
| `token_estimation_error` | An error occurred during token estimation |
| `message_processing_error` | An error occurred while processing a message |

## Implementation Notes

- All date/time values are in ISO 8601 format (UTC)
- Token counts are estimates and may not match exact tokenization of specific models
- Search scores are normalized between 0 and 1
- The API is stateful and maintains data between requests
- All IDs are UUIDs generated by the server