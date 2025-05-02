/**
 * Tabbed Sidebar Component
 * Handles the tabbed interface for the sidebar
 */

// Use LLM namespace
window.LLM = window.LLM || {};

LLM.TabbedSidebar = {
    selectedDocuments: [],
    
    init: function() {
        this.setupEventListeners();
        this.setupMockData(); // This would be replaced with actual data in production
        
        // Initialize document count
        if (LLM.Components && LLM.Components.ContextManager) {
            this.updateContextCount(LLM.Components.ContextManager.documents.length || 0);
            // Initialize token visualization with mock data for now
            this.updateTokenVisualization(this.mockDocuments);
        } else {
            this.updateContextCount(0);
        }
    },
    
    // This is temporary mock data for development/testing
    setupMockData: function() {
        this.mockDocuments = [
            { id: 'doc1', title: 'Introduction to RAG', tokens: 350, relevance: 0.92, auto_suggested: false },
            { id: 'doc2', title: 'Vector Embeddings', tokens: 420, relevance: 0.85, auto_suggested: true },
            { id: 'doc3', title: 'Context Window Optimization', tokens: 280, relevance: 0.78, auto_suggested: false },
            { id: 'doc4', title: 'Large Language Models', tokens: 510, relevance: 0.65, auto_suggested: true }
        ];
    },
    
    setupEventListeners: function() {
        const tabButtons = document.querySelectorAll('.tab-button');
        const selectAllBtn = document.getElementById('selectAllBtn');
        const deselectAllBtn = document.getElementById('deselectAllBtn');
        const addSelectedBtn = document.getElementById('addSelectedBtn');
        const drawerHandle = document.getElementById('drawerHandle');
        const sidebar = document.getElementById('sidebar');
        const sidebarToggle = document.querySelector('.sidebar-toggle');
        
        // Add click event listeners to tab buttons
        tabButtons.forEach(button => {
            button.addEventListener('click', this.switchTab.bind(this));
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
        });
        e.currentTarget.classList.add('active');
        
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
            const docId = checkbox.getAttribute('data-id');
            if (docId && !this.selectedDocuments.includes(docId)) {
                this.selectedDocuments.push(docId);
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
        
        // Add all selected documents to context
        if (LLM.Components && LLM.Components.ContextManager) {
            let addedCount = 0;
            
            this.selectedDocuments.forEach(docId => {
                // Find the document in the current document list
                const doc = LLM.Components.RAGSidebar && 
                            LLM.Components.RAGSidebar.documents.find(d => d.id === docId);
                
                if (doc) {
                    // Add to context if found
                    const added = LLM.Components.ContextManager.addDocument(doc);
                    if (added) addedCount++;
                }
            });
            
            // Give feedback
            alert(`Added ${addedCount} documents to context`);
            
            // Switch to the context tab
            const contextTabBtn = document.querySelector('.tab-button[data-tab="context"]');
            if (contextTabBtn) {
                contextTabBtn.click();
            }
        }
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
    
    // Add document to selected list
    addToSelected: function(docId) {
        if (!this.selectedDocuments.includes(docId)) {
            this.selectedDocuments.push(docId);
        }
    },
    
    // Remove document from selected list
    removeFromSelected: function(docId) {
        this.selectedDocuments = this.selectedDocuments.filter(id => id !== docId);
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
        const maxTokens = 2048; // Should be retrieved from API or config
        const percentage = Math.min(100, (totalTokens / maxTokens) * 100);
        
        // Update main token bar
        tokenUsed.style.width = `${percentage}%`;
        
        // Update token status text
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

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    LLM.TabbedSidebar.init();
});