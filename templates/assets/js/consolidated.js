/**
 * Consolidated JavaScript for the RAG UI
 * 
 * Contains:
 * - TabbedSidebar component
 * - DocumentReorder component
 * - MobileNavigation component
 */

// Use LLM namespace
window.LLM = window.LLM || {};

// Tabbed Sidebar Component
LLM.TabbedSidebar = {
    selectedDocuments: [],
    mockDocuments: [],
    currentProjectId: null,
    
    // Utility function for screen reader announcements
    announceToScreenReader: function(message) {
        // Create or get the live region
        let liveRegion = document.getElementById('sr-announcer');
        if (!liveRegion) {
            liveRegion = document.createElement('div');
            liveRegion.id = 'sr-announcer';
            liveRegion.className = 'sr-only';
            liveRegion.setAttribute('aria-live', 'assertive');
            liveRegion.setAttribute('aria-atomic', 'true');
            document.body.appendChild(liveRegion);
        }
        
        // Set the message text
        liveRegion.textContent = message;
        
        // Clear after a short delay
        setTimeout(() => {
            liveRegion.textContent = '';
        }, 3000);
    },
    
    // Required methods for RAGSidebar compatibility
    getSelectedDocuments: function() {
        return this.selectedDocuments;
    },
    
    getCurrentProject: function() {
        return this.currentProjectId;
    },
    
    init: function() {
        this.setupEventListeners();
        this.setupMockData(); // This would be replaced with actual data in production
        
        // Render the document list with the mock data
        this.renderDocumentList(this.mockDocuments);
        
        // Initialize document count
        if (LLM.Components && LLM.Components.ContextManager) {
            this.updateContextCount(LLM.Components.ContextManager.documents.length || 0);
            // Initialize token visualization with mock data for now
            this.updateTokenVisualization(this.mockDocuments);
        } else {
            this.updateContextCount(0);
        }
    },
    
    // Initialize document data
    setupMockData: function() {
        // In production, this should fetch actual data from the server
        // For now, use sample data if no real data is available
        
        if (window.ragState && window.ragState.documents && window.ragState.documents.length > 0) {
            // Use data from RAG state if available
            this.mockDocuments = window.ragState.documents;
        } else if (LLM.Components && 
                  LLM.Components.ContextManager && 
                  LLM.Components.ContextManager.documents && 
                  LLM.Components.ContextManager.documents.length > 0) {
            
            // Use real data if available
            this.mockDocuments = LLM.Components.ContextManager.documents;
        } else {
            // Fallback to sample data
            this.mockDocuments = [
                { id: 'doc1', title: 'Introduction to RAG', tokens: 350, relevance: 0.92, auto_suggested: false },
                { id: 'doc2', title: 'Vector Embeddings', tokens: 420, relevance: 0.85, auto_suggested: true },
                { id: 'doc3', title: 'Context Window Optimization', tokens: 280, relevance: 0.78, auto_suggested: false },
                { id: 'doc4', title: 'Large Language Models', tokens: 510, relevance: 0.65, auto_suggested: true }
            ];
        }
    },
    
    renderDocumentList: function(documents) {
        const listElement = document.getElementById('documentList');
        if (!listElement) return;
        
        if (!documents || documents.length === 0) {
            listElement.innerHTML = '<div class="empty-state">No documents found</div>';
            return;
        }
        
        console.log("Rendering document list with", documents.length, "documents");
        
        // Clear the selectedDocuments array since we're re-rendering the list
        this.selectedDocuments = [];
        
        let html = '';
        documents.forEach(doc => {
            if (!doc.id) {
                console.warn("Document missing ID, skipping:", doc);
                return;
            }
            
            const isSelected = false; // Start fresh with no selections
            html += `
                <div class="document-item ${isSelected ? 'selected' : ''}" data-id="${doc.id}">
                    <div class="document-selector">
                        <input type="checkbox" class="document-checkbox" id="doc-${doc.id}" ${isSelected ? 'checked' : ''}>
                        <label for="doc-${doc.id}" class="document-name">${doc.title || 'Untitled'}</label>
                    </div>
                    <div class="document-meta">
                        ${doc.updated_at ? new Date(doc.updated_at).toLocaleDateString() : 'Sample document'}
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
        
        // Attach event listeners to the new elements
        this.attachDocumentListEventListeners();
    },
    
    attachDocumentListEventListeners: function() {
        // Add checkbox event listeners
        document.querySelectorAll('.document-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', e => {
                const docId = checkbox.closest('.document-item').dataset.id;
                if (checkbox.checked) {
                    this.addToSelected(docId);
                } else {
                    this.removeFromSelected(docId);
                }
            });
        });
        
        // Add preview button listeners
        document.querySelectorAll('.preview-btn').forEach(btn => {
            btn.addEventListener('click', e => {
                e.stopPropagation();
                const docId = btn.dataset.id;
                if (window.viewDocument) {
                    window.viewDocument(docId);
                } else if (this.currentProjectId) {
                    // Use the API to fetch document details
                    window.API.RAG.getDocument(this.currentProjectId, docId)
                        .then(response => {
                            console.log("Document response:", response);
                            // Check if we have data in the right format
                            const doc = response && response.data ? response.data : response;
                            
                            if (doc && doc.title) {
                                // Show a basic preview of the document
                                alert(`Document: ${doc.title}\n\nContent: ${doc.content.substring(0, 200)}${doc.content.length > 200 ? '...' : ''}`);
                            } else {
                                alert('Could not retrieve document details');
                            }
                        })
                        .catch(error => {
                            console.error("Error fetching document:", error);
                            alert('Error fetching document. Please try again.');
                        });
                } else {
                    alert('Please select a project first');
                }
            });
        });
    },
    
    setupEventListeners: function() {
        const tabButtons = document.querySelectorAll('.tab-button');
        const selectAllBtn = document.getElementById('selectAllBtn');
        const deselectAllBtn = document.getElementById('deselectAllBtn');
        const addSelectedBtn = document.getElementById('addSelectedBtn');
        const drawerHandle = document.getElementById('drawerHandle');
        const sidebar = document.getElementById('sidebar');
        const sidebarToggle = document.querySelector('.sidebar-toggle');
        const documentSearch = document.getElementById('documentSearch');
        const clearSearch = document.getElementById('clearSearch');
        
        // Add click event listeners to tab buttons
        tabButtons.forEach(button => {
            button.addEventListener('click', this.switchTab.bind(this));
            
            // Add keyboard support for tabs
            button.addEventListener('keydown', (e) => {
                // Handle arrow keys for tab navigation
                if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
                    e.preventDefault();
                    const tabs = Array.from(tabButtons);
                    const currentIndex = tabs.indexOf(e.target);
                    let nextIndex;
                    
                    if (e.key === 'ArrowRight') {
                        nextIndex = (currentIndex + 1) % tabs.length;
                    } else {
                        nextIndex = (currentIndex - 1 + tabs.length) % tabs.length;
                    }
                    
                    tabs[nextIndex].focus();
                    tabs[nextIndex].click();
                }
                // Handle Home and End keys
                else if (e.key === 'Home') {
                    e.preventDefault();
                    tabButtons[0].focus();
                    tabButtons[0].click();
                }
                else if (e.key === 'End') {
                    e.preventDefault();
                    tabButtons[tabButtons.length - 1].focus();
                    tabButtons[tabButtons.length - 1].click();
                }
            });
        });
        
        // Document selection buttons
        if (selectAllBtn) {
            selectAllBtn.addEventListener('click', this.selectAllDocuments.bind(this));
        }
        
        if (deselectAllBtn) {
            deselectAllBtn.addEventListener('click', this.deselectAllDocuments.bind(this));
        }
        
        if (addSelectedBtn) {
            addSelectedBtn.addEventListener('click', this.addSelectedToContext.bind(this));
        }
        
        // Document search
        if (documentSearch) {
            documentSearch.addEventListener('input', this.filterDocuments.bind(this));
        }
        
        if (clearSearch) {
            clearSearch.addEventListener('click', this.clearSearch.bind(this));
        }
        
        // Mobile drawer handle
        if (drawerHandle && sidebar) {
            drawerHandle.addEventListener('click', () => {
                sidebar.classList.toggle('expanded');
            });
            
            // Also allow tapping the handle area when expanded to collapse
            sidebar.addEventListener('click', (e) => {
                // Only close if clicking directly on the sidebar background near the top
                // (not on any of its children)
                if (e.target === sidebar && e.clientY < sidebar.offsetTop + 40) {
                    sidebar.classList.remove('expanded');
                }
            });
        }
        
        // Sidebar toggle for desktop
        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', () => {
                document.body.classList.toggle('sidebar-collapsed');
            });
        }
        
        // Set up keyboard shortcuts for document selection
        document.addEventListener('keydown', this.handleKeyboardShortcuts.bind(this));
        
        // Handle mobile orientation changes
        this.setupResponsiveHandling();
    },
    
    // Setup responsive handling
    setupResponsiveHandling: function() {
        // Detect mobile vs desktop view
        const isMobile = () => window.innerWidth < 768;
        
        // Initial setup based on screen size
        if (isMobile()) {
            this.setupMobileView();
        } else {
            this.setupDesktopView();
        }
        
        // Listen for resize events
        window.addEventListener('resize', () => {
            if (isMobile()) {
                this.setupMobileView();
            } else {
                this.setupDesktopView();
            }
        });
    },
    
    // Set up mobile view
    setupMobileView: function() {
        const sidebar = document.getElementById('sidebar');
        if (sidebar) {
            sidebar.classList.remove('expanded');
        }
    },
    
    // Set up desktop view
    setupDesktopView: function() {
        const sidebar = document.getElementById('sidebar');
        if (sidebar) {
            sidebar.classList.remove('expanded');
        }
        document.body.classList.remove('sidebar-collapsed');
    },
    
    switchTab: function(e) {
        const targetTab = e.currentTarget.getAttribute('data-tab');
        
        // Update active tab button
        document.querySelectorAll('.tab-button').forEach(button => {
            button.classList.remove('active');
            button.setAttribute('aria-selected', 'false');
        });
        e.currentTarget.classList.add('active');
        e.currentTarget.setAttribute('aria-selected', 'true');
        
        // Update active tab pane
        document.querySelectorAll('.tab-pane').forEach(pane => {
            pane.classList.remove('active');
        });
        document.getElementById(`${targetTab}Tab`).classList.add('active');
    },
    
    updateContextCount: function(count) {
        const countElements = document.querySelectorAll('.context-count');
        countElements.forEach(element => {
            element.textContent = count;
        });
    },
    
    selectAllDocuments: function() {
        const checkboxes = document.querySelectorAll('.document-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.checked = true;
            
            // Add to selected documents if not already there
            const docItem = checkbox.closest('.document-item');
            if (docItem) {
                const docId = docItem.getAttribute('data-id');
                if (docId && !this.selectedDocuments.includes(docId)) {
                    this.selectedDocuments.push(docId);
                }
            }
        });
    },
    
    deselectAllDocuments: function() {
        const checkboxes = document.querySelectorAll('.document-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.checked = false;
        });
        
        this.selectedDocuments = [];
    },
    
    addSelectedToContext: function() {
        // Check if we have any documents selected
        if (this.selectedDocuments.length === 0) {
            alert('No documents selected');
            return;
        }
        
        // Check if project is selected
        if (!this.currentProjectId) {
            alert('Please select a project first');
            return;
        }
        
        // Add documents to context
        let addedCount = 0;
        let promises = [];
        
        // Make a single API call to get documents for this project
        window.API.RAG.getDocuments(this.currentProjectId)
            .then(response => {
                console.log("All documents response:", response);
                // Get the list of all documents
                const allDocs = response && response.data ? response.data : [];
                
                if (allDocs.length === 0) {
                    console.warn("No documents found in project");
                    alert("No documents found in this project");
                    return;
                }
                
                // Filter to only the selected document IDs
                const selectedDocs = allDocs.filter(doc => 
                    this.selectedDocuments.includes(doc.id)
                );
                
                console.log("Found", selectedDocs.length, "selected documents in the project");
                
                // Check if we have any selected documents
                if (selectedDocs.length === 0) {
                    alert("No documents selected. Please select documents first.");
                    return;
                }
                
                // Add each document to the context
                selectedDocs.forEach(doc => {
                    console.log("Adding document to context:", doc.title);
                    
                    let docAdded = false;
                    
                    // Add to window.ragState.contextDocuments if it exists
                    if (window.ragState && window.ragState.contextDocuments) {
                        if (!window.ragState.contextDocuments.some(d => d.id === doc.id)) {
                            window.ragState.contextDocuments.push(doc);
                            docAdded = true;
                            console.log("Added to ragState context");
                        }
                    }
                    
                    // Also try to add to the context manager if available
                    if (window.LLM.Components && window.LLM.Components.ContextManager) {
                        try {
                            if (!LLM.Components.ContextManager.documents.some(d => d.id === doc.id)) {
                                LLM.Components.ContextManager.addDocument(doc);
                                docAdded = true;
                                console.log("Added to ContextManager");
                            }
                        } catch (e) {
                            console.error("Error adding to context manager:", e);
                        }
                    }
                    
                    // Increment the counter if the document was added to any system
                    if (docAdded) {
                        addedCount++;
                    }
                    
                    // Make sure the document ID is in the selectedDocuments array for RAGSidebar integration
                    if (!this.selectedDocuments.includes(doc.id)) {
                        this.selectedDocuments.push(doc.id);
                        console.log("Added to selectedDocuments array for RAGSidebar integration");
                    }
                });
                
                // Update the context UI if function exists
                if (typeof window.updateContextBar === 'function') {
                    window.updateContextBar();
                }
                
                // Give feedback (only if we actually added something)
                if (addedCount > 0) {
                    alert(`Added ${addedCount} documents to context`);
                } else {
                    console.log("No new documents were added to context");
                }
                
                // Switch to the context tab
                const contextTabBtn = document.querySelector('.tab-button[data-tab="context"]');
                if (contextTabBtn) {
                    contextTabBtn.click();
                }
            })
            .catch(error => {
                console.error("Error loading documents:", error);
                alert("Error loading documents. Please try again.");
            });
        
        // No need for Promise.all anymore as we're handling everything in the API call above
    },
    
    handleKeyboardShortcuts: function(e) {
        // Handle Shift+click or Ctrl+click for document selection
        if ((e.shiftKey || e.ctrlKey) && e.target.classList.contains('document-checkbox')) {
            if (e.shiftKey) {
                // Implement range selection (select all checkboxes between last clicked and current)
                const checkboxes = Array.from(document.querySelectorAll('.document-checkbox'));
                const currentIndex = checkboxes.indexOf(e.target);
                
                // Find the index of the last checked checkbox
                const lastCheckedIndex = checkboxes.findIndex(cb => cb.checked && cb !== e.target);
                
                if (lastCheckedIndex !== -1) {
                    // Determine the range to select
                    const start = Math.min(currentIndex, lastCheckedIndex);
                    const end = Math.max(currentIndex, lastCheckedIndex);
                    
                    // Check all checkboxes in the range
                    for (let i = start; i <= end; i++) {
                        checkboxes[i].checked = true;
                        
                        // Add to selected documents if not already there
                        const docId = checkboxes[i].getAttribute('data-id');
                        if (docId && !this.selectedDocuments.includes(docId)) {
                            this.selectedDocuments.push(docId);
                        }
                    }
                    
                    // Prevent the default checkbox toggle behavior
                    e.preventDefault();
                }
            }
        }
    },
    
    // Filter documents based on search query
    filterDocuments: function() {
        const searchInput = document.getElementById('documentSearch');
        if (!searchInput) return;
        
        const query = searchInput.value.trim().toLowerCase();
        
        if (!query) {
            this.renderDocumentList(this.mockDocuments);
            return;
        }
        
        const filtered = this.mockDocuments.filter(doc => {
            const titleMatch = doc.title.toLowerCase().includes(query);
            const tagMatch = doc.tags && doc.tags.some(tag => tag.toLowerCase().includes(query));
            return titleMatch || tagMatch;
        });
        
        this.renderDocumentList(filtered);
    },
    
    // Clear search input and reset document list
    clearSearch: function() {
        const searchInput = document.getElementById('documentSearch');
        if (searchInput) {
            searchInput.value = '';
            this.renderDocumentList(this.mockDocuments);
        }
    },
    
    // Add document to selected list
    addToSelected: function(docId) {
        if (!this.selectedDocuments.includes(docId)) {
            this.selectedDocuments.push(docId);
            // Announce the selection for screen readers
            this.announceToScreenReader('Document added to selection');
        }
    },
    
    // Remove document from selected list
    removeFromSelected: function(docId) {
        this.selectedDocuments = this.selectedDocuments.filter(id => id !== docId);
        // Announce the deselection for screen readers
        this.announceToScreenReader('Document removed from selection');
    },
    
    // Handle context document expansion
    setupContextItemActions: function() {
        // Add click handler to all context items
        document.querySelectorAll('.context-item').forEach(item => {
            // Toggle expansion on click
            item.addEventListener('click', (e) => {
                // Don't toggle if clicking on remove button
                if (e.target.classList.contains('context-item-remove')) {
                    return;
                }
                
                // Toggle expanded class
                item.classList.toggle('expanded');
            });
        });
    },
    
    // Update token visualization with per-document contributions
    updateTokenVisualization: function(documents) {
        if (!documents || documents.length === 0) return;
        
        const barContainer = document.querySelector('.token-bar-container');
        const tokenStatus = document.getElementById('tokenStatus');
        const tokenBar = document.querySelector('.token-bar');
        const tokenUsed = document.getElementById('tokenUsed');
        
        if (!barContainer || !tokenStatus || !tokenBar || !tokenUsed) return;
        
        // Calculate total tokens and percentage
        const totalTokens = documents.reduce((sum, doc) => sum + (doc.tokens || 0), 0);
        
        // Get max tokens from ContextManager if available, or use default
        let maxTokens = 2048;
        if (LLM.Components && 
            LLM.Components.ContextManager && 
            LLM.Components.ContextManager.maxTokens) {
            maxTokens = LLM.Components.ContextManager.maxTokens;
        }
        
        const percentage = Math.min(100, (totalTokens / maxTokens) * 100);
        
        // Update main token bar
        tokenUsed.style.width = `${percentage}%`;
        
        // Update token status text and ARIA attributes
        const tokenBarContainer = document.querySelector('.token-bar-container');
        if (tokenBarContainer) {
            tokenBarContainer.setAttribute('aria-valuenow', Math.round(percentage));
        }
        
        if (percentage > 90) {
            tokenStatus.textContent = 'High usage';
            tokenUsed.className = 'token-used token-high';
        } else if (percentage > 70) {
            tokenStatus.textContent = 'Medium usage';
            tokenUsed.className = 'token-used token-medium';
        } else {
            tokenStatus.textContent = 'Low usage';
            tokenUsed.className = 'token-used token-low';
        }
        
        // Clear existing contribution markers
        document.querySelectorAll('.token-contribution').forEach(marker => {
            marker.remove();
        });
        
        // Only show individual contributions if we have multiple documents
        if (documents.length > 1) {
            // Sort documents by token count (highest first)
            const sortedDocs = [...documents].sort((a, b) => (b.tokens || 0) - (a.tokens || 0));
            
            // Calculate start position
            let startPosition = 0;
            
            // Add contribution markers for each document
            sortedDocs.forEach((doc, index) => {
                const docTokens = doc.tokens || 0;
                const docPercentage = (docTokens / maxTokens) * 100;
                
                // Create marker element
                const marker = document.createElement('div');
                marker.className = `token-contribution token-contribution-${(index % 7) + 1}`;
                marker.style.width = `${docPercentage}%`;
                marker.style.left = `${startPosition}%`;
                marker.title = `${doc.title || doc.id}: ${docTokens} tokens`;
                
                // Add to container
                barContainer.appendChild(marker);
                
                // Update start position for next marker
                startPosition += docPercentage;
            });
        }
    }
};

// Document Reordering Module
LLM.DocumentReorder = {
    init: function() {
        // Get the document container
        const contextItems = document.getElementById('contextItems');
        
        if (!contextItems) return;
        
        // Make the context items container sortable
        this.setupSortable(contextItems);
    },
    
    setupSortable: function(container) {
        // Track the dragged item and position
        let draggedItem = null;
        let placeholder = null;
        let startY = 0;
        
        // Handle dragstart
        const handleDragStart = (e) => {
            // Set the dragged item
            draggedItem = e.target;
            
            // Set data to enable dragging
            e.dataTransfer.effectAllowed = 'move';
            e.dataTransfer.setData('text/html', draggedItem.innerHTML);
            
            // Add dragging class for styling
            draggedItem.classList.add('dragging');
            
            // Create placeholder
            placeholder = document.createElement('div');
            placeholder.className = 'context-item placeholder';
            placeholder.style.height = `${draggedItem.offsetHeight}px`;
            
            // Record initial position
            startY = e.clientY;
        };
        
        // Handle dragover
        const handleDragOver = (e) => {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
            
            // Only proceed if we have a dragged item
            if (!draggedItem) return;
            
            // Find the target item being dragged over
            const targetItem = e.target.closest('.context-item');
            
            if (targetItem && targetItem !== draggedItem && targetItem !== placeholder) {
                // Determine if dragging up or down
                const targetRect = targetItem.getBoundingClientRect();
                const targetCenter = targetRect.top + (targetRect.height / 2);
                
                if (e.clientY < targetCenter) {
                    // Insert before target
                    container.insertBefore(placeholder, targetItem);
                } else {
                    // Insert after target
                    container.insertBefore(placeholder, targetItem.nextSibling);
                }
            }
        };
        
        // Handle drop
        const handleDrop = (e) => {
            e.preventDefault();
            
            // Only proceed if we have a dragged item
            if (!draggedItem || !placeholder) return;
            
            // Insert the dragged item where the placeholder is
            container.insertBefore(draggedItem, placeholder);
            
            // Remove the placeholder
            container.removeChild(placeholder);
            placeholder = null;
            
            // Update the document order in the model
            this.updateDocumentOrder();
            
            // Reset dragged item
            draggedItem.classList.remove('dragging');
            draggedItem = null;
        };
        
        // Handle dragend (cleanup)
        const handleDragEnd = () => {
            if (draggedItem) {
                draggedItem.classList.remove('dragging');
                draggedItem = null;
            }
            
            if (placeholder && placeholder.parentNode) {
                placeholder.parentNode.removeChild(placeholder);
                placeholder = null;
            }
        };
        
        // Add event listeners to container
        container.addEventListener('dragover', handleDragOver);
        container.addEventListener('drop', handleDrop);
        
        // Add event listeners to all existing context items
        this.setupDraggableItems(container);
        
        // Configure a mutation observer to handle new items
        const observer = new MutationObserver((mutations) => {
            mutations.forEach(mutation => {
                if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                    this.setupDraggableItems(container);
                }
            });
        });
        
        observer.observe(container, { childList: true });
    },
    
    setupDraggableItems: function(container) {
        // Make all context items draggable
        const items = container.querySelectorAll('.context-item');
        
        items.forEach(item => {
            // Skip if already draggable
            if (item.getAttribute('draggable') === 'true') return;
            
            // Set draggable attributes and roles for accessibility
            item.setAttribute('draggable', 'true');
            item.setAttribute('role', 'listitem');
            item.setAttribute('aria-grabbed', 'false');
            
            // Add drag event listeners
            item.addEventListener('dragstart', (e) => {
                // Don't initiate drag if clicking on the remove button
                if (e.target.classList.contains('context-item-remove')) {
                    e.preventDefault();
                    return false;
                }
                
                // Initialize the drag operation
                const handleDragStart = () => {
                    // Set the dragged item
                    const draggedItem = e.target;
                    
                    // Set data to enable dragging
                    e.dataTransfer.effectAllowed = 'move';
                    e.dataTransfer.setData('text/html', draggedItem.innerHTML);
                    
                    // Add dragging class for styling and update ARIA
                    draggedItem.classList.add('dragging');
                    draggedItem.setAttribute('aria-grabbed', 'true');
                    
                    // Create placeholder
                    const placeholder = document.createElement('div');
                    placeholder.className = 'context-item placeholder';
                    placeholder.style.height = `${draggedItem.offsetHeight}px`;
                    
                    // Insert placeholder
                    container.insertBefore(placeholder, draggedItem.nextSibling);
                };
                
                handleDragStart();
            });
            
            item.addEventListener('dragend', (e) => {
                e.target.classList.remove('dragging');
                e.target.setAttribute('aria-grabbed', 'false');
            });
        });
    },
    
    updateDocumentOrder: function() {
        // Get all context items in their current order
        const contextItems = document.querySelectorAll('.context-item');
        const newOrder = Array.from(contextItems).map(item => item.getAttribute('data-id'));
        
        // Update the order in the context manager
        if (LLM.Components && LLM.Components.ContextManager) {
            // Update document order in the context manager
            
            // Sort the documents array based on the new order
            LLM.Components.ContextManager.documents.sort((a, b) => {
                const aIndex = newOrder.indexOf(a.id);
                const bIndex = newOrder.indexOf(b.id);
                
                if (aIndex === -1) return 1;
                if (bIndex === -1) return -1;
                
                return aIndex - bIndex;
            });
            
            // Update UI
            LLM.Components.ContextManager.updateUI();
            
            // Announce reordering for screen readers
            if (LLM.TabbedSidebar && LLM.TabbedSidebar.announceToScreenReader) {
                LLM.TabbedSidebar.announceToScreenReader('Documents reordered');
            }
        }
    }
};

// Mobile Navigation Module
LLM.MobileNavigation = {
    init: function() {
        this.setupEventListeners();
        this.setupInitialState();
    },
    
    setupEventListeners: function() {
        const mobileTabBar = document.getElementById('mobileTabBar');
        if (!mobileTabBar) return;
        
        // Add click event listeners to mobile tab buttons
        const tabButtons = mobileTabBar.querySelectorAll('.mobile-tab-button');
        tabButtons.forEach(button => {
            button.addEventListener('click', this.handleTabClick.bind(this));
        });
    },
    
    setupInitialState: function() {
        // Initially set the Chat tab as active
        this.setActiveTab('chat');
    },
    
    handleTabClick: function(e) {
        const targetTab = e.currentTarget.getAttribute('data-target');
        this.setActiveTab(targetTab);
    },
    
    setActiveTab: function(targetTab) {
        // Update mobile tab button active state
        const tabButtons = document.querySelectorAll('.mobile-tab-button');
        tabButtons.forEach(button => {
            if (button.getAttribute('data-target') === targetTab) {
                button.classList.add('active');
                button.setAttribute('aria-pressed', 'true');
            } else {
                button.classList.remove('active');
                button.setAttribute('aria-pressed', 'false');
            }
        });
        
        // Handle tab-specific actions
        switch (targetTab) {
            case 'documents':
            case 'context':
            case 'settings':
                // Show the sidebar drawer with the appropriate tab
                this.showSidebarDrawer(targetTab);
                break;
                
            case 'chat':
                // Hide the sidebar drawer and show the chat
                this.hideSidebarDrawer();
                break;
        }
    },
    
    showSidebarDrawer: function(targetTab) {
        const sidebar = document.getElementById('sidebar');
        if (!sidebar) return;
        
        // Expand the drawer
        sidebar.classList.add('expanded');
        
        // Switch to the requested tab
        const tabButton = document.querySelector(`.tab-button[data-tab="${targetTab}"]`);
        if (tabButton) {
            tabButton.click();
        }
    },
    
    hideSidebarDrawer: function() {
        const sidebar = document.getElementById('sidebar');
        if (!sidebar) return;
        
        // Collapse the drawer
        sidebar.classList.remove('expanded');
    }
};

// Initialize all components when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Check if we're in a context with RAG enabled
    const isRagEnabled = document.body.hasAttribute('data-rag-enabled');
    
    if (isRagEnabled) {
        // RAG is enabled, initializing components
        
        // Initialize tabbed sidebar
        if (LLM.TabbedSidebar) {
            LLM.TabbedSidebar.init();
            
            // Register as LLM.Components.RAGSidebar
            if (!LLM.Components) {
                LLM.Components = {};
            }
            
            // Set TabbedSidebar as the RAGSidebar component
            // This enables context integration with the chat interface
            LLM.Components.RAGSidebar = LLM.TabbedSidebar;
        }
        
        // Initialize document reordering
        if (LLM.DocumentReorder) {
            LLM.DocumentReorder.init();
        }
        
        // Initialize mobile navigation (only on mobile devices)
        if (window.innerWidth < 768 && LLM.MobileNavigation) {
            LLM.MobileNavigation.init();
        }
        
        // Load projects and documents using the API
        setTimeout(function() {
            // Setup project selector event listener
            const projectSelect = document.getElementById('projectSelect');
            if (projectSelect) {
                projectSelect.addEventListener('change', function() {
                    const projectId = this.value;
                    if (projectId) {
                        console.log("Loading documents for project:", projectId);
                        // Load documents for the selected project
                        window.API.RAG.getDocuments(projectId)
                            .then(response => {
                                console.log("Documents response:", response);
                                // Check for data in the correct format
                                const documents = response && response.data ? response.data : [];
                                
                                // Store the current project ID for later use
                                LLM.TabbedSidebar.currentProjectId = projectId;
                                
                                // Update the documents list
                                LLM.TabbedSidebar.mockDocuments = documents;
                                LLM.TabbedSidebar.renderDocumentList(documents);
                                
                                console.log("Loaded " + documents.length + " documents");
                            })
                            .catch(error => {
                                console.error("Error loading documents:", error);
                                alert("Error loading documents. Please try again.");
                            });
                    }
                });
            }
            
            // Load projects from the API
            if (window.API && window.API.RAG) {
                window.API.RAG.getProjects()
                    .then(response => {
                        console.log("Projects response:", response);
                        // Check for data in the correct format
                        const projects = response && response.data ? response.data : [];
                        
                        if (projects && projects.length > 0) {
                            const selector = document.getElementById('projectSelect');
                            if (selector) {
                                // Keep the default option
                                const defaultOption = selector.querySelector('option[value=""]');
                                selector.innerHTML = '';
                                if (defaultOption) {
                                    selector.appendChild(defaultOption);
                                }
                                
                                // Add project options
                                projects.forEach(project => {
                                    const option = document.createElement('option');
                                    option.value = project.id;
                                    option.textContent = project.name;
                                    selector.appendChild(option);
                                });
                                
                                console.log("Added " + projects.length + " projects to dropdown");
                            }
                        }
                    })
                    .catch(error => {
                        console.error("Error fetching projects:", error);
                    });
            }
        }, 1000); // 1 second delay to ensure everything is loaded
    }
});