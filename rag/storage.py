#!/usr/bin/env python3
"""
Document storage module for the LLM Platform.

Provides functionality for storing and retrieving documents from different storage backends.
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Set, Callable

from core.logging import get_logger
from core.utils import load_json_file, save_json_file

# Import Document type but defer actual import to avoid circular imports
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from rag.documents import Document, DocumentCollection

# Get logger for this module
logger = get_logger("rag.storage")

class StorageBackend:
    """
    Base class for document storage backends.
    
    Provides a common interface for storing and retrieving documents.
    """
    
    def __init__(self):
        """Initialize the document storage."""
        pass
    
    def save_document(self, document: Document) -> bool:
        """
        Save a document to storage.
        
        Args:
            document: Document to save
            
        Returns:
            True if successful, False otherwise
        """
        raise NotImplementedError("save_document method must be implemented by subclasses")
    
    def get_document(self, document_id: str) -> Optional[Document]:
        """
        Get a document from storage by ID.
        
        Args:
            document_id: ID of the document to get
            
        Returns:
            Document if found, None otherwise
        """
        raise NotImplementedError("get_document method must be implemented by subclasses")
    
    def delete_document(self, document_id: str) -> bool:
        """
        Delete a document from storage.
        
        Args:
            document_id: ID of the document to delete
            
        Returns:
            True if successful, False otherwise
        """
        raise NotImplementedError("delete_document method must be implemented by subclasses")
    
    def list_documents(self) -> List[Dict[str, Any]]:
        """
        List all documents in storage.
        
        Returns:
            List of document metadata dictionaries
        """
        raise NotImplementedError("list_documents method must be implemented by subclasses")
    
    def search_documents(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for documents in storage.
        
        Args:
            query: Search query
            
        Returns:
            List of matching document metadata dictionaries
        """
        raise NotImplementedError("search_documents method must be implemented by subclasses")
        
    def get_all_documents(self):
        """
        Get all documents as a DocumentCollection.
        
        Returns:
            DocumentCollection containing all documents
        """
        raise NotImplementedError("get_all_documents method must be implemented by subclasses")

class FileSystemStorage(StorageBackend):
    """
    File system based document storage.
    
    Stores documents as markdown files with YAML frontmatter.
    """
    
    def __init__(self, directory: Union[str, Path]):
        """
        Initialize file system storage.
        
        Args:
            directory: Directory for storing documents
        """
        super().__init__()
        self.directory = Path(directory)
        
        # Ensure directory exists
        self.directory.mkdir(parents=True, exist_ok=True)
        
        # Cache for document metadata
        self.metadata_cache = {}
        self.cache_valid = False
    
    def save_document(self, document: Document) -> bool:
        """
        Save a document to storage.
        
        Args:
            document: Document to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Save document to file
            document.save(self.directory)
            
            # Invalidate cache
            self.cache_valid = False
            
            return True
        except Exception as e:
            logger.error(f"Error saving document {document.id}: {e}")
            return False
    
    def get_document(self, document_id: str) -> Optional[Document]:
        """
        Get a document from storage by ID.
        
        Args:
            document_id: ID of the document to get
            
        Returns:
            Document if found, None otherwise
        """
        file_path = self.directory / f"{document_id}.md"
        
        if not file_path.exists():
            return None
        
        try:
            return Document.from_file(file_path)
        except Exception as e:
            logger.error(f"Error loading document {document_id}: {e}")
            return None
    
    def delete_document(self, document_id: str) -> bool:
        """
        Delete a document from storage.
        
        Args:
            document_id: ID of the document to delete
            
        Returns:
            True if successful, False otherwise
        """
        file_path = self.directory / f"{document_id}.md"
        
        if not file_path.exists():
            return False
        
        try:
            os.remove(file_path)
            
            # Invalidate cache
            self.cache_valid = False
            
            return True
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {e}")
            return False
    
    def list_documents(self) -> List[Dict[str, Any]]:
        """
        List all documents in storage.
        
        Returns:
            List of document metadata dictionaries
        """
        # Use cache if valid
        if self.cache_valid and self.metadata_cache:
            return list(self.metadata_cache.values())
        
        # Rebuild cache
        self.metadata_cache = {}
        
        documents = []
        
        for file_path in self.directory.glob("*.md"):
            # Skip hidden files
            if file_path.name.startswith(".") or file_path.name.startswith("_"):
                continue
            
            try:
                # Load document
                document = Document.from_file(file_path)
                
                # Extract metadata
                metadata = {
                    "id": document.id,
                    "title": document.title,
                    "created_at": document.created_at,
                    "updated_at": document.updated_at,
                    "tags": document.tags,
                    "token_count": document.get_token_count(),
                    "preview": document.get_preview(200)
                }
                
                # Add to cache and result list
                self.metadata_cache[document.id] = metadata
                documents.append(metadata)
            except Exception as e:
                logger.error(f"Error loading document {file_path}: {e}")
        
        # Sort by updated_at (most recent first)
        documents.sort(key=lambda d: d.get("updated_at", ""), reverse=True)
        
        # Mark cache as valid
        self.cache_valid = True
        
        return documents
    
    def search_documents(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for documents in storage.
        
        Args:
            query: Search query
            
        Returns:
            List of matching document metadata dictionaries
        """
        if not query:
            return self.list_documents()
        
        query_lower = query.lower()
        results = []
        
        # Load all documents
        for file_path in self.directory.glob("*.md"):
            try:
                # Load document
                document = Document.from_file(file_path)
                
                # Check if it matches query
                if document.matches_query(query):
                    # Extract metadata
                    metadata = {
                        "id": document.id,
                        "title": document.title,
                        "created_at": document.created_at,
                        "updated_at": document.updated_at,
                        "tags": document.tags,
                        "token_count": document.get_token_count(),
                        "preview": document.get_preview(200)
                    }
                    
                    results.append(metadata)
            except Exception as e:
                logger.error(f"Error searching document {file_path}: {e}")
        
        # Sort by updated_at (most recent first)
        results.sort(key=lambda d: d.get("updated_at", ""), reverse=True)
        
        return results
    
    def get_all_documents(self):
        """
        Get all documents as a DocumentCollection.
        
        Returns:
            DocumentCollection containing all documents
        """
        # Import here to avoid circular imports
        from rag.documents import Document, DocumentCollection
        
        collection = DocumentCollection()
        
        for file_path in self.directory.glob("*.md"):
            try:
                document = Document.from_file(file_path)
                collection.add(document)
            except Exception as e:
                logger.error(f"Error loading document {file_path}: {e}")
        
        return collection
    
    def backup(self, backup_dir: Union[str, Path]) -> bool:
        """
        Backup all documents to another directory.
        
        Args:
            backup_dir: Directory to back up to
            
        Returns:
            True if successful, False otherwise
        """
        backup_dir = Path(backup_dir)
        
        # Ensure backup directory exists
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Copy all document files
            for file_path in self.directory.glob("*.md"):
                shutil.copy2(file_path, backup_dir)
            
            return True
        except Exception as e:
            logger.error(f"Error backing up documents: {e}")
            return False

