#!/usr/bin/env python3
"""
Document indexing module for the LLM Platform.

Provides functionality for indexing and searching documents.
"""

import re
import math
import time
from collections import Counter
from typing import Dict, List, Tuple, Optional, Any, Union, Set

from core.logging import get_logger

from rag.documents import Document, DocumentCollection

# Get logger for this module
logger = get_logger("rag.indexer")

class InvertedIndex:
    """
    Inverted index for document search.
    
    Maps terms to documents for efficient search.
    """
    
    def __init__(self):
        """Initialize an empty inverted index."""
        self.index = {}  # term -> {doc_id: frequency}
        self.document_count = 0
        self.document_lengths = {}  # doc_id -> token count
        self.last_update = 0
    
    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenize a string into individual terms.
        
        Args:
            text: Text to tokenize
            
        Returns:
            List of tokens
        """
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters and replace with spaces
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Split by whitespace and filter empty tokens
        tokens = [token for token in text.split() if token]
        
        return tokens
    
    def _get_document_terms(self, document: Document) -> Dict[str, int]:
        """
        Get terms and their frequencies from a document.
        
        Args:
            document: Document to process
            
        Returns:
            Dictionary mapping terms to their frequencies
        """
        # Extract terms from title (with higher weight)
        title_terms = self._tokenize(document.title)
        title_counter = Counter(title_terms)
        
        # Extract terms from content
        content_terms = self._tokenize(document.content)
        content_counter = Counter(content_terms)
        
        # Combine counters with title terms having higher weight (3x)
        for term, count in title_counter.items():
            content_counter[term] += count * 2
        
        # Add tags as terms (with higher weight)
        tag_terms = []
        for tag in document.tags:
            tag_terms.extend(self._tokenize(tag))
        
        tag_counter = Counter(tag_terms)
        for term, count in tag_counter.items():
            content_counter[term] += count * 3
        
        return dict(content_counter)
    
    def add_document(self, document: Document) -> None:
        """
        Add a document to the index.
        
        Args:
            document: Document to add
        """
        doc_id = document.id
        
        # Get terms from document
        term_freqs = self._get_document_terms(document)
        
        # Add document length
        self.document_lengths[doc_id] = sum(term_freqs.values())
        
        # Update index
        for term, freq in term_freqs.items():
            if term not in self.index:
                self.index[term] = {}
            self.index[term][doc_id] = freq
        
        self.document_count += 1
        self.last_update = time.time()
    
    def remove_document(self, doc_id: str) -> None:
        """
        Remove a document from the index.
        
        Args:
            doc_id: ID of the document to remove
        """
        # Remove document from term lists
        for term, docs in list(self.index.items()):
            if doc_id in docs:
                del docs[doc_id]
                
                # Remove term if it has no documents
                if not docs:
                    del self.index[term]
        
        # Remove document length
        if doc_id in self.document_lengths:
            del self.document_lengths[doc_id]
            self.document_count -= 1
        
        self.last_update = time.time()
    
    def search(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """
        Search for documents matching a query.
        
        Args:
            query: Search query
            top_k: Maximum number of results to return
            
        Returns:
            List of (doc_id, score) tuples, sorted by score in descending order
        """
        # Tokenize query
        query_terms = self._tokenize(query)
        
        if not query_terms:
            return []
        
        # Calculate TF-IDF scores
        scores = {}  # doc_id -> score
        
        for term in query_terms:
            if term not in self.index:
                continue
                
            # Calculate IDF (Inverse Document Frequency)
            # Add 1 to avoid division by zero
            idf = math.log((self.document_count + 1) / (len(self.index[term]) + 1)) + 1
            
            # Update scores for each document containing the term
            for doc_id, freq in self.index[term].items():
                # Calculate TF (Term Frequency)
                tf = freq / self.document_lengths.get(doc_id, 1)
                
                # Update score
                if doc_id not in scores:
                    scores[doc_id] = 0
                scores[doc_id] += tf * idf
        
        # Sort by score
        results = [(doc_id, score) for doc_id, score in scores.items()]
        results.sort(key=lambda x: x[1], reverse=True)
        
        # Return top-k results
        return results[:top_k]
    
    def index_collection(self, collection: DocumentCollection) -> None:
        """
        Index a collection of documents.
        
        Args:
            collection: DocumentCollection to index
        """
        # Clear existing index
        self.index = {}
        self.document_count = 0
        self.document_lengths = {}
        
        # Add each document
        for document in collection.list_all():
            self.add_document(document)
        
        logger.info(f"Indexed {self.document_count} documents")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the index.
        
        Returns:
            Dictionary of index statistics
        """
        return {
            "document_count": self.document_count,
            "term_count": len(self.index),
            "last_update": self.last_update,
            "avg_terms_per_doc": sum(self.document_lengths.values()) / max(1, self.document_count)
        }

