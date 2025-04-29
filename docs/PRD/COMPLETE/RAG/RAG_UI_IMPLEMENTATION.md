# RAG UI Implementation Guide (IMPLEMENTED)

## Overview
This document outlines the implementation approach for integrating the Retrieval Augmented Generation (RAG) user interface components into the LLM interface, following the global UI Integration Standards.

**Status: IMPLEMENTED** - All UI components described in this document have been successfully implemented and integrated.

## Feature Requirements
The RAG UI must provide these capabilities:
- Project creation and management
- Document upload, viewing, and organization
- Document search and filtering
- Context selection for chat
- Artifact generation and storage

## Interface Components

### 1. Project Management
**Extension Point**: `SIDEBAR`

```html
<div class="rag-project-panel">
    <div class="rag-project-selector">
        <select id="ragProjectSelect">
            <option value="">Select Project</option>
            <!-- Projects loaded dynamically -->
        </select>
        <button class="rag-btn rag-btn-small" id="ragNewProjectBtn">New</button>
    </div>
    <div class="rag-project-info" id="ragProjectInfo">
        <!-- Project stats shown here -->
    </div>
</div>
```

### 2. Document Management
**Extension Points**: `SIDEBAR`, `DIALOGS`

Sidebar component:
```html
<div class="rag-document-panel">
    <div class="rag-panel-header">
        <h3>Documents</h3>
        <div class="rag-actions">
            <button class="rag-btn rag-btn-small" id="ragAddDocBtn">Add</button>
            <button class="rag-btn rag-btn-icon" id="ragRefreshDocsBtn">↻</button>
        </div>
    </div>
    <div class="rag-search-bar">
        <input type="text" id="ragDocSearch" placeholder="Search documents...">
        <button class="rag-btn-clear" id="ragClearSearch">×</button>
    </div>
    <div class="rag-document-list" id="ragDocumentList">
        <!-- Documents loaded dynamically -->
    </div>
</div>
```

Add Document Dialog:
```html
<div class="rag-dialog" id="ragAddDocDialog">
    <div class="rag-dialog-header">
        <h2>Add Document</h2>
        <button class="rag-btn-close" id="ragCloseAddDocBtn">×</button>
    </div>
    <div class="rag-dialog-content">
        <label for="ragDocTitle">Title:</label>
        <input type="text" id="ragDocTitle" placeholder="Document title">
        
        <label for="ragDocTags">Tags (comma separated):</label>
        <input type="text" id="ragDocTags" placeholder="tag1, tag2, tag3">
        
        <label for="ragDocContent">Content (Markdown):</label>
        <textarea id="ragDocContent" placeholder="Document content..."></textarea>
    </div>
    <div class="rag-dialog-footer">
        <button class="rag-btn rag-btn-secondary" id="ragCancelAddDocBtn">Cancel</button>
        <button class="rag-btn" id="ragSaveDocBtn">Save Document</button>
    </div>
</div>
```

### 3. Context Management
**Extension Point**: `MAIN_CONTROLS`

```html
<div class="rag-context-bar" id="ragContextBar">
    <div class="rag-context-header">
        <h3>Context Documents</h3>
        <div class="rag-toggle">
            <label for="ragAutoContextToggle">Auto-suggest:</label>
            <label class="rag-switch">
                <input type="checkbox" id="ragAutoContextToggle">
                <span class="rag-slider"></span>
            </label>
        </div>
    </div>
    <div class="rag-context-items" id="ragContextItems">
        <!-- Selected documents shown here -->
    </div>
</div>
```

## CSS Implementation
Following the UI Standards, all CSS is namespaced with the `rag-` prefix:

```css
/* Core RAG components */
.rag-sidebar-section {
    margin-bottom: 1rem;
    padding: 0.5rem;
    border-radius: var(--border-radius);
    background: var(--card-background);
}

.rag-document-list {
    max-height: 300px;
    overflow-y: auto;
    border: 1px solid var(--border-color);
    border-radius: var(--border-radius);
}

.rag-document-item {
    padding: 0.5rem;
    border-bottom: 1px solid var(--border-color);
    cursor: pointer;
}

.rag-document-item:hover {
    background-color: var(--hover-color);
}

.rag-document-item.selected {
    background-color: var(--selection-background);
    border-left: 2px solid var(--primary-color);
}

/* Context management */
.rag-context-bar {
    margin-bottom: 1rem;
    padding: 0.8rem;
    background-color: var(--highlight-background);
    border-radius: var(--border-radius);
}

.rag-context-items {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-top: 0.5rem;
}

.rag-context-item {
    display: flex;
    align-items: center;
    gap: 0.3rem;
    padding: 0.3rem 0.6rem;
    background-color: var(--tag-background);
    border-radius: var(--border-radius-small);
    font-size: 0.8rem;
}

/* Responsive adjustments */
@media (max-width: 768px) {
    .rag-sidebar-collapsed .rag-sidebar-section {
        display: none;
    }
    
    .rag-context-bar {
        padding: 0.5rem;
    }
}
```

## JavaScript Implementation
Following the UI Standards, JavaScript is namespaced under the LLM interface:

