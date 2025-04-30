# Integration Testing Guide

## Overview

This document provides guidance on running and maintaining integration tests for the LLM Platform. Integration tests validate that different components of the system work together correctly, complementing the unit tests that verify individual components in isolation.

## Test Organization

Integration tests are organized into the following categories:

1. **Core-Models Integration** - Tests integration between core infrastructure and model loading/inference
2. **RAG Integration** - Tests integration between document management, search, and context generation
3. **Web-API Integration** - Tests integration between web server, API controllers, and template system
4. **End-to-End Tests** - Tests the complete system flow from model loading to inference and RAG

## Running the Tests

### Prerequisites

- A Python environment with all dependencies installed
- Access to the LLM Platform codebase

### Running All Integration Tests

```bash
cd /Volumes/LLM
python -m unittest discover -s tests/integration
```

### Running Specific Test Categories

```bash
# Run Core-Models integration tests
python -m unittest tests/integration/test_core_models_integration.py

# Run RAG integration tests
python -m unittest tests/integration/test_rag_integration.py

# Run Web-API integration tests
python -m unittest tests/integration/test_web_api_integration.py

# Run End-to-End tests
python -m unittest tests/integration/test_end_to_end.py
```

## Test Structure

Each integration test follows a similar structure:

1. `setUpClass` - Sets up the test environment, including creating temporary directories and mocking external dependencies
2. `tearDownClass` - Cleans up after all tests, including stopping patchers and removing temporary directories
3. `setUp` - Sets up the test environment for each test, creating necessary objects and data
4. `tearDown` - Cleans up after each test, ensuring a clean state for the next test
5. Test methods - One or more methods that test specific integration points

## Mocking Strategy

Integration tests use selective mocking to focus on specific integration points while isolating from external dependencies:

- **Core-Models Integration** - Mocks model loading but tests real file interactions and configurations
- **RAG Integration** - Mocks embedding models but tests real document management and search logic
- **Web-API Integration** - Mocks storage backends but tests real web server and API controllers
- **End-to-End Tests** - Minimal mocking, focusing on end-to-end flows

## Common Patterns

### Testing API Integrations

```python
def test_api_endpoint(self):
    # Make request to API
    response = requests.get(f"{self.base_url}/api/endpoint")
    
    # Check status code
    self.assertEqual(response.status_code, 200)
    
    # Check response format
    data = response.json()
    self.assertEqual(data["status"], "success")
    self.assertEqual(data["data"]["property"], expected_value)
```

### Testing Component Interactions

```python
def test_component_interaction(self):
    # Create input data
    input_data = {"property": "value"}
    
    # Pass data through component chain
    result1 = component1.process(input_data)
    result2 = component2.process(result1)
    
    # Verify final output
    self.assertEqual(result2["output_property"], expected_value)
```

## Extending the Tests

When adding new features or components to the system, follow these steps to update the integration tests:

1. Identify the appropriate test category (core-models, rag, web-api, end-to-end)
2. Add new test methods to the existing test classes or create new test classes if needed
3. Ensure that new tests follow the same patterns and mocking strategy as existing tests
4. Verify that all integration points are covered by tests

## Best Practices

1. **Use temporary directories** - All tests should create and use temporary directories to avoid interfering with the real system
2. **Clean up after tests** - Always clean up resources created during tests, especially temporary files and directories
3. **Mock external dependencies** - Use mocking to isolate from external dependencies and focus on specific integration points
4. **Test realistic scenarios** - Design tests to mimic real-world usage of the system
5. **Test error handling** - Include tests for error conditions and ensure proper error propagation
6. **Avoid testing implementation details** - Focus on the behavior of component interactions, not internal implementation
7. **Maintain independence** - Tests should not depend on each other or on external state

## Common Issues and Solutions

1. **Tests fail intermittently** - Check for race conditions or timing issues in the tests
2. **Tests leave behind temporary files** - Ensure proper cleanup in tearDown and tearDownClass methods
3. **Tests interfere with each other** - Check for shared state or resources between tests
4. **Tests are slow** - Consider further mocking or focusing on smaller integration points
5. **Tests require external dependencies** - Use mocking to remove external dependencies