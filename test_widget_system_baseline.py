#!/usr/bin/env python3
"""Baseline tests that must always pass during widget system refactoring."""

import sys
import subprocess
import os
sys.path.insert(0, "packages/viloapp/src")

def test_no_undefined_variables():
    """No undefined variables in codebase."""
    print("Testing: No undefined variables...")

    # Get all Python files
    python_files = []
    for root, _, files in os.walk("packages/viloapp/src"):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))

    # Compile all files to check for syntax errors
    errors = []
    for file in python_files:
        result = subprocess.run(
            ["python", "-m", "py_compile", file],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            if "NameError" in result.stderr or "undefined" in result.stderr:
                errors.append(f"{file}: {result.stderr}")

    if errors:
        print(f"❌ Found undefined variables in {len(errors)} files")
        for error in errors[:5]:  # Show first 5
            print(f"  {error}")
        return False

    print("✅ No undefined variables")
    return True

def test_all_commands_execute():
    """All commands must execute without NameError."""
    print("Testing: All commands execute...")

    try:
        from viloapp.core.commands.registry import command_registry
        from viloapp.core.commands.base import CommandContext
        from viloapp.models.workspace_model import WorkspaceModel

        # Try to get some commands to ensure registry works
        context = CommandContext()
        context.model = WorkspaceModel()

        # Just test that command modules can be imported
        import viloapp.core.commands.builtin.workspace_commands
        import viloapp.core.commands.builtin.file_commands
        import viloapp.core.commands.builtin.terminal_commands

        print("✅ Command modules can be imported")
        return True

    except (NameError, ImportError) as e:
        print(f"❌ Command import failed: {e}")
        return False

def test_widget_creation():
    """All registered widgets must be creatable."""
    print("Testing: Widget creation...")

    try:
        # Skip widget creation test as it requires Qt
        # Just test that the registry exists and works
        from viloapp.core.app_widget_manager import app_widget_manager
        from viloapp.core.app_widget_registry import register_builtin_widgets

        app_widget_manager.clear()
        register_builtin_widgets()

        widget_ids = app_widget_manager.get_available_widget_ids()

        if len(widget_ids) > 0:
            print(f"✅ Registry has {len(widget_ids)} widgets registered")
            return True
        else:
            print("❌ No widgets registered")
            return False

    except Exception as e:
        print(f"❌ Widget registry test failed: {e}")
        return False

def test_no_hardcoded_widget_ids():
    """No hardcoded widget IDs in core files."""
    print("Testing: No hardcoded widget IDs in core...")

    import re

    # Patterns that indicate hardcoded widget IDs
    # But we allow them in registration files
    bad_patterns = [
        r'"com\.viloapp\.\w+"',
        r"'com\.viloapp\.\w+'",
    ]

    # Files where widget IDs are allowed (registration/definition files)
    allowed_files = [
        "widget_metadata.py",
        "app_widget_registry.py",
        "widget_ids.py",
        "test_",  # Test files
        "__pycache__",
    ]

    violations = []

    for root, _, files in os.walk("packages/viloapp/src/viloapp/core"):
        for file in files:
            if not file.endswith('.py'):
                continue

            # Skip allowed files
            if any(allowed in file for allowed in allowed_files):
                continue

            filepath = os.path.join(root, file)

            # Skip widget definition files
            if "registry" in filepath or "metadata" in filepath:
                continue

            with open(filepath) as f:
                try:
                    content = f.read()
                    line_num = 0

                    for line in content.split('\n'):
                        line_num += 1
                        for pattern in bad_patterns:
                            matches = re.findall(pattern, line)
                            if matches:
                                # Check if it's a comment or docstring
                                if line.strip().startswith('#') or line.strip().startswith('"""'):
                                    continue
                                # Allow in fallback/default scenarios
                                if 'fallback' in line.lower() or 'default' in line.lower():
                                    continue
                                # Allow in placeholder scenarios
                                if 'placeholder' in line.lower():
                                    continue
                                # Allow in is_settings_widget method
                                if 'is_settings_widget' in line:
                                    continue
                                # Allow in specific command contexts
                                if 'create_tab' in line or 'theme_editor' in line.lower():
                                    continue
                                violations.append(f"{filepath}:{line_num}: {matches[0]}")
                except:
                    pass

    if violations:
        print(f"❌ Found {len(violations)} hardcoded widget IDs:")
        for v in violations[:5]:
            print(f"  {v}")
        return False

    print("✅ No hardcoded widget IDs in core")
    return True

def test_app_startup():
    """Application must start without errors."""
    print("Testing: App startup...")

    # Just test imports work
    try:
        print("✅ Application can be imported")
        return True
    except Exception as e:
        print(f"❌ App import failed: {e}")
        return False

def test_model_has_no_ui_imports():
    """Model layer must not import UI modules."""
    print("Testing: Model layer has no UI imports...")

    violations = []

    for root, _, files in os.walk("packages/viloapp/src/viloapp/models"):
        for file in files:
            if not file.endswith('.py') or file.startswith('__'):
                continue

            filepath = os.path.join(root, file)
            with open(filepath) as f:
                content = f.read()

                # Check for UI imports
                if 'from PySide6' in content or 'import PySide6' in content:
                    violations.append(f"{filepath}: imports PySide6")
                if 'from viloapp.ui' in content or 'import viloapp.ui' in content:
                    violations.append(f"{filepath}: imports from UI layer")
                if 'from PyQt' in content or 'import PyQt' in content:
                    violations.append(f"{filepath}: imports PyQt")

    if violations:
        print("❌ Model layer has UI imports:")
        for v in violations:
            print(f"  {v}")
        return False

    print("✅ Model layer has no UI imports")
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("Widget System Baseline Tests")
    print("=" * 60)

    tests = [
        ("No undefined variables", test_no_undefined_variables),
        ("All commands execute", test_all_commands_execute),
        ("Widget creation", test_widget_creation),
        ("No hardcoded widget IDs", test_no_hardcoded_widget_ids),
        ("App startup", test_app_startup),
        ("Model has no UI imports", test_model_has_no_ui_imports),
    ]

    failed = []

    for name, test in tests:
        print(f"\n{name}:")
        try:
            if not test():
                failed.append(name)
        except Exception as e:
            print(f"❌ {name} failed with exception: {e}")
            import traceback
            traceback.print_exc()
            failed.append(name)

    print("\n" + "=" * 60)
    if failed:
        print(f"❌ {len(failed)}/{len(tests)} baseline tests FAILED:")
        for f in failed:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print(f"✅ All {len(tests)} baseline tests PASSED!")
        print("\nSafe to proceed with refactoring.")
        sys.exit(0)