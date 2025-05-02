/**
 * Mobile Navigation Module
 * Handles mobile-specific navigation and UI interactions
 */

// Use LLM namespace
window.LLM = window.LLM || {};

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
            } else {
                button.classList.remove('active');
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

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize on mobile devices
    if (window.innerWidth < 768) {
        LLM.MobileNavigation.init();
    }
});