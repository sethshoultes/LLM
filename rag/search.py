#!/usr/bin/env python3
"""
Search functionality for the RAG system.

This module provides search capabilities for finding relevant documents
in the RAG system based on user queries.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging

from .documents import Document, DocumentCollection
from .indexer import InvertedIndex, TfidfIndex
from .storage import StorageBackend, FileSystemStorage

@dataclass
class SearchResult:
    """
    Represents a search result with document and relevance score.
    """
    document: Document
    score: float
    
    def __repr__(self) -> str:
        return f"SearchResult(doc='{self.document.title[:30]}...', score={self.score:.4f})"


class SearchEngine:
    """
    Search engine for finding relevant documents based on queries.
    
    Uses an index to quickly find matching documents and ranks them
    by relevance to the query.
    """
    
    def __init__(
        self, 
        index: Optional[InvertedIndex] = None,
        storage: Optional[StorageBackend] = None
    ):
        """
        Initialize the search engine.
        
        Args:
            index: The index to use for searching
            storage: The storage backend for document retrieval
        """
        self.index = index or TfidfIndex()
        self.storage = storage or FileSystemStorage()
        self.logger = logging.getLogger("rag.search")
    
    def index_documents(self, documents: List[Document]) -> None:
        """
        Index a list of documents for searching.
        
        Args:
            documents: List of documents to index
        """
        for document in documents:
            self.index.add_document(document)
            
        self.logger.info(f"Indexed {len(documents)} documents")
    
    def index_collection(self, collection: DocumentCollection) -> None:
        """
        Index all documents in a collection.
        
        Args:
            collection: The document collection to index
        """
        self.index_documents(collection.get_all_documents())
    
    def search(self, query: str, max_results: int = 5, threshold: float = 0.1) -> List[SearchResult]:
        """
        Search for documents matching the query.
        
        Args:
            query: The search query
            max_results: Maximum number of results to return
            threshold: Minimum relevance score threshold
            
        Returns:
            List of SearchResult objects with matching documents and scores
        """
        if not query.strip():
            self.logger.warning("Empty search query")
            return []
            
        matches = self.index.search(query)
        
        # Filter by threshold and sort by score (descending)
        filtered_matches = [
            SearchResult(document=doc, score=score)
            for doc, score in matches.items()
            if score >= threshold
        ]
        
        filtered_matches.sort(key=lambda x: x.score, reverse=True)
        
        return filtered_matches[:max_results]
    
    def search_by_tag(self, tag: str, max_results: int = 5) -> List[Document]:
        """
        Find documents with a specific tag.
        
        Args:
            tag: The tag to search for
            max_results: Maximum number of results to return
            
        Returns:
            List of documents with the specified tag
        """
        documents = self.storage.list_documents()
        matches = [doc for doc in documents if tag.lower() in [t.lower() for t in doc.tags]]
        
        return matches[:max_results]