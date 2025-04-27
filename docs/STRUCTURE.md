# Portable LLM Environment - Directory Structure

This document provides a detailed overview of the current system organization after the cleanup process.

## Top-Level Structure

```
/Volumes/LLM/                 # Base directory on the external drive
  ├── llm.sh                  # Main entry point script
  ├── README.md               # Project overview and getting started
  ├── launch_llm_interface.sh # Legacy launcher (not used in current system)
  ├── manage_models.sh        # Legacy model management script (not actively used)
  ├── requirements.txt        # Python dependencies
  ├── setup_llm_environment.sh # Environment setup script
  ├── docs/                   # Documentation
  ├── scripts/                # Core scripts and interfaces
  └── LLM-MODELS/             # Model storage and tools
```

## Active Components

The following directories and files are actively used in the current system:

### Core Scripts Directory (`/scripts`)

```
/Volumes/LLM/scripts/
  ├── minimal_inference_quiet.py  # Core inference engine - ACTIVELY USED
  ├── quiet_interface.py          # Main web interface - ACTIVELY USED
  ├── direct_download.sh          # Model download utility - ACTIVELY USED
  └── download_sample_models.sh   # Sample model downloader - ACTIVELY USED
```

### Model Storage (`/LLM-MODELS`)

```
/Volumes/LLM/LLM-MODELS/
  ├── quantized/                  # Quantized models - ACTIVELY USED
  │   ├── gguf/                   # GGUF format models - PRIMARY MODEL LOCATION
  │   ├── ggml/                   # GGML format models (legacy but supported)
  │   └── awq/                    # AWQ format models (placeholder)
  ├── open-source/                # Original models by family - ACTIVELY USED
  │   ├── llama/                  # LLaMA models
  │   │   ├── 7b/
  │   │   ├── 13b/
  │   │   └── 70b/
  │   ├── mistral/
  │   │   ├── 7b/
  │   │   └── instruct/
  │   ├── phi/
  │   └── mixtral/
  ├── embeddings/                 # Reserved for embedding models (unused)
  └── tools/                      # Tools and scripts - PARTIALLY ACTIVE
      ├── mac/                    # Mac-specific tools (empty placeholder)
      ├── pi/                     # Raspberry Pi tools (empty placeholder)
      ├── scripts/                # Environment activation scripts - ACTIVELY USED
      │   ├── activate_mac.sh     # Mac environment activation - CRITICAL
      │   └── activate_pi.sh      # Pi environment activation - CRITICAL
      └── python/                 # Python environment and modules
          └── llm_env/            # Python virtual environment - ACTIVELY USED
```

### Documentation (`/docs`)

```
/Volumes/LLM/docs/
 ├── README.md           # Documentation index
 ├── OVERVIEW.md         # System overview
 ├── USAGE.md            # Updated user guide
 ├── MODELS.md           # Updated model information
 ├── DEVELOPMENT.md      # Updated developer guide
 ├── STRUCTURE.md        # This file
 └── HISTORY.md          # Historical context (to be created)
      
```

## File Dependencies and Relationships

### Primary Operation Flow

1. User runs `/Volumes/LLM/llm.sh` with a command
2. Script activates Python environment using `/Volumes/LLM/LLM-MODELS/tools/scripts/activate_mac.sh`
3. Script launches `/Volumes/LLM/scripts/quiet_interface.py`
4. Interface imports `/Volumes/LLM/scripts/minimal_inference_quiet.py` for model operations
5. Interface serves web UI and handles API requests
6. Inference engine loads models from `/Volumes/LLM/LLM-MODELS/quantized/gguf/` or other model directories

### Critical Dependencies

- `llm.sh` → `activate_mac.sh` or `activate_pi.sh` → Python virtual environment
- `quiet_interface.py` → `minimal_inference_quiet.py` → Model files
- Web browser → HTTP server in `quiet_interface.py` → API endpoints

## Important Notes on Structure

1. **Virtual Environment Location**:
   The Python virtual environment is located at `/Volumes/LLM/LLM-MODELS/tools/python/llm_env/`
   This contains all Python dependencies (llama-cpp-python, transformers, etc.)

2. **Primary Script Location**:
   All actively used Python scripts are in `/Volumes/LLM/scripts/`
   This consolidation was part of the cleanup process

3. **Data Persistence**:
   Chat history and settings are stored in browser localStorage
   No server-side persistence is implemented

4. **Portable Design**:
   All paths use absolute references from the base directory
   The system assumes it's running from the external SSD mounted at `/Volumes/LLM`