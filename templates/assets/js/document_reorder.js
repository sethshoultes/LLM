/**
 * Document Reordering Module
 * Handles drag-and-drop reordering of context documents
 */

// Use LLM namespace
window.LLM = window.LLM || {};

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
            
            // Set draggable attributes
            item.setAttribute('draggable', 'true');
            
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
                    
                    // Add dragging class for styling
                    draggedItem.classList.add('dragging');
                    
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
            });
        });
    },
    
    updateDocumentOrder: function() {
        // Get all context items in their current order
        const contextItems = document.querySelectorAll('.context-item');
        const newOrder = Array.from(contextItems).map(item => item.getAttribute('data-id'));
        
        // Update the order in the context manager
        if (LLM.Components && LLM.Components.ContextManager) {
            console.log('Updating document order:', newOrder);
            
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
        }
    }
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    LLM.DocumentReorder.init();
});