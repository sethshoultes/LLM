# RAG System Improvements PRD

## Overview
This document outlines the plan to address critical issues in our RAG system implementation, focusing on Python module import problems, path handling, error handling, and ensuring tight integration with our existing architecture without duplication.

## Core Principles
- **KISS**: Keep improvements simple and straightforward
- **DRY**: No duplication of code or files
- **Cross-Platform**: Ensure system works across platforms
- **Preserve Core Files**: Maintain `llm.sh` as the central entry point
- **Lightweight**: Maintain minimal system footprint

## Critical Issues to Address

### 1. Module Import Error
**Problem**: The RAG system fails with `ModuleNotFoundError: No module named 'rag_support'` because Python cannot find the module.

**Solution**:
- Properly configure PYTHONPATH in shell scripts:
```bash
# In llm.sh - Add to existing file
export PYTHONPATH="$DIR:$PYTHONPATH"
```
- Add `__init__.py` files where needed for proper Python module recognition
- Fix import statements to use absolute imports:
```python
# Instead of: import rag_support
# Use: from path.to import module
```

### 2. Integration with llm.sh
**Problem**: Currently using separate `llm_rag.sh` which duplicates functionality.

**Solution**:
- Modify `llm.sh` to add RAG support option:
```bash
# In llm.sh - Add support for RAG mode
if [ "$1" == "rag" ]; then
    # Enable RAG features
    export LLM_RAG_ENABLED=1
    shift  # Remove the rag argument
fi

# Later in the script, when running quiet_interface.py
if [ "$LLM_RAG_ENABLED" == "1" ]; then
    # Pass appropriate flag to the Python script
    PYTHON_ARGS="--rag"
fi
```
- Allow `quiet_interface.py` to detect and enable RAG features:
```python
# In quiet_interface.py
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--rag', action='store_true', help='Enable RAG features')
args = parser.parse_args()

# Later in the script
if args.rag:
    # Import RAG extensions and enable features
```

### 3. Hardcoded Paths
**Problem**: All modules use hardcoded `/Volumes/LLM` path, breaking cross-platform compatibility.

**Solution**:
- Use the script's location for base path in Python:
```python
# Find base dir from the script location
import os
from pathlib import Path
SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent  # Go up one level
```
- Pass base dir from shell script:
```bash
# In llm.sh
export LLM_BASE_DIR="$DIR"
```
- Use environment variable in Python:
```python
BASE_DIR = Path(os.environ.get("LLM_BASE_DIR", str(SCRIPT_DIR.parent)))
```

### 4. Error Handling
**Problem**: Many operations lack robust error handling, causing silent failures.

**Solution**:
- Add specific exception handling for critical operations:
```python
try:
    # Operation
except (FileNotFoundError, PermissionError) as e:
    print(f"Error: {str(e)}")
    # Log error and return meaningful message
except Exception as e:
    print(f"Unexpected error: {str(e)}")
    # Log general error
```

## System Integration Approach

### 1. File Structure Changes
| File | Change | Reason |
|------|--------|--------|
| `llm.sh` | Modify to add RAG mode option | Central entry point for all features |
| `llm_rag.sh` | Remove after integrating with llm.sh | Eliminate duplication |
| `quiet_interface.py` | Add RAG integration option | Single interface file with toggleable RAG |
| `quiet_interface_rag.py` | Merge functionality into quiet_interface.py | Eliminate duplication |
| `rag_support/__init__.py` | Fix to properly initialize as Python module | Resolve import errors |

### 2. Modified Command Usage
```
# Current usage
./llm.sh                # Standard mode
./llm_rag.sh            # With RAG features (to be removed)

# New usage
./llm.sh                # Standard mode
./llm.sh rag            # With RAG features
```

## Implementation Plan

### Phase 1: Fix Critical Imports and Path Issues
1. Update `rag_support/__init__.py` to properly initialize as a Python module
2. Fix path handling to work cross-platform
3. Verify imports work correctly

### Phase 2: Integrate with llm.sh
1. Modify `llm.sh` to accept a 'rag' parameter
2. Update `quiet_interface.py` to conditionally load RAG features
3. Test both standard and RAG modes work with a single codebase

### Phase 3: Enhance Error Handling
1. Add improved error handling to critical operations
2. Implement context size management
3. Ensure informative error messages are displayed to users

## Detailed File Changes

### llm.sh
```bash
# Add near the top
RAG_ENABLED=0
if [ "$1" == "rag" ]; then
    RAG_ENABLED=1
    shift  # Remove the rag argument
fi

# Add to environment setup
export LLM_BASE_DIR="$DIR"
export LLM_RAG_ENABLED="$RAG_ENABLED"
export PYTHONPATH="$DIR:$PYTHONPATH"

# Modify the Python call
python "$DIR/scripts/quiet_interface.py" $@ $([ "$RAG_ENABLED" == "1" ] && echo "--rag")
```

### quiet_interface.py
```python
# Add near the top
import argparse
parser = argparse.ArgumentParser(description='LLM Interface')
parser.add_argument('--rag', action='store_true', help='Enable RAG features')
args = parser.parse_args()

# At appropriate point in script
if args.rag:
    try:
        from rag_support.api_extensions import api_handler
        from rag_support.ui_extensions import get_extended_html_template
        # Enable RAG features
        HTML_TEMPLATE = get_extended_html_template()
        RAG_ENABLED = True
    except ImportError as e:
        print(f"Error loading RAG modules: {e}")
        print("Falling back to standard mode")
        RAG_ENABLED = False
else:
    RAG_ENABLED = False
```

### RequestHandler class in quiet_interface.py
```python
# Modify do_GET and do_POST methods to check for RAG
def do_GET(self):
    if RAG_ENABLED and self.path.startswith('/api/projects'):
        # Handle RAG API requests
        parsed_path = urllib.parse.urlparse(self.path)
        query_params = {}
        if parsed_path.query:
            query_params = {k: v[0] for k, v in urllib.parse.parse_qs(parsed_path.query).items()}
        
        status_code, response_data = api_handler.handle_request(
            parsed_path.path, 
            'GET', 
            query_params=query_params
        )
        
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response_data).encode('utf-8'))
        return
    
    # Continue with standard handling
    # Original code here
```

## Compatibility Requirements
- All changes must maintain backward compatibility
- System must work with existing projects and file structures
- No new dependencies should be introduced
- Must work on various platforms (macOS, Linux, etc.)

## Future Considerations
- Optimize document storage for large collections
- Improve search relevance with simple algorithms
- Add document summarization to optimize context usage