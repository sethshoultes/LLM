# LLM Environment Documentation

This directory contains detailed documentation for the portable LLM environment.

## Core Documentation

- [**OVERVIEW.md**](OVERVIEW.md) - System overview and architecture
- [**USAGE.md**](USAGE.md) - User guide and command reference
- [**MODELS.md**](./PRD/MODELS.md) - Model information and recommendations
- [**DEVELOPMENT.md**](./PRD/DEVELOPMENT.md) - Developer guide for extending the system
- [**STRUCTURE.md**](./PRD/STRUCTURE.md) - Current file and directory structure

## Project Status

The project has undergone significant cleanup and consolidation. The current version maintains full functionality while simplifying the codebase:

- Uses a streamlined web interface (`quiet_interface.py`)
- Supports multiple model types (GGUF, GGML, PyTorch)
- Works across Mac and Raspberry Pi environments
- Provides a unified command interface through `llm.sh`

For historical context on the system's development and original structure, see [**HISTORY.md**](./PRD/HISTORY.md).

## Quick Links

- Go back to [main README](../../README.md)
- Run the environment with `../../llm.sh`