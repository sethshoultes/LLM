# RAG System Improvements PRD

## Overview
This document outlines the plan to address critical issues in our RAG system implementation, focusing on Python module import problems, path handling, error handling, and ensuring tight integration with our existing architecture without duplication.

## Core Principles
- **KISS**: Keep improvements simple and straightforward
- **DRY**: No duplication of code or files
- **Cross-Platform**: Ensure system works across platforms
- **Preserve Core Files**: Maintain `llm.sh` as the central entry point
- **Lightweight**: Maintain minimal system footprint
- **Cohesive Integration**: All modes work together as a unified whole

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
```
- Use environment variables directly in Python instead of command-line arguments:
```python
# In quiet_interface.py - Simpler than argument parsing
import os
RAG_ENABLED = os.environ.get("LLM_RAG_ENABLED") == "1"

# Later in the code
if RAG_ENABLED:
    # Load and enable RAG features
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
    # Log error with detailed information
    sys.exit(1)  # Exit with error code for visibility
except Exception as e:
    print(f"Unexpected error: {str(e)}")
    # Log general error with traceback
    sys.exit(1)  # Exit with error code for visibility
```
- No silent failures or fallbacks - errors should be visible and require fixes

## System Integration Approach

### 1. File Structure Changes
| File | Change | Reason |
|------|--------|--------|
| `llm.sh` | Modify to add RAG mode option | Central entry point for all features |
| `llm_rag.sh` | Remove after integrating with llm.sh | Eliminate duplication |
| `quiet_interface.py` | Add RAG integration option | Single interface file with integrated RAG |
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
2. Ensure informative error messages are displayed to users
3. Remove any silent failures that mask underlying issues

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
python "$DIR/scripts/quiet_interface.py" $@
```

### quiet_interface.py
```python
# Add near the top, after imports
import os
from pathlib import Path

# Get base directory from environment or script location
SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = Path(os.environ.get("LLM_BASE_DIR", str(SCRIPT_DIR.parent)))
RAG_ENABLED = os.environ.get("LLM_RAG_ENABLED") == "1"

# At appropriate point in script
if RAG_ENABLED:
    try:
        # Import RAG modules using fully qualified paths
        from rag_support.api_extensions import api_handler
        from rag_support.ui_extensions import get_extended_html_template
        
        # Set up RAG features
        HTML_TEMPLATE = get_extended_html_template()
        print("RAG features enabled")
    except ImportError as e:
        print(f"Error loading RAG modules: {e}")
        print("This is a critical error that must be fixed.")
        sys.exit(1)  # Exit with error code
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
        
        try:
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
        except Exception as e:
            print(f"Error handling RAG API request: {e}")
            self.send_error(500, f"Internal server error: {str(e)}")
            return
    
    # Continue with standard handling
    # Original code here
```

## Verification and Testing

### 1. Basic Verification Steps
After implementation, verify the system with these checks:

1. Check standard mode works:
```bash
./llm.sh
# Verify interface loads and operates normally
```

2. Check RAG mode works:
```bash
./llm.sh rag
# Verify RAG features appear and function correctly
```

3. Verify error handling:
```bash
# Temporarily rename rag_support folder to break imports
mv rag_support rag_support_test
./llm.sh rag
# Should show clear error message about missing modules
mv rag_support_test rag_support
```

4. Check path handling:
```bash
# Run from different directory
cd /some/other/path
/path/to/llm.sh rag
# Should still work correctly with right paths
```

### 2. Integration Testing
Test these scenarios to verify cohesive integration:

1. Create a project and documents in RAG mode
2. Generate responses using RAG context
3. Switch back to standard mode and verify no errors
4. Switch to RAG mode again and verify projects remain accessible

## Compatibility Requirements
- All changes must maintain backward compatibility
- System must work with existing projects and file structures
- No new dependencies should be introduced
- Must work on various platforms (macOS, Linux, etc.)

## Future Considerations
- Optimize document storage for large collections
- Improve search relevance with simple algorithms
- Add document summarization to optimize context usage