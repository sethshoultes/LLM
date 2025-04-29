# Interface Consolidation Taskmaster List

Reference: [INTERFACE_CONSOLIDATION_PRD.md](./INTERFACE_CONSOLIDATION_PRD.md)

## 1. File Cleanup and Consolidation

- [x] **1.1 Identify and remove duplicate files**
  - [x] Delete `quiet_interface_rag.py`
  - [x] Verify `llm_rag.sh` is removed (confirmed it doesn't exist)
  - [x] Check for and remove redundant `minimal_inference.py` (confirmed it doesn't exist)
  - [x] Scan for any other redundant interface files and remove them

- [x] **1.2 Audit remaining files for duplication**
  - [x] Review code in `quiet_interface.py` to identify duplicated functionality
  - [x] Review RAG UI extensions for duplicated code
  - [x] Document all identified duplications for refactoring

Duplication findings:
1. The `ui_extensions.py` file directly imports and modifies the HTML template from `quiet_interface.py`, creating a tight coupling
2. The RAG JavaScript code has duplicate functions that should be shared with the main interface
3. There is a duplication of request handling between regular and RAG modes in the handler classes

- [x] **1.3 Update llm.sh to use flags instead of positional arguments**
  - [x] Implement option parsing with `--rag` and `--debug` flags
  - [x] Update environment variable exports
  - [x] Remove all legacy mode handling
  - [x] Update help message to reflect new command structure

## 2. Fix Critical Issues

- [x] **2.1 Fix context window error in RAG mode**
  - [x] Analyze the token counting implementation
  - [x] Add token limiting for large documents
  - [x] Implement chunking for context documents
  - [x] Add token usage display in the console (UI display will be part of frontend implementation)

- [x] **2.2 Fix HTML/JavaScript errors**
  - [x] Debug and fix "Uncaught SyntaxError: Invalid or unexpected token (at (index):1499:29)"
  - [x] Validate HTML template
  - [x] Ensure proper escaping of JavaScript content
  - [x] Fix broken UI layout by using DOM manipulation instead of innerHTML replacement

- [x] **2.3 Fix Python module import issues**
  - [x] Review all import statements for consistency
  - [x] Verify PYTHONPATH is correctly set by adding sys.path validation
  - [x] Fix potential circular dependencies with try/except import blocks
  - [x] Add robust error handling for imports with detailed error messages

## 3. Interface Refactoring

- [x] **3.1 Enhance `quiet_interface.py`**
  - [x] Add environment variable checks for RAG and debug modes
  - [x] Refactor to handle all features in a single interface
  - [x] Implement robust error handling (no silent failures)
  - [x] Remove any fallback mechanisms

- [x] **3.2 Create error handling architecture**
  - [x] Implement standardized error reporting format with ErrorHandler class
  - [x] Ensure errors are logged and displayed appropriately with consistent formatting
  - [x] Add traceback capture for debugging with debug mode toggle
  - [x] Create user-friendly error messages with context information

## 4. Modern Frontend Implementation

- [x] **4.1 Create templating architecture**
  - [x] Create `/templates` directory structure
  - [x] Install lightweight templating engine (Jinja2)
  - [x] Convert HTML_TEMPLATE string to template files
  - [x] Add template loading mechanism to `quiet_interface.py`

- [x] **4.2 Separate HTML, CSS, and JavaScript**
  - [x] Extract CSS to separate files
  - [x] Extract JavaScript to separate files
  - [x] Organize templates by component
  - [x] Create proper asset handling

- [x] **4.3 Implement component-based architecture**
  - [x] Create header component (in main layout)
  - [x] Create sidebar component (sidebar.html)
  - [x] Create chat interface component (chat_interface.html)
  - [x] Create model selector component (model_selector.html)
  - [x] Create RAG sidebar component (integrated in sidebar.html)

## 5. RAG Integration

- [x] **5.1 Create collapsible RAG sidebar**
  - [x] Design sidebar layout
  - [x] Implement project selector
  - [x] Create document browser
  - [x] Add document preview
  - [x] Implement context selection

- [x] **5.2 Fix RAG context handling**
  - [x] Implement document chunking (token limiting)
  - [x] Add token counting (visualization in UI)
  - [x] Create context management UI
  - [x] Add token usage visualization

- [x] **5.3 Enhance RAG API**
  - [x] Refactor API endpoints for RESTful design
  - [x] Add proper error handling
  - [x] Document all API endpoints
  - [x] Implement seamless integration with UI

## 6. Testing and Validation

- [ ] **6.1 Develop testing protocol**
  - [ ] Create test cases for all features
  - [ ] Test interface with various models
  - [ ] Test RAG functionality with various document sizes
  - [ ] Create error case tests

- [ ] **6.2 Perform cross-platform testing**
  - [ ] Test on macOS
  - [ ] Test on Linux if applicable
  - [ ] Test on different browser versions
  - [ ] Verify all features work consistently

- [x] **6.3 Validate against requirements**
  - [x] Verify NO duplicate files exist
  - [x] Confirm NO fallback systems that hide errors
  - [x] Validate that DRY principles are followed
  - [x] Ensure KISS principle is maintained

## 7. Documentation and Deployment

- [x] **7.1 Update user documentation**
  - [x] Update USAGE.md with new command structure
  - [x] Create or update RAG_USAGE.md with simplified instructions
  - [x] Add troubleshooting section for common issues
  - [x] Document API endpoints for developers

- [x] **7.2 Add developer documentation**
  - [x] Document template system
  - [x] Create API documentation
  - [x] Document UI component structure
  - [x] Add extension points documentation

- [x] **7.3 Create implementation summary**
  - [x] Document key architectural decisions
  - [x] Summarize removed files and why
  - [x] Outline changes made to existing files
  - [x] Create before/after comparison

## 8. (Optional) React Frontend

- [ ] **8.1 Set up React development environment**
  - [ ] Create React app structure
  - [ ] Configure build system
  - [ ] Set up asset pipeline
  - [ ] Configure development server

- [ ] **8.2 Implement React components**
  - [ ] Create component hierarchy
  - [ ] Implement state management
  - [ ] Build UI components
  - [ ] Add API integration

- [ ] **8.3 Integrate with backend**
  - [ ] Ensure API compatibility
  - [ ] Configure build output location
  - [ ] Add serving of React app from Python server
  - [ ] Test end-to-end functionality

## Acceptance Criteria

1. Running `./llm.sh` launches a single unified interface
2. RAG features can be enabled with `./llm.sh --rag`
3. Debug mode can be enabled with `./llm.sh --debug`
4. No errors occur when loading the interface
5. All buttons and UI elements function correctly
6. RAG sidebar properly displays projects and documents
7. Context window errors are fixed when using RAG
8. No duplicate files exist in the codebase
9. No fallback mechanisms that hide errors
10. Interface works consistently across platforms
11. Documentation is updated to reflect changes