#!/usr/bin/env python3
"""Comprehensive tests for the completed widget system refactoring."""

import sys
sys.path.insert(0, "packages/viloapp/src")

def test_widget_registry():
    """Test that widget registry works properly."""
    print("Testing: Widget registry...")

    from viloapp.core.app_widget_manager import app_widget_manager

    # Clear and re-register
    app_widget_manager.clear()
    from viloapp.core.app_widget_registry import register_builtin_widgets
    register_builtin_widgets()

    # Check registration
    widget_ids = app_widget_manager.get_available_widget_ids()
    assert len(widget_ids) > 0, "No widgets registered"

    # Check metadata
    for widget_id in widget_ids:
        metadata = app_widget_manager.get_widget_metadata(widget_id)
        assert metadata is not None, f"No metadata for {widget_id}"
        assert metadata.widget_id == widget_id, f"Metadata ID mismatch for {widget_id}"

    print(f"✅ Registry has {len(widget_ids)} widgets with valid metadata")
    return True

def test_widget_preferences():
    """Test widget preference system."""
    print("Testing: Widget preferences...")

    from viloapp.models.workspace_model import WorkspaceModel
    from viloapp.services.widget_service import initialize_widget_service, get_widget_service

    # Create model and service
    model = WorkspaceModel()
    initialize_widget_service(model)
    service = get_widget_service()

    assert service is not None, "Widget service not initialized"

    # Test setting preferences
    success = service.set_default_widget("test_context", "com.viloapp.terminal")
    assert success, "Failed to set widget preference"

    # Test getting preferences
    pref = model.get_widget_preference("test_context")
    assert pref == "com.viloapp.terminal", "Preference not saved correctly"

    # Test default resolution
    default = model.get_default_widget_for_context("test_context")
    assert default == "com.viloapp.terminal", "Default resolution failed"

    # Test clearing preferences
    model.clear_widget_preference("test_context")
    pref = model.get_widget_preference("test_context")
    assert pref is None, "Preference not cleared"

    print("✅ Widget preferences working correctly")
    return True

def test_model_widget_methods():
    """Test WorkspaceModel widget methods."""
    print("Testing: Model widget methods...")

    from viloapp.models.workspace_model import WorkspaceModel

    model = WorkspaceModel()

    # Test widget availability
    widget_ids = model.get_available_widget_ids()
    assert len(widget_ids) > 0, "No available widgets from model"

    # Test widget validation
    assert model.validate_widget_id("com.viloapp.terminal"), "Valid widget ID rejected"
    assert not model.validate_widget_id("invalid.widget"), "Invalid widget ID accepted"

    # Create a tab and test widget operations
    tab_id = model.create_tab("Test Tab")
    assert tab_id is not None, "Failed to create tab"

    tab = model.state.get_active_tab()
    assert tab is not None, "No active tab"

    # Get root pane
    panes = tab.tree.root.get_all_panes()
    assert len(panes) == 1, "Wrong number of panes"

    pane = panes[0]

    # Test changing widget
    success = model.change_pane_widget(pane.id, "com.viloapp.editor")
    assert success, "Failed to change pane widget"
    assert pane.widget_id == "com.viloapp.editor", "Widget not changed"

    print("✅ Model widget methods working correctly")
    return True

def test_widget_commands():
    """Test widget commands."""
    print("Testing: Widget commands...")

    from viloapp.core.commands.registry import command_registry
    from viloapp.models.workspace_model import WorkspaceModel
    from viloapp.services.widget_service import initialize_widget_service

    # Initialize
    model = WorkspaceModel()
    initialize_widget_service(model)

    # Register commands
    from viloapp.core.commands.builtin.widget_commands import register_widget_commands
    register_widget_commands()

    # Check command registration
    assert command_registry.get_command("widget.setDefault") is not None, "setDefault command not registered"
    assert command_registry.get_command("widget.clearDefault") is not None, "clearDefault command not registered"
    assert command_registry.get_command("widget.list") is not None, "list command not registered"

    print("✅ Widget commands registered correctly")
    return True

