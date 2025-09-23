#!/usr/bin/env python3
"""
Test script to verify the widget refactoring is working correctly.
"""

import sys
import os

# Add the package to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "packages/viloapp/src"))

def test_widget_ids():
    """Test that widget IDs are defined correctly."""
    from viloapp.core.widget_ids import (
        TERMINAL,
        EDITOR,
        OUTPUT,
        SETTINGS,
        FILE_EXPLORER,
        migrate_widget_type
    )

    print("Testing widget IDs...")
    assert TERMINAL == "com.viloapp.terminal"
    assert EDITOR == "com.viloapp.editor"
    assert OUTPUT == "com.viloapp.output"
    assert SETTINGS == "com.viloapp.settings"
    assert FILE_EXPLORER == "com.viloapp.explorer"
    print("✓ Widget IDs are correct")

    # Test migration
    print("Testing widget type migration...")
    assert migrate_widget_type("terminal") == "com.viloapp.terminal"
    assert migrate_widget_type("editor") == "com.viloapp.editor"
    assert migrate_widget_type("text_editor") == "com.viloapp.editor"
    assert migrate_widget_type("custom") == "plugin.unknown"
    assert migrate_widget_type("plugin.markdown") == "plugin.markdown"
    print("✓ Widget type migration works")


def test_widget_metadata():
    """Test the widget metadata registry."""
    from viloapp.core.widget_metadata import (
        widget_metadata_registry,
        get_widget_display_name,
        WidgetMetadata
    )
    from viloapp.core.widget_ids import TERMINAL, EDITOR

    print("Testing widget metadata registry...")

    # Test built-in widgets are registered
    metadata = widget_metadata_registry.get_metadata(TERMINAL)
    assert metadata is not None
    assert metadata.display_name == "Terminal"
    assert metadata.icon == "terminal"
    assert "shell" in metadata.capabilities
    print("✓ Terminal widget metadata is correct")

    metadata = widget_metadata_registry.get_metadata(EDITOR)
    assert metadata is not None
    assert metadata.display_name == "Text Editor"
    assert metadata.icon == "file-text"
    assert "text_editing" in metadata.capabilities
    print("✓ Editor widget metadata is correct")

    # Test display name function
    assert get_widget_display_name(TERMINAL) == "Terminal"
    assert get_widget_display_name(EDITOR) == "Text Editor"
    assert get_widget_display_name("plugin.markdown_editor") == "Markdown Editor"
    print("✓ Display name resolution works")

    # Test registering a plugin widget
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
    """Test that the workspace model uses widget IDs."""
    from viloapp.models.workspace_model import WorkspaceModel
    from viloapp.core.widget_ids import TERMINAL, EDITOR

    print("Testing workspace model...")

    # Create a model
    model = WorkspaceModel()

    # Test creating a tab with widget ID
    tab_id = model.create_tab("Test Tab", widget_id=TERMINAL)
    assert tab_id is not None

    tab = model._find_tab(tab_id)
    assert tab is not None
    assert tab.name == "Test Tab"
    assert tab.tree.root.pane.widget_id == TERMINAL
    print("✓ Tab creation with widget ID works")

    # Test changing widget
    pane_id = tab.tree.root.pane.id
    success = model.change_pane_widget(pane_id, EDITOR)
    assert success
    assert tab.tree.root.pane.widget_id == EDITOR
    print("✓ Widget change works")

    # Test serialization
    state = model.save_state()
    assert "tabs" in state
    assert len(state["tabs"]) > 0
    tab_data = state["tabs"][0]
    assert "tree" in tab_data
    assert "pane" in tab_data["tree"]
    assert tab_data["tree"]["pane"]["widget_id"] == EDITOR
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
    assert restored_tab.tree.root.pane.widget_id == TERMINAL
    print("✓ Deserialization from old format works")


def test_no_widget_type_enum():
    """Verify that WidgetType enum no longer exists."""
    print("Testing WidgetType enum removal...")

    try:
        from viloapp.models.workspace_model import WidgetType
        assert False, "WidgetType should not exist!"
    except ImportError:
        print("✓ WidgetType enum has been removed")

    try:
        from viloapp.ui.widgets.widget_registry import WidgetType
        assert False, "WidgetType should not be in widget_registry!"
    except ImportError:
        print("✓ WidgetType not in widget_registry")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Widget System Refactoring Test Suite")
    print("=" * 60)
    print()

    try:
        test_widget_ids()
        print()

        test_widget_metadata()
        print()

        test_workspace_model()
        print()

        test_no_widget_type_enum()
        print()

        print("=" * 60)
        print("✅ All tests passed! Widget refactoring is working correctly.")
        print("=" * 60)

        return 0

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())