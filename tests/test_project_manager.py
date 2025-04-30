#!/usr/bin/env python3
"""
Test script for the refactored ProjectManager.

This script tests the integration between the refactored ProjectManager
and the new RAG system components.
"""

import os
import sys
import time
import json
import shutil
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Create a test projects directory
TEST_PROJECTS_DIR = Path(__file__).resolve().parent / "test_data" / "projects"
TEST_PROJECTS_DIR.mkdir(exist_ok=True, parents=True)

# Override PROJECTS_DIR in the project_manager module
import rag_support.utils.project_manager_refactored as pm
pm.PROJECTS_DIR = TEST_PROJECTS_DIR

# Import the refactored project manager
from rag_support.utils.project_manager_refactored import ProjectManager

def setup():
    """Set up the test environment."""
    print("\n=== Setting up test environment ===")
    
    # Clean up any existing test data
    if TEST_PROJECTS_DIR.exists():
        for item in TEST_PROJECTS_DIR.glob("*"):
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
    
    print(f"Test projects directory: {TEST_PROJECTS_DIR}")


def test_project_creation():
    """Test creating and managing projects."""
    print("\n=== Testing Project Creation ===")
    
    # Create a project manager
    manager = ProjectManager()
    
    # Create a test project
    project_id = manager.create_project(
        name="Test Project",
        description="A test project for the refactored ProjectManager"
    )
    
    print(f"Created project with ID: {project_id}")
    
    # Get all projects
    projects = manager.get_projects()
    
    print(f"Number of projects: {len(projects)}")
    print(f"Project name: {projects[0]['name']}")
    print(f"Project description: {projects[0]['description']}")
    
    # Update the project
    manager.update_project(
        project_id=project_id,
        name="Updated Test Project",
        description="An updated test project"
    )
    
    # Get the updated project
    project = manager.get_project(project_id)
    
    print(f"Updated project name: {project['name']}")
    print(f"Updated project description: {project['description']}")
    
    return project_id, manager


def test_document_operations(project_id, manager):
    """Test document operations."""
    print("\n=== Testing Document Operations ===")
    
    # Add documents to the project
    doc_ids = []
    
    for i in range(3):
        doc_id = manager.add_document(
            project_id=project_id,
            title=f"Test Document {i+1}",
            content=f"This is test document {i+1} for the refactored ProjectManager.",
            tags=[f"tag{i+1}", "test"]
        )
        
        doc_ids.append(doc_id)
        print(f"Added document {i+1} with ID: {doc_id}")
    
    # List all documents
    documents = manager.list_documents(project_id)
    
    print(f"Number of documents: {len(documents)}")
    
    # Get a specific document
    document = manager.get_document(project_id, doc_ids[0])
    
    print(f"Document title: {document['title']}")
    print(f"Document content: {document['content']}")
    print(f"Document tags: {document['tags']}")
    
    # Update a document
    manager.update_document(
        project_id=project_id,
        doc_id=doc_ids[0],
        title="Updated Test Document",
        content="This document has been updated.",
        tags=["updated", "test"]
    )
    
    # Get the updated document
    updated_doc = manager.get_document(project_id, doc_ids[0])
    
    print(f"Updated document title: {updated_doc['title']}")
    print(f"Updated document content: {updated_doc['content']}")
    print(f"Updated document tags: {updated_doc['tags']}")
    
    return doc_ids


def test_search_functionality(project_id, manager, doc_ids):
    """Test search functionality."""
    print("\n=== Testing Search Functionality ===")
    
    # Search for documents
    search_results = manager.search_documents(project_id, "updated")
    
    print(f"Number of search results for 'updated': {len(search_results)}")
    
    if search_results:
        print(f"First result title: {search_results[0]['title']}")
        print(f"First result score: {search_results[0]['score']}")
    
    # Search with tags
    tag_results = manager.search_documents(project_id, "", tags=["test"])
    
    print(f"Number of results with tag 'test': {len(tag_results)}")
    
    # Test search with both query and tags
    combined_results = manager.search_documents(project_id, "test", tags=["test"])
    
    print(f"Number of results with query 'test' and tag 'test': {len(combined_results)}")
    
    return search_results


def test_chat_operations(project_id, manager, doc_ids):
    """Test chat operations."""
    print("\n=== Testing Chat Operations ===")
    
    # Create a chat
    chat_id = manager.add_chat(project_id, "Test Chat")
    
    print(f"Created chat with ID: {chat_id}")
    
    # Add messages with document context
    manager.add_message(
        project_id=project_id,
        chat_id=chat_id,
        role="user",
        content="Hello, can you tell me about the test documents?",
        context_docs=[doc_ids[0], doc_ids[1]]
    )
    
    manager.add_message(
        project_id=project_id,
        chat_id=chat_id,
        role="assistant",
        content="I can see you have some test documents. One has been updated."
    )
    
    # Get the chat
    chat = manager.get_chat(project_id, chat_id)
    
    print(f"Chat title: {chat['title']}")
    print(f"Number of messages: {len(chat['messages'])}")
    print(f"First message: {chat['messages'][0]['content']}")
    print(f"Context documents: {chat['messages'][0].get('context_docs', [])}")
    
    # List all chats
    chats = manager.list_chats(project_id)
    
    print(f"Number of chats: {len(chats)}")
    
    return chat_id


def test_artifact_operations(project_id, manager):
    """Test artifact operations."""
    print("\n=== Testing Artifact Operations ===")
    
    # Save an artifact
    artifact_id = manager.save_artifact(
        project_id=project_id,
        content="# Test Artifact\n\nThis is a test artifact for the refactored ProjectManager.",
        title="Test Artifact",
        file_ext="md"
    )
    
    print(f"Saved artifact with ID: {artifact_id}")
    
    # Get the artifact
    artifact = manager.get_artifact(project_id, artifact_id)
    
    print(f"Artifact title: {artifact['title']}")
    print(f"Artifact content: {artifact['content'][:50]}...")
    
    # List all artifacts
    artifacts = manager.list_artifacts(project_id)
    
    print(f"Number of artifacts: {len(artifacts)}")
    
    return artifact_id


def cleanup(project_id, manager, doc_ids, chat_id, artifact_id):
    """Clean up test data."""
    print("\n=== Cleaning Up ===")
    
    # Delete individual items
    print("Deleting document...")
    manager.delete_document(project_id, doc_ids[0])
    
    print("Deleting chat...")
    manager.delete_chat(project_id, chat_id)
    
    print("Deleting artifact...")
    manager.delete_artifact(project_id, artifact_id)
    
    # Check counts after deletion
    project = manager.get_project(project_id)
    print(f"Document count after deletion: {project['document_count']}")
    print(f"Chat count after deletion: {project['chat_count']}")
    print(f"Artifact count after deletion: {project['artifact_count']}")
    
    # Delete the entire project
    print("Deleting project...")
    manager.delete_project(project_id)
    
    # Verify deletion
    projects = manager.get_projects()
    print(f"Number of projects after deletion: {len(projects)}")


def run_tests():
    """Run all tests."""
    try:
        print("Starting tests for refactored ProjectManager...")
        
        # Set up test environment
        setup()
        
        # Run tests
        project_id, manager = test_project_creation()
        doc_ids = test_document_operations(project_id, manager)
        search_results = test_search_functionality(project_id, manager, doc_ids)
        chat_id = test_chat_operations(project_id, manager, doc_ids)
        artifact_id = test_artifact_operations(project_id, manager)
        
        # Clean up
        cleanup(project_id, manager, doc_ids, chat_id, artifact_id)
        
        print("\n✅ All tests completed successfully!")
        return 0
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(run_tests())