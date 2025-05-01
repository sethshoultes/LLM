#!/usr/bin/env python3
"""
Schema definitions for RAG API requests and responses.

This module defines Pydantic models for validating RAG API requests and responses,
ensuring consistent data formats and validation.
"""

from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime


class ProjectBase(BaseModel):
    """Base model for project data."""
    name: str = Field(..., description="Project name")
    description: Optional[str] = Field(None, description="Project description")


class ProjectCreate(ProjectBase):
    """Schema for creating a new project."""
    pass


class Project(ProjectBase):
    """Schema for a complete project."""
    id: str = Field(..., description="Project ID")
    document_count: int = Field(0, description="Number of documents in the project")
    chat_count: int = Field(0, description="Number of chats in the project")
    artifact_count: int = Field(0, description="Number of artifacts in the project") 
    created_at: Optional[datetime] = Field(None, description="Project creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Project last update timestamp")


class ProjectList(BaseModel):
    """Schema for a list of projects."""
    projects: List[Project] = Field(..., description="List of projects")
    count: int = Field(..., description="Total number of projects")


class DocumentBase(BaseModel):
    """Base model for document data."""
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Document content")
    tags: Optional[List[str]] = Field(None, description="Document tags")


class DocumentCreate(DocumentBase):
    """Schema for creating a new document."""
    pass


class Document(DocumentBase):
    """Schema for a complete document."""
    id: str = Field(..., description="Document ID")
    project_id: str = Field(..., description="ID of the project this document belongs to")
    created_at: Optional[datetime] = Field(None, description="Document creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Document last update timestamp")


class DocumentList(BaseModel):
    """Schema for a list of documents."""
    documents: List[Document] = Field(..., description="List of documents")
    count: int = Field(..., description="Total number of documents")


class SearchOptions(BaseModel):
    """Options for document search."""
    max_results: Optional[int] = Field(10, description="Maximum number of results to return")
    semantic_weight: Optional[float] = Field(0.5, description="Weight for semantic search (0.0-1.0)")
    keyword_weight: Optional[float] = Field(0.5, description="Weight for keyword search (0.0-1.0)")
    
    @validator('semantic_weight', 'keyword_weight')
    def validate_weights(cls, v):
        """Validate that weights are between 0 and 1."""
        if v < 0 or v > 1:
            raise ValueError("Weight must be between 0.0 and 1.0")
        return v


class SearchQuery(BaseModel):
    """Schema for search queries."""
    query: str = Field(..., description="Search query text")
    options: Optional[SearchOptions] = Field(None, description="Search options")


class SearchResult(BaseModel):
    """Schema for search results."""
    documents: List[Document] = Field(..., description="List of matched documents")
    count: int = Field(..., description="Total number of results")
    query: str = Field(..., description="Original search query")
    search_type: str = Field(..., description="Type of search performed (keyword, semantic, or hybrid)")


class ContextRequest(BaseModel):
    """Schema for requesting context generation."""
    query: str = Field(..., description="Query to generate context for")
    project_id: str = Field(..., description="Project ID to search for documents")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens for context")
    document_ids: Optional[List[str]] = Field(None, description="Specific document IDs to use")


class ContextResponse(BaseModel):
    """Schema for context generation response."""
    context: str = Field(..., description="Generated context")
    tokens: int = Field(..., description="Number of tokens in the context")
    documents: List[str] = Field(..., description="IDs of documents used")
    truncated: bool = Field(False, description="Whether the context was truncated")


class ApiError(BaseModel):
    """Schema for API error responses."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    code: Optional[str] = Field(None, description="Error code")


class ApiResponse(BaseModel):
    """Schema for standard API responses."""
    status: str = Field("success", description="Response status")
    data: Any = Field(..., description="Response data")
    message: Optional[str] = Field(None, description="Response message")
    meta: Optional[Dict[str, Any]] = Field(None, description="Response metadata")