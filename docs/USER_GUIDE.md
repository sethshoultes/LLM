# LLM Platform User Guide

## Overview

The LLM Platform is a comprehensive environment for running large language models locally. It provides a user-friendly web interface, support for multiple model types, retrieval augmented generation (RAG), and powerful customization options.

This guide covers everything you need to know to get started and make the most of the platform.

## Table of Contents

- [Getting Started](#getting-started)
- [Command Reference](#command-reference)
- [Web Interface](#web-interface)
- [Model Management](#model-management)
- [Chat Interface](#chat-interface)
- [Generation Parameters](#generation-parameters)
- [Retrieval Augmented Generation (RAG)](#retrieval-augmented-generation-rag)
- [Advanced Features](#advanced-features)
- [Troubleshooting](#troubleshooting)
- [Tips and Best Practices](#tips-and-best-practices)

## Getting Started

### System Requirements

- **Operating System**: macOS, Linux, or Windows with WSL
- **RAM**: 8GB minimum, 16GB+ recommended
- **Storage**: 10GB+ free space for models and documents
- **CPU**: Modern multi-core processor
- **GPU**: Optional but recommended for faster inference

### Installation

1. Connect the external SSD to your computer
2. Open a terminal and navigate to the SSD directory:
   ```bash
   cd /Volumes/LLM
   ```
3. Ensure the launcher script is executable:
   ```bash
   chmod +x llm.sh
   ```
4. Run the platform:
   ```bash
   ./llm.sh
   ```
5. A web browser will open automatically to the interface (usually http://localhost:5100)

## Command Reference

The main script `llm.sh` accepts various flags and commands:

```bash
./llm.sh [OPTIONS] [COMMAND]
```

### Available Options

| Option | Description |
|--------|-------------|
| `--quiet` | Run in minimal interface mode |
| `--rag` | Enable Retrieval Augmented Generation features |
| `--debug` | Enable debug mode with detailed logging |
| `--port NUMBER` | Specify custom port (default: 5100) |
| `--no-browser` | Don't open browser automatically |
| `--help`, `-h` | Show help information |

### Available Commands

| Command | Description |
|---------|-------------|
| `download` | Download models from HuggingFace |
| `samples` | Download sample models for testing |
| `test MODEL_PATH` | Test a specific model file |
| `update` | Update dependencies |

### Examples

```bash
./llm.sh                      # Standard interface
./llm.sh --quiet              # Minimal interface
./llm.sh --rag                # Enable RAG features
./llm.sh --port 5200          # Use custom port
./llm.sh download             # Download models
./llm.sh test path/to/model   # Test specific model
```

## Web Interface

The web interface is divided into several sections:

1. **Header**: Contains the model selector and global controls
2. **Sidebar**: For RAG features and navigation
3. **Chat Area**: Displays conversation history
4. **Input Area**: For entering messages and adjusting parameters
5. **Context Bar**: Shows the current context (when using RAG)

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Enter` | Send message |
| `Ctrl+N` | New chat |
| `Ctrl+S` | Save chat |
| `Esc` | Clear input field |
| `Ctrl+/` | Show keyboard shortcuts |

## Model Management

### Model Types

The platform supports multiple model types:

1. **GGUF Models**: Most optimized for CPU inference (recommended)
2. **GGML Models**: Legacy format (still supported)
3. **PyTorch Models**: Full precision models for maximum quality
4. **Quantized Models**: Models reduced in size/precision for faster inference

### Model Directory Structure

Models should be organized as follows:

```
LLM-MODELS/
├── open-source/
│   ├── llama/
│   │   ├── 7b/
│   │   ├── 13b/
│   │   └── 70b/
│   └── mistral/
│       ├── 7b/
│       └── instruct/
├── quantized/
│   ├── gguf/
│   └── ggml/
└── embeddings/
```

### Downloading Models

#### Using the Download Script

1. Run `./llm.sh download` to launch the download manager
2. Follow the prompts to select a model repository and model
3. Wait for the download to complete
4. The model will be placed in the appropriate directory automatically

#### Sample Models

Run `./llm.sh samples` to download small test models:

```bash
./llm.sh samples
```

This will download TinyLlama (1.1B parameter model, ~600MB) for initial testing.

#### Manual Addition

You can also add models manually:

1. Download model files from HuggingFace or other sources
2. Place them in the appropriate directory based on model type and size
3. Restart the platform (or use the "Refresh Models" button)

## Chat Interface

### Starting a Chat

1. Select a model from the dropdown
2. Wait for the model to load (first time only)
3. Type your message in the input field and press Enter or click "Send"
4. The model will generate a response
5. Continue the conversation by sending more messages

### System Prompt

The system prompt sets the context for the entire conversation:

1. Click the "System Prompt" button above the chat
2. Enter instructions for the model (e.g., "You are a helpful assistant...")
3. Click "Save" to apply the system prompt
4. The model will follow these instructions throughout the conversation

### Chat Management

- **New Chat**: Starts a fresh conversation
- **Export Chat**: Downloads the conversation as a JSON file
- **Clear Chat**: Removes all messages from the current conversation
- **Delete Chat**: Permanently deletes the current conversation

## Generation Parameters

Fine-tune model behavior with these parameters:

### Basic Parameters

- **Temperature** (0.1-2.0): Controls randomness. Higher values produce more creative outputs.
- **Max Tokens** (64-4096): Maximum response length. Higher values allow longer answers.
- **Top P** (0.05-1.0): Controls diversity. Lower values make responses more focused.
- **Frequency Penalty** (0.0-2.0): Reduces repetition. Higher values discourage repeating phrases.

### Advanced Parameters

Click "Advanced Settings" to access:

- **Top K**: Limits token selection to top K options
- **Repeat Penalty**: Penalizes repetition of specific tokens
- **Presence Penalty**: Encourages introduction of new concepts
- **Context Window**: Adjusts how much conversation history is included

### Parameter Presets

Save your favorite parameter combinations:

1. Adjust parameters to your liking
2. Click "Save Preset"
3. Give your preset a name
4. Select it from the preset dropdown in the future

## Retrieval Augmented Generation (RAG)

RAG enhances the LLM by allowing it to reference your own documents when generating responses.

### Enabling RAG

Start the interface with RAG support:

```bash
./llm.sh --rag
```

### Project Management

RAG organizes documents into projects:

1. **Create a Project**: Click "New Project" in the sidebar
2. **Name Your Project**: Give it a name and optional description
3. **Select a Project**: Use the dropdown to switch between projects
4. **Delete Project**: Remove a project and all its documents
5. **Export Project**: Save all project documents as a ZIP file

### Document Management

Within each project, you can manage documents:

1. **Add Document**: Click "Add Document" in the sidebar
2. **Create Documents**: Add title, content (markdown supported), and optional tags
3. **View Documents**: Click on a document in the list to view its contents
4. **Edit Documents**: Update document content and metadata
5. **Delete Documents**: Remove documents from the project
6. **Import Documents**: Add external files (Markdown, Text, PDF)

### Search Functionality

Find relevant documents:

1. **Basic Search**: Use the search box to filter by title or content
2. **Tag Filtering**: Click on tags to filter documents
3. **Semantic Search**: Search by meaning (when enabled)
4. **Hybrid Search**: Combines keyword and semantic search

### Using Documents as Context

Two ways to use documents as context:

1. **Manual Selection**:
   - Select documents by clicking checkboxes
   - Documents appear in the context bar above the chat
   - Click "Clear Context" to remove all selected documents

2. **Auto-suggestion**:
   - Enable auto-suggestion in the context bar
   - System automatically suggests relevant documents based on your messages
   - Adjust the suggestion threshold in settings

### RAG Settings

Customize RAG behavior:

1. **Search Type**: Choose between keyword, semantic, or hybrid search
2. **Context Length**: Adjust maximum tokens for context
3. **Context Strategy**: Change how context is constructed (truncation, smart selection)
4. **Search Parameters**: Fine-tune search behavior

## Advanced Features

### API Access

Access the platform programmatically:

```bash
# Example: Generate text with curl
curl -X POST http://localhost:5100/api/completion \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Hello, world!",
    "model_id": "llama-7b",
    "params": {
      "temperature": 0.7,
      "max_tokens": 100
    }
  }'
```

See the [API Reference](API_REFERENCE.md) for full documentation.

### Custom Templates

Create templates for common prompts:

1. Go to Settings > Templates
2. Click "New Template"
3. Define template variables with `{{variable_name}}`
4. Save and access from the templates menu

### Chaining Models

Use multiple models in sequence:

1. Enable model chaining in Settings > Advanced
2. Define a chain workflow
3. Each model processes the output of the previous one

### Plugins

Extend platform functionality with plugins:

1. Go to Settings > Plugins
2. Enable available plugins
3. Configure plugin settings
4. Access plugin features through the interface

## Troubleshooting

### Interface Won't Start

- Check that you're in the correct directory (`/Volumes/LLM`)
- Ensure `llm.sh` has execute permissions: `chmod +x llm.sh`
- Try running with debug output: `./llm.sh --debug`
- Check for port conflicts: `lsof -i :5100`
- Try a different port: `./llm.sh --port 5200`

### Model Loading Errors

- Verify the model file exists and isn't corrupted
- Check if the model format is supported
- Ensure sufficient RAM is available
- Try a smaller or more quantized model
- Check Python environment: `source LLM-MODELS/tools/scripts/activate_mac.sh`
- Verify dependencies: `pip install -r config/requirements.txt`

### Generation Issues

- If responses are cut off, increase the Max Tokens parameter
- If responses are repetitive, increase the Frequency/Repeat Penalty
- If the model generates inappropriate content, use a more restrictive system prompt
- If generation is too slow, try a smaller model or more quantized version
- If responses seem random, lower the temperature

### RAG Problems

- **Missing RAG Features**: Ensure you started with `./llm.sh --rag`
- **Import Errors**: Check console for Python errors
- **Context Not Working**: Verify documents are properly selected
- **Search Not Finding Documents**: Try different search terms or methods
- **Slow Search**: Rebuild index if search performance degrades

## Tips and Best Practices

### Effective Prompting

For best results:

1. **Be specific**: Clear, detailed prompts get better responses
2. **Use system prompts**: Set the context for all interactions
3. **Provide examples**: Show the model what you expect
4. **Adjust parameters**: Different tasks need different settings
5. **Chain thoughts**: Break complex tasks into steps

### Recommended Model Settings

| Use Case | Temperature | Top P | Max Tokens | Frequency Penalty |
|----------|-------------|-------|------------|-------------------|
| Factual Q&A | 0.2-0.4 | 0.9 | 1024 | 0.0 |
| Creative Writing | 0.7-1.0 | 0.95 | 2048 | 0.5 |
| Code Generation | 0.3-0.5 | 0.95 | 1024 | 0.3 |
| Brainstorming | 0.8-1.2 | 0.98 | 1024 | 0.2 |

### Memory Management

- Only load one model at a time
- Unload models when not in use
- Use quantized models for lower memory usage
- Close other memory-intensive applications
- For larger models, ensure sufficient swap space

### RAG Best Practices

1. **Organize Documents**: Create separate projects for different domains
2. **Keep Documents Focused**: Shorter, specific documents work better than very long ones
3. **Use Clear Titles**: Helps with finding documents later
4. **Add Tags**: Makes filtering and searching easier
5. **Regular Maintenance**: Remove outdated documents
6. **Index Management**: Rebuild indexes periodically for optimal performance

### Security Considerations

- The platform runs locally without external API calls
- Your data stays on your device
- No internet connection is required after setup
- Models and documents are stored only on your device
- External plugins may have different privacy policies

## Additional Resources

- [Developer Guide](DEVELOPER_GUIDE.md): For extending the platform
- [API Reference](API_REFERENCE.md): For programmatic access
- [Architecture Overview](ARCHITECTURE.md): System design
- [Model Compatibility List](MODEL_COMPATIBILITY.md): Tested models
- [Community Forums](https://community.llm-platform.org): User discussions and tips