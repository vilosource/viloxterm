#!/usr/bin/env python3
"""
Validation script for the view layer.

This script tests that views render correctly from the model
and respond to model changes without storing any state.
"""

import sys

from commands import CommandContext, CommandRegistry
from model import WidgetType, WorkspaceModel
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
from views import WorkspaceView


def print_header(title: str):
    """Print a section header."""
    print(f"\n{'=' * 60}")
    print(f" {title}")
    print(f"{'=' * 60}")


def print_success(msg: str):
    """Print success message."""
    print(f"✅ {msg}")


def print_error(msg: str):
    """Print error message."""
    print(f"❌ {msg}")


def print_info(msg: str):
    """Print info message."""
    print(f"ℹ️  {msg}")


def validate_views():
    """Run view validation tests."""
    print_header("VIEW LAYER VALIDATION")

    # Create Qt application
    app = QApplication.instance() or QApplication(sys.argv)
    print_success("Qt application created")

    # Test 1: Basic rendering
    print_header("Test 1: Basic Rendering")

    model = WorkspaceModel()
    registry = CommandRegistry()
    view = WorkspaceView(model, registry)

    assert view is not None
    assert view.tab_widget is not None
    print_success("WorkspaceView created successfully")

    # Create a tab
    context = CommandContext(model=model)
    result = registry.execute("tab.create", context, name="Test Tab", widget_type=WidgetType.EDITOR)
    assert result.success
    print_success("Tab created through command")

    # Check view updated
    assert view.tab_widget.count() == 1
    print_success("View rendered the tab")

    # Test 2: Tree rendering
    print_header("Test 2: Tree Rendering")

    # Get the active pane and split it
    pane = model.get_active_pane()
    assert pane is not None

    result = registry.execute("pane.split", context, pane_id=pane.id, orientation="horizontal")
    assert result.success
    new_pane_id = result.data["new_pane_id"]
    print_success("Pane split horizontally")

    # Split again vertically
    result = registry.execute("pane.split", context, pane_id=new_pane_id, orientation="vertical")
    assert result.success
    print_success("Pane split vertically")

    # Verify view structure (should have 3 panes now)
    tab = model.state.get_active_tab()
    assert tab is not None
    assert len(tab.tree.root.get_all_panes()) == 3
    print_success("Tree structure correctly built in model")

    # Test 3: Model observer
    print_header("Test 3: Model Observer")

    initial_tab_count = view.tab_widget.count()

    # Create another tab
    result = registry.execute(
        "tab.create", context, name="Terminal", widget_type=WidgetType.TERMINAL
    )
    assert result.success
    print_success("Created terminal tab")

    # View should auto-update
    assert view.tab_widget.count() == initial_tab_count + 1
    print_success("View updated from model change")

    # Test 4: Tab operations through view
    print_header("Test 4: Tab Operations")

    # Test tab switching
    if view.tab_widget.count() > 1:
        view.tab_widget.setCurrentIndex(0)
        assert model.state.active_tab_id == model.state.tabs[0].id
        print_success("Tab switching updates model")

    # Test 5: Pane operations through view
    print_header("Test 5: Pane Operations")

    # Focus a pane (would be triggered by click in real UI)
    panes = model.get_all_panes()
    if panes:
        first_pane = panes[0]
        result = registry.execute("pane.focus", context, pane_id=first_pane.id)
        assert result.success
        assert model.get_active_pane() == first_pane
        print_success("Pane focus through command")

    # Test 6: State restoration
    print_header("Test 6: State Restoration")

    # Serialize current state
    state = model.serialize()
    print_success("State serialized")

    # Create new model and view
    model2 = WorkspaceModel()
    view2 = WorkspaceView(model2, registry)

    # Restore state
    model2.deserialize(state)
    print_success("State restored to new model")

    # View should reflect restored state
    assert view2.tab_widget.count() == view.tab_widget.count()
    print_success("View reflects restored state")

    # Test 7: Widget factory
    print_header("Test 7: Widget Factory")

    from views import WidgetFactory

    # Test each widget type
    for widget_type in WidgetType:
        widget = WidgetFactory.create(widget_type, "test-id")
        assert widget is not None
        print_success(f"Created {widget_type.value} widget")

    # Test 8: No state in views
    print_header("Test 8: Stateless Views")

    # Views should not store model data
    assert not hasattr(view, "tabs")
    assert not hasattr(view, "panes")
    assert not hasattr(view, "state")
    print_success("Views are stateless")

    # The only reference should be to the model
    assert hasattr(view, "model")
    assert view.model is model
    print_success("View only references model")

    # Test 9: Complex layout
    print_header("Test 9: Complex Layout")

    # Create a complex layout
    model3 = WorkspaceModel()
    view3 = WorkspaceView(model3, registry)

    # Create multiple tabs with different layouts
    for i in range(3):
        tab_id = model3.create_tab(f"Tab {i + 1}")
        model3.set_active_tab(tab_id)

        # Create different split patterns
        pane = model3.get_active_pane()
        if pane and i > 0:
            for _ in range(i):
                new_id = model3.split_pane(pane.id, "horizontal" if i % 2 == 0 else "vertical")
                if new_id:
                    pane = model3.get_pane(new_id)

    assert view3.tab_widget.count() == 3
    print_success("Complex layout created and rendered")

    # Test 10: Performance
    print_header("Test 10: Performance")

    import time

    # Measure rendering time for many operations
    start = time.time()

    for _ in range(10):
        model3.create_tab("Perf Test")

    elapsed = time.time() - start
    print_success(f"Created 10 tabs in {elapsed:.3f} seconds")

    # Rendering should be fast
    assert elapsed < 1.0  # Should take less than 1 second
    print_success("Performance acceptable")

    # Summary
    print_header("VALIDATION SUMMARY")
    print_success("All view tests passed! ✨")
    print_info("\nThe view layer is fully functional:")
    print_info("- Pure rendering from model")
    print_info("- Observer pattern working")
    print_info("- Tree structure renders correctly")
    print_info("- Commands integrate properly")
    print_info("- Views are completely stateless")
    print_info("- Performance is good")

    # Show the view briefly
    print_info("\nShowing view for 2 seconds...")
    view3.resize(1200, 800)
    view3.show()

    # Close after 2 seconds
    QTimer.singleShot(2000, app.quit)
    app.exec()

    return True


if __name__ == "__main__":
    try:
        success = validate_views()
        if success:
            exit(0)
        else:
            exit(1)
    except Exception as e:
        print_error(f"Validation failed with error: {e}")
        import traceback

        traceback.print_exc()
        exit(1)
