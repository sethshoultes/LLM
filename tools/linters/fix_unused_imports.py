#!/usr/bin/env python3
"""
Fix unused imports in __init__.py files.

This script adds __all__ declarations to __init__.py files to properly
expose imported symbols, fixing F401 (imported but unused) warnings.
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Set


def find_init_files(root_path: Path) -> List[Path]:
    """Find all __init__.py files in the project."""
    init_files = []
    
    for root, _, files in os.walk(root_path):
        # Skip excluded directories
        if (
            "/.git/" in root or 
            "/__pycache__/" in root or 
            "/env/" in root or 
            "/venv/" in root or
            "/LLM-MODELS/" in root
        ):
            continue
            
        if "__init__.py" in files:
            init_files.append(Path(root) / "__init__.py")
    
    return init_files


def extract_import_names(file_path: Path) -> List[str]:
    """Extract names imported in a file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    imported_names = []
    
    # Find from ... import ... statements
    from_import_pattern = r'from\s+[\.\w]+\s+import\s+([\w\s,]+)'
    from_imports = re.findall(from_import_pattern, content)
    
    for imports in from_imports:
        for name in imports.split(','):
            name = name.strip()
            if name and name != '*':
                if ' as ' in name:
                    # Handle aliases
                    original, alias = name.split(' as ')
                    imported_names.append(alias.strip())
                else:
                    imported_names.append(name)
    
    # Find direct import ... statements
    import_pattern = r'import\s+([\w\s,.]+)'
    imports = re.findall(import_pattern, content)
    
    for import_group in imports:
        for name in import_group.split(','):
            name = name.strip()
            if name:
                if '.' in name:
                    imported_names.append(name.split('.')[-1])
                else:
                    imported_names.append(name)
    
    return imported_names


def check_if_all_exists(file_path: Path) -> bool:
    """Check if __all__ already exists in the file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return '__all__' in content


def add_all_declaration(file_path: Path, names: List[str]) -> bool:
    """Add __all__ declaration to the file."""
    if not names:
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Format names for __all__
    names_str = "', '".join(names)
    all_declaration = f"\n\n# Export module components\n__all__ = ['{names_str}']\n"
    
    # Add __all__ before any existing docstring
    if '__version__' in content:
        # Add after version declaration
        content = re.sub(r'(__version__\s*=\s*.+)', r'\1' + all_declaration, content)
    else:
        # Add at the end of imports
        import_section_end = 0
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            if line.strip() and not line.strip().startswith('#') and (
                line.strip().startswith('import ') or 
                line.strip().startswith('from ')
            ):
                import_section_end = i
        
        if import_section_end > 0:
            content = '\n'.join(lines[:import_section_end + 1]) + all_declaration + '\n'.join(lines[import_section_end + 1:])
        else:
            # Just add to the end of the file
            content += all_declaration
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python fix_unused_imports.py <path>")
        return 1
    
    root_path = Path(sys.argv[1]).resolve()
    print(f"Fixing unused imports in __init__.py files in {root_path}...")
    
    init_files = find_init_files(root_path)
    print(f"Found {len(init_files)} __init__.py files")
    
    fixed_files = 0
    
    for file_path in init_files:
        if check_if_all_exists(file_path):
            print(f"Skipping {file_path} (already has __all__ declaration)")
            continue
        
        imported_names = extract_import_names(file_path)
        
        if imported_names:
            print(f"Adding __all__ to {file_path} with {len(imported_names)} names")
            if add_all_declaration(file_path, imported_names):
                fixed_files += 1
    
    print(f"Fixed {fixed_files} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())