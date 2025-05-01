# Developer Guide

## Introduction

This guide is designed to help developers work with the LLM Platform codebase. It covers the development environment setup, coding conventions, testing procedures, and guidelines for extending the platform.

## Development Environment Setup

### Prerequisites

- Python 3.9 or higher
- Git
- pip

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd llm-platform
   ```

2. Create and activate a virtual environment:
   ```bash
   # Option 1: Using venv
   python -m venv env
   source env/bin/activate  # On Windows: env\Scripts\activate

   # Option 2: Using the provided script
   source LLM-MODELS/tools/scripts/activate_mac.sh  # On macOS
   source LLM-MODELS/tools/scripts/activate_pi.sh   # On Raspberry Pi
   ```

3. Install dependencies:
   ```bash
   pip install -r config/requirements.txt
   ```

### Environment Configuration

1. Configure the environment by creating a `config.json` file in the config directory or by setting environment variables. The platform will look for configuration in the following order:
   - Environment variables
   - `config.json` file
   - Default values

2. Sample configuration:
   ```json
   {
     "paths": {
       "models_dir": "/path/to/models",
       "logs_dir": "/path/to/logs",
       "projects_dir": "/path/to/projects"
     },
     "models": {
       "default": "llama-7b",
       "preload": []
     },
     "server": {
       "host": "localhost",
       "port": 5100,
       "open_browser": true
     }
   }
   ```

## Running the Platform

### Start the Server

```bash
# Start in normal mode
./llm.sh

# Start in quiet mode (minimal interface)
./llm.sh quiet
```

### Test Model Loading

```bash
python scripts/minimal_inference_quiet.py /path/to/model
```

### Test the Interface

```bash
python scripts/quiet_interface.py
```

## Project Structure

The LLM Platform follows a modular structure organized by functionality:

```
/Volumes/LLM/
├── CLAUDE.md             # Claude-specific instructions
├── config/               # Configuration files
│   └── requirements.txt  # Python dependencies
├── core/                 # Core infrastructure
│   ├── paths.py          # Path resolution
│   ├── config.py         # Configuration management
│   ├── logging.py        # Logging utilities
│   ├── errors.py         # Error handling
│   └── utils.py          # Common utilities
├── models/               # Model management
│   ├── registry.py       # Model registration
│   ├── loader.py         # Model loading
│   ├── generation.py     # Text generation
│   ├── formatter.py      # Prompt formatting
│   └── caching.py        # Model caching
├── rag/                  # RAG system
│   ├── documents.py      # Document representation
│   ├── storage.py        # Storage backends
│   ├── parser.py         # Document parsing
│   ├── indexer.py        # Document indexing
│   └── search.py         # Search functionality
├── rag_support/          # Support for RAG
│   ├── utils/            # Utility functions
│   ├── templates/        # UI templates
│   └── projects/         # Project storage
├── web/                  # Web interface
│   ├── server.py         # HTTP server
│   ├── router.py         # Request routing
│   ├── middleware.py     # Request middleware
│   ├── handlers_new.py   # Request handlers
│   ├── api/              # API implementation
│   └── templates/        # Template system
├── scripts/              # Utility scripts
├── templates/            # Web templates
├── tests/                # Test suite
│   ├── unit/             # Unit tests
│   └── integration/      # Integration tests
├── docs/                 # Documentation
└── llm.sh                # Main entry script
```

## Coding Conventions

### Style Guide

The LLM Platform follows PEP 8 for Python code style:

- **Indentation**: 4 spaces (no tabs)
- **Line Length**: Max 100 characters
- **Naming**:
  - Classes: `CamelCase`
  - Functions/Variables: `snake_case`
  - Constants: `ALL_CAPS`
- **Comments**: Use docstrings for all modules, classes, and functions

### Import Order

Follow this order for imports:
1. Standard library imports
2. Third-party library imports
3. Local application imports

Example:
```python
import os
import json
from typing import Dict, Any

import numpy as np
from flask import Flask

from core.config import get_config
from models.loader import load_model
```

### Error Handling

- Use specific exception types rather than catching all exceptions
- Include useful error messages
- Log exceptions with appropriate level
- Always clean up resources in finally blocks

Example:
```python
try:
    result = process_data(data)
except ValueError as e:
    logger.error(f"Invalid data format: {e}")
    raise InvalidDataError(f"Could not process data: {e}") from e
except IOError as e:
    logger.error(f"IO error processing data: {e}")
    raise ProcessingError(f"IO error: {e}") from e
finally:
    cleanup_resources()
```

### Documentation

- All modules should have a module-level docstring
- All classes and functions should have docstrings
- Use Google style docstrings:

```python
def function(arg1, arg2):
    """Description of function.
    
    Args:
        arg1: Description of arg1
        arg2: Description of arg2
        
    Returns:
        Description of return value
        
    Raises:
        ErrorType: When and why this error is raised
    """
    # Function body
