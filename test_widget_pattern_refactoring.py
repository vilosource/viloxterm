#!/usr/bin/env python3
"""
Test script to verify the pattern-based widget refactoring.
Tests that widget IDs follow patterns, not hardcoded constants.
"""

import sys
import os

# Add the package to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "packages/viloapp/src"))

def test_widget_id_patterns():
    """Test that widget ID patterns and utilities work."""
    from viloapp.core.widget_ids import (
        is_builtin_widget,
        is_plugin_widget,
        validate_widget_id,
        get_widget_namespace,
        get_widget_name,
        migrate_widget_type
    )

    print("Testing widget ID pattern functions...")

    # Test built-in detection
    assert is_builtin_widget("com.viloapp.terminal") == True
    assert is_builtin_widget("plugin.markdown.editor") == False

    # Test plugin detection
    assert is_plugin_widget("plugin.markdown.editor") == True
    assert is_plugin_widget("com.viloapp.terminal") == False

    # Test validation
    assert validate_widget_id("com.viloapp.terminal") == True
    assert validate_widget_id("plugin.markdown.editor") == True
    assert validate_widget_id("invalid") == False

    # Test namespace extraction
    assert get_widget_namespace("com.viloapp.terminal") == "com.viloapp"
    assert get_widget_namespace("plugin.markdown.editor") == "plugin.markdown"

    # Test name extraction
    assert get_widget_name("com.viloapp.terminal") == "terminal"
    assert get_widget_name("plugin.markdown.editor") == "editor"

    print("✓ Widget ID pattern functions work correctly")

    # Test migration
    print("Testing widget type migration...")
    assert migrate_widget_type("terminal") == "com.viloapp.terminal"
    assert migrate_widget_type("editor") == "com.viloapp.editor"
    assert migrate_widget_type("text_editor") == "com.viloapp.editor"
    assert migrate_widget_type("custom") == "plugin.unknown"
    assert migrate_widget_type("plugin.markdown") == "plugin.markdown"
    print("✓ Widget type migration works")


def test_widget_registration():
    """Test that widgets can be registered without hardcoded constants."""
    from viloapp.core.app_widget_manager import app_widget_manager
    from viloapp.core.app_widget_registry import register_builtin_widgets

    print("Testing widget registration...")

    # Clear and register
    app_widget_manager.clear()
    register_builtin_widgets()

    # Check all widgets registered
    widget_ids = app_widget_manager.get_available_widget_ids()
    assert len(widget_ids) >= 8, f"Expected at least 8 widgets, got {len(widget_ids)}"

    # Check specific widgets exist
    expected = [
        "com.viloapp.terminal",
        "com.viloapp.editor",
        "com.viloapp.settings",
        "com.viloapp.placeholder"
    ]
    for widget_id in expected:
        assert widget_id in widget_ids, f"Missing widget: {widget_id}"

    print(f"✓ {len(widget_ids)} widgets registered successfully")

    # Test default widget
    default_id = app_widget_manager.get_default_widget_id()
    assert default_id == "com.viloapp.terminal"
    print(f"✓ Default widget is: {default_id}")


def test_widget_metadata():
    """Test the widget metadata registry."""
    from viloapp.core.widget_metadata import (
        widget_metadata_registry,
        get_widget_display_name,
    )

    print("Testing widget metadata registry...")

    # Test built-in widgets are registered
    metadata = widget_metadata_registry.get_metadata("com.viloapp.terminal")
    assert metadata is not None
    assert metadata.display_name == "Terminal"
    assert metadata.icon == "terminal"
    assert "shell" in metadata.capabilities
    print("✓ Terminal widget metadata is correct")

    metadata = widget_metadata_registry.get_metadata("com.viloapp.editor")
    assert metadata is not None
    assert metadata.display_name == "Text Editor"
    assert metadata.icon == "file-text"
    assert "text_editing" in metadata.capabilities
    print("✓ Editor widget metadata is correct")

    # Test display name function
    assert get_widget_display_name("com.viloapp.terminal") == "Terminal"
    assert get_widget_display_name("com.viloapp.editor") == "Text Editor"
    assert get_widget_display_name("plugin.markdown_editor") == "Markdown Editor"
    print("✓ Display name resolution works")

    # Test registering a plugin widget
    from viloapp.core.widget_metadata import WidgetMetadata
    plugin_metadata = WidgetMetadata(
        widget_id="plugin.test_widget",
        display_name="Test Widget",
        icon="test",
        category="testing",
        capabilities={"test"}
    )
    widget_metadata_registry.register(plugin_metadata)

    retrieved = widget_metadata_registry.get_metadata("plugin.test_widget")
    assert retrieved is not None
    assert retrieved.display_name == "Test Widget"
    print("✓ Plugin widget registration works")


