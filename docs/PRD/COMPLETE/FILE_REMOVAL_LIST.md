# File Removal List

This document keeps track of files that have been refactored and their replacements, to ensure we maintain a clean codebase with no duplicates, in line with the refactoring principles.

## Completed Removals

| Original File | Replacement | Status | Date |
|--------------|-------------|--------|------|
| `/Volumes/LLM/rag_support/utils/search_refactored.py` | `/Volumes/LLM/rag_support/utils/search.py` | Removed | 2025-04-29 |
| `/Volumes/LLM/rag_support/utils/context_manager_refactored.py` | `/Volumes/LLM/rag_support/utils/context_manager.py` | Removed | 2025-04-29 |

## Pending Removals

These files represent potential duplication that needs to be addressed:

| File | Duplicate/Alternative | Notes | Priority |
|------|----------------------|-------|----------|
| `/Volumes/LLM/rag/search.py` | `/Volumes/LLM/rag_support/utils/search.py` | Core search module that is imported by the enhanced version. Need to consolidate functionality or establish clear separation of concerns. | Medium |

## Next Steps

1. Review and analyze dependencies between original and replacement files
2. Confirm that all functionality has been migrated properly
3. Update imports in other files that may reference the original files
4. Run comprehensive tests before and after removal to ensure functionality is preserved
5. Document architectural decisions regarding file organization

## Guidelines

* Every file in the codebase must have exactly one purpose
* No functionality should be duplicated across multiple files
* Legacy/old implementations must be completely replaced
* File paths should be logical and follow the project's architectural principles
* Each file removal must be documented in this list