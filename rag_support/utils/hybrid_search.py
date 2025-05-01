#!/usr/bin/env python3
"""
Hybrid search module for the LLM Platform.

Combines keyword-based TF-IDF search with semantic embedding-based search
to provide more accurate and relevant document retrieval for RAG systems.
"""

import os
import json
import time
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Import from core modules
from core.logging import get_logger
from core.utils import timer
from core.paths import ensure_dir

# Import RAG types but defer actual import to avoid circular imports
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass  # Will be used for type annotations in future

# Get logger for this module
logger = get_logger("rag_support.hybrid_search")

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

# Import search engine for TF-IDF search
try:
    from rag_support.utils.search import search_engine as tfidf_search
except ImportError:
    logger.error("Failed to import search_engine - hybrid search will be limited")
    tfidf_search = None

# Constants
DEFAULT_CACHE_EXPIRY = 3600  # Default embedding cache expiry time in seconds (1 hour)
EMBEDDING_CACHE_DIR = BASE_DIR / "rag_support" / "cache" / "embeddings"
SEMANTIC_WEIGHT = 0.6  # Weight for semantic search (0.0-1.0)
KEYWORD_WEIGHT = 0.4  # Weight for keyword search (0.0-1.0)
DEFAULT_MAX_RESULTS = 10  # Default maximum number of search results
DEFAULT_EMBEDDING_DIM = 384  # Default embedding dimension (sentence-transformers default)


