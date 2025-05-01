#!/usr/bin/env python3
# ui_extensions.py - Extensions to the quiet_interface.py UI for RAG support

import os
from pathlib import Path

# Import BASE_DIR from rag_support
try:
    from rag_support import BASE_DIR
except ImportError:
    # Fallback if the import fails
    import os

    SCRIPT_DIR = Path(__file__).resolve().parent
    BASE_DIR = SCRIPT_DIR.parent
    # Use environment variable if available
    BASE_DIR = Path(os.environ.get("LLM_BASE_DIR", str(BASE_DIR)))

# CSS styles to add to the existing UI
RAG_CSS = """
/* RAG sidebar */
.interface-container {
    display: grid;
    grid-template-columns: 250px 1fr;
    gap: 1rem;
}

.sidebar {
    background: #fff;
    border-radius: 12px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    padding: 1rem;
    height: calc(100vh - 2rem);
    overflow-y: auto;
    display: flex;
    flex-direction: column;
}

.sidebar-section {
    margin-bottom: 1rem;
}

.sidebar-hidden .sidebar {
    display: none;
}

.sidebar-hidden .main-content {
    grid-column: 1 / -1;
}

.sidebar-toggle {
    font-size: 1.5rem;
    cursor: pointer;
    color: #333;
    background: none;
    border: none;
    padding: 0.5rem;
}

/* Document management */
.document-list {
    overflow-y: auto;
    flex-grow: 1;
    border-top: 1px solid #eee;
    padding-top: 0.5rem;
}

.document-item {
    padding: 0.5rem;
    border-bottom: 1px solid #eee;
    cursor: pointer;
    font-size: 0.9rem;
    display: flex;
    flex-direction: column;
}

.document-item:hover {
    background-color: #f5f5f5;
}

.document-item.selected {
    background-color: #e6f7ff;
    border-left: 2px solid #1890ff;
}

.document-selector {
    display: flex;
    align-items: flex-start;
    margin-bottom: 0.2rem;
}

.document-selector input[type="checkbox"] {
    margin-right: 0.5rem;
    margin-top: 0.2rem;
}

.document-title {
    font-weight: 500;
    flex: 1;
}

.document-meta {
    font-size: 0.8rem;
    color: #888;
}

.document-actions {
    display: flex;
    justify-content: flex-end;
    margin-top: 0.3rem;
}

.preview-btn {
    background: none;
    border: none;
    font-size: 1rem;
    cursor: pointer;
    padding: 0;
    margin-left: 0.5rem;
}

.tags-list {
    display: flex;
    flex-wrap: wrap;
    gap: 0.3rem;
    margin-top: 0.3rem;
}

.tag {
    background: #f0f0f0;
    padding: 0.1rem 0.4rem;
    border-radius: 10px;
    font-size: 0.7rem;
    color: #555;
}

/* Context bar */
.context-bar {
    background-color: #f9f9f9;
    border-radius: 8px;
    padding: 0.8rem;
    margin-bottom: 1rem;
    font-size: 0.9rem;
}

.context-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
}

.context-header h3 {
    margin: 0;
    font-size: 1rem;
    color: #333;
}

.small-btn {
    padding: 0.2rem 0.4rem;
    font-size: 0.8rem;
}

.context-title {
    font-weight: 500;
    margin-bottom: 0.3rem;
    font-size: 0.85rem;
    color: #666;
}

.context-items {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-bottom: 0.8rem;
}

.empty-context {
    color: #888;
    font-style: italic;
    font-size: 0.9rem;
    padding: 0.5rem 0;
}

.context-item {
    background-color: #e6f7ff;
    border-radius: 8px;
    padding: 0.3rem 0.6rem;
    font-size: 0.8rem;
    display: flex;
    align-items: center;
    gap: 0.3rem;
}

.context-stats {
    margin-top: 0.8rem;
    font-size: 0.8rem;
    color: #666;
}

.token-usage {
    margin-bottom: 0.5rem;
}

.token-bar {
    height: 8px;
    background-color: #eee;
    border-radius: 4px;
    overflow: hidden;
    margin-bottom: 0.3rem;
}

.token-used {
    height: 100%;
    background-color: #0070f3;
    border-radius: 4px;
    transition: width 0.3s ease;
}

.token-used.warning {
    background-color: #f5a623;
}

.token-used.danger {
    background-color: #ff4d4f;
}

.token-info {
    display: flex;
    justify-content: space-between;
    font-size: 0.75rem;
}

.remove-context {
    cursor: pointer;
    color: #999;
}

.remove-context:hover {
    color: #666;
}

/* Dialogs */
.overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0,0,0,0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
}

.dialog {
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    width: 500px;
    max-width: 90%;
    max-height: 90vh;
    overflow-y: auto;
}

.dialog-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
}

.dialog-content {
    margin-bottom: 1.5rem;
}

.dialog-footer {
    display: flex;
    justify-content: flex-end;
    gap: 0.8rem;
}

/* Responsive */
@media (max-width: 768px) {
    .interface-container {
        grid-template-columns: 1fr;
    }
    
    .sidebar-toggle-mobile {
        display: block;
        position: fixed;
        bottom: 1rem;
        right: 1rem;
        z-index: 101;
        width: 3rem;
        height: 3rem;
        border-radius: 50%;
        background: #0070f3;
        color: white;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
    }
}

/* Collapsible sidebar */
.sidebar-collapsed .interface-container {
    grid-template-columns: auto 1fr;
}

.sidebar-collapsed .sidebar {
    width: 50px;
    padding: 0.5rem;
}

.sidebar-collapsed .sidebar-section {
    display: none;
}

.sidebar-collapsed .sidebar-toggle-section {
    display: block;
}

.sidebar-collapsed .document-list {
    display: none;
}

/* Toggle switch */
.toggle-switch {
    display: flex;
    align-items: center;
    margin-bottom: 0.5rem;
    border-top: 1px solid #eee;
    padding-top: 0.8rem;
    margin-top: 0.8rem !important;
}

.toggle-switch label {
    margin-bottom: 0;
    margin-right: 0.5rem;
    font-size: 0.85rem;
    color: #333;
}

.toggle-hint {
    margin-top: 0.4rem;
    font-size: 0.8rem;
    color: #666;
    font-style: italic;
    width: 100%;
}

.switch {
    position: relative;
    display: inline-block;
    width: 40px;
    height: 20px;
}

.switch input {
    opacity: 0;
    width: 0;
    height: 0;
}

.slider {
    position: absolute;
    cursor: pointer;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: #ccc;
    transition: .2s;
    border-radius: 20px;
}

.slider:before {
    position: absolute;
    content: "";
    height: 14px;
    width: 14px;
    left: 3px;
    bottom: 3px;
    background-color: white;
    transition: .2s;
    border-radius: 50%;
}

input:checked + .slider {
    background-color: #0070f3;
}

input:checked + .slider:before {
    transform: translateX(20px);
}
"""

