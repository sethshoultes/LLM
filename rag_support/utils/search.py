#!/usr/bin/env python3
"""
Search utility module for the LLM Platform.

Provides search functionality for the RAG system, including document
retrieval, tag-based filtering, and context extraction.
"""

import os
import re
import math
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union

# Import from core modules
from core.logging import get_logger
from core.utils import timer, estimate_tokens

# Import RAG types but defer actual import to avoid circular imports
from typing import TYPE_CHECKING
if TYPE_CHECKING:

# Get logger for this module
logger = get_logger("rag_support.search")

# Import BASE_DIR from rag_support
try:
    from rag_support import BASE_DIR
except ImportError:
    # Fallback if the import fails
    import os
    SCRIPT_DIR = Path(__file__).resolve().parent
    BASE_DIR = SCRIPT_DIR.parent.parent
    # Use environment variable if available
    BASE_DIR = Path(os.environ.get("LLM_BASE_DIR", str(BASE_DIR)))

# Import project manager for document access
try:
    from rag_support.utils.project_manager import project_manager
except ImportError:
    logger.error("Failed to import project_manager - search functionality will be limited")
    project_manager = None

# Constants
DEFAULT_TOKENS_PER_CHAR = 0.25  # Approximation of tokens per character (1 token ~= 4 chars)
DEFAULT_MAX_RESULTS = 10  # Default maximum number of search results
DEFAULT_CACHE_EXPIRY = 300  # Default cache expiry time in seconds (5 minutes)

