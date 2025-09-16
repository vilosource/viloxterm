"""
Test that UI components don't directly use ServiceLocator.

This test enforces the Command Pattern Architecture by ensuring UI components
don't bypass the command system by directly accessing services.
"""

import os
import pytest
from pathlib import Path


def get_ui_files():
    """Get all Python files in the UI directory."""
    ui_dir = Path(__file__).parent.parent.parent / "ui"
    if not ui_dir.exists():
        pytest.skip("UI directory not found")

    ui_files = []
    for file in ui_dir.rglob("*.py"):
        if "__pycache__" not in str(file):
            ui_files.append(file)

    return ui_files


def test_no_service_locator_imports_in_ui():
    """Test that UI files don't import ServiceLocator."""
    ui_files = get_ui_files()
    violations = []

    for file_path in ui_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check for ServiceLocator imports
            lines = content.split('\n')
            for line_num, line in enumerate(lines, 1):
                line_stripped = line.strip()

                # Skip comments
                if line_stripped.startswith('#'):
                    continue

                # Check for ServiceLocator imports
                if ('from services.service_locator import ServiceLocator' in line or
                    'from services import ServiceLocator' in line or
                    'import services.service_locator' in line):

                    violations.append({
                        'file': str(file_path.relative_to(file_path.parent.parent.parent)),
                        'line': line_num,
                        'content': line_stripped,
                        'type': 'import'
                    })

        except (UnicodeDecodeError, PermissionError) as e:
            # Skip files that can't be read
            continue

    if violations:
        error_msg = "ServiceLocator imports found in UI files:\n"
        for violation in violations:
            error_msg += f"  {violation['file']}:{violation['line']} - {violation['content']}\n"
        error_msg += "\nUI components should use commands instead of direct service access."

        pytest.fail(error_msg)


def test_no_service_locator_usage_in_ui():
    """Test that UI files don't use ServiceLocator methods."""
    ui_files = get_ui_files()
    violations = []

    for file_path in ui_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            lines = content.split('\n')
            for line_num, line in enumerate(lines, 1):
                line_stripped = line.strip()

                # Skip comments
                if line_stripped.startswith('#'):
                    continue

                # Check for ServiceLocator usage
                if ('ServiceLocator.get_instance()' in line or
                    'ServiceLocator.get(' in line or
                    'ServiceLocator.register(' in line or
                    '.get_service(' in line):  # Common service access pattern

                    # Allow certain exceptions (like comments explaining what NOT to do)
                    if ('# Get theme colors using command instead of ServiceLocator' in line or
                        '# NEVER use ServiceLocator' in line or
                        '# Don\'t use ServiceLocator' in line):
                        continue

                    violations.append({
                        'file': str(file_path.relative_to(file_path.parent.parent.parent)),
                        'line': line_num,
                        'content': line_stripped,
                        'type': 'usage'
                    })

        except (UnicodeDecodeError, PermissionError) as e:
            continue

    if violations:
        error_msg = "ServiceLocator usage found in UI files:\n"
        for violation in violations:
            error_msg += f"  {violation['file']}:{violation['line']} - {violation['content']}\n"
        error_msg += "\nUI components should use commands for service access."

        pytest.fail(error_msg)


def test_ui_architecture_compliance():
    """Test overall UI architecture compliance."""
    ui_files = get_ui_files()

    # Collect all violations
    violations = {
        'direct_service_access': [],
        'service_locator_usage': [],
        'command_bypass': []
    }

    for file_path in ui_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Skip main_window.py as it's allowed to bootstrap services
            if 'main_window.py' in str(file_path):
                continue

            lines = content.split('\n')
            for line_num, line in enumerate(lines, 1):
                line_stripped = line.strip()

                # Skip comments and docstrings
                if line_stripped.startswith(('#', '"""', "'''")):
                    continue

                # Check for various architectural violations
                if 'ServiceLocator' in line and '# ' not in line:
                    violations['service_locator_usage'].append({
                        'file': str(file_path.relative_to(file_path.parent.parent.parent)),
                        'line': line_num,
                        'content': line_stripped
                    })

                # Check for direct service imports (common violation)
                if ('from services.' in line and
                    'service_locator' not in line and
                    'from services import' not in line):
                    violations['direct_service_access'].append({
                        'file': str(file_path.relative_to(file_path.parent.parent.parent)),
                        'line': line_num,
                        'content': line_stripped
                    })

        except (UnicodeDecodeError, PermissionError):
            continue

    # Report violations
    error_messages = []

    if violations['service_locator_usage']:
        error_messages.append("ServiceLocator usage in UI files:")
        for v in violations['service_locator_usage'][:5]:  # Limit to first 5
            error_messages.append(f"  {v['file']}:{v['line']} - {v['content']}")
        if len(violations['service_locator_usage']) > 5:
            error_messages.append(f"  ... and {len(violations['service_locator_usage']) - 5} more")

    if violations['direct_service_access']:
        error_messages.append("\nDirect service imports in UI files:")
        for v in violations['direct_service_access'][:5]:
            error_messages.append(f"  {v['file']}:{v['line']} - {v['content']}")
        if len(violations['direct_service_access']) > 5:
            error_messages.append(f"  ... and {len(violations['direct_service_access']) - 5} more")

    if error_messages:
        error_messages.append("\nUI components should use the Command Pattern:")
        error_messages.append("  User Action → Command → Service → UI Update")
        error_messages.append("  Never: UI Component → ServiceLocator → Service")

        pytest.fail("\n".join(error_messages))


if __name__ == "__main__":
    # Allow running the test standalone for debugging
    pytest.main([__file__, "-v"])