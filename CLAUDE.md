# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands
- Run system: `./llm.sh` or `./llm.sh quiet` 
- Test model loading: `python scripts/minimal_inference_quiet.py [model_path]`
- Test interface: `python scripts/quiet_interface.py`
- Activate environment: `source LLM-MODELS/tools/scripts/activate_mac.sh`

## Code Style
- Follow PEP 8 with descriptive snake_case names
- Use Path objects for cross-platform path handling
- Class names: CamelCase, functions/variables: snake_case
- Import order: standard library → third-party → local modules
- Error handling: Use try/except with specific exceptions
- Provide descriptive error messages with traceback when appropriate
- Document functions with docstrings and comment complex sections

## Dependencies
- Core: Python 3.9+, llama-cpp-python, torch, transformers, flask
- Document new dependencies in config/requirements.txt