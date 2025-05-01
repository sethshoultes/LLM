#!/usr/bin/env python3
"""
Test the RAG context integration to verify our fixes.
This script tests if context is properly incorporated into prompts.
"""

import sys
import os
from pathlib import Path

# Add the parent directory to the path
parent_dir = Path(__file__).resolve().parent.parent
if str(parent_dir) not in sys.path:
    sys.path.append(str(parent_dir))

# Imports for testing
from rag_support.utils.project_manager import project_manager
from rag_support.utils.hybrid_search import hybrid_search
from rag_support.api_extensions import api_handler
from rag.context import context_manager

# Test importing context modules
print("Step 1: Testing module imports")
print(f"  - Project manager imported: {project_manager is not None}")
print(f"  - Hybrid search imported: {hybrid_search is not None}")
print(f"  - Context manager imported: {context_manager is not None}")
print(f"  - API handler imported: {api_handler is not None}")
print()

# Create test project if it doesn't exist
print("Step 2: Creating test project and document")
project_name = "Test RAG Context"
test_content = """Seth Shoultes is a founder of Event Espresso. 
Seth is not a musician but a software developer that works at Caseproof."""

projects = project_manager.get_projects()
test_project = None

for project in projects:
    if project.get('name') == project_name:
        test_project = project
        print(f"  - Found existing test project: {project['id']}")
        break

if not test_project:
    project_id = project_manager.create_project(project_name, "For testing RAG context integration")
    test_project = project_manager.get_project(project_id)
    print(f"  - Created new test project: {project_id}")

# Add test document if not already present
documents = project_manager.list_documents(test_project['id'])
test_doc_id = None
test_doc_title = "Seth Shoultes Info"

for doc in documents:
    if doc.get('title') == test_doc_title:
        test_doc_id = doc['id']
        print(f"  - Found existing test document: {test_doc_id}")
        break

if not test_doc_id:
    test_doc_id = project_manager.add_document(test_project['id'], test_doc_title, test_content)
    print(f"  - Created new test document: {test_doc_id}")
print()

# Test hybrid search
print("Step 3: Testing hybrid search")
if hybrid_search:
    print("  - Testing embedding generation")
    embedding = hybrid_search.get_embedding("Seth Shoultes")
    if embedding is not None:
        print(f"  - Successfully generated embedding with shape: {embedding.shape}")
    else:
        print("  - Failed to generate embedding")
        
    # Test search
    print("  - Testing search functionality")
    query = "Seth Shoultes"
    try:
        # Try semantic search
        if hasattr(hybrid_search, "semantic_search"):
            semantic_results = hybrid_search.semantic_search(test_project['id'], query)
            print(f"  - Semantic search returned {len(semantic_results)} results")
            
        # Try hybrid search
        hybrid_results = hybrid_search.hybrid_search(test_project['id'], query)
        print(f"  - Hybrid search returned {len(hybrid_results)} results")
        
        if hybrid_results:
            print(f"    Top result score: {hybrid_results[0].get('score', 0)}")
            print(f"    Top result title: {hybrid_results[0].get('title', 'Unknown')}")
    except Exception as e:
        print(f"  - Search error: {e}")
else:
    print("  - Hybrid search module not available")
print()

# Test context generation
print("Step 4: Testing context generation")
try:
    # Get the test document
    doc = project_manager.get_document(test_project['id'], test_doc_id)
    
    if doc:
        # Prepare message history
        messages = [{"role": "user", "content": "What does Seth Shoultes do?"}]
        
        # Test context integration
        system_prompt, context_info = context_manager.prepare_context_for_prompt(
            documents=[doc],
            query="What does Seth Shoultes do?",
            system_message="You are a helpful assistant.",
            messages=messages,
        )
        
        print(f"  - Context info: {len(context_info)} documents used")
        print(f"  - System prompt length: {len(system_prompt)} characters")
        print(f"  - System prompt sample: {system_prompt[:100]}...")
        
        # Check if context is included
        if "Seth Shoultes" in system_prompt and "Event Espresso" in system_prompt:
            print("  - SUCCESS: Context is correctly included in the system prompt")
        else:
            print("  - ERROR: Context is missing from the system prompt")
    else:
        print("  - ERROR: Could not retrieve test document")
except Exception as e:
    print(f"  - Context generation error: {e}")
print()

# Test minimal_inference prompt construction
print("Step 5: Testing minimal_inference prompt format")
try:
    from scripts.minimal_inference_quiet import model_manager
    
    # Test Mistral model prompt format
    user_prompt = "What does Seth Shoultes do?"
    
    # Create a simulated system prompt with context
    test_system_prompt = "You are a helpful assistant.\n\nUse the following information:\n\n## Seth Shoultes Info\n\nSeth Shoultes is a founder of Event Espresso. Seth is not a musician but a software developer that works at Caseproof."
    
    # Test for "mistral" model path
    mistral_path = "LLM-MODELS/quantized/gguf/mistral-7b-instruct-v0.2.Q4_K_M.gguf"
    
    # Format the prompt manually to see what it would look like
    if "mistral" in mistral_path.lower():
        formatted_prompt = f"<s>[INST] {test_system_prompt}\n\n{user_prompt} [/INST]"
        print(f"  - Mistral formatted prompt: {formatted_prompt[:100]}...")
    else:
        print("  - No Mistral model path found for testing")
        
    # Test conversation history formatting
    messages = [
        {"role": "user", "content": "What does Seth Shoultes do?"}
    ]
    
    formatted_history = model_manager.format_conversation_history(
        messages, 
        system_prompt=test_system_prompt,
        model_path=mistral_path
    )
    
    print(f"  - Formatted conversation history: {formatted_history[:100]}...")
    
    # Check for key components
    if "<s>" in formatted_history and "Event Espresso" in formatted_history:
        print("  - SUCCESS: Conversation history contains properly formatted prompt with context")
    else:
        print("  - ERROR: Conversation history is missing expected components")
        
except ImportError:
    print("  - Could not import minimal_inference_quiet for testing")
except Exception as e:
    print(f"  - Error testing minimal_inference: {e}")
    
print("\nRAG Context Integration Test Complete")