```

## Testing

### Running Tests

```bash
# Run all tests
python -m unittest discover

# Run unit tests
python -m unittest discover -s tests/unit

# Run integration tests
python -m unittest discover -s tests/integration

# Run a specific test file
python -m unittest tests/unit/test_module.py
```

### Writing Tests

- All new code should have corresponding unit tests
- Follow the existing test patterns
- Use mocking to isolate units being tested
- Ensure tests are independent and don't rely on external state

Example:
```python
class TestModule(unittest.TestCase):
    def setUp(self):
        # Set up test environment
        self.test_data = [...]
        
    def tearDown(self):
        # Clean up test environment
        pass
        
    def test_functionality(self):
        # Test a specific functionality
        result = module.function(self.test_data)
        self.assertEqual(result, expected_result)
        
    @patch('module.dependency')
    def test_with_mock(self, mock_dependency):
        # Test using a mock
        mock_dependency.return_value = 'mock value'
        result = module.function_using_dependency()
        self.assertEqual(result, 'expected with mock value')
        mock_dependency.assert_called_once()
```

## Extending the Platform

### Adding a New Model Type

1. Create a loader for the new model type in `models/loader.py`:
   ```python
   def _load_new_model_type(model_path, **kwargs):
       # Load model implementation
       return model
   ```

2. Update the model loading function to use the new loader:
   ```python
   def load_model(model_id, **kwargs):
       # Get model info
       model_info = get_model_info(model_id)
       model_type = model_info.get("type")
       
       # Load based on type
       if model_type == "new_model_type":
           return _load_new_model_type(model_info["path"], **kwargs)
       # ... existing model types ...
   ```

3. Add a formatter for the new model type in `models/formatter.py`

### Adding a New Search Method

1. Create a new search implementation in `rag/search.py`:
   ```python
   def new_search_method(project_id, query, **kwargs):
       # Implement search logic
       return results
   ```

2. Update the search function to use the new method:
   ```python
   def search(project_id, query, method="default", **kwargs):
       if method == "new_method":
           return new_search_method(project_id, query, **kwargs)
       # ... existing methods ...
   ```

### Adding a New API Endpoint

1. Create a new controller method in the appropriate controller:
   ```python
   def new_endpoint(self, param1, param2):
       # Implement business logic
       return result
   ```

2. Add a new route in the appropriate routes file:
   ```python
   @router.get("/api/new-endpoint")
   def new_endpoint(request, response):
       param1 = request.query_params.get("param1")
       param2 = request.query_params.get("param2")
       result = controller.new_endpoint(param1, param2)
       response.json(result)
   ```

3. Add validation if needed:
   ```python
   class NewEndpointSchema(BaseModel):
       param1: str
       param2: int
   ```

## Troubleshooting

### Common Issues

#### Model Loading Errors

- Check that the model path is correct
- Ensure the model format is supported
- Verify that dependencies for that model type are installed

#### Server Startup Issues

- Check if the port is already in use
- Verify that the configuration file is valid
- Check permissions for log and model directories

#### RAG System Errors

- Ensure the projects directory exists and is writable
- Check that the search index is properly initialized
- Verify that document formats are supported

### Logging

The platform uses a structured logging system. Logs are written to the console and to log files in the configured log directory.

To adjust the log level, modify the configuration:
```json
{
  "logging": {
    "level": "DEBUG",
    "file": "llm-platform.log"
  }
}
```

## Contributing

### Pull Request Process

1. Ensure all tests pass before submitting
2. Update documentation for any changed functionality
3. Add tests for new functionality
4. Follow the coding conventions
5. Get review from at least one other developer

### Code Review Checklist

- Does the code follow style guidelines?
- Are there appropriate tests?
- Is the documentation updated?
- Are error cases handled properly?
- Is the code efficient and maintainable?
- Are there any security concerns?

## Security Considerations

- Never commit secret keys or credentials
- Validate all user inputs
- Use proper permissions for file operations
- Be careful with dynamic code evaluation
- Follow security best practices for web services

## Performance Tips

- Use caching where appropriate
- Be mindful of memory usage, especially with large models
- Use asynchronous processing for long-running tasks
- Profile performance bottlenecks
- Consider quantizing models for faster inference

## Additional Resources

- Python Documentation: https://docs.python.org/
- Flask Documentation: https://flask.palletsprojects.com/
- Jinja2 Documentation: https://jinja.palletsprojects.com/
- HuggingFace Transformers: https://huggingface.co/docs/transformers/
- LLaMA.cpp Documentation: https://github.com/ggerganov/llama.cpp