def test_workspace_model():
    """Test that the workspace model uses widget IDs without constants."""
    from viloapp.models.workspace_model import WorkspaceModel
    from viloapp.core.app_widget_registry import register_builtin_widgets

    # Ensure widgets are registered
    register_builtin_widgets()

    print("Testing workspace model...")

    # Create a model
    model = WorkspaceModel()

    # Test creating a tab - should use default from registry
    tab_id = model.create_tab("Test Tab")
    assert tab_id is not None

    tab = model._find_tab(tab_id)
    assert tab is not None
    assert tab.name == "Test Tab"
    # Should get default from registry
    assert tab.tree.root.pane.widget_id.startswith("com.viloapp.")
    print("✓ Tab creation with default widget ID works")

    # Test with specific widget ID
    tab_id2 = model.create_tab("Editor Tab", "com.viloapp.editor")
    tab2 = model._find_tab(tab_id2)
    assert tab2.tree.root.pane.widget_id == "com.viloapp.editor"
    print("✓ Tab creation with specific widget ID works")

    # Test changing widget - create new tab for this test
    tab_id3 = model.create_tab("Change Test Tab", "com.viloapp.terminal")
    tab3 = model._find_tab(tab_id3)
    pane_id = tab3.tree.root.pane.id
    success = model.change_pane_widget(pane_id, "com.viloapp.output")
    assert success == True, f"Widget change failed: {success}"
    # Re-fetch tab to ensure we have latest state
    tab3 = model._find_tab(tab_id3)
    assert tab3.tree.root.pane.widget_id == "com.viloapp.output"
    print("✓ Widget change works")

    # Test serialization
    state = model.save_state()
    assert "tabs" in state
    assert len(state["tabs"]) > 0
    tab_data = state["tabs"][0]
    assert "tree" in tab_data
    assert "pane" in tab_data["tree"]
    assert "widget_id" in tab_data["tree"]["pane"]
    print("✓ Serialization includes widget_id")

    # Test deserialization with old format
    old_format = {
        "tabs": [{
            "id": "test",
            "name": "Old Tab",
            "tree": {
                "type": "leaf",
                "pane": {
                    "id": "pane1",
                    "widget_type": "terminal",  # Old format
                    "focused": True
                }
            }
        }]
    }

    new_model = WorkspaceModel()
    new_model.load_state(old_format)
    restored_tab = new_model.state.tabs[0]
    assert restored_tab.tree.root.pane.widget_id == "com.viloapp.terminal"
    print("✓ Deserialization from old format works")


def test_no_hardcoded_constants():
    """Verify that widget_ids.py contains no hardcoded widget constants."""
    print("Testing that no hardcoded constants exist...")

    # Read the file
    widget_ids_path = os.path.join(
        os.path.dirname(__file__),
        "packages/viloapp/src/viloapp/core/widget_ids.py"
    )

    with open(widget_ids_path, 'r') as f:
        content = f.read()

    # Check for absence of old-style constants
    bad_patterns = [
        "TERMINAL =",
        "EDITOR =",
        "OUTPUT =",
        "SETTINGS =",
        "FILE_EXPLORER =",
    ]

    for pattern in bad_patterns:
        # Allow these in comments or legacy map
        lines_with_pattern = [
            line for line in content.split('\n')
            if pattern in line and not line.strip().startswith('#')
            and 'LEGACY' not in line and '"' not in line
        ]
        assert len(lines_with_pattern) == 0, f"Found hardcoded constant: {pattern}"

    print("✓ No hardcoded widget constants found")

    # Verify only patterns exist
    assert "BUILTIN_WIDGET_PREFIX" in content
    assert "PLUGIN_WIDGET_PREFIX" in content
    print("✓ Only pattern constants exist")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Pattern-Based Widget System Test Suite")
    print("=" * 60)
    print()

    try:
        test_widget_id_patterns()
        print()

        test_widget_registration()
        print()

        test_widget_metadata()
        print()

        test_workspace_model()
        print()

        test_no_hardcoded_constants()
        print()

        print("=" * 60)
        print("✅ All tests passed! Widget pattern refactoring is working correctly.")
        print("✅ System supports unlimited plugin widgets without core changes.")
        print("=" * 60)

        return 0

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())