# HTML templates for the sidebar and dialogs
# Using tabbed sidebar component instead of sidebar
RAG_SIDEBAR_HTML = """
<!-- Sidebar now uses tabbed_sidebar -->
{% include "components/tabbed_sidebar/tabbed_sidebar.html" %}
"""

# Using tabbed sidebar component instead of context bar
RAG_CONTEXT_BAR_HTML = """
<!-- Context functionality is now integrated into the tabbed sidebar -->
"""

RAG_DIALOGS_HTML = """
<!-- New Project Dialog -->
<div class="overlay" id="newProjectDialog" style="display: none;">
    <div class="dialog">
        <div class="dialog-header">
            <h2>Create New Project</h2>
            <button class="text-button" id="closeNewProjectBtn">×</button>
        </div>
        <div class="dialog-content">
            <label for="projectName">Project Name:</label>
            <input type="text" id="projectName" placeholder="My Project">
            
            <label for="projectDescription">Description (optional):</label>
            <textarea id="projectDescription" placeholder="Project description..."></textarea>
        </div>
        <div class="dialog-footer">
            <button class="secondary-btn" id="cancelNewProjectBtn">Cancel</button>
            <button id="createProjectBtn">Create Project</button>
        </div>
    </div>
</div>

<!-- Add Document Dialog -->
<div class="overlay" id="addDocumentDialog" style="display: none;">
    <div class="dialog">
        <div class="dialog-header">
            <h2>Add Document</h2>
            <button class="text-button" id="closeAddDocumentBtn">×</button>
        </div>
        <div class="dialog-content">
            <label for="documentTitle">Document Title:</label>
            <input type="text" id="documentTitle" placeholder="Document title">
            
            <label for="documentTags">Tags (comma separated):</label>
            <input type="text" id="documentTags" placeholder="tag1, tag2, tag3">
            
            <label for="documentContent">Content (Markdown):</label>
            <textarea id="documentContent" placeholder="Document content in markdown format..." style="height: 200px;"></textarea>
        </div>
        <div class="dialog-footer">
            <button class="secondary-btn" id="cancelAddDocumentBtn">Cancel</button>
            <button id="saveDocumentBtn">Save Document</button>
        </div>
    </div>
</div>

<!-- View Document Dialog -->
<div class="overlay" id="viewDocumentDialog" style="display: none;">
    <div class="dialog">
        <div class="dialog-header">
            <h2 id="viewDocumentTitle">Document</h2>
            <button class="text-button" id="closeViewDocumentBtn">×</button>
        </div>
        <div class="dialog-content">
            <div class="tags-list" id="viewDocumentTags"></div>
            <div class="markdown" id="viewDocumentContent"></div>
        </div>
        <div class="dialog-footer">
            <button class="secondary-btn" id="editDocumentBtn">Edit</button>
            <button class="secondary-btn" id="useAsContextBtn">Use as Context</button>
            <button id="closeViewDocBtn">Close</button>
        </div>
    </div>
</div>
"""