class DocumentIndexer:
    """
    Document indexer with search capabilities.
    
    Manages the indexing and searching of documents.
    """
    
    def __init__(self):
        """Initialize the document indexer."""
        self.index = InvertedIndex()
        self.documents = {}  # doc_id -> Document
    
    def index_document(self, document: Document) -> None:
        """
        Index a document.
        
        Args:
            document: Document to index
        """
        # Store document
        self.documents[document.id] = document
        
        # Add to index
        self.index.add_document(document)
    
    def remove_document(self, doc_id: str) -> None:
        """
        Remove a document from the index.
        
        Args:
            doc_id: ID of the document to remove
        """
        # Remove from index
        self.index.remove_document(doc_id)
        
        # Remove document
        if doc_id in self.documents:
            del self.documents[doc_id]
    
    def search(self, query: str, max_results: int = 10) -> List[Document]:
        """
        Search for documents matching a query.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            List of matching documents, sorted by relevance
        """
        # Search the index
        results = self.index.search(query, max_results)
        
        # Get document objects
        documents = []
        for doc_id, score in results:
            if doc_id in self.documents:
                document = self.documents[doc_id]
                # We could add the score to the document if needed
                documents.append(document)
        
        return documents
    
    def search_with_scores(self, query: str, max_results: int = 10) -> List[Tuple[Document, float]]:
        """
        Search for documents matching a query, returning scores.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            List of (document, score) tuples, sorted by score in descending order
        """
        # Search the index
        results = self.index.search(query, max_results)
        
        # Get document objects with scores
        documents = []
        for doc_id, score in results:
            if doc_id in self.documents:
                document = self.documents[doc_id]
                documents.append((document, score))
        
        return documents
    
    def index_collection(self, collection: DocumentCollection) -> None:
        """
        Index a collection of documents.
        
        Args:
            collection: DocumentCollection to index
        """
        # Clear existing data
        self.documents = {}
        
        # Store documents
        for document in collection.list_all():
            self.documents[document.id] = document
        
        # Build index
        self.index.index_collection(collection)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the indexer.
        
        Returns:
            Dictionary of indexer statistics
        """
        stats = self.index.get_stats()
        stats["indexed_document_count"] = len(self.documents)
        return stats

class TfidfIndex(InvertedIndex):
    """
    TF-IDF (Term Frequency-Inverse Document Frequency) index for document search.
    
    Enhanced version of InvertedIndex with better relevance scoring.
    """
    
    def __init__(self):
        """Initialize an empty TF-IDF index."""
        super().__init__()
        self.idf_cache = {}  # term -> IDF value
    
    def add_document(self, document: Document) -> None:
        """
        Add a document to the index.
        
        Args:
            document: Document to add
        """
        super().add_document(document)
        # Invalidate IDF cache since document count changed
        self.idf_cache = {}
    
    def remove_document(self, doc_id: str) -> None:
        """
        Remove a document from the index.
        
        Args:
            doc_id: ID of the document to remove
        """
        super().remove_document(doc_id)
        # Invalidate IDF cache since document count changed
        self.idf_cache = {}
    
    def _calculate_idf(self, term: str) -> float:
        """
        Calculate IDF (Inverse Document Frequency) for a term.
        
        Args:
            term: Term to calculate IDF for
            
        Returns:
            IDF value
        """
        if term in self.idf_cache:
            return self.idf_cache[term]
        
        # If term not in index, return a low IDF
        if term not in self.index:
            return 1.0
        
        # Calculate IDF with smoothing to avoid division by zero
        # and reduce impact of very rare terms
        df = len(self.index[term])  # Document frequency
        idf = math.log((self.document_count + 1) / (df + 1)) + 1
        
        # Cache the value
        self.idf_cache[term] = idf
        
        return idf
    
    def search(self, query: str, top_k: int = 10) -> Dict[str, float]:
        """
        Search for documents matching a query using TF-IDF scoring.
        
        Args:
            query: Search query
            top_k: Maximum number of results to return
            
        Returns:
            Dictionary mapping document IDs to relevance scores
        """
        # Tokenize query
        query_terms = self._tokenize(query)
        
        if not query_terms:
            return {}
        
        # Calculate term frequencies in query
        query_tf = Counter(query_terms)
        
        # Normalize query term frequencies
        query_length = len(query_terms)
        query_tf = {term: freq / query_length for term, freq in query_tf.items()}
        
        # Calculate scores using cosine similarity with TF-IDF weights
        scores = {}  # doc_id -> score
        
        for term, query_term_freq in query_tf.items():
            # Skip terms not in index
            if term not in self.index:
                continue
            
            # Get IDF for term
            idf = self._calculate_idf(term)
            
            # Calculate query weight (TF * IDF)
            query_weight = query_term_freq * idf
            
            # Update scores for documents containing the term
            for doc_id, doc_term_freq in self.index[term].items():
                # Calculate document weight (TF * IDF)
                if self.document_lengths.get(doc_id, 0) == 0:
                    continue
                    
                doc_tf = doc_term_freq / self.document_lengths[doc_id]
                doc_weight = doc_tf * idf
                
                # Update cosine similarity score
                if doc_id not in scores:
                    scores[doc_id] = 0
                scores[doc_id] += query_weight * doc_weight
        
        # Normalize scores by document length (for cosine similarity)
        result = {}
        for doc_id, score in scores.items():
            if self.document_lengths.get(doc_id, 0) == 0:
                continue
                
            # Add the normalized score
            result[doc_id] = score
        
        # Sort by score and return top-k
        sorted_scores = sorted(result.items(), key=lambda x: x[1], reverse=True)[:top_k]
        return {doc_id: score for doc_id, score in sorted_scores}

# Global indexer instance
document_indexer = DocumentIndexer()

# Convenience functions
def index_document(document: Document) -> None:
    """Index a document."""
    document_indexer.index_document(document)

def remove_document(doc_id: str) -> None:
    """Remove a document from the index."""
    document_indexer.remove_document(doc_id)

def search_documents(query: str, max_results: int = 10) -> List[Document]:
    """Search for documents matching a query."""
    return document_indexer.search(query, max_results)

def search_with_scores(query: str, max_results: int = 10) -> List[Tuple[Document, float]]:
    """Search for documents matching a query, returning scores."""
    return document_indexer.search_with_scores(query, max_results)

def index_collection(collection: DocumentCollection) -> None:
    """Index a collection of documents."""
    document_indexer.index_collection(collection)

def get_indexer_stats() -> Dict[str, Any]:
    """Get statistics about the indexer."""
    return document_indexer.get_stats()