```javascript
// Initialize RAG namespace
window.LLMInterface = window.LLMInterface || {};
window.LLMInterface.RAG = {
    state: {
        currentProject: null,
        documents: [],
        contextDocuments: [],
        autoSuggestEnabled: false
    },
    
    init: function() {
        // Initialize RAG components
        this.initProjectSelector();
        this.initDocumentList();
        this.initContextBar();
        this.initDialogs();
        this.attachEventListeners();
    },
    
    initProjectSelector: function() {
        // Implementation
    },
    
    initDocumentList: function() {
        // Implementation
    },
    
    initContextBar: function() {
        // Implementation
    },
    
    initDialogs: function() {
        // Implementation
    },
    
    attachEventListeners: function() {
        // Attach event listeners for RAG components
        document.getElementById('ragNewProjectBtn').addEventListener('click', this.showNewProjectDialog.bind(this));
        document.getElementById('ragAddDocBtn').addEventListener('click', this.showAddDocumentDialog.bind(this));
        document.getElementById('ragDocSearch').addEventListener('input', this.filterDocuments.bind(this));
        document.getElementById('ragAutoContextToggle').addEventListener('change', this.toggleAutoSuggest.bind(this));
        
        // Listen for chat events
        document.addEventListener('llm-message-sending', this.onMessageSending.bind(this));
    },
    
    // Event handlers and methods
    showNewProjectDialog: function() {
        // Implementation
    },
    
    showAddDocumentDialog: function() {
        // Implementation
    },
    
    filterDocuments: function(event) {
        // Implementation
    },
    
    toggleAutoSuggest: function(event) {
        // Implementation
    },
    
    onMessageSending: function(event) {
        // Add context to message if necessary
        if (this.state.contextDocuments.length > 0) {
            // Add context to message
            const messageData = event.detail;
            messageData.contextDocuments = this.state.contextDocuments.map(doc => doc.id);
        }
    },
    
    // API methods
    API: {
        getProjects: async function() {
            // Implementation
            return fetch('/api/projects').then(r => r.json());
        },
        
        createProject: async function(data) {
            // Implementation
            return fetch('/api/projects', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            }).then(r => r.json());
        },
        
        // Other API methods
    }
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    if (document.body.hasAttribute('data-rag-enabled')) {
        window.LLMInterface.RAG.init();
    }
});
```

## Integration with LLM Interface

### Entry Point Modifications
The main interface loads RAG components conditionally:

```python
# In quiet_interface.py
RAG_ENABLED = os.environ.get("LLM_RAG_ENABLED") == "1"

# When preparing the HTML template
html_template = HTML_TEMPLATE

if RAG_ENABLED:
    # Add RAG attribute to body for JS detection
    html_template = html_template.replace("<body>", "<body data-rag-enabled=\"true\">")
    
    # Register RAG UI extensions
    from rag_support.ui_extensions import get_rag_ui_extensions
    extensions = get_rag_ui_extensions()
    
    # Apply extensions to template
    html_template = render_template_with_extensions(html_template, extensions)
```

### Model Response Integration
RAG context is passed to the model generation:

```javascript
// Original sendMessage function is extended
const originalSendMessage = window.LLMInterface.sendMessage;

window.LLMInterface.sendMessage = function(message, options) {
    // Get any RAG context if available
    if (window.LLMInterface.RAG && window.LLMInterface.RAG.state.contextDocuments.length > 0) {
        options = options || {};
        options.contextDocuments = window.LLMInterface.RAG.state.contextDocuments.map(doc => doc.id);
    }
    
    // Call original function with enhanced options
    return originalSendMessage(message, options);
};
```

## Implementation Phases (COMPLETED)

### Phase 1: Extension Point Setup ✅
1. ✅ Modified `quiet_interface.py` to include extension points in HTML_TEMPLATE
   - Added extension points for HEAD, SIDEBAR, MAIN_CONTROLS, DIALOGS, SCRIPTS
   - Implemented standardized marker format
2. ✅ Created the template processing function in ui_extensions.py
   - Added get_rag_ui_extensions() function
   - Added extension rendering logic
3. ✅ Tested basic extension mechanism
   - Verified extension points are properly detected and populated
   - Validated output HTML structure

### Phase 2: Core RAG UI Components ✅
1. ✅ Implemented project selector and management
   - Added project creation dialog
   - Implemented project selection dropdown
2. ✅ Implemented document list and search
   - Added document listing component
   - Implemented search functionality
3. ✅ Implemented context bar
   - Added context selection UI
   - Implemented context document display
4. ✅ Created necessary dialogs
   - Added document creation dialog
   - Added document viewing dialog

### Phase 3: Integration with Chat ✅
1. ✅ Connected context selection to message sending
   - Implemented message enhancement with context
   - Added context document transmission
2. ✅ Implemented auto-suggestion
   - Added toggle for auto-suggestion feature
   - Implemented query-based document suggestion
3. ✅ Added source attribution for responses
   - Added source display on responses
   - Implemented source tracking

## Testing Checklist

- [x] Project creation, selection and management works correctly
- [x] Documents can be added, viewed, and deleted
- [x] Document search filters correctly
- [x] Context selection works and appears in the context bar
- [x] LLM responses incorporate selected context
- [x] UI is responsive on mobile devices
- [x] Auto-suggest feature correctly identifies relevant documents
- [x] All components follow UI standards
- [x] Error handling shows appropriate messages

## Implementation Notes

In addition to the planned implementation, the following enhancements were added:

1. **Improved Template Integration**: Used a more flexible extension point system
2. **Enhanced Error Handling**: Added more robust error feedback in the UI
3. **Better Cross-Platform Support**: Fixed path handling for consistent operation
4. **Unified Documentation**: Updated USAGE.md with RAG instructions

## Dependencies

This implementation depends on these components:
- `quiet_interface.py` with extension points
- RAG API endpoints in `api_extensions.py`
- Project and document management in `project_manager.py`
- Search functionality in `search.py`

## Compatibility Considerations

- Ensures RAG functionality works alongside standard LLM interface
- Gracefully handles absence of RAG backend components
- Maintains performance when RAG features are disabled
- Works with existing model loading and inference code