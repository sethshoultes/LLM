#!/usr/bin/env python3
"""
Integration tests for the RAG (Retrieval-Augmented Generation) system.

This script tests the integration between various RAG components:
- Document management
- Storage backends
- Indexing and search
- Project management
"""

import os
import sys
import json
import shutil
import uuid
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Create test directory
TEST_DIR = Path(__file__).resolve().parent / "test_data" / "integration"
TEST_DIR.mkdir(exist_ok=True, parents=True)

# Import RAG components
try:
    from rag.documents import Document, DocumentCollection
    from rag.storage import FileSystemStorage, MemoryStorage
    from rag.parser import MarkdownParser, TextParser
    from rag.indexer import TfidfIndex
    from rag.search import SearchEngine
    from rag_support.utils.project_manager_refactored import ProjectManager
except ImportError as e:
    print(f"Error importing RAG components: {e}")
    sys.exit(1)

def setup():
    """Set up the test environment."""
    print("\n=== Setting up integration test environment ===")
    
    # Clean up any existing test data
    if TEST_DIR.exists():
        for item in TEST_DIR.glob("*"):
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
    
    print(f"Integration test directory: {TEST_DIR}")


def test_document_creation_and_storage():
    """Test document creation and storage."""
    print("\n=== Testing Document Creation and Storage ===")
    
    # Create documents
    documents = []
    for i in range(3):
        doc = Document.create(
            title=f"Test Document {i+1}",
            content=f"This is test document {i+1} for the integration test. It contains some unique words like {uuid.uuid4()} to test search functionality.",
            tags=["test", f"tag{i+1}"]
        )
        documents.append(doc)
        print(f"Created document: {doc}")
    
    # Create a document collection
    collection = DocumentCollection()
    for doc in documents:
        collection.add(doc)
    
    print(f"Document collection size: {len(collection)}")
    
    # Test file system storage
    fs_storage = FileSystemStorage(TEST_DIR / "documents")
    for doc in documents:
        fs_storage.save_document(doc)
    
    # Test memory storage
    mem_storage = MemoryStorage()
    for doc in documents:
        mem_storage.save_document(doc)
    
    # Verify storage
    fs_docs = fs_storage.list_documents()
    mem_docs = mem_storage.list_documents()
    
    print(f"FileSystemStorage document count: {len(fs_docs)}")
    print(f"MemoryStorage document count: {len(mem_docs)}")
    
    return documents, collection, fs_storage, mem_storage


def test_indexing_and_search(documents, collection, storage):
    """Test indexing and search."""
    print("\n=== Testing Indexing and Search Integration ===")
    
    # Create index
    index = TfidfIndex()
    
    # Index documents
    for doc in documents:
        index.add_document(doc)
    
    print(f"Indexed {len(documents)} documents")
    
    # Create search engine
    search_engine = SearchEngine(index=index, storage=storage)
    
    # Test search
    search_results = search_engine.search("test document")
    
    print(f"Search results for 'test document': {len(search_results)}")
    for i, result in enumerate(search_results[:2]):  # Show top 2 results
        print(f"  Result {i+1}: {result.document.title} (score: {result.score:.4f})")
    
    # Test search with tags
    tagged_docs = collection.filter_by_tags(["tag1"])
    print(f"Documents with tag 'tag1': {len(tagged_docs)}")
    
    return search_engine


