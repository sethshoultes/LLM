#!/usr/bin/env python3
"""
Utility script to identify duplicate files in the LLM codebase.

This script scans the codebase to identify:
1. Files with similar names (e.g., filename.py vs filename_refactored.py)
2. Files with duplicate functionality (based on imports and function signatures)
3. Older implementation files that have been refactored or replaced

The script follows the refactoring principles in the SYSTEM_REFACTORING_PRD.md,
particularly the requirement that all replaced or duplicate files MUST be removed.
"""

import sys
import re
from pathlib import Path
from typing import List, Dict, Set, Tuple

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Directories to check
CORE_DIRS = [
    BASE_DIR / "core",
    BASE_DIR / "models",
    BASE_DIR / "rag",
    BASE_DIR / "rag_support",
    BASE_DIR / "scripts",
    BASE_DIR / "templates"
]

# File patterns to look for
REFACTORED_PATTERNS = [
    r"(.+)_refactored\.(py|js|html|css)$",  # _refactored suffix
    r"(.+)_new\.(py|js|html|css)$",         # _new suffix
    r"(.+)_v\d+\.(py|js|html|css)$",        # version suffix
    r"new_(.+)\.(py|js|html|css)$",         # new_ prefix
    r"refactored_(.+)\.(py|js|html|css)$"   # refactored_ prefix
]

# Files to ignore (not considered duplicates)
IGNORE_FILES = [
    "requirements.txt",
    "README.md",
    "LICENSE",
    ".gitignore",
    "setup.py",
    "__init__.py"
]

def find_refactored_files() -> List[Tuple[Path, Path]]:
    """
    Find files with refactored/new naming patterns.
    
    Returns:
        List of tuples (original_file, refactored_file)
    """
    refactored_pairs = []
    
    # Create a dictionary of all Python files
    all_files = {}
    for directory in CORE_DIRS:
        if not directory.exists():
            continue
            
        for file_path in directory.glob("**/*"):
            if file_path.is_file() and file_path.suffix in ['.py', '.js', '.html', '.css']:
                all_files[file_path.name] = file_path
    
    # Check for refactored patterns
    for file_name, file_path in all_files.items():
        for pattern in REFACTORED_PATTERNS:
            match = re.match(pattern, file_name)
            if match:
                base_name = match.group(1)
                extension = match.group(2)
                original_name = f"{base_name}.{extension}"
                
                # Check if original file exists
                if original_name in all_files:
                    refactored_pairs.append((all_files[original_name], file_path))
    
    return refactored_pairs

def find_similar_functionality(threshold: float = 0.7) -> List[Tuple[Path, Path, float]]:
    """
    Find files with similar functionality based on imports and code patterns.
    
    Args:
        threshold: Similarity threshold (0.0 to 1.0)
        
    Returns:
        List of tuples (file1, file2, similarity_score)
    """
    similar_files = []
    
    # Get all Python files
    python_files = []
    for directory in CORE_DIRS:
        if not directory.exists():
            continue
            
        for file_path in directory.glob("**/*.py"):
            if file_path.is_file() and file_path.name not in IGNORE_FILES:
                python_files.append(file_path)
    
    # Create file signatures (imports, classes, functions)
    file_signatures = {}
    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Extract imports
            imports = re.findall(r'^import\s+(.+)|^from\s+(.+?)\s+import', content, re.MULTILINE)
            
            # Extract class definitions
            classes = re.findall(r'^class\s+([A-Za-z0-9_]+)', content, re.MULTILINE)
            
            # Extract function definitions
            functions = re.findall(r'^def\s+([A-Za-z0-9_]+)', content, re.MULTILINE)
            
            # Create signature
            signature = {
                'imports': set(i[0] or i[1] for i in imports),
                'classes': set(classes),
                'functions': set(functions)
            }
            
            file_signatures[file_path] = signature
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    # Compare file signatures
    for i, file1 in enumerate(python_files):
        for file2 in python_files[i+1:]:
            # Skip files in different top-level directories (they may have legitimate overlaps)
            if file1.parts[1] != file2.parts[1]:
                continue
                
            # Get signatures
            sig1 = file_signatures.get(file1, {'imports': set(), 'classes': set(), 'functions': set()})
            sig2 = file_signatures.get(file2, {'imports': set(), 'classes': set(), 'functions': set()})
            
            # Calculate similarities
            import_similarity = len(sig1['imports'] & sig2['imports']) / max(1, len(sig1['imports'] | sig2['imports']))
            class_similarity = len(sig1['classes'] & sig2['classes']) / max(1, len(sig1['classes'] | sig2['classes']))
            func_similarity = len(sig1['functions'] & sig2['functions']) / max(1, len(sig1['functions'] | sig2['functions']))
            
            # Weight the similarities (functions are most important)
            overall_similarity = (import_similarity * 0.3) + (class_similarity * 0.3) + (func_similarity * 0.4)
            
            if overall_similarity >= threshold:
                similar_files.append((file1, file2, overall_similarity))
    
    return similar_files

