#!/usr/bin/env python3
"""
Script to refactor WidgetType enum to widget_id strings throughout the codebase.
"""

import re
from pathlib import Path

# Base directory for the refactoring
BASE_DIR = Path("/home/kuja/GitHub/viloapp/packages/viloapp/src/viloapp")

# Patterns to replace
REPLACEMENTS = [
    # Replace WidgetType enum values with string constants
    (r'WidgetType\.TERMINAL', 'TERMINAL'),
    (r'WidgetType\.EDITOR', 'EDITOR'),
    (r'WidgetType\.TEXT_EDITOR', 'EDITOR'),
    (r'WidgetType\.OUTPUT', 'OUTPUT'),
    (r'WidgetType\.SETTINGS', 'SETTINGS'),
    (r'WidgetType\.FILE_EXPLORER', 'FILE_EXPLORER'),
    (r'WidgetType\.EXPLORER', 'FILE_EXPLORER'),
    (r'WidgetType\.CUSTOM', '"plugin.unknown"'),
    (r'WidgetType\.PLACEHOLDER', 'PLACEHOLDER'),
    (r'WidgetType\.THEME_EDITOR', 'THEME_EDITOR'),
    (r'WidgetType\.SHORTCUT_CONFIG', 'SHORTCUT_CONFIG'),

    # Replace parameter names
    (r'widget_type:', 'widget_id:'),
    (r'widget_type =', 'widget_id ='),
    (r'\.widget_type', '.widget_id'),
    (r'"widget_type"', '"widget_id"'),
    (r"'widget_type'", "'widget_id'"),

    # Replace widget_type parameters in function signatures
    (r'widget_type:\s*WidgetType', 'widget_id: str'),
    (r'widget_type:\s*Optional\[WidgetType\]', 'widget_id: Optional[str]'),
]

# Files to skip (already manually updated)
SKIP_FILES = [
    "workspace_model.py",
    "widget_ids.py",
]

def update_imports(content):
    """Update import statements."""
    # Check if file uses WidgetType
    if 'WidgetType' in content:
        # Check what constants are used
        constants_used = set()
        for const in ['TERMINAL', 'EDITOR', 'OUTPUT', 'SETTINGS', 'FILE_EXPLORER',
                      'PLACEHOLDER', 'THEME_EDITOR', 'SHORTCUT_CONFIG']:
            if const in content:
                constants_used.add(const)

        if constants_used:
            # Replace WidgetType import with widget_ids import
            import_line = f"from viloapp.core.widget_ids import {', '.join(sorted(constants_used))}"

            # Replace various import patterns
            content = re.sub(
                r'from viloapp\.models\.workspace_model import .*?WidgetType.*?\n',
                f'{import_line}\n',
                content
            )
            content = re.sub(
                r'from viloapp\.ui\.widgets\.widget_registry import .*?WidgetType.*?\n',
                f'{import_line}\n',
                content
            )
            content = re.sub(
                r'from \.\.models\.workspace_model import .*?WidgetType.*?\n',
                f'{import_line}\n',
                content
            )

    return content

def process_file(filepath):
    """Process a single Python file."""
    if filepath.name in SKIP_FILES:
        print(f"Skipping {filepath.name}")
        return False

    try:
        with open(filepath, 'r') as f:
            original_content = f.read()
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return False

    content = original_content

    # Apply replacements
    for pattern, replacement in REPLACEMENTS:
        content = re.sub(pattern, replacement, content)

    # Update imports
    content = update_imports(content)

    # Only write if changed
    if content != original_content:
        try:
            with open(filepath, 'w') as f:
                f.write(content)
            print(f"Updated {filepath}")
            return True
        except Exception as e:
            print(f"Error writing {filepath}: {e}")
            return False

    return False

def main():
    """Run the refactoring."""
    updated_files = []

    # Process all Python files
    for filepath in BASE_DIR.rglob("*.py"):
        if process_file(filepath):
            updated_files.append(filepath)

    print("\nRefactoring complete!")
    print(f"Updated {len(updated_files)} files")

    if updated_files:
        print("\nUpdated files:")
        for f in updated_files:
            print(f"  - {f.relative_to(BASE_DIR)}")

if __name__ == "__main__":
    main()