# JavaScript for RAG functionality
RAG_JAVASCRIPT = """
// RAG functionality
const ragState = {
    currentProject: null,
    currentChat: null,
    documents: [],
    contextDocuments: [],
    // Default to true, but respect saved preference if it exists
    autoSuggestContext: localStorage.getItem('rag_auto_suggest') !== null 
        ? localStorage.getItem('rag_auto_suggest') === 'true' 
        : true
};

// Initialize RAG UI
function initRagUI() {
    // Add sidebar toggle button
    const chatContainer = document.querySelector('.card:nth-child(3)');
    if (chatContainer) {
        const toggleBtn = document.createElement('button');
        toggleBtn.className = 'sidebar-toggle';
        toggleBtn.innerHTML = '⋮';
        toggleBtn.title = 'Toggle RAG Sidebar';
        toggleBtn.onclick = toggleRagSidebar;
        
        chatContainer.insertBefore(toggleBtn, chatContainer.firstChild);
    }
    
    // Add context bar to chat interface
    const chatHistoryElement = document.getElementById('chatHistory');
    if (chatHistoryElement) {
        const contextBar = document.createElement('div');
        contextBar.innerHTML = RAG_CONTEXT_BAR_HTML;
        chatHistoryElement.parentNode.insertBefore(contextBar.firstElementChild, chatHistoryElement);
        
        // Make sure the context bar is visible
        const contextBarElement = document.getElementById('contextBar');
        if (contextBarElement) {
            contextBarElement.style.display = 'block';
            
            // Initialize the Auto-suggest toggle
            const autoToggle = document.getElementById('autoContextToggle');
            if (autoToggle) {
                autoToggle.checked = ragState.autoSuggestContext;
            }
        }
    }
    
    // Add event listeners
    setupRagEventListeners();
    
    // Load projects
    loadProjects();
    
    // Initialize the context bar with empty state message
    updateContextBar();
    
    // Add clear all button event listener
    document.getElementById('clearContextBtn')?.addEventListener('click', clearAllContextDocs);
}

// Setup event listeners for RAG UI
function setupRagEventListeners() {
    // Project management
    document.getElementById('newProjectBtn')?.addEventListener('click', showNewProjectDialog);
    document.getElementById('closeNewProjectBtn')?.addEventListener('click', hideNewProjectDialog);
    document.getElementById('cancelNewProjectBtn')?.addEventListener('click', hideNewProjectDialog);
    document.getElementById('createProjectBtn')?.addEventListener('click', createNewProject);
    document.getElementById('projectSelect')?.addEventListener('change', selectProject);
    
    // Document management
    document.getElementById('addDocumentBtn')?.addEventListener('click', showAddDocumentDialog);
    document.getElementById('closeAddDocumentBtn')?.addEventListener('click', hideAddDocumentDialog);
    document.getElementById('cancelAddDocumentBtn')?.addEventListener('click', hideAddDocumentDialog);
    document.getElementById('saveDocumentBtn')?.addEventListener('click', saveDocument);
    document.getElementById('refreshDocsBtn')?.addEventListener('click', () => loadDocuments(ragState.currentProject));
    
    // Document search
    document.getElementById('documentSearch')?.addEventListener('input', filterDocuments);
    document.getElementById('clearSearch')?.addEventListener('click', clearSearch);
    
    // Context management
    const autoToggle = document.getElementById('autoContextToggle');
    if (autoToggle) {
        // Set initial state from saved preference
        autoToggle.checked = ragState.autoSuggestContext;
        autoToggle.addEventListener('change', toggleAutoContext);
    }
    document.getElementById('refreshTokens')?.addEventListener('click', updateTokenCounts);
    
    // Monitor user input to update token counts
    document.getElementById('userInput')?.addEventListener('input', debounce(updateTokenCounts, 500));
    
    // Document viewing
    document.getElementById('closeViewDocumentBtn')?.addEventListener('click', hideViewDocumentDialog);
    document.getElementById('closeViewDocBtn')?.addEventListener('click', hideViewDocumentDialog);
    document.getElementById('useAsContextBtn')?.addEventListener('click', addCurrentDocToContext);
    document.getElementById('editDocumentBtn')?.addEventListener('click', editCurrentDocument);
    
    // Override send button to include context
    const originalSendBtn = document.getElementById('sendBtn');
    if (originalSendBtn) {
        const originalOnclick = originalSendBtn.onclick;
        originalSendBtn.onclick = function(e) {
            if (ragState.contextDocuments.length > 0) {
                sendMessageWithContext();
            } else {
                originalOnclick.call(this, e);
            }
        };
    }
}

// Toggle RAG sidebar visibility
function toggleRagSidebar() {
    document.body.classList.toggle('sidebar-hidden');
}

// API functions
async function fetchProjects() {
    try {
        const response = await fetch('/api/projects');
        const data = await response.json();
        return data.projects || [];
    } catch (error) {
        console.error('Error fetching projects:', error);
        return [];
    }
}

async function createProject(name, description) {
    try {
        const response = await fetch('/api/projects', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name, description })
        });
        return await response.json();
    } catch (error) {
        console.error('Error creating project:', error);
        return { error: 'Failed to create project' };
    }
}

async function fetchDocuments(projectId) {
    try {
        const response = await fetch(`/api/projects/${projectId}/documents`);
        const data = await response.json();
        return data.documents || [];
    } catch (error) {
        console.error('Error fetching documents:', error);
        return [];
    }
}

async function fetchDocument(projectId, documentId) {
    try {
        const response = await fetch(`/api/projects/${projectId}/documents/${documentId}`);
        return await response.json();
    } catch (error) {
        console.error('Error fetching document:', error);
        return { error: 'Failed to fetch document' };
    }
}

async function addDocument(projectId, title, content, tags) {
    try {
        const response = await fetch(`/api/projects/${projectId}/documents`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ title, content, tags })
        });
        return await response.json();
    } catch (error) {
        console.error('Error adding document:', error);
        return { error: 'Failed to add document' };
    }
}

async function searchDocuments(projectId, query) {
    try {
        const response = await fetch(`/api/projects/${projectId}/search?q=${encodeURIComponent(query)}`);
        const data = await response.json();
        return data.results || [];
    } catch (error) {
        console.error('Error searching documents:', error);
        return [];
    }
}

async function suggestRelevantDocuments(projectId, query) {
    try {
        const response = await fetch(`/api/projects/${projectId}/suggest?q=${encodeURIComponent(query)}`);
        const data = await response.json();
        return data.suggestions || [];
    } catch (error) {
        console.error('Error getting suggestions:', error);
        return [];
    }
}

async function estimateTokens(projectId, text, contextDocs) {
    try {
        const response = await fetch('/api/tokens', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                project_id: projectId,
                text: text,
                context_docs: contextDocs
            })
        });
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error estimating tokens:', error);
        return {
            total_tokens: 0,
            text_tokens: 0,
            context_tokens: 0,
            contexts: [],
            available_tokens: 0,
            is_over_limit: false
        };
    }
}

// UI Functions
function populateProjectSelector(projects) {
    const selector = document.getElementById('projectSelect');
    if (!selector) return;
    
    selector.innerHTML = '<option value="">Select Project</option>';
    
    projects.forEach(project => {
        const option = document.createElement('option');
        option.value = project.id;
        option.textContent = project.name;
        selector.appendChild(option);
    });
}

function updateProjectInfo(project) {
    const infoElement = document.getElementById('projectInfo');
    if (!infoElement) return;
    
    if (!project) {
        infoElement.textContent = 'No project selected';
        return;
    }
    
    infoElement.innerHTML = `
        <strong>${project.name}</strong><br>
        <span>${project.description || 'No description'}</span><br>
        <small>${project.document_count || 0} documents · 
               ${project.chat_count || 0} chats</small>
    `;
}

function renderDocumentList(documents) {
    const listElement = document.getElementById('documentList');
    if (!listElement) return;
    
    if (!documents || documents.length === 0) {
        listElement.innerHTML = '<div class="empty-state">No documents found</div>';
        return;
    }
    
    let html = '';
    documents.forEach(doc => {
        const isSelected = ragState.contextDocuments.some(d => d.id === doc.id);
        html += `
            <div class="document-item ${isSelected ? 'selected' : ''}" data-id="${doc.id}">
                <div class="document-selector">
                    <input type="checkbox" class="document-checkbox" id="doc-${doc.id}" ${isSelected ? 'checked' : ''}>
                    <div class="document-title">${doc.title}</div>
                </div>
                <div class="document-meta">
                    ${new Date(doc.updated_at).toLocaleDateString()}
                </div>
                <div class="tags-list">
                    ${(doc.tags || []).map(tag => `<span class="tag">${tag}</span>`).join('')}
                </div>
                <div class="document-actions">
                    <button class="preview-btn" data-id="${doc.id}" title="Preview">👁️</button>
                </div>
            </div>
        `;
    });
    
    listElement.innerHTML = html;
    
    // Add click event listeners for document view
    document.querySelectorAll('.document-item').forEach(item => {
        item.addEventListener('click', (e) => {
            // Only trigger view if not clicking on checkbox or preview button
            if (!e.target.closest('.document-checkbox') && !e.target.closest('.preview-btn')) {
                viewDocument(item.dataset.id);
            }
        });
    });
    
    // Add change listeners for checkboxes
    document.querySelectorAll('.document-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', (e) => {
            e.stopPropagation(); // Prevent triggering the document click event
            const docId = checkbox.closest('.document-item').dataset.id;
            const doc = ragState.documents.find(d => d.id === docId);
            
            if (checkbox.checked) {
                // Add to context documents if not already there
                if (!ragState.contextDocuments.some(d => d.id === docId) && doc) {
                    ragState.contextDocuments.push(doc);
                    updateContextBar();
                }
            } else {
                // Remove from context documents
                removeFromContext(docId);
            }
        });
    });
    
    // Add preview button handlers
    document.querySelectorAll('.preview-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation(); // Prevent triggering the document click event
            const docId = btn.dataset.id;
            viewDocument(docId);
        });
    });
}

function updateContextBar() {
    const contextBar = document.getElementById('contextBar');
    const contextItems = document.getElementById('contextItems');
    if (!contextBar || !contextItems) return;
    
    // Always show the context bar, even when empty
    contextBar.style.display = 'block';
    
    // Generate HTML for context documents
    let html = '';
    
    if (ragState.contextDocuments.length === 0) {
        // Show an empty state message in the context items area
        html = '<div class="empty-context">No documents selected. Use the checkboxes to add documents or enable Auto-suggest.</div>';
    } else {
        // Add document items
        ragState.contextDocuments.forEach(doc => {
            html += `
                <div class="context-item" data-id="${doc.id}">
                    ${doc.title}
                    <span class="remove-context" data-id="${doc.id}">×</span>
                </div>
            `;
        });
    }
    
    contextItems.innerHTML = html;
    
    // Add remove event listeners
    document.querySelectorAll('.remove-context').forEach(item => {
        item.addEventListener('click', (e) => {
            e.stopPropagation();
            removeFromContext(item.dataset.id);
        });
    });
    
    // Update token counts
    updateTokenCounts();
}

async function updateTokenCounts() {
    if (!ragState.currentProject || ragState.contextDocuments.length === 0) {
        // Reset token display
        resetTokenDisplay();
        return;
    }
    
    // Get current user input
    const userInput = document.getElementById('userInput')?.value || '';
    
    // Get context document IDs
    const contextDocIds = ragState.contextDocuments.map(doc => doc.id);
    
    try {
        // Call token estimation API
        const tokenInfo = await estimateTokens(
            ragState.currentProject,
            userInput,
            contextDocIds
        );
        
        // Update token display
        updateTokenDisplay(tokenInfo);
        
    } catch (error) {
        console.error('Error updating token counts:', error);
        resetTokenDisplay();
    }
}

function updateTokenDisplay(tokenInfo) {
    const tokenUsedElement = document.getElementById('tokenUsed');
    const tokenCountElement = document.getElementById('tokenCount');
    const tokenPercentageElement = document.getElementById('tokenPercentage');
    
    if (!tokenUsedElement || !tokenCountElement || !tokenPercentageElement) {
        return;
    }
    
    // Update token count text
    tokenCountElement.textContent = tokenInfo.total_tokens;
    tokenPercentageElement.textContent = `${tokenInfo.usage_percentage}%`;
    
    // Update token usage bar
    tokenUsedElement.style.width = `${tokenInfo.usage_percentage}%`;
    
    // Add warning or danger classes based on usage
    tokenUsedElement.classList.remove('warning', 'danger');
    if (tokenInfo.usage_percentage > 90) {
        tokenUsedElement.classList.add('danger');
    } else if (tokenInfo.usage_percentage > 75) {
        tokenUsedElement.classList.add('warning');
    }
}

function resetTokenDisplay() {
    const tokenUsedElement = document.getElementById('tokenUsed');
    const tokenCountElement = document.getElementById('tokenCount');
    const tokenPercentageElement = document.getElementById('tokenPercentage');
    
    if (!tokenUsedElement || !tokenCountElement || !tokenPercentageElement) {
        return;
    }
    
    // Reset to zero
    tokenCountElement.textContent = '0';
    tokenPercentageElement.textContent = '0%';
    tokenUsedElement.style.width = '0%';
    tokenUsedElement.classList.remove('warning', 'danger');
}

// Actions
function showNewProjectDialog() {
    const dialog = document.getElementById('newProjectDialog');
    if (!dialog) return;
    
    document.getElementById('projectName').value = '';
    document.getElementById('projectDescription').value = '';
    dialog.style.display = 'flex';
}

function hideNewProjectDialog() {
    const dialog = document.getElementById('newProjectDialog');
    if (dialog) dialog.style.display = 'none';
}

async function createNewProject() {
    const nameInput = document.getElementById('projectName');
    const descInput = document.getElementById('projectDescription');
    if (!nameInput || !descInput) return;
    
    const name = nameInput.value.trim();
    const description = descInput.value.trim();
    
    if (!name) {
        alert('Please enter a project name');
        return;
    }
    
    const result = await createProject(name, description);
    if (result.error) {
        alert(`Error: ${result.error}`);
        return;
    }
    
    hideNewProjectDialog();
    await loadProjects();
    
    // Select the new project
    const selector = document.getElementById('projectSelect');
    if (selector) {
        selector.value = result.id;
        await selectProject();
    }
}

async function loadProjects() {
    const projects = await fetchProjects();
    populateProjectSelector(projects);
}

async function selectProject() {
    const selector = document.getElementById('projectSelect');
    if (!selector) return;
    
    const projectId = selector.value;
    
    if (!projectId) {
        ragState.currentProject = null;
        updateProjectInfo(null);
        renderDocumentList([]);
        ragState.contextDocuments = [];
        updateContextBar();
        return;
    }
    
    try {
        const response = await fetch(`/api/projects/${projectId}`);
        const project = await response.json();
        
        ragState.currentProject = projectId;
        updateProjectInfo(project);
        
        // Load documents
        await loadDocuments(projectId);
        
        // Clear context
        ragState.contextDocuments = [];
        updateContextBar();
        
    } catch (error) {
        console.error('Error selecting project:', error);
        alert('Error loading project');
    }
}

async function loadDocuments(projectId) {
    if (!projectId) return;
    
    const documents = await fetchDocuments(projectId);
    ragState.documents = documents;
    renderDocumentList(documents);
}

function showAddDocumentDialog() {
    const dialog = document.getElementById('addDocumentDialog');
    if (!dialog) return;
    
    if (!ragState.currentProject) {
        alert('Please select a project first');
        return;
    }
    
    document.getElementById('documentTitle').value = '';
    document.getElementById('documentTags').value = '';
    document.getElementById('documentContent').value = '';
    dialog.style.display = 'flex';
}

function hideAddDocumentDialog() {
    const dialog = document.getElementById('addDocumentDialog');
    if (dialog) dialog.style.display = 'none';
}

async function saveDocument() {
    const titleInput = document.getElementById('documentTitle');
    const tagsInput = document.getElementById('documentTags');
    const contentInput = document.getElementById('documentContent');
    if (!titleInput || !tagsInput || !contentInput) return;
    
    const title = titleInput.value.trim();
    const content = contentInput.value.trim();
    const tagsText = tagsInput.value.trim();
    
    if (!title) {
        alert('Please enter a document title');
        return;
    }
    
    if (!content) {
        alert('Please enter document content');
        return;
    }
    
    // Parse tags
    const tags = tagsText ? tagsText.split(',').map(tag => tag.trim()).filter(Boolean) : [];
    
    const result = await addDocument(ragState.currentProject, title, content, tags);
    if (result.error) {
        alert(`Error: ${result.error}`);
        return;
    }
    
    hideAddDocumentDialog();
    await loadDocuments(ragState.currentProject);
}

function filterDocuments() {
    const searchInput = document.getElementById('documentSearch');
    if (!searchInput) return;
    
    const query = searchInput.value.trim().toLowerCase();
    
    if (!query) {
        renderDocumentList(ragState.documents);
        return;
    }
    
    const filtered = ragState.documents.filter(doc => {
        const titleMatch = doc.title.toLowerCase().includes(query);
        const tagMatch = doc.tags && doc.tags.some(tag => tag.toLowerCase().includes(query));
        return titleMatch || tagMatch;
    });
    
    renderDocumentList(filtered);
}

function clearSearch() {
    const searchInput = document.getElementById('documentSearch');
    if (searchInput) searchInput.value = '';
    renderDocumentList(ragState.documents);
}

async function viewDocument(docId) {
    const dialog = document.getElementById('viewDocumentDialog');
    if (!dialog) return;
    
    const doc = await fetchDocument(ragState.currentProject, docId);
    
    if (doc.error) {
        alert(`Error: ${doc.error}`);
        return;
    }
    
    document.getElementById('viewDocumentTitle').textContent = doc.title;
    
    // Render tags
    const tagsElement = document.getElementById('viewDocumentTags');
    if (tagsElement) {
        tagsElement.innerHTML = (doc.tags || [])
            .map(tag => `<span class="tag">${tag}</span>`)
            .join('');
    }
    
    // Render content as markdown
    const contentElement = document.getElementById('viewDocumentContent');
    if (contentElement) {
        contentElement.innerHTML = formatMarkdown(doc.content);
    }
    
    // Store current document ID for context adding
    dialog.dataset.docId = docId;
    
    dialog.style.display = 'flex';
}

function hideViewDocumentDialog() {
    const dialog = document.getElementById('viewDocumentDialog');
    if (dialog) dialog.style.display = 'none';
}

function addCurrentDocToContext() {
    const dialog = document.getElementById('viewDocumentDialog');
    if (!dialog) return;
    
    const docId = dialog.dataset.docId;
    const doc = ragState.documents.find(d => d.id === docId);
    
    if (!doc) return;
    
    // Add to context if not already there
    if (!ragState.contextDocuments.some(d => d.id === docId)) {
        ragState.contextDocuments.push(doc);
        updateContextBar();
        
        // Also check the checkbox in the document list
        const checkbox = document.querySelector(`input[id="doc-${docId}"]`);
        if (checkbox) {
            checkbox.checked = true;
        }
        
        renderDocumentList(ragState.documents); // Update selection state
    }
    
    hideViewDocumentDialog();
}

function removeFromContext(docId) {
    ragState.contextDocuments = ragState.contextDocuments.filter(doc => doc.id !== docId);
    updateContextBar();
    renderDocumentList(ragState.documents); // Update selection state
}

// Function to clear all context documents
function clearAllContextDocs() {
    ragState.contextDocuments = []; // Empty the array
    updateContextBar();
    renderDocumentList(ragState.documents); // Update selection state
}

function editCurrentDocument() {
    alert('Document editing not implemented in this demo');
}

function toggleAutoContext(e) {
    ragState.autoSuggestContext = e.target.checked;
    // Save preference to localStorage
    localStorage.setItem('rag_auto_suggest', e.target.checked);
}

async function sendMessageWithContext() {
    const userInput = document.getElementById('userInput');
    const modelSelect = document.getElementById('modelSelect');
    const systemInput = document.getElementById('systemInput');
    if (!userInput || !modelSelect || !systemInput) return;
    
    const message = userInput.value.trim();
    const modelPath = modelSelect.value;
    
    if (!message) return;
    if (!modelPath) {
        alert('Please select a model first');
        return;
    }
    
    // Get context documents
    const contextDocIds = ragState.contextDocuments.map(doc => doc.id);
    
    // Auto-suggest context if enabled
    if (ragState.autoSuggestContext && ragState.currentProject) {
        try {
            const suggestions = await suggestRelevantDocuments(ragState.currentProject, message);
            
            // Add suggested documents to context if not already there
            let newContextAdded = false;
            suggestions.forEach(suggestion => {
                if (!ragState.contextDocuments.some(doc => doc.id === suggestion.id)) {
                    const doc = ragState.documents.find(d => d.id === suggestion.id);
                    if (doc) {
                        ragState.contextDocuments.push(doc);
                        newContextAdded = true;
                    }
                }
            });
            
            if (newContextAdded) {
                updateContextBar();
                renderDocumentList(ragState.documents);
            }
        } catch (error) {
            console.error('Error suggesting context:', error);
        }
    }
    
    // Prepare context content
    let contextContent = '';
    let contextSummary = '';
    
    if (contextDocIds.length > 0 && ragState.currentProject) {
        for (const docId of contextDocIds) {
            try {
                const doc = await fetchDocument(ragState.currentProject, docId);
                if (doc && !doc.error) {
                    contextContent += `## ${doc.title}\n\n${doc.content}\n\n`;
                    contextSummary += `${doc.title}, `;
                }
            } catch (e) {
                console.error(`Error loading context document ${docId}:`, e);
            }
        }
        contextSummary = contextSummary.slice(0, -2); // Remove trailing comma and space
    }
    
    // Get system prompt
    let systemPrompt = systemInput.value.trim();
    
    // Add context to system prompt if available
    if (contextContent) {
        // Add context instruction to system prompt
        if (systemPrompt) {
            systemPrompt += "\n\n";
        }
        systemPrompt += "Use the following information to answer the user's question:\n\n" + contextContent;
    }
    
    // Add user message to chat history
    addMessageToHistory('user', message);
    
    // Clear input field
    userInput.value = '';
    
    // Show spinner
    const spinner = document.getElementById('spinner');
    if (spinner) spinner.style.display = 'inline-block';
    
    // Disable send button
    const sendBtn = document.getElementById('sendBtn');
    if (sendBtn) sendBtn.disabled = true;
    
    // Send request to API
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                model: modelPath,
                message: message,
                system: systemPrompt,
                temperature: parseFloat(document.getElementById('temperature')?.value || 0.7),
                max_tokens: parseInt(document.getElementById('maxTokens')?.value || 1024),
                top_p: parseFloat(document.getElementById('topP')?.value || 0.95),
                frequency_penalty: parseFloat(document.getElementById('freqPenalty')?.value || 0),
                history: [],
                context_docs: contextDocIds
            })
        });
        
        const data = await response.json();
        
        // Hide spinner
        if (spinner) spinner.style.display = 'none';
        
        let responseContent = data.response || 'No response from model';
        
        // Add context reference if context was used
        if (contextSummary) {
            responseContent += `\n\n*Sources: ${contextSummary}*`;
        }
        
        // Add assistant message to chat history
        addMessageToHistory('assistant', responseContent);
        
        // Show stats if available
        const statsDiv = document.getElementById('stats');
        if (statsDiv && (data.time_taken || data.tokens_generated)) {
            statsDiv.style.display = 'block';
            let statsText = `Generation time: ${data.time_taken}s | Tokens: ${data.tokens_generated}`;
            
            // Add model type and format if available
            if (data.model_type) {
                statsText += ` | Type: ${data.model_type}`;
            }
            if (data.model_format) {
                statsText += ` | Format: ${data.model_format}`;
            }
            
            statsDiv.textContent = statsText;
        }
    } catch (error) {
        console.error('Error sending message:', error);
        addMessageToHistory('assistant', 'Error: ' + error.message);
    } finally {
        // Re-enable send button
        if (sendBtn) sendBtn.disabled = false;
    }
}

function formatMarkdown(text) {
    // Very basic markdown formatting - in a real app, use a proper markdown library
    let html = text;
    
    // Code blocks
    html = html.replace(/```([a-z]*)\n([\s\S]*?)\n```/g, '<pre><code>$2</code></pre>');
    
    // Inline code
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
    
    // Headers
    html = html.replace(/^# (.*$)/gm, '<h1>$1</h1>');
    html = html.replace(/^## (.*$)/gm, '<h2>$1</h2>');
    html = html.replace(/^### (.*$)/gm, '<h3>$1</h3>');
    
    // Bold and italic
    html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');
    
    // Links
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>');
    
    // Lists (basic)
    html = html.replace(/^\s*\*\s*(.*)/gm, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>\n)<li>/g, '$1<li>');
    html = html.replace(/(<li>.*<\/li>)/g, '<ul>$1</ul>');
    
    // Line breaks
    html = html.replace(/\n/g, '<br>');
    
    return html;
}

// Utility function to debounce frequent events
function debounce(func, delay) {
    let timeout;
    return function(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), delay);
    };
}

// Helper function to add message to history (copied from existing chat UI)
function addMessageToHistory(role, content) {
    if (typeof chatHistory === 'undefined') {
        console.error('Chat history not available');
        return;
    }
    
    chatHistory.push({
        role,
        content,
        timestamp: Date.now()
    });
    
    try {
        saveChatHistory();
    } catch (e) {
        console.error('Error saving chat history:', e);
    }
    
    renderChatHistory();
}

// Inject RAG UI elements and initialize
document.addEventListener('DOMContentLoaded', function() {
    // Create a wrapper for the content instead of replacing innerHTML directly
    const wrapper = document.createElement('div');
    wrapper.className = 'interface-container';
    
    // Create sidebar element
    const sidebar = document.createElement('div');
    sidebar.innerHTML = RAG_SIDEBAR_HTML;
    
    // Create main content container
    const mainContent = document.createElement('div');
    mainContent.className = 'main-content';
    
    // Move all body children to main content
    while (document.body.firstChild) {
        mainContent.appendChild(document.body.firstChild);
    }
    
    // Add sidebar and main content to wrapper
    wrapper.appendChild(sidebar.firstElementChild);
    wrapper.appendChild(mainContent);
    
    // Create dialogs container
    const dialogs = document.createElement('div');
    dialogs.className = 'rag-dialogs';
    dialogs.innerHTML = RAG_DIALOGS_HTML;
    
    // Add wrapper and dialogs to body
    document.body.appendChild(wrapper);
    while (dialogs.firstChild) {
        document.body.appendChild(dialogs.firstChild);
    }
    
    // Inject CSS
    const styleTag = document.createElement('style');
    styleTag.textContent = RAG_CSS;
    document.head.appendChild(styleTag);
    
    // Initialize RAG UI after a short delay to ensure the original UI is ready
    setTimeout(initRagUI, 500);
});
"""


