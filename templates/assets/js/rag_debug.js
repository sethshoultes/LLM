/**
 * Debug script for RAG UI
 * This helps diagnose issues with the RAG interface
 */

// Execute debug function when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Wait for 2 seconds to ensure everything is loaded
    setTimeout(function() {
        console.log("RAG Debug - Starting diagnostics");
        
        // Check if basic structures exist
        console.log("Basic structures:");
        console.log("- window.API exists:", !!window.API);
        console.log("- window.API.RAG exists:", !!(window.API && window.API.RAG));
        console.log("- window.ragState exists:", !!window.ragState);
        console.log("- LLM.TabbedSidebar exists:", !!(window.LLM && window.LLM.TabbedSidebar));
        
        // Check if critical DOM elements exist
        console.log("\nDOM elements:");
        console.log("- #projectSelect exists:", !!document.getElementById('projectSelect'));
        console.log("- #documentList exists:", !!document.getElementById('documentList'));
        console.log("- #contextItems exists:", !!document.getElementById('contextItems'));
        console.log("- Tab buttons exist:", !!document.querySelector('.tab-button'));
        
        // Check event listeners
        const projectSelect = document.getElementById('projectSelect');
        if (projectSelect) {
            console.log("\nChecking projectSelect event listeners...");
            const oldValue = projectSelect.value;
            
            // Create and dispatch a change event
            const event = new Event('change');
            projectSelect.dispatchEvent(event);
            
            console.log("- Change event dispatched to projectSelect");
        }
        
        // Print RAG state if it exists
        if (window.ragState) {
            console.log("\nCurrent RAG state:");
            console.log("- currentProject:", window.ragState.currentProject);
            console.log("- documents count:", (window.ragState.documents || []).length);
            console.log("- contextDocuments count:", (window.ragState.contextDocuments || []).length);
            console.log("- autoSuggestContext:", window.ragState.autoSuggestContext);
        }
        
        // Check API functionality
        if (window.API && window.API.RAG) {
            console.log("\nTesting API.RAG.getProjects()...");
            window.API.RAG.getProjects()
                .then(response => {
                    console.log("- API.RAG.getProjects() successful");
                    console.log("- Response:", response);
                    
                    // If projects exist, try to load documents for the first project
                    if (response && response.data && response.data.length > 0) {
                        const firstProject = response.data[0];
                        console.log("\nTesting API.RAG.getDocuments for project:", firstProject.id);
                        
                        return window.API.RAG.getDocuments(firstProject.id)
                            .then(docResponse => {
                                console.log("- API.RAG.getDocuments() successful");
                                console.log("- Documents response:", docResponse);
                                console.log("- Documents found:", docResponse.data ? docResponse.data.length : 0);
                                
                                // Try to get a single document
                                if (docResponse.data && docResponse.data.length > 0) {
                                    const firstDoc = docResponse.data[0];
                                    console.log("\nTesting API.RAG.getDocument for:", firstDoc.id);
                                    
                                    return window.API.RAG.getDocument(firstProject.id, firstDoc.id)
                                        .then(singleDocResp => {
                                            console.log("- API.RAG.getDocument() successful");
                                            console.log("- Document response:", singleDocResp);
                                            return { project: firstProject, docs: docResponse, singleDoc: singleDocResp };
                                        });
                                }
                                
                                return { project: firstProject, docs: docResponse };
                            });
                    }
                })
                .catch(error => {
                    console.error("- API.RAG.getProjects() failed:", error);
                });
        }
        
        // List all global functions related to RAG
        console.log("\nGlobal RAG functions:");
        const ragFunctions = Object.keys(window).filter(key => 
            typeof window[key] === 'function' && 
            (key.toLowerCase().includes('rag') || 
             key.toLowerCase().includes('project') || 
             key.toLowerCase().includes('document') || 
             key.toLowerCase().includes('context'))
        );
        console.log("- Found functions:", ragFunctions);
        
        console.log("\nRAG Debug - Diagnostics complete");
    }, 2000);
});