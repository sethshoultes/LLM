# Portable LLM Environment - Developer Guide

## Current Architecture

The portable LLM environment follows a streamlined architecture after recent cleanup efforts. This guide explains the current system design and how to extend it.

### Core Components

1. **Entry Point**: `llm.sh`
   - Main script that activates the Python environment
   - Handles command routing to different interfaces
   - Sets appropriate environment variables

2. **Inference Engine**: `scripts/minimal_inference_quiet.py`
   - Model loading and management system
   - Multi-format support (GGUF, GGML, PyTorch)
   - Text generation with parameter control
   - Conversation history formatting

3. **Web Interface**: `scripts/quiet_interface.py`
   - HTTP server using Python's built-in http.server
   - Static HTML/JS/CSS web interface
   - API endpoints for model listing and text generation
   - Simple browser-based chat UI

4. **Utility Scripts**:
   - `scripts/direct_download.sh`: Downloads models from HuggingFace
   - `scripts/download_sample_models.sh`: Downloads test models

### Current Directory Structure

```
/Volumes/LLM/
  ├── llm.sh                  # Main entry point script
  ├── scripts/                # Core scripts
  │   ├── minimal_inference_quiet.py    # Inference engine
  │   ├── quiet_interface.py            # Primary web interface
  │   ├── direct_download.sh            # Model download utility
  │   ├── download_sample_models.sh     # Sample downloader
  │   ├── simplified_interface.py       # Alternative interface
  │   ├── minimal_interface.py          # Basic interface
  │   └── flask_launch.sh               # Legacy Flask launcher
  ├── LLM-MODELS/             # Model storage
  │   ├── quantized/          # Quantized models
  │   │   ├── gguf/           # GGUF format models
  │   │   ├── ggml/           # GGML format models
  │   │   └── awq/            # AWQ format models (future)
  │   ├── open-source/        # Original models by family
  │   │   ├── llama/
  │   │   ├── mistral/
  │   │   ├── phi/
  │   │   └── mixtral/
  │   ├── embeddings/         # Reserved for embedding models
  │   └── tools/              # Tools and scripts
  │       ├── mac/            # Mac-specific tools
  │       ├── pi/             # Raspberry Pi tools
  │       ├── scripts/        # Environment activation scripts
  │       └── python/         # Python environment and modules
  └── docs/                   # Documentation
      └── updated/            # Current documentation
```

## Development Workflow

### Setting Up Development Environment

1. Clone or access the volume at `/Volumes/LLM`
2. Activate the Python environment:
   ```bash
   source /Volumes/LLM/LLM-MODELS/tools/scripts/activate_mac.sh
   ```
3. Make code changes as needed
4. Test by running:
   ```bash
   cd /Volumes/LLM
   ./llm.sh
   ```

### Key Files for Modification

When extending the system, focus on these files:

| File | Purpose | When to Modify |
|------|---------|----------------|
| `minimal_inference_quiet.py` | Core inference engine | Adding model formats, changing inference behavior |
| `quiet_interface.py` | Web interface and API | UI changes, endpoint modifications |
| `llm.sh` | Main entry point | Adding new commands, changing startup behavior |
| `direct_download.sh` | Model downloader | Changing download sources or methods |

## Adding New Features

### Adding a New Model Format

To add support for a new model format:

1. Modify `minimal_inference_quiet.py`:
   - Add format detection in the `load_model` method
   - Implement format-specific loading logic
   - Add appropriate generation handling

Example:
```python
# For new format models
elif file_ext == '.new_format':
    try:
        # Import relevant library
        import new_format_library
        
        # Load with appropriate parameters
        model = new_format_library.load_model(
            model_path=full_path,
            parameters=settings
        )
        
        self.models[model_path] = {
            "model": model,
            "type": "new_format",
            "model_format": "new_format",
            "loaded_at": time.time()
        }
        
        return True
    except ImportError:
        print("new_format_library not installed.")
        return False
    except Exception as e:
        print(f"Error loading new format model: {e}")
        return False
```

2. Update `generate_text` and `generate_with_history` methods to handle the new format
3. Add prompt formatting appropriate for the model type

### Modifying the Web Interface

To change or extend the web interface:

1. Locate the HTML template in `quiet_interface.py` (HTML_TEMPLATE variable)
2. Make changes to the HTML, CSS, or JavaScript
3. Add any new API endpoints by modifying the `do_GET` and `do_POST` methods in the RequestHandler class

Example of adding a new API endpoint:
```python
elif parsed_path.path == '/api/new_feature':
    self.send_response(200)
    self.send_header('Content-type', 'application/json')
    self.end_headers()
    
    # Implement the new feature
    result = {"success": True, "data": "New feature response"}
    self.wfile.write(json.dumps(result).encode('utf-8'))
```

### Adding Command Line Options

To add new commands to `llm.sh`:

1. Add a new case in the command switch structure:
```bash
"new_command")
    print_banner
    echo -e "Starting new feature..."
    python3 "$DIR/scripts/new_feature_script.py"
    ;;
```

2. Update the help function to document the new command:
```bash
echo -e "  ${GREEN}new_command${NC}  - Description of the new command"
```

## Testing Your Changes

When testing modifications:

1. **Cross-platform Testing**:
   - Test on Mac and Raspberry Pi if possible
   - Check in both high and low memory configurations

2. **Model Format Testing**:
   - Test with GGUF models (most common)
   - Test with other formats if you've modified format handling

3. **Error Handling**:
   - Test with missing dependencies
   - Test with invalid inputs
   - Check for graceful failure modes

4. **Browser Testing**:
   - Test in multiple browsers if you've changed the UI
   - Verify mobile usability

## Dependency Management

The system is designed to minimize dependencies:

- Core requirements: Python 3.9+, llama-cpp-python
- Optional: transformers, torch (for PyTorch models)

When adding features:

1. Make additional dependencies optional where possible
2. Add graceful fallbacks when dependencies are missing
3. Document new dependencies in the documentation

## Code Style Guidelines

Maintain these practices for consistency:

1. Use Python's built-in modules when possible
2. Follow PEP 8 style guidelines
3. Use descriptive variable and function names
4. Add comments for complex logic
5. Use absolute paths with `Path` objects for cross-platform compatibility
6. Handle errors with descriptive messages

## Documentation

When making significant changes:

1. Update relevant docs in `/Volumes/LLM/docs/updated/`
2. Add code comments explaining non-obvious logic
3. Include examples for new features
4. Document any new dependencies or requirements

## Common Development Tasks

### Adding a New User Interface

1. Create a new Python script in the `scripts` directory
2. Implement the HTTP server and UI logic
3. Add an entry point in `llm.sh`
4. Leverage the existing inference engine via import

### Implementing a New Download Source

1. Modify `direct_download.sh` or create a new download script
2. Add authentication handling if needed
3. Implement proper file path handling
4. Update documentation with the new source

### Optimizing for a New Device

1. Detect the device type in `llm.sh`
2. Set appropriate environment variables
3. Adjust model loading parameters in `minimal_inference_quiet.py`
4. Document the optimization in the documentation