# Function to get extension point content
def get_rag_ui_extensions():
    """Get the RAG UI extensions for each extension point

    Returns a dictionary with extension point names as keys and content as values
    """
    extensions = {
        "HEAD": f"<style>{RAG_CSS}</style>",
        "SIDEBAR_EXTENSIONS": RAG_SIDEBAR_HTML,
        "MAIN_CONTROLS": RAG_CONTEXT_BAR_HTML,
        "DIALOGS": RAG_DIALOGS_HTML,
        "SCRIPTS": f"<script>{RAG_JAVASCRIPT}</script>",
    }

    return extensions


# Function to get HTML with RAG extensions
def get_extended_html_template():
    """Get the HTML template with RAG extensions

    This function modifies the original HTML template to add RAG support
    without duplicating the entire interface
    """
    from scripts.quiet_interface import HTML_TEMPLATE

    # Load original template
    html = HTML_TEMPLATE

    # Get extensions
    extensions = get_rag_ui_extensions()

    # Apply extensions to template
    for point, content in extensions.items():
        marker = f"<!-- EXTENSION_POINT: {point} -->"

        # For the SCRIPTS extension point, wrap in proper script tags
        if point == "SCRIPTS":
            # Properly escape any problematic JavaScript characters
            # Ensure the script content is properly formatted
            escaped_content = content.replace("${", r"$\{").replace("`", r"\`")
            html = html.replace(marker, f"{marker}\n{escaped_content}")
        else:
            html = html.replace(marker, f"{marker}\n{content}")

    return html
