# RAG UI Usage Guide

## Overview
This guide explains how to use the new tabbed sidebar interface for Retrieval-Augmented Generation (RAG) in our LLM environment. The new interface offers improved organization, mobile support, and better document management features.

## Getting Started

### Launching with RAG Features
Start the interface with RAG support:

```bash
./llm.sh --rag
```

This launches the interface with the tabbed sidebar enabled.

## Understanding the New Interface

### Tabbed Sidebar
The sidebar now has three tabs:
1. **Documents** - For managing projects and documents
2. **Context** - For viewing and managing selected context documents
3. **Settings** - For model selection and parameter controls

### Mobile Support
On mobile devices:
- The sidebar appears as a bottom drawer that can be pulled up
- A navigation bar at the bottom provides quick access to key functions
- All features are fully accessible on touch devices

## Tab Functions

### Documents Tab
This tab allows you to:
- Select or create projects
- Search for documents using the search box
- View and select documents to use as context
- Upload new documents

**Document Selection**:
- Use checkboxes to select multiple documents
- Use Shift+click for range selection
- Use Ctrl+click (Cmd+click on Mac) for multiple selection
- Click "Add Selected" to add documents to context

### Context Tab 
This tab shows:
- Currently selected context documents
- Token usage visualization
- Auto-suggest toggle

**Context Management**:
- Click on context items to expand and see details
- Drag and drop to reorder documents (affects priority)
- Click the X to remove a document from context
- Use "Clear All" to remove all context documents
- Toggle "Auto-suggest" to automatically find relevant documents

**Token Visualization**:
- The token bar shows total usage as a percentage
- Color coding indicates usage level (green, yellow, red)
- Individual document contributions are shown as segments

### Settings Tab
This tab contains:
- Model selection dropdown
- Generation parameters (temperature, max tokens, etc.)
- System prompt editor

## Advanced Features

### Keyboard Navigation
- Use Tab key to navigate interface elements
- Use arrow keys to move between tabs
- Press Space or Enter to activate buttons
- Use Home/End keys to jump to first/last tab

### Document Reordering
- Context documents can be dragged and reordered
- Order affects how context is prioritized for the model
- Documents at the top have higher priority

### Accessibility Features
- Full keyboard navigation support
- Screen reader compatibility with ARIA attributes
- High contrast mode support
- Focus indicators for keyboard users

## Tips for Effective Use

### Document Organization
- Keep documents focused and concise for better results
- Use clear, descriptive names for easy identification
- Add helpful tags when creating documents

### Context Management
- Monitor token usage to avoid exceeding model limits
- Remove unnecessary documents from context
- Reorder documents to prioritize most important information

### Mobile Usage
- Use the bottom tab bar for navigation
- Pull up the drawer to access sidebar functionality
- Pin the sidebar open on larger tablet screens

## Troubleshooting

### Interface Issues
- If tabs aren't responding, refresh the page
- If the sidebar is collapsed, click ❮ to expand it
- On mobile, ensure you're pulling from the handle at the top of the drawer

### Context Problems
- If token usage is too high (red), remove some documents
- If relevant documents aren't showing up in auto-suggest, try adding key terms from the document to your query
- If context reordering isn't working, ensure JavaScript is enabled

## Implementation Note
This new interface replaces the previous sidebar and context bar with a unified, tabbed approach that works across all device sizes while maintaining full functionality.