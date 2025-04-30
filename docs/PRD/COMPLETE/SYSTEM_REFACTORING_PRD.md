# System Refactoring PRD

## Overview

This PRD outlines a comprehensive refactoring plan for the LLM platform to address inefficiencies, code duplication, and architectural issues identified during the code review. The goal is to create a more modular, maintainable, and efficient codebase that strictly adheres to DRY (Don't Repeat Yourself) and KISS (Keep It Simple, Stupid) principles.

## Current State Assessment

### Core Components
1. **Main Application (llm.sh)** - Shell script entry point
2. **Web Interface (quiet_interface.py)** - HTTP server with UI and API endpoints
3. **Inference Engine (minimal_inference_quiet.py)** - Model loading and text generation
4. **RAG Support Modules** - Project management, search, and context handling

### Key Issues Identified

1. **Code Duplication**
   - Multiple implementations of document parsing (project_manager.py and search.py)
   - Duplicated token estimation logic across modules
   - Redundant file system operations

2. **Inconsistent Error Handling**
   - Mixture of logging, print statements, and error responses
   - Inconsistent exception handling across modules

3. **Tight Coupling**
   - Hard-coded paths and dependencies
   - Direct imports creating circular dependencies
   - Insufficient abstraction layers

4. **Configuration Management**
   - Environment variables mixed with hardcoded values
   - Lack of centralized configuration
   - Inconsistent path handling

5. **Inefficient Resource Management**
   - Multiple instances where models are unnecessarily reloaded
   - Suboptimal caching strategies
   - Duplicated computations

## Architecture Improvements

### 1. Core System Layer

Implement a proper layered architecture:

```
LLM Platform
├── Core (core/)
│   ├── Configuration (config.py)
│   ├── Logging (logging.py)
│   ├── Paths (paths.py)
│   └── Errors (errors.py)
├── Models (models/)
│   ├── Registry (registry.py)
│   ├── Loader (loader.py)
│   └── Generation (generation.py)
├── Web (web/)
│   ├── Server (server.py)
│   ├── API (api.py)
│   └── Templates (templates.py)
└── RAG (rag/)
    ├── Projects (projects.py)
    ├── Documents (documents.py)
    ├── Search (search.py)
    └── Context (context.py)
```

### 2. Central Configuration System

Create a unified configuration system that:
- Loads from environment variables, config files, and command-line arguments
- Provides sensible defaults
- Validates configuration values
- Offers a clean API for accessing configuration

### 3. Unified Token Management

Implement a single source of truth for token-related operations:
- Standard token estimation based on model type
- Context window management
- Token allocation strategies
- Token usage tracking

### 4. Common Data Models

Establish well-defined data models for all entities:
- Documents, Projects, Chats, Messages, Artifacts
- Model metadata and capabilities
- API requests and responses

## Implementation Plan

### Phase 1: Core Infrastructure

1. **Create Core Module**
   - Implement the centralized configuration system
   - Develop unified error handling and logging
   - Establish a consistent path resolution mechanism
   - Create a clean API for environment and runtime information

2. **Refactor Model Management**
   - Extract model handling from minimal_inference_quiet.py to a dedicated module
   - Implement a model registry with proper metadata
   - Create a unified model loading strategy with smart caching
   - Standardize prompt formatting across different model types

### Phase 2: RAG System Refactoring

1. **Consolidate Document Operations**
   - Create a unified document handling module
   - Standardize frontmatter parsing
   - Implement proper document versioning and metadata
   - Create a consistent document storage layer

2. **Improve Search Functionality**
   - Refactor the search engine for better performance
   - Implement a proper inverted index for faster searching
   - Add semantic search capabilities alongside keyword search
   - Create a unified document relevance scoring system

3. **Enhance Context Management**
   - Centralize token allocation strategies
   - Improve document prioritization algorithms
   - Implement adaptive context management based on model capabilities
   - Add feedback mechanisms to improve context selection over time

### Phase 3: Web Interface and API

1. **Modernize Server Implementation**
   - Replace the custom HTTP handler with a lightweight framework
   - Implement proper routing with standardized patterns
   - Create a modular middleware system
   - Improve error handling and request validation

2. **Standardize API Architecture**
   - Create a consistent RESTful API design
   - Implement proper API versioning
   - Add comprehensive request validation
   - Create detailed API documentation

3. **Enhance Template System**
   - Improve template organization and inheritance
   - Implement component-based UI architecture
   - Add proper asset bundling and caching
   - Create a development mode with hot reloading

## Technical Specifications

### 1. Unified Document Module

```python
# documents.py (pseudocode)
class Document:
    """Unified document representation"""
    
    def __init__(self, id, title, content, metadata=None):
        self.id = id
        self.title = title
        self.content = content
        self.metadata = metadata or {}
        
    @classmethod
    def from_file(cls, file_path):
        """Create document from a file"""
        content = read_file(file_path)
        return cls.from_content(file_path.stem, content)
    
    @classmethod
    def from_content(cls, id, content):
        """Create document from content string"""
        # Parse frontmatter if present
        metadata, content = parse_frontmatter(content)
        return cls(
            id=id, 
            title=metadata.get('title', id),
            content=content,
            metadata=metadata
        )
    
    def to_dict(self):
        """Convert to dictionary representation"""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            **self.metadata
        }
    
    def save(self, directory):
        """Save document to file"""
        # Format with frontmatter
        formatted = format_with_frontmatter(self)
        write_file(directory / f"{self.id}.md", formatted)
```

### 2. Centralized Configuration

```python
# config.py (pseudocode)
class Config:
    """Centralized configuration management"""
    
    def __init__(self):
        self._config = {
            'debug': False,
            'rag_enabled': False,
            'smart_context': True,
            'model_paths': [],
            'base_dir': None,
            'port': 5100,
            'max_port': 5110
        }
        self._load_from_env()
        self._load_from_files()
    
    def _load_from_env(self):
        """Load configuration from environment variables"""
        # Map environment variables to configuration keys
        env_mapping = {
            'LLM_DEBUG_MODE': ('debug', bool),
            'LLM_RAG_ENABLED': ('rag_enabled', bool),
            'LLM_RAG_SMART_CONTEXT': ('smart_context', bool),
            'LLM_BASE_DIR': ('base_dir', Path),
        }
        
        for env_var, (config_key, convert) in env_mapping.items():
            if env_var in os.environ:
                self._config[config_key] = convert(os.environ[env_var])
    
    def get(self, key, default=None):
        """Get configuration value"""
        return self._config.get(key, default)
    
    def set(self, key, value):
        """Set configuration value"""
        self._config[key] = value
```

### 3. Token Management

```python
# tokens.py (pseudocode)
class TokenManager:
    """Centralized token management"""
    
    def __init__(self, model_registry):
        self.model_registry = model_registry
    
    def estimate_tokens(self, text, model_path=None):
        """Estimate tokens for text with model-specific tokenizer if available"""
        if not text:
            return 0
            
        # Use model-specific tokenizer if available
        if model_path and self.model_registry.is_loaded(model_path):
            model = self.model_registry.get_model(model_path)
            if hasattr(model, 'tokenizer'):
                return len(model.tokenizer.encode(text))
        
        # Fall back to character ratio approximation
        return max(1, int(len(text) * 0.25))  # ~4 chars per token
    
    def allocate_context(self, model_path, history_tokens, system_tokens, query_tokens):
        """Allocate token budget for context, system, history, and response"""
        # Get model context window
        context_window = self.model_registry.get_context_window(model_path)
        
        # Reserve tokens for response and overhead
        reserve_tokens = max(256, int(context_window * 0.15))
        
        # Calculate available tokens for RAG context
        available = max(0, context_window - history_tokens - system_tokens - query_tokens - reserve_tokens)
        
        return {
            'context_window': context_window,
            'available_for_context': available,
            'history': history_tokens,
            'system': system_tokens,
            'query': query_tokens,
            'reserved': reserve_tokens
        }
```

## Success Criteria

The refactoring will be considered successful when:

1. **Zero Duplication**
   - No duplicated code or functionality across the codebase
   - Single source of truth for all key operations

2. **Improved Error Handling**
   - Consistent, structured error handling throughout the system
   - Proper error logging and reporting
   - Helpful error messages for users and developers

3. **Better Performance**
   - Reduced memory usage
   - Faster model loading and inference
   - More efficient search operations

4. **Enhanced Maintainability**
   - Clear separation of concerns
   - Well-defined interfaces between components
   - Comprehensive inline documentation
   - Consistent coding style and patterns

5. **Complete Test Coverage**
   - Unit tests for all core components
   - Integration tests for critical workflows
   - End-to-end tests for user-facing features

## Implementation Timeline

1. **Phase 1** (Core Infrastructure): 1 week
   - Day 1-2: Core module implementation
   - Day 3-5: Model management refactoring
   - Day 6-7: Testing and validation

2. **Phase 2** (RAG System): 1 week
   - Day 1-2: Document operations consolidation
   - Day 3-4: Search functionality improvements
   - Day 5-7: Context management enhancements

3. **Phase 3** (Web Interface and API): 1 week
   - Day 1-2: Server implementation modernization
   - Day 3-4: API standardization
   - Day 5-7: Template system enhancements

## Conclusion

This refactoring effort will significantly improve the maintainability, performance, and extensibility of the LLM platform. By adhering strictly to DRY and KISS principles, the refactored system will provide a solid foundation for future features and enhancements while ensuring a better experience for both users and developers.