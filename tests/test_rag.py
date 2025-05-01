#!/usr/bin/env python3
"""
Test script for the RAG system components.

This script tests the core functionality of the RAG system:
- Document creation and management
- Storage backends
- Document parsing
- Indexing and search
"""

import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import RAG components
try:
    from rag.documents import Document, DocumentCollection
    from rag.indexer import InvertedIndex, TfidfIndex
except ImportError as e:
    print(f"Error importing RAG components: {e}")
    sys.exit(1)

# Create test directory
TEST_DIR = Path(__file__).resolve().parent / "test_data"
TEST_DIR.mkdir(exist_ok=True)

def test_document_creation():
    """Test document creation and manipulation."""
    print("\n=== Testing Document Creation ===")
    
    # Create a document
    doc = Document.create(
        title="Test Document",
        content="This is a test document with some content for searching.",
        tags=["test", "document", "rag"]
    )
    
    print(f"Created document: {doc}")
    print(f"Document ID: {doc.id}")
    print(f"Document title: {doc.title}")
    print(f"Document preview: {doc.get_preview(50)}")
    print(f"Document token count: {doc.get_token_count()}")
    
    # Update document
    doc.update(
        content="Updated content for the test document.",
        tags=["test", "updated"]
    )
    
    print(f"Updated document: {doc}")
    print(f"Updated tags: {doc.tags}")
    
    # Test document conversion
    doc_dict = doc.to_dict()
    print(f"Document as dict: {json.dumps(doc_dict, indent=2)[:100]}...")
    
    # Test document frontmatter
    doc_frontmatter = doc.to_frontmatter()
    print(f"Document with frontmatter: {doc_frontmatter[:100]}...")
    
    return doc

def test_document_collection(doc):
    """Test document collection functionality."""
    print("\n=== Testing Document Collection ===")
    
    # Create a collection
    collection = DocumentCollection()
    
    # Add the document
    collection.add(doc)
    
    # Create additional documents
    for i in range(3):
        new_doc = Document.create(
            title=f"Sample Document {i+1}",
            content=f"This is sample document {i+1} with different content for search testing.",
            tags=["sample", f"doc{i+1}"]
        )
        collection.add(new_doc)
    
    print(f"Collection size: {len(collection)}")
    
    # Test search
    search_results = collection.search("sample")
    print(f"Search results for 'sample': {len(search_results)} documents")
    for doc in search_results:
        print(f"  - {doc.title}")
    
    # Test filtering by tags
    tag_results = collection.filter_by_tags(["sample"])
    print(f"Documents with tag 'sample': {len(tag_results)}")
    
    return collection

def test_storage_backends(doc, collection):
    """Test storage backends."""
    print("\n=== Testing Storage Backends ===")
    
    # Test memory storage
    memory_storage = MemoryStorage()
    memory_storage.save_document(doc)
    
    retrieved_doc = memory_storage.get_document(doc.id)
    print(f"Retrieved document from memory: {retrieved_doc.title}")
    
    # Test file system storage
    fs_storage = FileSystemStorage(TEST_DIR)
    fs_storage.save_document(doc)
    
    file_path = TEST_DIR / f"{doc.id}.md"
    print(f"Document saved to file: {file_path}")
    print(f"File exists: {file_path.exists()}")
    
    # Save all documents in collection
    for doc in collection.list_all():
        fs_storage.save_document(doc)
    
    # List documents
    docs = fs_storage.list_documents()
    print(f"Documents in storage: {len(docs)}")
    for doc_meta in docs[:2]:  # Show first 2
        print(f"  - {doc_meta['title']}")
    
    # Search documents
    search_results = fs_storage.search_documents("sample")
    print(f"Search results for 'sample': {len(search_results)} documents")
    
    return fs_storage

def test_indexing_and_search(collection):
    """Test document indexing and search."""
    print("\n=== Testing Indexing and Search ===")
    
    # Create an index
    index = InvertedIndex()
    
    # Index the collection
    index.index_collection(collection)
    
    # Get index stats
    stats = index.get_stats()
    print(f"Index stats: {stats}")
    
    # Search the index
    search_results = index.search("test")
    print(f"Search results for 'test': {len(search_results)} documents")
    for doc_id, score in search_results:
        print(f"  - Document {doc_id}: score {score:.4f}")
    
    # Test TfidfIndex
    tfidf_index = TfidfIndex()
    tfidf_index.index_collection(collection)
    
    # Search with TF-IDF
    tfidf_results = tfidf_index.search("sample")
    print(f"TF-IDF search results for 'sample':")
    for doc_id, score in tfidf_results.items():
        print(f"  - Document {doc_id}: score {score:.4f}")
    
    # Test search engine
    search_engine = SearchEngine(index=tfidf_index)
    engine_results = search_engine.search("document test", max_results=3)
    print(f"Search engine results for 'document test':")
    for result in engine_results:
        print(f"  - {result.document.title}: {result.score:.4f}")
    
    return search_engine

def test_parsers():
    """Test document parsers."""
    print("\n=== Testing Document Parsers ===")
    
    # Test markdown parser
    md_content = """---
title: Test Markdown
tags: [markdown, test]
---

# Heading

This is a markdown document.
"""
    md_parser = MarkdownParser()
    md_meta, md_text = md_parser.parse(md_content)
    print(f"Markdown metadata: {md_meta}")
    print(f"Markdown content: {md_text[:50]}...")
    
    # Test text parser
    text_content = "This is a plain text document.\nIt has multiple lines."
    text_parser = TextParser()
    text_meta, text_text = text_parser.parse(text_content)
    print(f"Text metadata: {text_meta}")
    print(f"Text content: {text_text}")
    
    # Test HTML parser
    html_content = """<!DOCTYPE html>
<html>
<head>
    <title>Test HTML</title>
    <meta name="author" content="Test User">
</head>
<body>
    <h1>Heading</h1>
    <p>This is an HTML document.</p>
</body>
</html>"""
    html_parser = HTMLParser()
    html_meta, html_text = html_parser.parse(html_content)
    print(f"HTML metadata: {html_meta}")
    print(f"HTML content: {html_text[:50]}...")

def cleanup():
    """Clean up test data."""
    print("\n=== Cleaning up ===")
    
    # Remove test files
    for file_path in TEST_DIR.glob("*.md"):
        file_path.unlink()
    
    print(f"Removed {len(list(TEST_DIR.glob('*')))} test files")

def run_tests():
    """Run all tests."""
    try:
        print("Starting RAG system tests...")
        
        # Run tests
        doc = test_document_creation()
        collection = test_document_collection(doc)
        storage = test_storage_backends(doc, collection)
        search_engine = test_indexing_and_search(collection)
        test_parsers()
        
        # Clean up
        cleanup()
        
        print("\n✅ All tests completed successfully!")
        return 0
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(run_tests())