class MemoryStorage(StorageBackend):
    """
    In-memory document storage.
    
    Stores documents in memory for testing or temporary storage.
    """
    
    def __init__(self):
        """Initialize in-memory storage."""
        super().__init__()
        self.documents = {}
    
    def save_document(self, document: Document) -> bool:
        """
        Save a document to storage.
        
        Args:
            document: Document to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Store document in memory
            self.documents[document.id] = document
            return True
        except Exception as e:
            logger.error(f"Error saving document {document.id}: {e}")
            return False
    
    def get_document(self, document_id: str) -> Optional[Document]:
        """
        Get a document from storage by ID.
        
        Args:
            document_id: ID of the document to get
            
        Returns:
            Document if found, None otherwise
        """
        return self.documents.get(document_id)
    
    def delete_document(self, document_id: str) -> bool:
        """
        Delete a document from storage.
        
        Args:
            document_id: ID of the document to delete
            
        Returns:
            True if successful, False otherwise
        """
        if document_id in self.documents:
            del self.documents[document_id]
            return True
        return False
    
    def list_documents(self) -> List[Dict[str, Any]]:
        """
        List all documents in storage.
        
        Returns:
            List of document metadata dictionaries
        """
        documents = []
        
        for document in self.documents.values():
            # Extract metadata
            metadata = {
                "id": document.id,
                "title": document.title,
                "created_at": document.created_at,
                "updated_at": document.updated_at,
                "tags": document.tags,
                "token_count": document.get_token_count(),
                "preview": document.get_preview(200)
            }
            
            documents.append(metadata)
        
        # Sort by updated_at (most recent first)
        documents.sort(key=lambda d: d.get("updated_at", ""), reverse=True)
        
        return documents
    
    def search_documents(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for documents in storage.
        
        Args:
            query: Search query
            
        Returns:
            List of matching document metadata dictionaries
        """
        if not query:
            return self.list_documents()
        
        query_lower = query.lower()
        results = []
        
        for document in self.documents.values():
            # Check if it matches query
            if document.matches_query(query):
                # Extract metadata
                metadata = {
                    "id": document.id,
                    "title": document.title,
                    "created_at": document.created_at,
                    "updated_at": document.updated_at,
                    "tags": document.tags,
                    "token_count": document.get_token_count(),
                    "preview": document.get_preview(200)
                }
                
                results.append(metadata)
        
        # Sort by updated_at (most recent first)
        results.sort(key=lambda d: d.get("updated_at", ""), reverse=True)
        
        return results
    
    def get_all_documents(self):
        """
        Get all documents as a DocumentCollection.
        
        Returns:
            DocumentCollection containing all documents
        """
        # Import here to avoid circular imports
        from rag.documents import DocumentCollection
        
        collection = DocumentCollection()
        
        for document in self.documents.values():
            collection.add(document)
        
        return collection
    
    def clear(self) -> None:
        """Clear all documents from storage."""
        self.documents.clear()

# Factory function to create a storage backend
def create_storage(storage_type: str, **kwargs) -> StorageBackend:
    """
    Create a document storage backend.
    
    Args:
        storage_type: Type of storage to create ('file' or 'memory')
        **kwargs: Additional parameters for the storage backend
        
    Returns:
        StorageBackend instance
        
    Raises:
        ValueError: If the storage type is not supported
    """
    if storage_type == 'file':
        directory = kwargs.get('directory')
        if not directory:
            raise ValueError("directory parameter is required for file storage")
        return FileSystemStorage(directory)
    elif storage_type == 'memory':
        return MemoryStorage()
    else:
        raise ValueError(f"Unsupported storage type: {storage_type}")

# Convenience function to get a file storage instance
def get_file_storage(directory: Union[str, Path]) -> FileSystemStorage:
    """Get a file storage instance for a directory."""
    return FileSystemStorage(directory)