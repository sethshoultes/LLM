#!/usr/bin/env python3
"""
Dependency analyzer for the LLM Platform.

This script analyzes Python imports across the codebase to identify:
1. Unused imports
2. Duplicate imports
3. Circular dependencies
4. Import style inconsistencies
5. Missing requirements

Usage:
    python dependency_analyzer.py [--fix] [path]
"""

import os
import sys
import re
import ast
import argparse
import pkg_resources
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from collections import defaultdict


class ImportAnalyzer(ast.NodeVisitor):
    """AST visitor for analyzing imports in Python files."""
    
    def __init__(self):
        """Initialize the import analyzer."""
        self.imports = []
        self.from_imports = []
        self.import_usages = set()
        self.star_imports = []
    
    def visit_Import(self, node):
        """Visit Import nodes."""
        for name in node.names:
            alias = name.asname if name.asname else name.name
            self.imports.append((name.name, alias, node.lineno))
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        """Visit ImportFrom nodes."""
        if node.module is None:
            # Handle relative imports
            self.star_imports.append(("." * node.level, node.lineno))
            return
            
        module = node.module
        for name in node.names:
            if name.name == '*':
                self.star_imports.append((module, node.lineno))
            else:
                alias = name.asname if name.asname else name.name
                self.from_imports.append((module, name.name, alias, node.lineno))
        self.generic_visit(node)
    
    def visit_Name(self, node):
        """Visit Name nodes to track usage of imported names."""
        if isinstance(node.ctx, ast.Load):
            self.import_usages.add(node.id)
        self.generic_visit(node)
    
    def visit_Attribute(self, node):
        """Visit Attribute nodes to track usage of imported module attributes."""
        if isinstance(node.value, ast.Name):
            self.import_usages.add(node.value.id)
        self.generic_visit(node)


def get_python_files(path: Path) -> List[Path]:
    """Get all Python files in the specified path recursively.
    
    Args:
        path: The root directory to search
        
    Returns:
        List of Python file paths
    """
    python_files = []
    for root, _, files in os.walk(path):
        # Skip .git, __pycache__, and virtual environments
        if (
            "/.git/" in root or 
            "/__pycache__/" in root or 
            "/env/" in root or 
            "/venv/" in root or
            "/LLM-MODELS/tools/" in root
        ):
            continue
            
        for file in files:
            if file.endswith(".py"):
                python_files.append(Path(root) / file)
    return python_files


