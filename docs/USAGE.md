# Portable LLM Environment - User Guide

## Getting Started

1. Connect the external SSD to your computer
2. Open a terminal and navigate to the SSD directory: `cd /Volumes/LLM`
3. Run the main script: `./llm.sh`
4. A web browser will open automatically to the interface (usually http://localhost:5100)
5. Select a model from the dropdown and start chatting

## Command Reference

The main script `llm.sh` accepts various commands:

```bash
./llm.sh [COMMAND]
```

### Available Commands

| Command | Description |
|---------|-------------|
| `start` | Start the default interface (same as no command) |
| `quiet` | Start the quiet interface (recommended, suppresses debug output) |
| `download` | Download models from HuggingFace |
| `samples` | Download sample models for testing |
| `help` | Show help information |

### Legacy Commands

These commands are maintained for backward compatibility but all redirect to the quiet interface:

- `flask`: Originally launched a Flask-based interface
- `simple`: Originally launched a simple HTTP interface
- `minimal`: Originally launched a minimal interface

## Using the Web Interface

### Model Selection

1. When the interface loads, it automatically scans for available models
2. Select a model from the dropdown to load it
3. The first time you load a model, it may take a few moments
4. Once loaded, the model stays in memory until you select a different one

### Chat Interface

The interface includes:

- **System Prompt**: Optional context/instructions for the model
- **Chat History**: Saved conversation with timestamps
- **Input Area**: Text field for your messages
- **Generation Controls**: Parameters to adjust model behavior

### Model Parameters

Fine-tune model behavior with these controls:

- **Temperature** (0.1-2.0): Controls randomness. Higher values produce more creative outputs.
- **Max Tokens** (64-4096): Maximum response length. Higher values allow longer answers.
- **Top P** (0.05-1.0): Controls diversity. Lower values make responses more focused.
- **Frequency Penalty** (0.0-2.0): Reduces repetition. Higher values discourage repeating the same phrases.

### Session Management

- Chat history is saved automatically in your browser
- Click "New Chat" to start a fresh conversation
- Click "Export Chat" to download your conversation as a JSON file

## Downloading Models

### Sample Models

Run `./llm.sh samples` to download small test models:

```bash
./llm.sh samples
```

This will download TinyLlama (1.1B parameter model, ~600MB) for initial testing.

### Downloading Specific Models

Run `./llm.sh download` to download a model:

```bash
./llm.sh download
```

This launches the direct download script that fetches models from HuggingFace.

### Manual Model Addition

You can also add models manually:

1. Download the model file from HuggingFace or other sources
2. Place it in the appropriate directory:
   - GGUF models: `/Volumes/LLM/LLM-MODELS/quantized/gguf/`
   - GGML models: `/Volumes/LLM/LLM-MODELS/quantized/ggml/`
   - PyTorch models: `/Volumes/LLM/LLM-MODELS/open-source/{family}/{size}/`

## Getting Good Results

### Effective Prompting

For best results:

1. **Be specific**: Clear, detailed prompts get better responses
2. **Use system prompts**: Set the context with a system prompt (e.g., "You are a helpful assistant...")
3. **Adjust parameters**: Lower temperature (0.3-0.5) for factual responses, higher (0.7-1.0) for creative content
4. **Provide context**: Include necessary background information in your messages

### Recommended Model Settings

| Use Case | Temperature | Top P | Max Tokens | Frequency Penalty |
|----------|-------------|-------|------------|-------------------|
| Factual Q&A | 0.2-0.4 | 0.9 | 1024 | 0.0 |
| Creative Writing | 0.7-1.0 | 0.95 | 2048 | 0.5 |
| Code Generation | 0.3-0.5 | 0.95 | 1024 | 0.3 |
| Brainstorming | 0.8-1.2 | 0.98 | 1024 | 0.2 |

## Troubleshooting

### Interface Won't Start

- Check that you're in the correct directory (`/Volumes/LLM`)
- Ensure `llm.sh` has execute permissions: `chmod +x llm.sh`
- Try running Python directly: `python3 scripts/quiet_interface.py`

### Model Loading Errors

- Verify the model file exists and isn't corrupted
- Check that the Python environment is activated: `source LLM-MODELS/tools/scripts/activate_mac.sh`
- Ensure llama-cpp-python is installed: `pip install llama-cpp-python`
- Check for sufficient available memory (top command on Mac/Linux)

### Generation Issues

- If responses are cut off, increase the Max Tokens parameter
- If responses are repetitive, increase the Frequency Penalty
- If the model generates inappropriate content, use a more restrictive system prompt
- If generation is too slow, try a smaller model or more quantized version

### "No models found" Error

- Check that the models are in the correct location
- Run `./llm.sh samples` to download a test model
- Verify that the path structure matches what the system expects