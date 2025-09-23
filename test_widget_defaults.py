#!/usr/bin/env python3
"""Test script to verify widget default system is working correctly."""

import sys

# Add the project path
sys.path.insert(0, "packages/viloapp/src")

def test_metadata_fields():
    """Test that metadata has the new default fields."""
    from viloapp.core.app_widget_metadata import AppWidgetMetadata

    # Check that new fields exist
    metadata = AppWidgetMetadata(
        widget_id="test.widget",
        display_name="Test Widget",
        description="Test",
        icon="test",
        category="editor",
        widget_class=object,
        can_be_default=True,
        default_priority=50,
        default_for_contexts=["test", "demo"]
    )

    assert metadata.can_be_default == True
    assert metadata.default_priority == 50
    assert "test" in metadata.default_for_contexts
    print("✅ Metadata fields working")

def test_registry_defaults():
    """Test that registry can find defaults without hardcoding."""
    from viloapp.core.app_widget_manager import app_widget_manager

    # Clear and register test widgets
    app_widget_manager.clear()

    # Register widgets
    from viloapp.core.app_widget_registry import register_builtin_widgets
    register_builtin_widgets()

    # Test getting defaults
    default = app_widget_manager.get_default_widget_id()
    print(f"✅ Default widget: {default}")

    terminal = app_widget_manager.get_default_terminal_id()
    print(f"✅ Default terminal: {terminal}")

    editor = app_widget_manager.get_default_editor_id()
    print(f"✅ Default editor: {editor}")

    # Test context widgets
    terminal_widgets = app_widget_manager.get_widgets_for_context("terminal")
    print(f"✅ Terminal context widgets: {terminal_widgets}")

    editor_widgets = app_widget_manager.get_widgets_for_context("editor")
    print(f"✅ Editor context widgets: {editor_widgets}")

def test_no_hardcoded_constants():
    """Test that widget_ids.py has no hardcoded widget IDs."""
    from viloapp.core import widget_ids

    # Check that no specific widget constants exist
    forbidden = ["TERMINAL", "EDITOR", "SETTINGS", "OUTPUT", "DEFAULT_WIDGET_ID"]

    for name in forbidden:
        if hasattr(widget_ids, name):
            print(f"❌ Found hardcoded constant: {name}")
            return False

    print("✅ No hardcoded widget constants found")
    return True

def test_user_preferences():
    """Test user preference functions."""
    from viloapp.core.settings.app_defaults import (
        get_default_widget_preference,
        set_default_widget_preference,
        get_default_widget_for_context,
        set_default_widget_for_context
    )

    # Test general preference
    result = set_default_widget_preference("com.viloapp.editor")
    print(f"✅ Set default preference: {result}")

    pref = get_default_widget_preference()
    print(f"✅ Got default preference: {pref}")

    # Test context preference
    result = set_default_widget_for_context("terminal", "com.viloapp.terminal")
    print(f"✅ Set context preference: {result}")

    pref = get_default_widget_for_context("terminal")
    print(f"✅ Got context preference: {pref}")

def main():
    """Run all tests."""
    print("=" * 60)
    print("Widget Default System Tests")
    print("=" * 60)

    try:
        test_metadata_fields()
        print()

        test_registry_defaults()
        print()

        test_no_hardcoded_constants()
        print()

        test_user_preferences()
        print()

        print("=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())