def test_project_manager_integration(documents):
    """Test project manager integration with RAG components."""
    print("\n=== Testing Project Manager Integration ===")
    
    # Override PROJECTS_DIR in the project_manager module
    import rag_support.utils.project_manager_refactored as pm
    test_projects_dir = TEST_DIR / "projects"
    test_projects_dir.mkdir(exist_ok=True)
    pm.PROJECTS_DIR = test_projects_dir
    
    # Create a project manager
    manager = ProjectManager()
    
    # Create a project
    project_id = manager.create_project(
        name="Integration Test Project",
        description="A project for testing RAG integration"
    )
    
    print(f"Created project with ID: {project_id}")
    
    # Add documents using both approaches
    
    # 1. Using the built-in add_document method
    doc1_id = manager.add_document(
        project_id=project_id,
        title="PM Test Document 1",
        content="This is a test document added through the project manager.",
        tags=["test", "pm"]
    )
    
    print(f"Added document through PM with ID: {doc1_id}")
    
    # 2. Using raw Document objects through the storage backend
    storage = manager.get_storage(project_id)
    doc2 = documents[0]  # Reuse an existing document
    storage.save_document(doc2)
    
    print(f"Added document through storage with ID: {doc2.id}")
    
    # Test search through project manager
    search_results = manager.search_documents(
        project_id=project_id,
        query="test"
    )
    
    print(f"PM search results for 'test': {len(search_results)}")
    
    # Test search engine directly
    search_engine = manager.get_search_engine(project_id)
    direct_results = search_engine.search("test")
    
    print(f"Direct search results for 'test': {len(direct_results)}")
    
    return manager, project_id


def test_end_to_end_workflow():
    """Test an end-to-end RAG workflow."""
    print("\n=== Testing End-to-End RAG Workflow ===")
    
    # Create a project manager
    import rag_support.utils.project_manager_refactored as pm
    test_projects_dir = TEST_DIR / "workflow"
    test_projects_dir.mkdir(exist_ok=True)
    pm.PROJECTS_DIR = test_projects_dir
    
    manager = ProjectManager()
    
    # 1. Create a project
    project_id = manager.create_project("Workflow Test", "End-to-end workflow test")
    
    # 2. Add multiple documents
    doc_ids = []
    for i in range(5):
        doc_id = manager.add_document(
            project_id=project_id,
            title=f"Workflow Document {i+1}",
            content=f"This is document {i+1} in the workflow test. It contains specific information about topic {i+1}.",
            tags=["workflow", f"topic{i+1}"]
        )
        doc_ids.append(doc_id)
    
    print(f"Added {len(doc_ids)} documents to the project")
    
    # 3. Create a chat
    chat_id = manager.add_chat(project_id, "Workflow Chat")
    
    # 4. Simulate search and context selection
    search_results = manager.search_documents(project_id, "topic 3")
    selected_doc_ids = [result["id"] for result in search_results[:2]]
    
    print(f"Selected context documents: {selected_doc_ids}")
    
    # 5. Add a message with context
    manager.add_message(
        project_id=project_id,
        chat_id=chat_id,
        role="user",
        content="Can you tell me about topic 3?",
        context_docs=selected_doc_ids
    )
    
    # 6. Add a response
    manager.add_message(
        project_id=project_id,
        chat_id=chat_id,
        role="assistant",
        content="Topic 3 is covered in the documents you provided. It contains specific information as described in the documents."
    )
    
    # 7. Generate an artifact
    artifact_id = manager.save_artifact(
        project_id=project_id,
        content="# Summary of Topic 3\n\nThis document contains a summary of information found in the context documents about topic 3.",
        title="Topic 3 Summary",
        file_ext="md"
    )
    
    print(f"Saved artifact with ID: {artifact_id}")
    
    # 8. Retrieve chat with messages
    chat = manager.get_chat(project_id, chat_id)
    
    print(f"Chat message count: {len(chat['messages'])}")
    print(f"Context documents in first message: {chat['messages'][0].get('context_docs', [])}")
    
    return manager, project_id, chat_id, artifact_id


def cleanup():
    """Clean up test data."""
    print("\n=== Cleaning up ===")
    
    if TEST_DIR.exists():
        shutil.rmtree(TEST_DIR)
        print(f"Removed test directory: {TEST_DIR}")


def run_tests():
    """Run all integration tests."""
    try:
        print("Starting RAG integration tests...")
        
        # Set up test environment
        setup()
        
        # Run tests
        documents, collection, fs_storage, mem_storage = test_document_creation_and_storage()
        search_engine = test_indexing_and_search(documents, collection, fs_storage)
        manager, project_id = test_project_manager_integration(documents)
        workflow_manager, workflow_project, chat_id, artifact_id = test_end_to_end_workflow()
        
        # Clean up
        cleanup()
        
        print("\n✅ All integration tests completed successfully!")
        return 0
    except Exception as e:
        print(f"\n❌ Integration tests failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(run_tests())