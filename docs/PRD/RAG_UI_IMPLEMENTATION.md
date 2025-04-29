# RAG UI Implementation Guide

## Overview
This document outlines the implementation approach for integrating the Retrieval Augmented Generation (RAG) user interface components into the LLM interface, following the global UI Integration Standards.

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

## Implementation Phases

### Phase 1: Extension Point Setup
1. Modify `quiet_interface.py` to include extension points in HTML_TEMPLATE
2. Create the template processing function
3. Test basic extension mechanism

### Phase 2: Core RAG UI Components
1. Implement project selector and management
2. Implement document list and search
3. Implement context bar
4. Create necessary dialogs

### Phase 3: Integration with Chat
1. Connect context selection to message sending
2. Implement auto-suggestion based on message content
3. Display sources for responses that used context

## Testing Checklist

- [ ] Project creation, selection and management works correctly
- [ ] Documents can be added, viewed, and deleted
- [ ] Document search filters correctly
- [ ] Context selection works and appears in the context bar
- [ ] LLM responses incorporate selected context
- [ ] UI is responsive on mobile devices
- [ ] Auto-suggest feature correctly identifies relevant documents
- [ ] All components follow UI standards
- [ ] Error handling shows appropriate messages

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