#!/usr/bin/env python3
"""
Document management module for the LLM Platform.

Provides a unified Document class and related functionality for working with documents.
"""

import os
import json
import uuid
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Set

from core.logging import get_logger
from core.utils import parse_frontmatter, format_with_frontmatter, estimate_tokens, safe_file_name

# Get logger for this module
logger = get_logger("rag.documents")

class Document:
    """
    Unified document representation for RAG system.
    
    Represents a document with content, metadata, and related functionality.
    """
    
    def __init__(self, id: str, title: str, content: str, **kwargs):
        """
        Initialize a document.
        
        Args:
            id: Document ID
            title: Document title
            content: Document content
            **kwargs: Additional metadata
        """
        self.id = id
        self.title = title
        self.content = content
        
        # Standard metadata
        self.created_at = kwargs.get('created_at', datetime.now().isoformat())
        self.updated_at = kwargs.get('updated_at', datetime.now().isoformat())
        self.tags = kwargs.get('tags', [])
        
        # Store additional metadata
        self.metadata = kwargs
        
        # Cache for token count
        self._token_count = None
    
    @classmethod
    def from_file(cls, file_path: Union[str, Path]) -> 'Document':
        """
        Create a document from a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Document instance
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file format is not supported
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Document file not found: {file_path}")
        
        # Check file extension
        if file_path.suffix.lower() != '.md':
            raise ValueError(f"Unsupported file format: {file_path.suffix}")
        
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse frontmatter and content
        metadata, content_text = parse_frontmatter(content)
        
        # Get ID from filename or metadata
        doc_id = metadata.get('id', file_path.stem)
        
        # Get title from metadata or fallback to filename
        title = metadata.get('title', file_path.stem)
        
        # Create document instance
        return cls(
            id=doc_id,
            title=title,
            content=content_text,
            **metadata
        )
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Document':
        """
        Create a document from a dictionary.
        
        Args:
            data: Dictionary containing document data
            
        Returns:
            Document instance
            
        Raises:
            ValueError: If required fields are missing
        """
        # Check required fields
        if 'id' not in data:
            data['id'] = str(uuid.uuid4())
        
        if 'title' not in data:
            raise ValueError("Document title is required")
        
        if 'content' not in data:
            raise ValueError("Document content is required")
        
        # Create document instance
        return cls(
            id=data['id'],
            title=data['title'],
            content=data['content'],
            **{k: v for k, v in data.items() if k not in ['id', 'title', 'content']}
        )
    
    @classmethod
    def create(cls, title: str, content: str, tags: Optional[List[str]] = None, 
             **kwargs) -> 'Document':
        """
        Create a new document.
        
        Args:
            title: Document title
            content: Document content
            tags: Optional list of tags
            **kwargs: Additional metadata
            
        Returns:
            Document instance
        """
        # Generate a new ID
        doc_id = str(uuid.uuid4())
        
        # Set timestamps
        now = datetime.now().isoformat()
        
        # Create document instance
        return cls(
            id=doc_id,
            title=title,
            content=content,
            created_at=now,
            updated_at=now,
            tags=tags or [],
            **kwargs
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the document to a dictionary.
        
        Returns:
            Dictionary representation of the document
        """
        # Start with metadata
        result = self.metadata.copy()
        
        # Add core properties
        result.update({
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'tags': self.tags
        })
        
        return result
    
    def to_frontmatter(self) -> str:
        """
        Format the document with YAML frontmatter.
        
        Returns:
            Document content with frontmatter
        """
        # Extract metadata for frontmatter
        frontmatter_data = {
            'id': self.id,
            'title': self.title,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'tags': self.tags
        }
        
        # Add any additional metadata
        for key, value in self.metadata.items():
            if key not in frontmatter_data and key != 'content':
                frontmatter_data[key] = value
        
        # Format with frontmatter
        return format_with_frontmatter(frontmatter_data, self.content)
    
    def save(self, directory: Union[str, Path]) -> Path:
        """
        Save the document to a file.
        
        Args:
            directory: Directory to save the document in
            
        Returns:
            Path to the saved file
            
        Raises:
            IOError: If the document couldn't be saved
        """
        directory = Path(directory)
        
        # Ensure directory exists
        directory.mkdir(parents=True, exist_ok=True)
        
        # Create file path
        file_path = directory / f"{self.id}.md"
        
        # Format content with frontmatter
        content = self.to_frontmatter()
        
        # Write to file
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.debug(f"Document saved to {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"Error saving document {self.id}: {e}")
            raise IOError(f"Failed to save document: {e}")
    
    def update(self, **kwargs) -> None:
        """
        Update document properties.
        
        Args:
            **kwargs: Properties to update
        """
        # Update content if provided
        if 'content' in kwargs:
            self.content = kwargs.pop('content')
            self._token_count = None  # Reset token count cache
        
        # Update title if provided
        if 'title' in kwargs:
            self.title = kwargs.pop('title')
        
        # Update tags if provided
        if 'tags' in kwargs:
            self.tags = kwargs.pop('tags')
        
        # Update other metadata
        self.metadata.update(kwargs)
        
        # Always update the updated_at timestamp
        now = datetime.now().isoformat()
        self.updated_at = now
        self.metadata['updated_at'] = now
    
    def get_preview(self, max_length: int = 200) -> str:
        """
        Get a preview of the document content.
        
        Args:
            max_length: Maximum length of the preview
            
        Returns:
            Preview of the document content
        """
        if not self.content:
            return ""
        
        if len(self.content) <= max_length:
            return self.content
        
        # Try to find a good breaking point near the max length
        breakpoint = max(
            self.content[:max_length].rfind('. '),
            self.content[:max_length].rfind('! '),
            self.content[:max_length].rfind('? '),
            self.content[:max_length].rfind('\n\n')
        )
        
        # If no good breakpoint found, just cut at max length
        if breakpoint == -1:
            return self.content[:max_length] + "..."
        
        # Include the punctuation and space
        return self.content[:breakpoint + 2] + "..."
    
    def get_token_count(self) -> int:
        """
        Get the estimated token count for the document.
        
        Returns:
            Estimated token count
        """
        if self._token_count is None:
            self._token_count = estimate_tokens(self.content)
        
        return self._token_count
    
    def matches_query(self, query: str, match_title: bool = True, 
                    match_content: bool = True, match_tags: bool = True) -> bool:
        """
        Check if the document matches a search query.
        
        Args:
            query: Search query
            match_title: Whether to search in the title
            match_content: Whether to search in the content
            match_tags: Whether to search in the tags
            
        Returns:
            True if the document matches the query, False otherwise
        """
        if not query:
            return True
        
        query_lower = query.lower()
        
        # Check title
        if match_title and query_lower in self.title.lower():
            return True
        
        # Check content
        if match_content and query_lower in self.content.lower():
            return True
        
        # Check tags
        if match_tags and any(query_lower in tag.lower() for tag in self.tags):
            return True
        
        return False
    
    def has_tags(self, tags: List[str], require_all: bool = False) -> bool:
        """
        Check if the document has specific tags.
        
        Args:
            tags: List of tags to check for
            require_all: Whether all specified tags must be present
            
        Returns:
            True if the document has the specified tags, False otherwise
        """
        if not tags:
            return True
        
        document_tags = {tag.lower() for tag in self.tags}
        search_tags = {tag.lower() for tag in tags}
        
        if require_all:
            return search_tags.issubset(document_tags)
        else:
            return bool(search_tags.intersection(document_tags))
    
    def __str__(self) -> str:
        """Get string representation of the document."""
        return f"Document({self.id}: {self.title})"
    
    def __repr__(self) -> str:
        """Get detailed string representation of the document."""
        return f"Document(id='{self.id}', title='{self.title}', tags={self.tags}, token_count={self.get_token_count()})"

class DocumentCollection:
    """
    Collection of documents with searching and filtering capabilities.
    
    Provides an interface for working with multiple documents.
    """
    
    def __init__(self):
        """Initialize an empty document collection."""
        self.documents = {}  # Map of ID -> Document
    
    def add(self, document: Document) -> None:
        """
        Add a document to the collection.
        
        Args:
            document: Document to add
        """
        self.documents[document.id] = document
    
    def get(self, document_id: str) -> Optional[Document]:
        """
        Get a document by ID.
        
        Args:
            document_id: ID of the document to get
            
        Returns:
            Document if found, None otherwise
        """
        return self.documents.get(document_id)
    
    def remove(self, document_id: str) -> bool:
        """
        Remove a document from the collection.
        
        Args:
            document_id: ID of the document to remove
            
        Returns:
            True if the document was removed, False if it wasn't found
        """
        if document_id in self.documents:
            del self.documents[document_id]
            return True
        return False
    
    def list_all(self) -> List[Document]:
        """
        List all documents in the collection.
        
        Returns:
            List of all documents
        """
        return list(self.documents.values())
    
    def search(self, query: str, match_title: bool = True, 
              match_content: bool = True, match_tags: bool = True) -> List[Document]:
        """
        Search for documents matching a query.
        
        Args:
            query: Search query
            match_title: Whether to search in the title
            match_content: Whether to search in the content
            match_tags: Whether to search in the tags
            
        Returns:
            List of matching documents
        """
        results = []
        
        for document in self.documents.values():
            if document.matches_query(query, match_title, match_content, match_tags):
                results.append(document)
        
        return results
    
    def filter_by_tags(self, tags: List[str], require_all: bool = False) -> List[Document]:
        """
        Filter documents by tags.
        
        Args:
            tags: List of tags to filter by
            require_all: Whether all specified tags must be present
            
        Returns:
            List of documents with the specified tags
        """
        if not tags:
            return self.list_all()
        
        results = []
        
        for document in self.documents.values():
            if document.has_tags(tags, require_all):
                results.append(document)
        
        return results
    
    def load_directory(self, directory: Union[str, Path]) -> int:
        """
        Load all documents from a directory.
        
        Args:
            directory: Directory to load documents from
            
        Returns:
            Number of documents loaded
        """
        directory = Path(directory)
        
        if not directory.exists() or not directory.is_dir():
            logger.warning(f"Directory does not exist: {directory}")
            return 0
        
        count = 0
        
        for file_path in directory.glob("*.md"):
            try:
                document = Document.from_file(file_path)
                self.add(document)
                count += 1
            except Exception as e:
                logger.error(f"Error loading document {file_path}: {e}")
        
        logger.info(f"Loaded {count} documents from {directory}")
        return count
    
    def save_directory(self, directory: Union[str, Path]) -> int:
        """
        Save all documents to a directory.
        
        Args:
            directory: Directory to save documents to
            
        Returns:
            Number of documents saved
        """
        directory = Path(directory)
        
        # Ensure directory exists
        directory.mkdir(parents=True, exist_ok=True)
        
        count = 0
        
        for document in self.documents.values():
            try:
                document.save(directory)
                count += 1
            except Exception as e:
                logger.error(f"Error saving document {document.id}: {e}")
        
        logger.info(f"Saved {count} documents to {directory}")
        return count
    
    def __len__(self) -> int:
        """Get the number of documents in the collection."""
        return len(self.documents)
    
    def __contains__(self, document_id: str) -> bool:
        """Check if a document is in the collection."""
        return document_id in self.documents

# Convenience functions
def load_document(file_path: Union[str, Path]) -> Document:
    """Load a document from a file."""
    return Document.from_file(file_path)

def create_document(title: str, content: str, tags: Optional[List[str]] = None, 
                  **kwargs) -> Document:
    """Create a new document."""
    return Document.create(title, content, tags, **kwargs)

def load_documents(directory: Union[str, Path]) -> DocumentCollection:
    """Load all documents from a directory."""
    collection = DocumentCollection()
    collection.load_directory(directory)
    return collection