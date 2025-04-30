#!/usr/bin/env python3
"""
Document prioritization module for the LLM Platform.

Provides algorithms for ranking and prioritizing documents based on
relevance scores, query analysis, conversation history, and other factors
to optimize context selection for RAG systems.
"""

import re
from typing import Dict, List, Any, Optional, Union, Tuple, Set
from collections import Counter

# Import core modules
from core.logging import get_logger
from core.utils import timer

# Import from tokens module

# Configure logger
logger = get_logger("rag.prioritizer")

# Constants
DEFAULT_MAX_RESULTS = 10  # Default maximum number of documents to return


class DocumentPrioritizer:
    """
    Document prioritizer for RAG systems.

    Provides methods for ranking and prioritizing documents based on
    various factors to optimize context selection.
    """

    def __init__(self):
        """Initialize the document prioritizer."""
        # Configure feature flags
        self.use_query_analysis = True  # Use query analysis for prioritization
        self.use_history_aware = True  # Use conversation history for prioritization
        self.use_diversity = True  # Promote diversity in document selection

    @timer
    def prioritize_documents(
        self,
        documents: List[Dict[str, Any]],
        query: str,
        history: List[Dict[str, Any]] = None,
        max_documents: int = DEFAULT_MAX_RESULTS,
    ) -> List[Dict[str, Any]]:
        """
        Prioritize documents based on relevance and other factors.

        Args:
            documents: List of documents with relevance scores
            query: User query for relevance determination
            history: Optional conversation history
            max_documents: Maximum number of documents to return

        Returns:
            Prioritized list of documents
        """
        if not documents:
            return []

        # Make a copy of the documents to avoid modifying originals
        docs = [doc.copy() for doc in documents]

        # Apply prioritization strategies
        if self.use_query_analysis and query:
            docs = self._apply_query_analysis(docs, query)

        if self.use_history_aware and history:
            docs = self._apply_history_analysis(docs, history)

        if self.use_diversity:
            docs = self._apply_diversity_promotion(docs)

        # Sort by final priority score
        prioritized = sorted(
            docs, key=lambda d: d.get("priority_score", d.get("score", 0)), reverse=True
        )

        # Limit to max documents
        return prioritized[:max_documents]

    def _apply_query_analysis(
        self, documents: List[Dict[str, Any]], query: str
    ) -> List[Dict[str, Any]]:
        """
        Apply query analysis to refine document priorities.

        Args:
            documents: List of documents to prioritize
            query: User query for analysis

        Returns:
            Documents with updated priority scores
        """
        # Extract key terms from query
        query_terms = self._extract_terms(query)

        if not query_terms:
            return documents

        # Calculate term frequency in query
        query_term_freq = Counter(query_terms)

        # Evaluate each document for term matches
        for doc in documents:
            # Get document content and title
            content = doc.get("content", "")
            title = doc.get("title", "")

            # Extract terms from document
            doc_terms = self._extract_terms(title + " " + content)
            doc_term_freq = Counter(doc_terms)

            # Calculate term overlap score
            overlap_score = 0

            for term, query_freq in query_term_freq.items():
                if term in doc_term_freq:
                    # Weight matches by term frequency in query
                    overlap_score += query_freq * min(doc_term_freq[term], query_freq)

            # Normalize overlap score (0-1)
            max_possible_score = sum(freq**2 for freq in query_term_freq.values())
            normalized_overlap = overlap_score / max_possible_score if max_possible_score > 0 else 0

            # Combine with existing score
            base_score = doc.get("score", 0)
            query_weight = 0.3  # Weight for query analysis (can be adjusted)

            priority_score = (base_score * (1 - query_weight)) + (normalized_overlap * query_weight)

            # Update document
            doc["priority_score"] = priority_score
            doc["query_overlap"] = normalized_overlap

        return documents

    def _apply_history_analysis(
        self, documents: List[Dict[str, Any]], history: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Apply conversation history analysis to refine document priorities.

        Args:
            documents: List of documents to prioritize
            history: Conversation history

        Returns:
            Documents with updated priority scores
        """
        if not history:
            return documents

        # Extract terms from recent conversation
        recent_messages = history[-3:]  # Consider last 3 messages
        conversation_text = " ".join(msg.get("content", "") for msg in recent_messages)
        conversation_terms = self._extract_terms(conversation_text)

        if not conversation_terms:
            return documents

        # Calculate term frequency in conversation
        conversation_term_freq = Counter(conversation_terms)

        # Track previously referenced documents
        referenced_docs = set()
        for msg in history:
            for doc_id in msg.get("context_docs", []):
                referenced_docs.add(doc_id)

        # Evaluate each document
        for doc in documents:
            # Get document content and title
            content = doc.get("content", "")
            title = doc.get("title", "")
            doc_id = doc.get("id")

            # Extract terms from document
            doc_terms = self._extract_terms(title + " " + content)
            doc_term_freq = Counter(doc_terms)

            # Calculate conversation relevance
            relevance_score = 0

            for term, conv_freq in conversation_term_freq.items():
                if term in doc_term_freq:
                    relevance_score += conv_freq * min(doc_term_freq[term], conv_freq)

            # Normalize relevance score (0-1)
            max_possible_score = sum(freq**2 for freq in conversation_term_freq.values())
            normalized_relevance = (
                relevance_score / max_possible_score if max_possible_score > 0 else 0
            )

            # Apply continuity boost for previously referenced documents
            continuity_boost = 0.1 if doc_id in referenced_docs else 0

            # Get current priority score
            current_score = doc.get("priority_score", doc.get("score", 0))

            # Apply history analysis with weighting
            history_weight = 0.2  # Weight for history analysis

            updated_score = (
                current_score * (1 - history_weight)
                + (normalized_relevance + continuity_boost) * history_weight
            )

            # Update document
            doc["priority_score"] = updated_score
            doc["history_relevance"] = normalized_relevance
            doc["continuity_boost"] = continuity_boost

        return documents

    def _apply_diversity_promotion(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Promote diversity in document selection.

        Args:
            documents: List of documents to diversify

        Returns:
            Documents with updated priority scores
        """
        if len(documents) <= 2:  # No need for diversity with few documents
            return documents

        # Collect all tags across documents
        all_tags = set()
        doc_tags = {}

        for doc in documents:
            tags = doc.get("tags", [])
            if tags:
                doc_tags[doc.get("id")] = set(tags)
                all_tags.update(tags)

        # If no tags, try to promote diversity by other means
        if not all_tags:
            return self._diversify_by_content(documents)

        # Calculate tag frequency across documents
        tag_frequency = Counter()
        for tags in doc_tags.values():
            tag_frequency.update(tags)

        # Apply diversity boost based on rare tags
        for doc in documents:
            doc_id = doc.get("id")
            tags = doc_tags.get(doc_id, set())

            if not tags:
                continue

            # Calculate tag rarity score (higher for less common tags)
            rarity_score = 0
            for tag in tags:
                # Inverse of tag frequency, normalized
                rarity_score += 1 / (tag_frequency[tag] + 0.1)

            # Normalize rarity score (0-1)
            rarity_score = min(1.0, rarity_score / len(tags) / len(documents))

            # Apply diversity boost
            current_score = doc.get("priority_score", doc.get("score", 0))
            diversity_weight = 0.1  # Weight for diversity promotion

            updated_score = current_score * (1 - diversity_weight) + rarity_score * diversity_weight

            # Update document
            doc["priority_score"] = updated_score
            doc["diversity_score"] = rarity_score

        return documents

    def _diversify_by_content(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Diversify documents by content similarity when tags are not available.

        Args:
            documents: List of documents to diversify

        Returns:
            Documents with updated priority scores
        """
        if len(documents) <= 2:
            return documents

        # Extract terms from each document
        doc_terms = {}

        for doc in documents:
            doc_id = doc.get("id")
            content = doc.get("content", "")
            title = doc.get("title", "")

            terms = self._extract_terms(title + " " + content)
            if terms:
                doc_terms[doc_id] = set(terms)

        # Calculate similarity between documents
        similarity_scores = {}

        for i, doc1 in enumerate(documents):
            doc1_id = doc1.get("id")
            doc1_terms = doc_terms.get(doc1_id, set())

            if not doc1_terms:
                continue

            total_similarity = 0

            for j, doc2 in enumerate(documents):
                if i == j:
                    continue

                doc2_id = doc2.get("id")
                doc2_terms = doc_terms.get(doc2_id, set())

                if not doc2_terms:
                    continue

                # Calculate Jaccard similarity
                intersection = len(doc1_terms.intersection(doc2_terms))
                union = len(doc1_terms.union(doc2_terms))

                similarity = intersection / union if union > 0 else 0
                total_similarity += similarity

            # Average similarity to other documents (lower is more unique)
            avg_similarity = total_similarity / (len(documents) - 1) if len(documents) > 1 else 0
            similarity_scores[doc1_id] = avg_similarity

        # Apply diversity boost based on uniqueness
        for doc in documents:
            doc_id = doc.get("id")
            similarity = similarity_scores.get(doc_id, 0)

            # Calculate uniqueness (1 - similarity)
            uniqueness = 1 - similarity

            # Apply diversity boost
            current_score = doc.get("priority_score", doc.get("score", 0))
            diversity_weight = 0.1  # Weight for diversity promotion

            updated_score = current_score * (1 - diversity_weight) + uniqueness * diversity_weight

            # Update document
            doc["priority_score"] = updated_score
            doc["uniqueness"] = uniqueness

        return documents

    def _extract_terms(self, text: str) -> List[str]:
        """
        Extract important terms from text.

        Args:
            text: Text to extract terms from

        Returns:
            List of extracted terms
        """
        if not text:
            return []

        # Convert to lowercase and split into words
        text = text.lower()

        # Remove punctuation
        text = re.sub(r"[^\w\s]", " ", text)

        # Split into words
        words = text.split()

        # Filter out common stop words
        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "is",
            "are",
            "was",
            "were",
            "in",
            "on",
            "at",
            "to",
            "for",
            "with",
            "by",
            "of",
            "that",
            "this",
            "it",
            "as",
            "be",
            "they",
            "their",
            "have",
            "has",
            "had",
            "do",
            "does",
        }

        terms = [word for word in words if word not in stop_words and len(word) > 2]

        return terms


# Create singleton instance for global use
document_prioritizer = DocumentPrioritizer()
