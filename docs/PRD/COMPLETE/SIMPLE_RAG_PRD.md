# Minimal RAG Enhancement PRD

## Overview
Extend our existing LLM interface with simple document retrieval capabilities and project organization, while maintaining a unified codebase and prioritizing simplicity, speed, and offline usage.

## Core Principles
- **KISS**: Keep everything as simple as possible
- **DRY**: Extend existing code rather than creating duplicates
- **Offline-First**: All functionality must work without internet
- **Unified Interface**: Maintain a single entry point for all LLM interactions
- **Resource-Efficient**: Minimal memory/CPU footprint

## Implementation Approach
- Extend current `/Volumes/LLM/scripts/quiet_interface.py` rather than creating a new interface
- Add RAG support as optional functionality within existing UI
- Reuse existing model loading and inference code
- Keep the same API structure for compatibility

## Goals
- Add basic markdown file indexing and retrieval
- Implement simple project-based organization 
- Support artifact generation and archiving
- Maintain speed and responsiveness

## Challenges & Limitations (Devil's Advocate View)
- **Complexity Risk**: Adding features to existing codebase might make it harder to maintain
- **Storage Growth**: Even plain text can accumulate rapidly - need plan for cleanup
- **Search Quality**: Simple search may yield irrelevant results without vectors
- **Performance Degradation**: Search speed will decrease as document count grows
- **Context Window Limits**: Models have fixed context - too much retrieval hurts performance

## Extensions to Existing System

### 1. File Storage System
- Simple flat-file storage with directory-based organization
- Project structure adjacent to existing code:
  ```
  /rag_support/
    /projects/
      /{project_id}/
        /documents/
          /{doc_id}.md
        /artifacts/
          /{artifact_id}.{ext}
        project.json
  ```
- No database required (avoids SQLite overhead)

### 2. UI Enhancements
- Add project/document management panel as collapsible sidebar
- Document upload and search within existing interface
- Toggle for RAG mode in chat interface
- "Add context" button with document selector

### 3. API Extensions
- Add endpoints to the existing HTTP server:
  - `/api/projects` - Project management
  - `/api/projects/{id}/documents` - Document management
  - `/api/projects/{id}/search` - Document search
- Keep current model API endpoints unchanged

### 4. LLM Integration
- Use existing model loading and inference system
- Pass document context through current prompt template mechanism
- Add optional context-injection to the generation process

## User Flows

### Document Usage (in existing interface)
1. Toggle "RAG mode" in the interface
2. Import markdown files into current project
3. Select documents to include as context
4. Send messages with added context

### Artifact Generation (in existing interface)
1. Request LLM to create artifact (diagram, code, etc.)
2. View artifact in chat interface
3. Save artifact to project or export

## Technical Implementation

### Storage
- Plain files for maximum compatibility
- JSON for metadata
- Markdown for documents and artifacts

### Search
- Implemented with Python standard library
- Full-text basic pattern matching
- Tag-based filtering

### Code Organization
- Add RAG utilities as separate module imported by main interface
- Extend `RequestHandler` class to handle new endpoints
- Minimize changes to core model interaction code

## Implementation Phases

### Phase 1: Core RAG Module
- Implement project/document management utilities
- Create minimal search functionality
- Test independently of main interface

### Phase 2: UI Integration
- Extend existing HTML template with RAG components
- Add API endpoints to existing server
- Connect UI components to backend

### Phase 3: LLM Integration
- Add context support to inference process
- Implement document suggestion based on message content
- Add artifact saving functionality

## Progress Report
- [x] Created project documentation (PRD)
- [x] Added project organization structure
- [x] Implemented document management utilities
- [x] Created basic search functionality
- [x] Created API extensions
- [x] Integrated with existing interface
- [x] Added launch script for RAG-enhanced interface
- [x] Created user documentation
- [x] Committed changes to version control

## Decisions and Rationale
- **Single Interface**: Maintaining one interface avoids duplication and confusion
- **Flat-file Storage**: Simpler than database, easier to manage and backup
- **Lightweight Search**: Full vector embeddings would add unnecessary complexity
- **Optional RAG Mode**: Users can switch between simple and RAG-enhanced chat

## Code Review and Issues

### Strengths
- Maintains DRY principles by extending existing interface rather than duplicating
- Modular design with clear separation of concerns
- Simple file-based storage that works offline and is portable
- Lightweight search that doesn't require external dependencies
- Flexible project structure that can be extended

### Issues to Address

#### Critical Issues
1. **Hardcoded Paths**: All modules use hardcoded `/Volumes/LLM` path which breaks cross-platform compatibility
   - Fix: Use relative paths from script location or environment variables

2. **Error Handling**: Many operations lack robust error handling which could lead to silent failures
   - Fix: Add more comprehensive try/except blocks with error logging

3. **Context Management**: Adding too many documents to context could exceed model's context window
   - Fix: Add size estimation and warning when context gets too large

#### Moderate Issues
1. **UI Integration**: Current integration injects HTML/JS into existing template which may break with template changes
   - Fix: Use a more structured approach to UI extension

2. **Project Discovery**: No automatic discovery of existing projects on startup
   - Fix: Scan projects directory on initialization

3. **Performance Concerns**: Search implementation may not scale well with many documents
   - Fix: Add pagination and limit results

4. **Testing**: Lack of automated tests for the RAG components
   - Fix: Add unit and integration tests

#### Minor Issues
1. **Documentation**: API documentation is minimal
   - Fix: Add more detailed API documentation

2. **Caching Strategy**: Current caching of projects/documents may lead to stale data
   - Fix: Implement more robust cache invalidation

3. **Code Formatting**: Inconsistent indentation in some files
   - Fix: Apply consistent code formatting

### Future Improvements
1. Add option for lightweight vector embeddings for improved search (e.g., using a small model that runs offline)
2. Implement document versioning for tracking changes
3. Add import/export functionality for projects
4. Add basic visualization of document relevance
5. Implement document summarization to optimize context usage