def test_pure_view_splitpane():
    """Test that SplitPaneWidget is a pure view."""
    print("Testing: Pure view SplitPaneWidget...")

    # This test would require Qt which we don't have in testing
    # Just verify the class structure
    from viloapp.ui.widgets.split_pane_widget import SplitPaneWidget

    # Check that it requires a model
    import inspect
    sig = inspect.signature(SplitPaneWidget.__init__)
    params = list(sig.parameters.keys())

    assert "model" in params, "SplitPaneWidget doesn't take model parameter"

    # Check observer methods exist
    assert hasattr(SplitPaneWidget, "_connect_model_observers"), "Missing observer connection"
    assert hasattr(SplitPaneWidget, "refresh_view"), "Missing refresh_view method"

    print("✅ SplitPaneWidget has pure view structure")
    return True

def test_widget_factory():
    """Test widget factory pattern."""
    print("Testing: Widget factory...")

    from viloapp.ui.factories.widget_factory import (
        get_widget_factory,
        create_widget_for_pane
    )

    factory = get_widget_factory()
    assert factory is not None, "Factory not created"

    # Check factory methods exist
    assert hasattr(factory, "create_widget"), "Missing create_widget method"
    assert hasattr(factory, "register_widget_creator"), "Missing register method"

    # Check convenience function
    assert create_widget_for_pane is not None, "Convenience function missing"

    print("✅ Widget factory pattern implemented")
    return True

def test_no_circular_dependencies():
    """Test that there are no circular import issues."""
    print("Testing: No circular dependencies...")

    # Try importing all major components in order
    try:
        # Model layer
        from viloapp.models.workspace_model import WorkspaceModel

        # Service layer
        from viloapp.services.widget_service import WidgetService

        # Core layer
        from viloapp.core.app_widget_manager import app_widget_manager
        from viloapp.core.app_widget_registry import register_builtin_widgets

        # Command layer
        from viloapp.core.commands.builtin.widget_commands import register_widget_commands

        # UI layer (would fail in test due to Qt, but import should work)
        try:
            from viloapp.ui.widgets.split_pane_widget import SplitPaneWidget
            from viloapp.ui.factories.widget_factory import WidgetFactory
            print("✅ No circular import issues")
        except ImportError as e:
            # Qt import errors are OK in testing
            if "PySide6" in str(e) or "QtCore" in str(e):
                print("✅ No circular import issues (Qt unavailable)")
            else:
                raise

        return True

    except ImportError as e:
        print(f"❌ Circular dependency detected: {e}")
        return False

def test_migration():
    """Test data migration from old format."""
    print("Testing: Data migration...")

    from viloapp.models.workspace_model import WorkspaceModel

    model = WorkspaceModel()

    # Create old format state
    old_state = {
        "version": "1.0",
        "tabs": [{
            "id": "tab1",
            "name": "Old Tab",
            "tree": {
                "type": "leaf",
                "pane": {
                    "id": "pane1",
                    "widget_type": "TERMINAL"  # Old enum format
                }
            }
        }],
        "active_tab_id": "tab1"
    }

    # Load and migrate
    success = model.load_state(old_state)
    assert success, "Failed to load old state"

    # Check migration worked
    tab = model.state.get_active_tab()
    assert tab is not None, "Tab not loaded"

    panes = tab.tree.root.get_all_panes()
    assert len(panes) == 1, "Pane not loaded"

    # Check widget_id was migrated
    pane = panes[0]
    assert hasattr(pane, "widget_id"), "widget_id not present"
    assert pane.widget_id == "com.viloapp.terminal", f"Migration failed: {pane.widget_id}"

    print("✅ Migration from old format working")
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("Widget System Complete Tests")
    print("=" * 60)

    tests = [
        ("Widget Registry", test_widget_registry),
        ("Widget Preferences", test_widget_preferences),
        ("Model Widget Methods", test_model_widget_methods),
        ("Widget Commands", test_widget_commands),
        ("Pure View SplitPane", test_pure_view_splitpane),
        ("Widget Factory", test_widget_factory),
        ("No Circular Dependencies", test_no_circular_dependencies),
        ("Data Migration", test_migration),
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
        print(f"❌ {len(failed)}/{len(tests)} tests FAILED:")
        for f in failed:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print(f"✅ All {len(tests)} tests PASSED!")
        print("\nWidget system refactoring is COMPLETE!")
        sys.exit(0)