def analyze_file(file_path: Path) -> Tuple[Dict[str, Any], List[str]]:
    """Analyze imports in a Python file.
    
    Args:
        file_path: Path to the Python file
        
    Returns:
        Tuple of (file_info, errors)
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        tree = ast.parse(content)
        analyzer = ImportAnalyzer()
        analyzer.visit(tree)
        
        # Extract module name from file path
        rel_path = file_path.relative_to(Path.cwd())
        module_path = str(rel_path).replace("/", ".").replace(".py", "")
        
        return {
            "path": file_path,
            "module": module_path,
            "imports": analyzer.imports,
            "from_imports": analyzer.from_imports,
            "import_usages": analyzer.import_usages,
            "star_imports": analyzer.star_imports,
            "content": content
        }, []
    except Exception as e:
        return {}, [f"Error analyzing {file_path}: {str(e)}"]


def find_unused_imports(file_info: Dict[str, Any]) -> List[str]:
    """Find unused imports in a file.
    
    Args:
        file_info: File information from analyze_file
        
    Returns:
        List of unused import descriptions
    """
    unused = []
    
    # Check regular imports
    for module, alias, lineno in file_info["imports"]:
        if alias not in file_info["import_usages"]:
            unused.append(f"{file_info['path']}:{lineno}: Unused import '{module}' as '{alias}'")
    
    # Check from imports
    for module, name, alias, lineno in file_info["from_imports"]:
        # Skip common special imports like __future__
        if module == "__future__":
            continue
            
        # Skip typing imports (often used for type hints which don't show as usages in AST)
        if module == "typing" or module.startswith("typing."):
            continue
            
        if alias not in file_info["import_usages"]:
            unused.append(f"{file_info['path']}:{lineno}: Unused import '{name}' from '{module}' as '{alias}'")
    
    return unused


def find_star_imports(file_info: Dict[str, Any]) -> List[str]:
    """Find star imports in a file.
    
    Args:
        file_info: File information from analyze_file
        
    Returns:
        List of star import descriptions
    """
    star_imports = []
    
    for module, lineno in file_info["star_imports"]:
        star_imports.append(f"{file_info['path']}:{lineno}: Star import 'from {module} import *'")
    
    return star_imports


def check_import_style(file_info: Dict[str, Any]) -> List[str]:
    """Check import style issues.
    
    Args:
        file_info: File information from analyze_file
        
    Returns:
        List of style issue descriptions
    """
    style_issues = []
    
    # Get all imports with line numbers
    all_imports = [(module, lineno) for module, _, lineno in file_info["imports"]]
    all_imports.extend([(module, lineno) for module, _, _, lineno in file_info["from_imports"]])
    
    # Sort by line number
    all_imports.sort(key=lambda x: x[1])
    
    # Check if imports are grouped properly (standard library, third-party, local)
    if len(all_imports) > 1:
        groups = []
        current_group = []
        current_lineno = all_imports[0][1]
        
        for module, lineno in all_imports:
            # Check if there's a gap in line numbers (blank line)
            if lineno > current_lineno + 1:
                if current_group:
                    groups.append(current_group)
                    current_group = []
            
            current_group.append(module)
            current_lineno = lineno
        
        if current_group:
            groups.append(current_group)
        
        # Check if groups follow the convention:
        # 1. Standard library imports
        # 2. Third-party imports
        # 3. Local application imports
        if len(groups) > 1:
            # Simple heuristic: standard libs don't have dots, third-party have dots but don't start with local module names, local start with local module names
            local_prefixes = {"core", "models", "rag", "web", "tests"}
            
            for i, group in enumerate(groups):
                is_std_lib = all(("." not in mod) for mod in group)
                is_third_party = any(("." in mod) for mod in group) and not any(mod.split(".")[0] in local_prefixes for mod in group)
                is_local = any(mod.split(".")[0] in local_prefixes for mod in group)
                
                if i == 0 and not is_std_lib and any("." in mod for mod in group):
                    style_issues.append(f"{file_info['path']}: First import group should be standard library")
                elif i == 1 and not is_third_party and is_local:
                    style_issues.append(f"{file_info['path']}: Second import group should be third-party")
    
    return style_issues


def find_duplicate_imports(all_files: List[Dict[str, Any]]) -> List[str]:
    """Find duplicate imports across the codebase.
    
    Args:
        all_files: List of file information from analyze_file
        
    Returns:
        List of duplicate import descriptions
    """
    duplicate_imports = []
    module_to_files = defaultdict(list)
    
    # Build map of modules to files that import them
    for file_info in all_files:
        for module, _, _ in file_info["imports"]:
            module_to_files[module].append(file_info["path"])
        
        for module, _, _, _ in file_info["from_imports"]:
            module_to_files[module].append(file_info["path"])
    
    # Check for duplicates
    for module, files in module_to_files.items():
        if len(files) > 1:
            # Only report if files are in similar directories (possible duplicates)
            file_paths = [str(f) for f in files]
            for i, path1 in enumerate(file_paths):
                for path2 in file_paths[i+1:]:
                    parts1 = path1.split(os.sep)
                    parts2 = path2.split(os.sep)
                    
                    # Check if both files have similar paths (indicating possible duplicate code)
                    if (
                        len(parts1) >= 3 and 
                        len(parts2) >= 3 and 
                        parts1[-3] == parts2[-3] and
                        parts1[-1] != "__init__.py" and
                        parts2[-1] != "__init__.py"
                    ):
                        duplicate_imports.append(f"Module '{module}' imported in similar files: {path1} and {path2}")
    
    return duplicate_imports


def find_circular_dependencies(all_files: List[Dict[str, Any]]) -> List[str]:
    """Find circular dependencies between modules.
    
    Args:
        all_files: List of file information from analyze_file
        
    Returns:
        List of circular dependency descriptions
    """
    circular_deps = []
    
    # Build dependency graph
    dependencies = defaultdict(set)
    modules = {}
    
    for file_info in all_files:
        module_name = file_info["module"]
        modules[module_name] = file_info["path"]
        
        for module, _, _ in file_info["imports"]:
            if not module.startswith("importlib") and not module.startswith("__future__"):
                dependencies[module_name].add(module)
        
        for module, _, _, _ in file_info["from_imports"]:
            if not module.startswith("importlib") and not module.startswith("__future__"):
                dependencies[module_name].add(module)
    
    # Find cycles using DFS
    def find_cycle(node, path, visited):
        if node in path:
            cycle_start = path.index(node)
            return path[cycle_start:] + [node]
        
        if node in visited:
            return []
        
        visited.add(node)
        
        for neighbor in dependencies.get(node, []):
            if neighbor in modules:  # Only check local modules
                cycle = find_cycle(neighbor, path + [node], visited)
                if cycle:
                    return cycle
        
        return []
    
    # Check each module for cycles
    for module in modules:
        cycle = find_cycle(module, [], set())
        if cycle:
            # Format cycle description
            cycle_desc = " -> ".join(cycle)
            circular_deps.append(f"Circular dependency detected: {cycle_desc}")
    
    return circular_deps


def check_missing_requirements(all_files: List[Dict[str, Any]]) -> List[str]:
    """Check for third-party imports that might be missing from requirements.txt.
    
    Args:
        all_files: List of file information from analyze_file
        
    Returns:
        List of potentially missing requirements
    """
    missing_reqs = []
    
    # Get installed packages
    installed_packages = {pkg.key for pkg in pkg_resources.working_set}
    
    # Load requirements.txt if it exists
    requirements = set()
    req_files = ["requirements.txt", "config/requirements.txt"]
    
    for req_file in req_files:
        if os.path.exists(req_file):
            with open(req_file, "r") as f:
                for line in f:
                    # Skip comments and empty lines
                    if not line.strip() or line.strip().startswith("#"):
                        continue
                        
                    # Extract package name (ignoring version specifiers)
                    package = line.strip().split("==")[0].split(">=")[0].split(">")[0].split("<")[0].strip()
                    requirements.add(package.lower())
    
    # Collect all third-party imports
    third_party_imports = set()
    
    for file_info in all_files:
        for module, _, _ in file_info["imports"]:
            # Get top-level package
            top_level = module.split(".")[0]
            
            # Skip standard library and local modules
            if (
                top_level in installed_packages and 
                top_level not in sys.builtin_module_names and
                not top_level.startswith("_") and
                top_level not in {"core", "models", "rag", "web", "tests"}
            ):
                third_party_imports.add(top_level)
        
        for module, _, _, _ in file_info["from_imports"]:
            # Get top-level package
            top_level = module.split(".")[0]
            
            # Skip standard library and local modules
            if (
                top_level in installed_packages and 
                top_level not in sys.builtin_module_names and
                not top_level.startswith("_") and
                top_level not in {"core", "models", "rag", "web", "tests"}
            ):
                third_party_imports.add(top_level)
    
    # Check for missing requirements
    for pkg in third_party_imports:
        # Handle common package name differences
        pkg_variants = [pkg, pkg.replace("-", "_"), pkg.replace("_", "-")]
        
        if not any(variant.lower() in requirements for variant in pkg_variants):
            missing_reqs.append(f"Potentially missing requirement: {pkg}")
    
    return missing_reqs


def auto_fix_imports(file_info: Dict[str, Any], issues: List[str]) -> Optional[str]:
    """Auto-fix import issues in a file.
    
    Args:
        file_info: File information from analyze_file
        issues: List of import issues to fix
        
    Returns:
        New file content if changes were made, None otherwise
    """
    if not issues:
        return None
        
    content = file_info["content"]
    lines = content.split("\n")
    
    # Collect line numbers to remove (unused imports)
    lines_to_remove = set()
    
    for issue in issues:
        if "Unused import" in issue:
            match = re.search(r"^.*?:(\d+):", issue)
            if match:
                lineno = int(match.group(1))
                lines_to_remove.add(lineno - 1)  # Adjust for 0-based indexing
    
    # Remove unused imports
    if lines_to_remove:
        new_lines = [line for i, line in enumerate(lines) if i not in lines_to_remove]
        return "\n".join(new_lines)
    
    return None


def print_summary(all_issues: Dict[str, List[str]]):
    """Print a summary of all issues found.
    
    Args:
        all_issues: Dictionary of issue type to list of issues
    """
    total_issues = sum(len(issues) for issues in all_issues.values())
    
    print(f"\n{'=' * 80}")
    print(f"SUMMARY: Found {total_issues} issues")
    print(f"{'=' * 80}")
    
    for issue_type, issues in all_issues.items():
        if issues:
            print(f"\n{issue_type}: {len(issues)} issues")
            print(f"{'-' * 80}")
            for issue in issues[:10]:  # Show only first 10 issues
                print(issue)
            
            if len(issues) > 10:
                print(f"... and {len(issues) - 10} more issues")
    
    print(f"\n{'=' * 80}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Analyze Python imports in the codebase")
    parser.add_argument("--fix", action="store_true", help="Auto-fix issues where possible")
    parser.add_argument("path", nargs="?", default=".", help="Path to analyze (default: current directory)")
    args = parser.parse_args()
    
    path = Path(args.path).resolve()
    print(f"Analyzing Python files in {path}...")
    
    python_files = get_python_files(path)
    print(f"Found {len(python_files)} Python files")
    
    all_file_info = []
    all_errors = []
    
    # Analyze files
    for file_path in python_files:
        file_info, errors = analyze_file(file_path)
        
        if errors:
            all_errors.extend(errors)
        elif file_info:
            all_file_info.append(file_info)
    
    # Track all issue types
    all_issues = {
        "ERRORS": all_errors,
        "UNUSED IMPORTS": [],
        "STAR IMPORTS": [],
        "IMPORT STYLE ISSUES": [],
        "DUPLICATE IMPORTS": [],
        "CIRCULAR DEPENDENCIES": [],
        "MISSING REQUIREMENTS": []
    }
    
    # Find issues
    for file_info in all_file_info:
        all_issues["UNUSED IMPORTS"].extend(find_unused_imports(file_info))
        all_issues["STAR IMPORTS"].extend(find_star_imports(file_info))
        all_issues["IMPORT STYLE ISSUES"].extend(check_import_style(file_info))
    
    all_issues["DUPLICATE IMPORTS"] = find_duplicate_imports(all_file_info)
    all_issues["CIRCULAR DEPENDENCIES"] = find_circular_dependencies(all_file_info)
    all_issues["MISSING REQUIREMENTS"] = check_missing_requirements(all_file_info)
    
    # Print issues
    print_summary(all_issues)
    
    # Auto-fix issues if requested
    if args.fix:
        fixed_files = 0
        
        # Group issues by file
        file_to_issues = defaultdict(list)
        
        for issue in all_issues["UNUSED IMPORTS"]:
            match = re.search(r"^(.*?):", issue)
            if match:
                file_path = match.group(1)
                file_to_issues[file_path].append(issue)
        
        # Fix each file
        for file_info in all_file_info:
            file_path = str(file_info["path"])
            if file_path in file_to_issues:
                new_content = auto_fix_imports(file_info, file_to_issues[file_path])
                
                if new_content:
                    with open(file_path, "w") as f:
                        f.write(new_content)
                    fixed_files += 1
        
        print(f"\nFixed issues in {fixed_files} files")
    
    # Return non-zero exit code if issues were found
    if sum(len(issues) for issues in all_issues.values()) > 0:
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())