class HybridSearch:
    """
    Hybrid search engine for RAG systems.

    Combines keyword-based TF-IDF search with semantic embedding-based search
    for improved accuracy and recall.
    """

    def __init__(self):
        """Initialize the hybrid search engine."""
        # Cache for document embeddings
        self.embeddings_cache = {}  # project_id -> {doc_id -> embedding}
        self.cache_timestamp = 0
        self.cache_expiry = DEFAULT_CACHE_EXPIRY

        # Initialize embedding model
        self.embedding_model = None
        self.model_loaded = False

        # Ensure embedding cache directory exists
        ensure_dir(EMBEDDING_CACHE_DIR)

        # Load embedding model lazily on first use
        logger.info("Initialized hybrid search engine")

    def _load_embedding_model(self):
        """Load the embedding model if not already loaded."""
        if self.model_loaded:
            return True

        try:
            try:
                # Try to import sentence_transformers
                from sentence_transformers import SentenceTransformer
                
                # Use a small, efficient model for sentence embeddings
                self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
                self.model_loaded = True
                logger.info("Loaded embedding model: all-MiniLM-L6-v2")
                return True
            except (ImportError, ModuleNotFoundError):
                logger.warning(
                    "Failed to import sentence_transformers. "
                    "Using fallback embedding model."
                )
                # Create a simple fallback embedding model
                return self._create_fallback_embedding_model()
        except Exception as e:
            logger.error(f"Error loading embedding model: {e}", exc_info=True)
            
            # Create a simple fallback embedding model
            return self._create_fallback_embedding_model()
            
    def _create_fallback_embedding_model(self):
        """Create a simple fallback embedding model when sentence-transformers is unavailable."""
        try:
            # Create a very simple embedding model using numpy
            # This is not as good as proper embeddings but allows basic functionality
            import numpy as np
            from collections import Counter
            import re
            
            class DeterministicEmbedder:
                def __init__(self, embedding_dim=DEFAULT_EMBEDDING_DIM):
                    self.embedding_dim = embedding_dim
                    self.word_vectors = {}
                    self.char_vectors = {}  # Character-level vectors for OOV words
                    self.initialized = False
                    # Pre-initialize special vectors
                    np.random.seed(42)  # Ensure deterministic vectors
                    self._initialize_char_vectors()
                    logger.info("Created improved fallback embedding model")
                    
                def _initialize_char_vectors(self):
                    """Initialize vectors for characters to handle unknown words consistently"""
                    # Create vectors for all ASCII characters with fixed seed
                    for i in range(128):
                        char = chr(i)
                        # Each character gets a consistent vector
                        self._get_char_vector(char)
                    
                def _get_char_vector(self, char):
                    """Get or create a deterministic vector for a character"""
                    if char not in self.char_vectors:
                        # Use character code as seed for determinism
                        char_code = ord(char)
                        np.random.seed(42 + char_code)
                        self.char_vectors[char] = np.random.rand(self.embedding_dim)
                        # Reset the seed to avoid affecting other random operations
                        np.random.seed(42)
                    return self.char_vectors[char]
                
                def _get_word_vector(self, word):
                    """Get or create a deterministic vector for a word"""
                    if word not in self.word_vectors:
                        if len(word) == 0:
                            return np.zeros(self.embedding_dim)
                            
                        # Create word vector from character n-grams for consistency
                        word_vec = np.zeros(self.embedding_dim)
                        
                        # Add character vectors
                        for char in word:
                            word_vec += self._get_char_vector(char)
                        
                        # Add bigram vectors for local word structure
                        if len(word) > 1:
                            for i in range(len(word) - 1):
                                bigram = word[i:i+2]
                                # Hash the bigram to an integer and use as seed
                                bigram_hash = sum(ord(c) for c in bigram)
                                np.random.seed(42 + bigram_hash)
                                bigram_vec = np.random.rand(self.embedding_dim)
                                word_vec += bigram_vec * 0.5  # Lower weight for bigrams
                                np.random.seed(42)  # Reset seed
                        
                        # Normalize the word vector
                        if np.linalg.norm(word_vec) > 0:
                            word_vec = word_vec / np.linalg.norm(word_vec)
                            
                        self.word_vectors[word] = word_vec
                        
                    return self.word_vectors[word]
                
                def encode(self, text, normalize_embeddings=True):
                    """Create semantically meaningful embeddings using improved algorithm"""
                    # Extract words and preprocess text
                    words = re.findall(r'\b\w+\b', text.lower())
                    if not words:
                        # Return zeros for empty text
                        return np.zeros(self.embedding_dim)
                    
                    # Get term frequency dictionary
                    word_counts = Counter(words)
                    total_words = sum(word_counts.values())
                    
                    # Calculate IDF-like weights (more weight to less common words)
                    unique_words = len(word_counts)
                    word_weights = {}
                    for word, count in word_counts.items():
                        # Modified TF-IDF inspired weighting (more weight to rarer terms)
                        word_weights[word] = (count / total_words) * (1 + np.log(unique_words / 1))
                    
                    # Create weighted average of word vectors with position-aware weighting
                    embedding = np.zeros(self.embedding_dim)
                    
                    # Apply positional weighting (words at start/end of text get more weight)
                    positions = []
                    for i, word in enumerate(words):
                        # Position weight: more weight to start and end of text (U-shaped)
                        rel_pos = i / len(words)
                        # Weight is higher for words at beginning or end
                        pos_weight = 1.2 - (abs(rel_pos - 0.5) * 0.4)
                        positions.append((word, pos_weight))
                    
                    # Combine word vectors with multiple weighting factors
                    for word, count in word_counts.items():
                        word_vec = self._get_word_vector(word)
                        # Combine term frequency weight with position weight
                        word_pos_weights = [pw for w, pw in positions if w == word]
                        avg_pos_weight = sum(word_pos_weights) / len(word_pos_weights) if word_pos_weights else 1.0
                        
                        # Final weight combines frequency and position
                        final_weight = word_weights[word] * avg_pos_weight
                        embedding += word_vec * final_weight
                    
                    # Normalize if requested
                    if normalize_embeddings and np.linalg.norm(embedding) > 0:
                        embedding = embedding / np.linalg.norm(embedding)
                    
                    return embedding
            
            self.embedding_model = DeterministicEmbedder()
            self.model_loaded = True
            logger.warning("Using deterministic fallback embedding model with character n-grams and position-aware weighting")
            logger.info("For better results, install sentence-transformers: pip install sentence-transformers")
            return True
        except Exception as e:
            logger.error(f"Failed to create fallback embedding model: {e}", exc_info=True)
            return False

    @timer
    def get_embedding(self, text: str) -> Optional[np.ndarray]:
        """
        Get embedding for a text string.

        Args:
            text: Text to embed

        Returns:
            Embedding vector as numpy array, or None if embedding failed
        """
        if not text or not text.strip():
            return None

        # Load model if needed
        if not self._load_embedding_model():
            return None

        try:
            # Generate embedding
            embedding = self.embedding_model.encode(text, normalize_embeddings=True)
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}", exc_info=True)
            return None

    @timer
    def load_document_embeddings(self, project_id: str) -> Dict[str, np.ndarray]:
        """
        Load document embeddings for a project from cache or generate if needed.

        Args:
            project_id: ID of the project

        Returns:
            Dictionary mapping document IDs to embeddings
        """
        # Check if cached embeddings are valid
        current_time = time.time()
        cache_key = f"project_{project_id}"

        if (
            cache_key in self.embeddings_cache
            and current_time - self.cache_timestamp < self.cache_expiry
        ):
            return self.embeddings_cache[cache_key]

        # Try to load from disk cache
        embeddings_file = EMBEDDING_CACHE_DIR / f"{project_id}_embeddings.npz"
        metadata_file = EMBEDDING_CACHE_DIR / f"{project_id}_metadata.json"

        if embeddings_file.exists() and metadata_file.exists():
            try:
                # Load embeddings
                embeddings_data = np.load(embeddings_file)

                # Load metadata
                with open(metadata_file, "r") as f:
                    metadata = json.load(f)

                # Check if metadata has document timestamps that match the actual documents
                if self._validate_embedding_cache(project_id, metadata):
                    # Reconstruct the embeddings dictionary
                    embeddings = {}
                    for doc_id in metadata["documents"]:
                        if doc_id in embeddings_data:
                            embeddings[doc_id] = embeddings_data[doc_id]

                    # Cache in memory
                    self.embeddings_cache[cache_key] = embeddings
                    self.cache_timestamp = current_time

                    logger.info(f"Loaded embeddings for {len(embeddings)} documents from cache")
                    return embeddings
            except Exception as e:
                logger.error(f"Error loading cached embeddings: {e}", exc_info=True)

        # Generate embeddings for all documents in the project
        embeddings = self._generate_document_embeddings(project_id)

        # Cache in memory
        self.embeddings_cache[cache_key] = embeddings
        self.cache_timestamp = current_time

        # Cache to disk
        if embeddings:
            self._save_embeddings_to_cache(project_id, embeddings)

        return embeddings

    def _validate_embedding_cache(self, project_id: str, metadata: Dict) -> bool:
        """
        Validate that cached embeddings match current documents.

        Args:
            project_id: ID of the project
            metadata: Embedding metadata with document information

        Returns:
            True if cache is valid, False otherwise
        """
        # Import here to avoid circular imports
        try:
            from rag_support.utils.project_manager import project_manager

            if not project_manager:
                return False

            # Get current document list
            current_docs = project_manager.list_documents(project_id)
            current_doc_map = {doc["id"]: doc for doc in current_docs}

            # Check if all cached documents exist and haven't been modified
            for doc_id, doc_info in metadata["documents"].items():
                if doc_id not in current_doc_map:
                    # Document no longer exists
                    return False

                current_doc = current_doc_map[doc_id]
                if current_doc.get("updated_at") != doc_info.get("updated_at"):
                    # Document has been modified
                    return False

            # Check if there are new documents that don't have embeddings
            for doc_id in current_doc_map:
                if doc_id not in metadata["documents"]:
                    # New document without embedding
                    return False

            return True
        except Exception as e:
            logger.error(f"Error validating embedding cache: {e}", exc_info=True)
            return False

    @timer
    def _generate_document_embeddings(self, project_id: str) -> Dict[str, np.ndarray]:
        """
        Generate embeddings for all documents in a project.

        Args:
            project_id: ID of the project

        Returns:
            Dictionary mapping document IDs to embeddings
        """
        # Import here to avoid circular imports
        try:
            from rag_support.utils.project_manager import project_manager

            if not project_manager or not self._load_embedding_model():
                return {}

            # Get all documents in the project
            docs = project_manager.list_documents(project_id)
            embeddings = {}

            for doc_meta in docs:
                doc_id = doc_meta["id"]

                # Get the full document
                doc = project_manager.get_document(project_id, doc_id)
                if not doc:
                    continue

                # Prepare text for embedding (combine title and content)
                text = doc.get("title", "") + "\n\n" + doc.get("content", "")
                if not text.strip():
                    continue

                # Generate embedding
                embedding = self.get_embedding(text)
                if embedding is not None:
                    embeddings[doc_id] = embedding

            logger.info(f"Generated embeddings for {len(embeddings)} documents")
            return embeddings
        except Exception as e:
            logger.error(f"Error generating document embeddings: {e}", exc_info=True)
            return {}

    def _save_embeddings_to_cache(self, project_id: str, embeddings: Dict[str, np.ndarray]):
        """
        Save document embeddings to disk cache.

        Args:
            project_id: ID of the project
            embeddings: Dictionary mapping document IDs to embeddings
        """
        try:
            # Import project manager to get document metadata
            from rag_support.utils.project_manager import project_manager

            if not project_manager:
                return

            # Collect document metadata for cache validation
            docs = project_manager.list_documents(project_id)
            doc_metadata = {}

            for doc in docs:
                if doc["id"] in embeddings:
                    doc_metadata[doc["id"]] = {
                        "updated_at": doc.get("updated_at", ""),
                        "title": doc.get("title", ""),
                    }

            # Create metadata file
            metadata = {
                "timestamp": time.time(),
                "document_count": len(embeddings),
                "model": "all-MiniLM-L6-v2",
                "embedding_dim": (
                    embeddings[next(iter(embeddings))].shape[0]
                    if embeddings
                    else DEFAULT_EMBEDDING_DIM
                ),
                "documents": doc_metadata,
            }

            # Save metadata
            metadata_file = EMBEDDING_CACHE_DIR / f"{project_id}_metadata.json"
            with open(metadata_file, "w") as f:
                json.dump(metadata, f, indent=2)

            # Save embeddings
            embeddings_file = EMBEDDING_CACHE_DIR / f"{project_id}_embeddings.npz"
            np.savez_compressed(embeddings_file, **embeddings)

            logger.info(f"Saved embeddings for {len(embeddings)} documents to cache")
        except Exception as e:
            logger.error(f"Error saving embeddings to cache: {e}", exc_info=True)

    @timer
    def semantic_search(
        self, project_id: str, query: str, max_results: int = DEFAULT_MAX_RESULTS
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search based on embeddings.

        Args:
            project_id: ID of the project
            query: Search query
            max_results: Maximum number of results to return

        Returns:
            List of document metadata dictionaries with semantic similarity scores
        """
        if not query or not query.strip():
            return []

        # Get query embedding
        query_embedding = self.get_embedding(query)
        if query_embedding is None:
            logger.warning("Failed to generate embedding for query")
            return []

        # Load document embeddings
        doc_embeddings = self.load_document_embeddings(project_id)
        if not doc_embeddings:
            logger.warning("No document embeddings available")
            return []

        # Compute similarity scores
        results = []
        for doc_id, embedding in doc_embeddings.items():
            # Calculate cosine similarity
            similarity = np.dot(query_embedding, embedding)
            # Normalize to a [0, 1] range (embedding vectors are already normalized)

            results.append({"id": doc_id, "score": float(similarity)})

        # Sort by similarity (descending)
        results.sort(key=lambda x: x["score"], reverse=True)

        # Take top results
        top_results = results[:max_results]

        # Get document details for top results
        enriched_results = []
        try:
            from rag_support.utils.project_manager import project_manager

            if project_manager:
                for result in top_results:
                    doc = project_manager.get_document(project_id, result["id"])
                    if doc:
                        # Create a copy with score and preview
                        doc_copy = doc.copy()
                        doc_copy["score"] = round(result["score"], 3)

                        # Add preview of content
                        if "content" in doc_copy:
                            preview_length = 200
                            content = doc_copy["content"]
                            doc_copy["preview"] = (
                                content[:preview_length] + "..."
                                if len(content) > preview_length
                                else content
                            )
                            # Remove full content from result
                            del doc_copy["content"]

                        enriched_results.append(doc_copy)
        except Exception as e:
            logger.error(f"Error enriching semantic search results: {e}", exc_info=True)
            # Return bare results if enrichment fails
            return top_results

        return enriched_results

    @timer
    def hybrid_search(
        self,
        project_id: str,
        query: str,
        semantic_weight: float = SEMANTIC_WEIGHT,
        keyword_weight: float = KEYWORD_WEIGHT,
        max_results: int = DEFAULT_MAX_RESULTS,
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining semantic and keyword-based approaches.

        Args:
            project_id: ID of the project
            query: Search query
            semantic_weight: Weight for semantic search results (0.0-1.0)
            keyword_weight: Weight for keyword search results (0.0-1.0)
            max_results: Maximum number of results to return

        Returns:
            List of document metadata dictionaries with combined scores
        """
        if not query or not query.strip():
            return []

        # Normalize weights to sum to 1.0
        total_weight = semantic_weight + keyword_weight
        if total_weight <= 0:
            # Default to equal weights if invalid values provided
            semantic_weight = 0.5
            keyword_weight = 0.5
        else:
            semantic_weight = semantic_weight / total_weight
            keyword_weight = keyword_weight / total_weight

        # Get results from both search methods
        semantic_results = []
        keyword_results = []

        # Semantic search
        if semantic_weight > 0:
            # Return more results from each method to ensure we have enough for combining
            internal_max = max(max_results * 2, 20)
            semantic_results = self.semantic_search(project_id, query, max_results=internal_max)

        # Keyword search
        if keyword_weight > 0 and tfidf_search:
            # Return more results from each method to ensure we have enough for combining
            internal_max = max(max_results * 2, 20)
            keyword_results = tfidf_search.search(project_id, query, max_results=internal_max)

        # Combine and normalize scores
        combined_results = self._combine_search_results(
            semantic_results, keyword_results, semantic_weight, keyword_weight
        )

        # Sort by combined score (descending)
        combined_results.sort(key=lambda x: x["score"], reverse=True)

        # Return top results
        return combined_results[:max_results]

    def _combine_search_results(
        self,
        semantic_results: List[Dict[str, Any]],
        keyword_results: List[Dict[str, Any]],
        semantic_weight: float,
        keyword_weight: float,
    ) -> List[Dict[str, Any]]:
        """
        Combine results from semantic and keyword searches.

        Args:
            semantic_results: Results from semantic search
            keyword_results: Results from keyword search
            semantic_weight: Weight for semantic scores
            keyword_weight: Weight for keyword scores

        Returns:
            Combined results with normalized scores
        """
        # Create dictionaries for faster lookups
        semantic_dict = {r["id"]: r for r in semantic_results}
        keyword_dict = {r["id"]: r for r in keyword_results}

        # Get all unique document IDs
        all_ids = set(semantic_dict.keys()) | set(keyword_dict.keys())

        # Combine scores for each document
        combined_results = []
        for doc_id in all_ids:
            semantic_score = semantic_dict.get(doc_id, {}).get("score", 0.0)
            keyword_score = keyword_dict.get(doc_id, {}).get("score", 0.0)

            # Calculate combined score
            combined_score = (semantic_score * semantic_weight) + (keyword_score * keyword_weight)

            # Get document metadata (prefer keyword results as they contain more metadata)
            doc = keyword_dict.get(doc_id, semantic_dict.get(doc_id, {})).copy()

            # Update the score
            doc["score"] = round(combined_score, 3)

            # Add score breakdown for debugging/transparency
            doc["score_breakdown"] = {
                "semantic": round(semantic_score, 3),
                "keyword": round(keyword_score, 3),
                "semantic_weight": semantic_weight,
                "keyword_weight": keyword_weight,
            }

            combined_results.append(doc)

        return combined_results


# Create an instance of the hybrid search engine
hybrid_search = HybridSearch()

if __name__ == "__main__":
    # Simple test
    logger.info("Testing hybrid search...")

    # Example search
    project_id = "test_project"  # Replace with a real project ID
    results = hybrid_search.hybrid_search(project_id, "example query")

    logger.info(f"Hybrid search results: {len(results)} documents found")
