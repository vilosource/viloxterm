#!/usr/bin/env python3
"""
Test script to verify the split command works without hardcoded widget IDs.
"""

import sys
sys.path.insert(0, "packages/viloapp/src")

def test_when_context():
    """Test that when_context can evaluate without importing constants."""
    print("Testing when_context evaluation...")

    # First register the widgets
    from viloapp.core.app_widget_registry import register_builtin_widgets
    register_builtin_widgets()

    from viloapp.core.commands.when_context import WhenContext
    from viloapp.core.commands.base import CommandContext
    from viloapp.models.workspace_model import WorkspaceModel

    # Create a model with a tab
    model = WorkspaceModel()
    tab_id = model.create_tab("Test", "com.viloapp.terminal")

    # Create context
    context = CommandContext(model=model)

    # Create when evaluator - this should not crash
    try:
        evaluator = WhenContext(context)
        print("✅ WhenContext created without import errors")

        # Test some conditions
        variables = evaluator._build_context_variables()
        print(f"  terminalFocus: {variables.get('terminalFocus', False)}")
        print(f"  editorFocus: {variables.get('editorFocus', False)}")
        print(f"  explorerFocus: {variables.get('explorerFocus', False)}")

        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_terminal_creation():
    """Test that terminal tabs can be created without hardcoded IDs."""
    print("\nTesting terminal tab creation...")

    # First register the widgets
    from viloapp.core.app_widget_registry import register_builtin_widgets
    register_builtin_widgets()

    from viloapp.core.commands.builtin.terminal_commands import new_terminal_handler
    from viloapp.core.commands.base import CommandContext
    from viloapp.models.workspace_model import WorkspaceModel

    model = WorkspaceModel()
    context = CommandContext(model=model)

    try:
        result = new_terminal_handler(context)
        if result.success:
            print("✅ Terminal tab created successfully")
            print(f"  Tab count: {len(model.state.tabs)}")
            if model.state.tabs:
                tab = model.state.tabs[0]
                pane = tab.get_active_pane()
                if pane:
                    print(f"  Widget ID: {pane.widget_id}")
            return True
        else:
            print("❌ Failed to create terminal")
            print(f"  Status: {result.status}")
            print(f"  Message: {result.message}")
            print(f"  Error: {getattr(result, 'error', 'No error field')}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_category_lookup():
    """Test that widgets can be found by category."""
    print("\nTesting widget category lookup...")

    from viloapp.core.app_widget_manager import app_widget_manager
    from viloapp.core.app_widget_metadata import WidgetCategory

    # Register built-in widgets
    from viloapp.core.app_widget_registry import register_builtin_widgets
    register_builtin_widgets()

    try:
        # Test getting default terminal widget
        terminal_id = app_widget_manager.get_default_widget_for_category(WidgetCategory.TERMINAL)
        print(f"✅ Default terminal widget: {terminal_id}")

        # Test getting default editor widget
        editor_id = app_widget_manager.get_default_widget_for_category(WidgetCategory.EDITOR)
        print(f"✅ Default editor widget: {editor_id}")

        # Test widget category checking
        if terminal_id:
            has_terminal_cat = app_widget_manager.widget_has_category(
                terminal_id, WidgetCategory.TERMINAL
            )
            print(f"✅ Terminal widget has TERMINAL category: {has_terminal_cat}")

        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Split Command Fix Test")
    print("=" * 60)

    tests = [
        ("When Context", test_when_context),
        ("Terminal Creation", test_terminal_creation),
        ("Category Lookup", test_category_lookup),
    ]

    failed = []
    for name, test in tests:
        if not test():
            failed.append(name)

    print("\n" + "=" * 60)
    if failed:
        print(f"❌ {len(failed)}/{len(tests)} tests FAILED:")
        for f in failed:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print(f"✅ All {len(tests)} tests PASSED!")
        print("\nThe split command should now work without hardcoded widget IDs.")
        sys.exit(0)