def find_old_implementations() -> List[Path]:
    """
    Find files that implement older versions of functionality.
    
    Returns:
        List of paths to old implementation files
    """
    old_files = []
    
    # Look for common patterns in old implementations
    patterns = [
        "minimal_inference.py",  # Older inference scripts
        "inference_engine.py",   # Older inference engines
        "*_old.py",              # Files marked as old
        "legacy_*.py",           # Legacy-prefixed files
        "deprecated_*.py",       # Deprecated-prefixed files
    ]
    
    for directory in CORE_DIRS:
        if not directory.exists():
            continue
            
        for pattern in patterns:
            for file_path in directory.glob(f"**/{pattern}"):
                old_files.append(file_path)
    
    return old_files

def print_results(
    refactored_pairs: List[Tuple[Path, Path]],
    similar_files: List[Tuple[Path, Path, float]],
    old_implementations: List[Path]
) -> None:
    """
    Print the results in a formatted way.
    
    Args:
        refactored_pairs: List of (original, refactored) file pairs
        similar_files: List of (file1, file2, similarity) tuples
        old_implementations: List of old implementation files
    """
    print("\n" + "=" * 80)
    print("REFACTORING CLEANUP REPORT")
    print("=" * 80)
    
    print("\n1. Refactored File Pairs (original & refactored versions):")
    print("-" * 80)
    if refactored_pairs:
        for original, refactored in refactored_pairs:
            rel_original = original.relative_to(BASE_DIR)
            rel_refactored = refactored.relative_to(BASE_DIR)
            print(f"ORIGINAL: {rel_original}")
            print(f"REFACTOR: {rel_refactored}")
            print("-" * 40)
    else:
        print("No refactored file pairs found.")
    
    print("\n2. Files with Similar Functionality:")
    print("-" * 80)
    if similar_files:
        for file1, file2, similarity in sorted(similar_files, key=lambda x: x[2], reverse=True):
            rel_file1 = file1.relative_to(BASE_DIR)
            rel_file2 = file2.relative_to(BASE_DIR)
            print(f"SIMILAR FILES (similarity: {similarity:.2f}):")
            print(f"  - {rel_file1}")
            print(f"  - {rel_file2}")
            print("-" * 40)
    else:
        print("No files with similar functionality found.")
    
    print("\n3. Old Implementation Files:")
    print("-" * 80)
    if old_implementations:
        for file_path in old_implementations:
            rel_path = file_path.relative_to(BASE_DIR)
            print(f"OLD IMPLEMENTATION: {rel_path}")
        print("-" * 40)
    else:
        print("No old implementation files found.")
    
    print("\nSUMMARY:")
    print("-" * 80)
    print(f"- Refactored file pairs: {len(refactored_pairs)}")
    print(f"- Similar functionality files: {len(similar_files)}")
    print(f"- Old implementation files: {len(old_implementations)}")
    total_files = len(refactored_pairs) + len(similar_files) + len(old_implementations)
    print(f"- Total files to review: {total_files}")
    
    print("\nACTION REQUIRED:")
    print("-" * 80)
    print("According to the System Refactoring PRD, all replaced or duplicate files")
    print("MUST be removed from the codebase without exceptions. Please review these")
    print("files and decide which ones to keep and which ones to remove.")
    print("=" * 80)

def main():
    """Main function."""
    print("Scanning for duplicate/replaced files...")
    
    # Find refactored files
    refactored_pairs = find_refactored_files()
    
    # Find files with similar functionality
    similar_files = find_similar_functionality()
    
    # Find old implementations
    old_implementations = find_old_implementations()
    
    # Print results
    print_results(refactored_pairs, similar_files, old_implementations)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())