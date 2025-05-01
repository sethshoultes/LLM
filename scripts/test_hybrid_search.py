#!/usr/bin/env python3
"""
Test the hybrid_search module.

This script tests the hybrid_search module to ensure it can be properly imported
and that the basic functionality works.
"""

import sys
import os
from pathlib import Path

# Add the parent directory to the path
parent_dir = Path(__file__).resolve().parent.parent
if str(parent_dir) not in sys.path:
    sys.path.append(str(parent_dir))

# Try to import the hybrid_search module
print("Testing hybrid_search import...")
try:
    from rag_support import hybrid_search
    print("  SUCCESS: Imported hybrid_search from rag_support package")
except ImportError as e:
    print(f"  ERROR: Failed to import hybrid_search: {e}")
    sys.exit(1)

# Check if hybrid_search is initialized
print("\nChecking hybrid_search object...")
if hybrid_search is not None:
    print("  SUCCESS: hybrid_search object exists")
else:
    print("  ERROR: hybrid_search object is None")
    sys.exit(1)

# Test getting an embedding
print("\nTesting embedding generation...")
try:
    test_text = "This is a test sentence for embedding generation."
    embedding = hybrid_search.get_embedding(test_text)
    
    if embedding is not None:
        print(f"  SUCCESS: Generated embedding with shape {embedding.shape}")
    else:
        print("  WARNING: Embedding is None, could not generate embedding")
        print("  Attempting to create a test project and document...")
except Exception as e:
    print(f"  ERROR: Failed to generate embedding: {e}")
    
# Test simple project creation and document search
print("\nTesting simple project functions...")
try:
    from rag_support.utils.project_manager import project_manager
    
    # Create test project if needed
    test_project_id = "test_hybrid_search"
    test_project = project_manager.get_project(test_project_id)
    
    if not test_project:
        print("  Creating test project...")
        project_manager.create_project("Test Hybrid Search", "Project for testing hybrid search")
        test_project = project_manager.get_project(test_project_id)
        
    if test_project:
        print(f"  SUCCESS: Test project available: {test_project.get('name')}")
        
        # Check if there are documents
        docs = project_manager.list_documents(test_project_id)
        if not docs:
            print("  No documents found, creating a test document...")
            doc_id = project_manager.add_document(
                test_project_id, 
                "Test Document", 
                "This is a test document for hybrid search. It contains information about machine learning and embeddings."
            )
            if doc_id:
                print(f"  SUCCESS: Created test document with ID: {doc_id}")
            else:
                print("  ERROR: Failed to create test document")
        else:
            print(f"  SUCCESS: Found {len(docs)} existing documents")
            
        # Test search functionality
        print("\nTesting search functionality...")
        query = "machine learning"
        
        # Try different search methods if available
        if hasattr(hybrid_search, "hybrid_search"):
            print("  Testing hybrid search...")
            try:
                results = hybrid_search.hybrid_search(test_project_id, query)
                print(f"  SUCCESS: Hybrid search returned {len(results)} results")
            except Exception as e:
                print(f"  ERROR: Hybrid search failed: {e}")
                
        if hasattr(hybrid_search, "semantic_search"):
            print("  Testing semantic search...")
            try:
                results = hybrid_search.semantic_search(test_project_id, query)
                print(f"  SUCCESS: Semantic search returned {len(results)} results")
            except Exception as e:
                print(f"  ERROR: Semantic search failed: {e}")
                
    else:
        print("  ERROR: Could not get test project")
except Exception as e:
    print(f"  ERROR: Failed to test project functions: {e}")

print("\nHybrid Search Module Test Complete")