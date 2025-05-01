# RAG UI Improvements PRD

## Overview

The current RAG (Retrieval-Augmented Generation) UI has several issues that need to be addressed:

1. **Disjointed Layout**: The interface feels fragmented with unclear visual hierarchy
2. **Inconsistent Styling**: Multiple styling approaches are being used
3. **Redundant Controls**: Some controls have overlapping functionality
4. **Poor Information Architecture**: Important controls are buried while less important ones are prominent
5. **Suboptimal User Flow**: The document selection and context management flow is not intuitive

This PRD outlines a comprehensive plan to improve the RAG UI by creating a more cohesive, intuitive, and streamlined experience.

## Current UI Analysis

### Sidebar
- Project selection and document browsing are in a separate sidebar
- Document list takes up most of the space
- Search functionality is underutilized
- Document selection requires multiple clicks

### Context Bar
- Appears as a separate component above the chat interface
- Contains controls for Auto-suggest, Clear All, and token information
- Selected documents are shown as pills with limited information
- Empty state message when no documents are selected

### Chat Interface
- Standard chat interface below the context bar
- No direct visual connection to the context documents
- Limited feedback about how context affects the model's responses

## Proposed Improvements

### 1. Unified Layout with Tabs

**Problem**: The interface is split between sidebar and context bar, with unclear relationships between components.

**Solution**: Create a unified sidebar with tabs for different functions:

```
┌─────────────────────────────┐┌───────────────────────────┐
│ [Documents] [Context] [Chat]││                           │
├─────────────────────────────┤│                           │
│                             ││                           │
│  Document-specific content  ││                           │
│  based on selected tab      ││     Chat Interface        │
│                             ││                           │
│  • When "Documents" active: ││                           │
│    Show project selection,  ││                           │
│    document list & search   ││                           │
│                             ││                           │
│  • When "Context" active:   ││                           │
│    Show selected documents  ││                           │
│    with token usage,        ││                           │
│    controls for removing    ││                           │
│                             ││                           │
│  • When "Chat" active:      ││                           │
│    Show chat history,       ││                           │
│    parameters, system       ││                           │
│    prompt settings          ││                           │
│                             ││                           │
└─────────────────────────────┘└───────────────────────────┘
```

### 2. Contextual Controls

**Problem**: Controls are scattered across the interface with unclear context.

**Solution**: Group controls logically by function and show them only in relevant tabs:

- **Documents Tab**:
  - Project selector + New Project button
  - Document search
  - Add Document button
  - Document list with selection checkboxes
  - Refresh button

- **Context Tab**:
  - Auto-suggest toggle with tooltip
  - Clear All button
  - Token usage visualization
  - List of selected documents with remove option
  - Additional context for each document (tokens used, relevance score)

- **Chat Tab**:
  - Model selector
  - Parameter controls (temperature, etc.)
  - System prompt editor
  - Chat history controls (clear, export)

### 3. Improved Document Selection Flow

**Problem**: Adding documents to context is cumbersome and requires multiple actions.

**Solution**: Simplify with more intuitive interactions:

- Allow multi-select in document list with checkboxes
- Add "Add to Context" button that appears when documents are selected
- Provide visual feedback when documents are added to context
- Show count of documents in Context tab (e.g., "Context (3)")

### 4. Enhanced Context Visualization

**Problem**: It's hard to understand how context documents affect the response.

**Solution**: Provide clear visualization of context influence:

- Add collapsible sections in the Context tab to group documents by source/type
- Show token usage for each document proportionally
- Indicate which documents were auto-suggested vs. manually selected
- Add relevance score visualization for auto-suggested documents
- Allow reordering documents to prioritize certain context

### 5. Mobile-Responsive Design

**Problem**: Current interface doesn't adapt well to small screens.

**Solution**: Create a responsive layout that works on all devices:

- On mobile: Collapsible bottom drawer for context management
- Tab bar at the bottom for switching between Documents/Context/Chat
- Simplified controls that work well with touch interactions

## Detailed Component Specifications

### Unified Sidebar with Tabs

```html
<div class="sidebar">
  <div class="sidebar-tabs">
    <button class="tab-button active" data-tab="documents">Documents</button>
    <button class="tab-button" data-tab="context">Context <span class="count">0</span></button>
    <button class="tab-button" data-tab="chat-settings">Settings</button>
  </div>
  
  <div class="tab-content">
    <!-- Documents Tab Content -->
    <div class="tab-pane active" id="documents-tab">
      <!-- Project selection & document management -->
    </div>
    
    <!-- Context Tab Content -->
    <div class="tab-pane" id="context-tab">
      <!-- Selected documents & context controls -->
    </div>
    
    <!-- Chat Settings Tab Content -->
    <div class="tab-pane" id="chat-settings-tab">
      <!-- Model & parameter settings -->
    </div>
  </div>
</div>
```

### Enhanced Context Items

```html
<div class="context-item">
  <div class="context-item-header">
    <div class="context-item-title">Document Title</div>
    <div class="context-item-actions">
      <button class="context-item-expand">▾</button>
      <button class="context-item-remove">×</button>
    </div>
  </div>
  
  <div class="context-item-details">
    <div class="context-item-stats">
      <div class="token-count">145 tokens (7%)</div>
      <div class="relevance-score">
        Relevance: <span class="score high">0.92</span>
        <span class="auto-suggested-badge">Auto-suggested</span>
      </div>
    </div>
    
    <div class="context-item-preview">
      Document preview text truncated to 2-3 lines with ellipsis...
    </div>
  </div>
</div>
```

## Implementation Plan

### Phase 1: Layout Restructuring
- Create tabbed sidebar structure
- Move existing functionality into appropriate tabs
- Ensure all current features remain accessible

### Phase 2: Enhanced Context Management
- Implement improved document selection flow
- Add enhanced context visualization
- Improve token usage display

### Phase 3: Mobile Optimization
- Add responsive breakpoints
- Create mobile-specific layouts
- Test and optimize touch interactions

### Phase 4: Visual Polish
- Unify styling across components
- Add smooth transitions between states
- Improve visual hierarchy and information display

## Success Metrics

1. **Usability**: Reduce clicks needed to add documents to context by 30%
2. **Clarity**: Improve user understanding of which documents are influencing responses
3. **Efficiency**: Reduce time spent managing context by 40%
4. **Adoption**: Increase usage of advanced features like Auto-suggest by 50%
5. **Satisfaction**: Gather positive feedback on the new interface through user testing

## Appendix: Style Guide

### Colors
- Primary: #1890ff (blue)
- Secondary: #52c41a (green)
- Warning: #faad14 (amber)
- Danger: #f5222d (red)
- Background: #f5f7f9
- Card Background: #ffffff
- Border: #e1e4e8

### Typography
- Base Size: 14px
- Headings: 18px, 16px, 14px (h1, h2, h3)
- UI Controls: 13px 
- Metadata: 12px

### Spacing
- Base Unit: 8px
- Compact: 4px
- Standard: 8px
- Large: 16px
- Extra Large: 24px