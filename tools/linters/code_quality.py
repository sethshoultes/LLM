#!/usr/bin/env python3
"""
Code quality checker for the LLM Platform.

This script runs various code quality tools on the codebase:
1. Flake8 for linting
2. Black for code formatting
3. Pylint for more comprehensive linting
4. MyPy for type checking (optional)

Usage:
    python code_quality.py [--fix] [--check-types] [path]
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple, Set


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Run code quality checks")
    parser.add_argument("--fix", action="store_true", help="Automatically fix issues where possible")
    parser.add_argument("--check-types", action="store_true", help="Run type checking with MyPy")
    parser.add_argument("path", nargs="?", default=".", help="Path to check (default: current directory)")
    
    return parser.parse_args()


def find_python_files(path: Path, exclude_dirs: List[str]) -> List[Path]:
    """Find Python files to check.
    
    Args:
        path: Root directory to search
        exclude_dirs: Directories to exclude
        
    Returns:
        List of Python file paths
    """
    python_files = []
    
    for root, dirs, files in os.walk(path):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith(".")]
        
        for file in files:
            if file.endswith(".py"):
                file_path = Path(root) / file
                python_files.append(file_path)
    
    return python_files


def run_flake8(path: Path, config_file: Path) -> Tuple[bool, List[str]]:
    """Run Flake8 on Python files.
    
    Args:
        path: Directory to check
        config_file: Path to Flake8 config file
        
    Returns:
        Tuple of (success, error_messages)
    """
    print("Running Flake8...")
    
    cmd = ["flake8", "--config", str(config_file), str(path)]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Flake8 passed")
            return True, []
        else:
            print("❌ Flake8 found issues")
            return False, result.stdout.strip().split("\n")
    except Exception as e:
        print(f"Error running Flake8: {e}")
        return False, [f"Error running Flake8: {e}"]


def run_black(path: Path, config_file: Path, fix: bool) -> Tuple[bool, List[str]]:
    """Run Black on Python files.
    
    Args:
        path: Directory to check
        config_file: Path to Black config file
        fix: Whether to automatically fix issues
        
    Returns:
        Tuple of (success, error_messages)
    """
    print("Running Black...")
    
    cmd = ["black"]
    
    if not fix:
        cmd.append("--check")
    
    cmd.extend(["--config", str(config_file), str(path)])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Black passed")
            return True, []
        else:
            if not fix:
                print("❌ Black found issues")
                return False, result.stderr.strip().split("\n")
            else:
                print("🔧 Black reformatted files")
                return True, result.stderr.strip().split("\n")
    except Exception as e:
        print(f"Error running Black: {e}")
        return False, [f"Error running Black: {e}"]


def run_pylint(path: Path, config_file: Path) -> Tuple[bool, List[str]]:
    """Run Pylint on Python files.
    
    Args:
        path: Directory to check
        config_file: Path to Pylint config file
        
    Returns:
        Tuple of (success, error_messages)
    """
    print("Running Pylint...")
    
    cmd = ["pylint", "--rcfile", str(config_file), str(path)]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Pylint returns 0 for no errors, 1 for fatal errors, 2 for errors,
        # 4 for warnings, 8 for refactor messages, 16 for convention messages,
        # 32 for usage errors
        if result.returncode == 0:
            print("✅ Pylint passed")
            return True, []
        elif result.returncode & (1 | 2 | 32):  # Fatal errors, errors, or usage errors
            print("❌ Pylint found issues")
            return False, result.stdout.strip().split("\n")
        else:
            # Warnings, refactor messages, or convention messages
            print("⚠️ Pylint found non-critical issues")
            return True, result.stdout.strip().split("\n")
    except Exception as e:
        print(f"Error running Pylint: {e}")
        return False, [f"Error running Pylint: {e}"]


def run_mypy(path: Path, config_file: Path) -> Tuple[bool, List[str]]:
    """Run MyPy for type checking.
    
    Args:
        path: Directory to check
        config_file: Path to MyPy config file
        
    Returns:
        Tuple of (success, error_messages)
    """
    print("Running MyPy...")
    
    cmd = ["mypy", "--config-file", str(config_file), str(path)]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ MyPy passed")
            return True, []
        else:
            print("❌ MyPy found issues")
            return False, result.stdout.strip().split("\n")
    except Exception as e:
        print(f"Error running MyPy: {e}")
        return False, [f"Error running MyPy: {e}"]


def format_errors(errors: List[str], max_errors: int = 20) -> str:
    """Format error messages for display.
    
    Args:
        errors: List of error messages
        max_errors: Maximum number of errors to show
        
    Returns:
        Formatted error string
    """
    if not errors:
        return "No errors found"
    
    formatted = "\n".join(errors[:max_errors])
    
    if len(errors) > max_errors:
        formatted += f"\n... and {len(errors) - max_errors} more issues"
    
    return formatted


def summarize_results(results: Dict[str, Tuple[bool, List[str]]]) -> bool:
    """Summarize results from all tools.
    
    Args:
        results: Dictionary mapping tool names to (success, error_messages) tuples
        
    Returns:
        True if all critical checks passed, False otherwise
    """
    print("\n" + "=" * 80)
    print("CODE QUALITY SUMMARY")
    print("=" * 80)
    
    all_passed = True
    
    for tool, (success, errors) in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{tool}: {status}")
        
        if not success:
            all_passed = False
            print(f"  Found {len(errors)} issues")
            print(f"  Sample: {errors[0] if errors else 'No details'}")
    
    print("=" * 80)
    
    if all_passed:
        print("All code quality checks passed!")
    else:
        print("Some code quality checks failed. See above for details.")
    
    return all_passed


def main() -> int:
    """Main function."""
    args = parse_args()
    
    # Convert path to absolute path
    path = Path(args.path).resolve()
    
    # Directory containing this script
    script_dir = Path(__file__).resolve().parent
    
    # Config files
    pyproject_toml = script_dir / "pyproject.toml"
    setup_cfg = script_dir / "setup.cfg"
    
    # Check if config files exist
    if not pyproject_toml.exists():
        print(f"Error: {pyproject_toml} not found")
        return 1
    
    if not setup_cfg.exists():
        print(f"Error: {setup_cfg} not found")
        return 1
    
    print(f"Checking code quality in {path}...")
    
    # Excluded directories
    exclude_dirs = [
        ".git",
        "__pycache__",
        "LLM-MODELS",
        "env",
        "venv",
        "build",
        "dist",
    ]
    
    # Run tools
    results = {}
    
    # Run Flake8
    flake8_success, flake8_errors = run_flake8(path, setup_cfg)
    results["Flake8"] = (flake8_success, flake8_errors)
    
    # Run Black
    black_success, black_errors = run_black(path, pyproject_toml, args.fix)
    results["Black"] = (black_success, black_errors)
    
    # Run Pylint
    pylint_success, pylint_errors = run_pylint(path, pyproject_toml)
    results["Pylint"] = (pylint_success, pylint_errors)
    
    # Run MyPy if requested
    if args.check_types:
        mypy_success, mypy_errors = run_mypy(path, pyproject_toml)
        results["MyPy"] = (mypy_success, mypy_errors)
    
    # Summarize results
    all_passed = summarize_results(results)
    
    # Output detailed errors if requested
    for tool, (success, errors) in results.items():
        if errors:
            print(f"\nDetailed {tool} issues:")
            print(format_errors(errors))
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())