class EnhancedSearch:
    """
    Enhanced search engine for the RAG system.
    
    Uses the underlying RAG search components but adds additional functionality
    like caching, similarity search, and context extraction.
    """
    
    def __init__(self):
        """Initialize the search engine."""
        # Cache to improve performance
        self.document_cache = {}  # project_id -> List[doc]
        self.cache_timestamp = 0
        self.cache_expiry = DEFAULT_CACHE_EXPIRY  # 5 minutes
        
        # Initialize local search engine if new RAG components are available
        self.use_new_search = False
        try:
            # Import here to avoid circular imports
            from rag.search import SearchEngine
            from rag.indexer import TfidfIndex
            self.search_engine = SearchEngine(index=TfidfIndex())
            self.use_new_search = True
            logger.info("Using new RAG search components")
        except ImportError:
            logger.warning("New RAG search components not available, using direct file access")
    
    @timer
    def search(self, project_id: str, query: str, max_results: int = DEFAULT_MAX_RESULTS) -> List[Dict[str, Any]]:
        """
        Search for documents in a project.
        
        Args:
            project_id: ID of the project to search
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            List of document metadata dictionaries matching the search
        """
        if not query or not query.strip():
            return []
        
        if project_manager and self.use_new_search:
            # Use new RAG components via project manager
            try:
                return project_manager.search_documents(project_id, query, max_results=max_results)
            except Exception as e:
                logger.error(f"Error searching documents with new RAG components: {e}", exc_info=True)
                # Fall back to legacy implementation
        
        # Legacy implementation using direct file access
        # Tokenize query
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []
        
        # Load documents from project
        documents = self._load_documents(project_id)
        
        # Compute scores
        scored_docs = self._compute_document_scores(query_tokens, documents)
        
        # Sort by score (descending) and take top results
        scored_docs.sort(reverse=True, key=lambda x: x[0])
        top_docs = scored_docs[:max_results]
        
        # Format results
        results = []
        for score, doc in top_docs:
            if score > 0:  # Only include relevant documents
                # Add score to document and exclude full content
                doc_copy = doc.copy()
                doc_copy["score"] = round(score, 3)
                
                # Truncate content for preview
                if "content" in doc_copy:
                    preview_length = 200
                    content = doc_copy["content"]
                    doc_copy["preview"] = content[:preview_length] + "..." if len(content) > preview_length else content
                    del doc_copy["content"]  # Remove full content
                
                results.append(doc_copy)
        
        return results
    
    @timer
    def search_by_tags(self, project_id: str, tags: List[str], max_results: int = DEFAULT_MAX_RESULTS) -> List[Dict[str, Any]]:
        """
        Search for documents with specific tags.
        
        Args:
            project_id: ID of the project to search
            tags: List of tags to filter by
            max_results: Maximum number of results to return
            
        Returns:
            List of document metadata dictionaries with the specified tags
        """
        if not tags:
            return []
        
        if project_manager and self.use_new_search:
            # Use new RAG components via project manager
            try:
                return project_manager.search_documents(project_id, "", tags=tags, max_results=max_results)
            except Exception as e:
                logger.error(f"Error searching documents by tags with new RAG components: {e}", exc_info=True)
                # Fall back to legacy implementation
        
        # Legacy implementation
        # Load documents from project
        documents = self._load_documents(project_id)
        
        # Filter documents by tags
        results = []
        for doc in documents:
            doc_tags = set(doc.get("tags", []))
            if doc_tags and all(tag in doc_tags for tag in tags):
                # Create a copy with truncated content
                doc_copy = doc.copy()
                if "content" in doc_copy:
                    preview_length = 200
                    content = doc_copy["content"]
                    doc_copy["preview"] = content[:preview_length] + "..." if len(content) > preview_length else content
                    del doc_copy["content"]  # Remove full content
                
                results.append(doc_copy)
        
        # Sort by updated_at (most recent first) and limit results
        results.sort(key=lambda d: d.get("updated_at", ""), reverse=True)
        return results[:max_results]
    
    @timer
    def get_document(self, project_id: str, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a document by ID.
        
        Args:
            project_id: ID of the project
            doc_id: ID of the document
            
        Returns:
            Document dictionary if found, None otherwise
        """
        if project_manager:
            # Use project manager
            try:
                return project_manager.get_document(project_id, doc_id)
            except Exception as e:
                logger.error(f"Error getting document with project manager: {e}", exc_info=True)
                # Fall back to legacy implementation
        
        # Legacy implementation
        # Skip hidden files
        if doc_id.startswith(".") or doc_id.startswith("._"):
            return None
        
        PROJECTS_DIR = BASE_DIR / "rag_support" / "projects"
        doc_path = PROJECTS_DIR / project_id / "documents" / f"{doc_id}.md"
        
        if not doc_path.exists():
            return None
        
        try:
            with open(doc_path, "r") as f:
                content = f.read()
            
            # Parse document
            metadata = {}
            document_content = content
            
            if content.startswith("---"):
                # Extract frontmatter
                try:
                    _, frontmatter, markdown = content.split("---", 2)
                    document_content = markdown.strip()
                    
                    # Parse frontmatter
                    for line in frontmatter.strip().split("\n"):
                        if ":" in line:
                            key, value = line.split(":", 1)
                            try:
                                metadata[key.strip()] = json.loads(value.strip())
                            except:
                                metadata[key.strip()] = value.strip()
                except:
                    # Failed to parse frontmatter, use the whole content
                    document_content = content
            
            return {
                "id": doc_id,
                "title": metadata.get("title", doc_id),
                "content": document_content,
                "tags": metadata.get("tags", []),
                "created_at": metadata.get("created_at", ""),
                "updated_at": metadata.get("updated_at", "")
            }
        except Exception as e:
            logger.error(f"Error loading document {doc_path}: {e}", exc_info=True)
            return None
    
    @timer
    def find_similar(self, project_id: str, doc_id: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Find documents similar to a given document.
        
        Args:
            project_id: ID of the project
            doc_id: ID of the document to find similar documents for
            max_results: Maximum number of results to return
            
        Returns:
            List of document metadata dictionaries similar to the specified document
        """
        # Get the source document
        source_doc = self.get_document(project_id, doc_id)
        if not source_doc:
            return []
        
        # Extract key terms from source document (simple implementation)
        content = source_doc.get("content", "") + " " + source_doc.get("title", "")
        tokens = self._tokenize(content)
        
        # Count token frequency
        from collections import Counter
        token_counts = Counter(tokens)
        
        # Use top N tokens as query
        top_tokens = [token for token, _ in token_counts.most_common(10)]
        query = " ".join(top_tokens)
        
        # Search using these tokens
        results = self.search(project_id, query, max_results + 1)
        
        # Remove the source document from results
        return [doc for doc in results if doc.get("id") != doc_id]
    
    @timer
    def extract_relevant_contexts(self, project_id: str, query: str, 
                                max_docs: int = 3, 
                                max_chars: int = 3000) -> List[Dict[str, Any]]:
        """
        Extract the most relevant contexts for a query.
        
        Args:
            project_id: ID of the project
            query: Search query
            max_docs: Maximum number of documents to include
            max_chars: Maximum total character length for all contexts
            
        Returns:
            List of document contexts most relevant to the query
        """
        # Search for relevant documents
        docs = self.search(project_id, query, max_results=max_docs)
        
        contexts = []
        total_length = 0
        total_tokens = 0
        
        for doc in docs:
            # Get full document content
            full_doc = self.get_document(project_id, doc["id"])
            if not full_doc:
                continue
            
            content = full_doc.get("content", "")
            title = full_doc.get("title", "")
            
            # Estimate token count for this document
            doc_title_text = f"# {title}\n\n"
            doc_token_count = self.estimate_token_count(doc_title_text + content)
            
            # Check if we need to limit the content
            max_tokens = int(max_chars / 4)  # Approximate token limit
            remaining_tokens = max_tokens - total_tokens
            
            if remaining_tokens <= 0:
                break
            
            # Create context entry
            if doc_token_count > remaining_tokens:
                # Need to truncate
                # First, estimate tokens for just the title
                title_tokens = self.estimate_token_count(doc_title_text)
                
                # Calculate how many tokens we can use for content
                content_tokens = remaining_tokens - title_tokens
                
                # Estimate characters based on token count (rough approximation)
                content_chars = content_tokens * 4
                
                # Truncate content
                truncated_content = self._truncate_text(content, content_chars)
                context_text = doc_title_text + truncated_content
                
                # Update the doc token count to the actual used amount
                doc_token_count = self.estimate_token_count(context_text)
            else:
                # Can use the full document
                context_text = doc_title_text + content
            
            contexts.append({
                "id": doc["id"],
                "title": title,
                "content": context_text,
                "score": doc.get("score", 0),
                "tokens": doc_token_count,
                "truncated": doc_token_count < self.estimate_token_count(doc_title_text + content)
            })
            
            total_length += len(context_text)
            total_tokens += doc_token_count
            
            # Stop if we've reached the maximum size
            if total_tokens >= max_tokens:
                break
        
        # Add token information to the overall result
        for context in contexts:
            context["token_percentage"] = round((context["tokens"] / total_tokens) * 100 if total_tokens > 0 else 0, 1)
        
        return contexts
    
    def _truncate_text(self, text: str, max_chars: int) -> str:
        """
        Truncate text to a given maximum character length.
        
        Args:
            text: Text to truncate
            max_chars: Maximum character length
            
        Returns:
            Truncated text ending at a sentence boundary if possible
        """
        # If text is already shorter than the limit, return it unchanged
        if len(text) <= max_chars:
            return text
        
        # Find a good breaking point (end of sentence or paragraph)
        # Look for the last period, question mark, or exclamation mark followed by whitespace
        # within the allowed character limit
        breakpoint = max(
            text[:max_chars].rfind('. '),
            text[:max_chars].rfind('! '),
            text[:max_chars].rfind('? '),
            text[:max_chars].rfind('\n\n')
        )
        
        # If no good breakpoint found, just cut at the character limit
        if breakpoint == -1:
            return text[:max_chars] + "..."
        else:
            # Include the period/etc and the space
            return text[:breakpoint + 2] + "..."
    
    def estimate_token_count(self, text: str) -> int:
        """
        Estimate the number of tokens in a text string.
        
        Args:
            text: Text to estimate tokens for
            
        Returns:
            Estimated token count
        """
        # Try to use the utility function from core module
        try:
            return estimate_tokens(text)
        except (ImportError, NameError):
            # Fall back to simple approximation if the utility is not available
            if not text:
                return 0
            
            # Simple approximation: 1 token is roughly 4 characters for English text
            char_count = len(text)
            token_estimate = char_count // 4
            
            # Account for whitespace which is typically tokenized differently
            whitespace_count = len([c for c in text if c.isspace()])
            whitespace_token_adjustment = whitespace_count // 8
            
            return max(1, token_estimate + whitespace_token_adjustment)
    
    def _tokenize(self, text: str) -> List[str]:
        """
        Convert text to tokens.
        
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
    
    def _compute_tf(self, text: str) -> Dict[str, float]:
        """
        Compute term frequency for a document.
        
        Args:
            text: Document text
            
        Returns:
            Dictionary mapping terms to their frequencies
        """
        from collections import Counter
        
        tokens = self._tokenize(text)
        token_count = len(tokens)
        
        # Count frequency of each token
        tf_dict = Counter(tokens)
        
        # Normalize by document length
        if token_count > 0:
            for token in tf_dict:
                tf_dict[token] = tf_dict[token] / token_count
        
        return dict(tf_dict)
    
    def _compute_document_scores(self, query_tokens: List[str], 
                               documents: List[Dict[str, Any]]) -> List[Tuple[float, Dict[str, Any]]]:
        """
        Compute relevance scores for documents.
        
        Args:
            query_tokens: Tokenized query
            documents: List of documents to score
            
        Returns:
            List of (score, document) tuples
        """
        # Calculate inverse document frequency
        doc_count = len(documents)
        idf = {}
        
        for token in query_tokens:
            token_docs = sum(1 for doc in documents if token in self._tokenize(doc.get("content", "") + " " + doc.get("title", "")))
            idf[token] = math.log(doc_count / (token_docs + 1)) + 1.0  # Add 1 to avoid division by zero
        
        # Calculate scores for each document
        scored_docs = []
        for doc in documents:
            score = 0.0
            content = doc.get("content", "") + " " + doc.get("title", "")
            
            # Calculate TF for document
            doc_tf = self._compute_tf(content)
            
            # Calculate TF-IDF score
            for token in query_tokens:
                if token in doc_tf:
                    score += doc_tf[token] * idf.get(token, 1.0)
            
            # Boost score for tokens in title
            title = doc.get("title", "").lower()
            for token in query_tokens:
                if token in title:
                    score += 0.5
            
            # Boost documents with matching tags
            if "tags" in doc and isinstance(doc["tags"], list):
                for token in query_tokens:
                    if any(token in tag.lower() for tag in doc["tags"]):
                        score += 0.3
            
            # Include the document and its score
            scored_docs.append((score, doc))
        
        return scored_docs
    
    def _load_documents(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Load and cache documents from a project.
        
        Args:
            project_id: ID of the project
            
        Returns:
            List of document dictionaries
        """
        current_time = time.time()
        
        # Use cached documents if available and not expired
        cache_key = f"project_{project_id}"
        if (
            cache_key in self.document_cache and 
            current_time - self.cache_timestamp < self.cache_expiry
        ):
            return self.document_cache[cache_key]
        
        if project_manager:
            # Try to use project manager (more efficient)
            try:
                documents = []
                for doc_meta in project_manager.list_documents(project_id):
                    # Get the full document with content
                    doc = project_manager.get_document(project_id, doc_meta["id"])
                    if doc:
                        documents.append(doc)
                
                # Update cache
                self.document_cache[cache_key] = documents
                self.cache_timestamp = current_time
                
                return documents
            except Exception as e:
                logger.error(f"Error loading documents with project manager: {e}", exc_info=True)
                # Fall back to legacy implementation
        
        # Legacy implementation: load documents directly from file system
        PROJECTS_DIR = BASE_DIR / "rag_support" / "projects"
        documents = []
        documents_dir = PROJECTS_DIR / project_id / "documents"
        
        if not documents_dir.exists():
            return []
        
        for doc_path in documents_dir.glob("*.md"):
            # Skip hidden files and macOS metadata files
            if doc_path.name.startswith(".") or doc_path.name.startswith("._"):
                continue
            
            try:
                with open(doc_path, "r") as f:
                    content = f.read()
                
                # Parse document
                doc_id = doc_path.stem
                
                # Extract frontmatter if present
                metadata = {}
                document_content = content
                
                if content.startswith("---"):
                    # Extract frontmatter
                    try:
                        _, frontmatter, markdown = content.split("---", 2)
                        document_content = markdown.strip()
                        
                        # Parse frontmatter
                        for line in frontmatter.strip().split("\n"):
                            if ":" in line:
                                key, value = line.split(":", 1)
                                try:
                                    metadata[key.strip()] = json.loads(value.strip())
                                except:
                                    metadata[key.strip()] = value.strip()
                    except:
                        # Failed to parse frontmatter, use the whole content
                        document_content = content
                
                document = {
                    "id": doc_id,
                    "title": metadata.get("title", doc_id),
                    "content": document_content,
                    "tags": metadata.get("tags", []),
                    "created_at": metadata.get("created_at", ""),
                    "updated_at": metadata.get("updated_at", "")
                }
                
                documents.append(document)
            except Exception as e:
                logger.error(f"Error loading document {doc_path}: {e}", exc_info=True)
        
        # Update cache
        self.document_cache[cache_key] = documents
        self.cache_timestamp = current_time
        
        return documents

# Create a default instance
search_engine = EnhancedSearch()

if __name__ == "__main__":
    # Simple test
    logger.info("Testing search engine...")
    
    # Example search
    project_id = "test_project"  # Replace with a real project ID
    results = search_engine.search(project_id, "example query")
    
    logger.info(f"Search results: {len(results)} documents found")