#!/usr/bin/env python3
"""
Validation script for the new WorkspaceModel.

This script tests all model operations to ensure they work correctly
before we proceed with the view layer.
"""

import json

from model import WidgetType, WorkspaceModel


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


def validate_model():
    """Run comprehensive model validation."""
    print_header("WORKSPACE MODEL VALIDATION")

    # Create model
    model = WorkspaceModel()
    print_success("Model created successfully")

    # Track events
    events = []

    def event_tracker(event: str, data):
        events.append({"event": event, "data": data})
        print_info(f"Event: {event} - {data}")

    model.add_observer(event_tracker)
    print_success("Observer attached")

    # Test 1: Create tabs
    print_header("Test 1: Tab Creation")
    tab1_id = model.create_tab("Editor Tab", WidgetType.EDITOR)
    print_success(f"Created tab 1: {tab1_id}")

    tab2_id = model.create_tab("Terminal Tab", WidgetType.TERMINAL)
    print_success(f"Created tab 2: {tab2_id}")

    # Verify state
    assert len(model.state.tabs) == 2, "Should have 2 tabs"
    assert model.state.active_tab_id == tab2_id, "Tab 2 should be active"
    print_success("Tab state verified")

    # Test 2: Get active pane
    print_header("Test 2: Active Pane")
    pane = model.get_active_pane()
    if pane:
        print_success(f"Active pane ID: {pane.id}")
        print_success(f"Active pane type: {pane.widget_type.value}")
        initial_pane_id = pane.id
    else:
        print_error("No active pane found")
        return False

    # Test 3: Split pane
    print_header("Test 3: Pane Splitting")
    new_pane_id = model.split_pane(initial_pane_id, "horizontal")
    if new_pane_id:
        print_success(f"Split pane horizontally, new pane: {new_pane_id}")
    else:
        print_error("Failed to split pane")
        return False

    # Check tree structure
    tab = model.state.get_active_tab()
    assert tab is not None
    assert tab.tree.root.is_split(), "Root should be a split node"
    assert tab.tree.root.first is not None
    assert tab.tree.root.second is not None
    print_success("Tree structure verified")

    # Test 4: Split again (vertical)
    print_header("Test 4: Nested Splitting")
    new_pane_id2 = model.split_pane(new_pane_id, "vertical")
    if new_pane_id2:
        print_success(f"Split pane vertically, new pane: {new_pane_id2}")
    else:
        print_error("Failed to split pane vertically")
        return False

    # Verify we have 3 panes
    all_panes = model.get_all_panes()
    assert len(all_panes) == 3, f"Should have 3 panes, got {len(all_panes)}"
    print_success(f"Total panes: {len(all_panes)}")

    # Test 5: Focus pane
    print_header("Test 5: Pane Focus")
    success = model.focus_pane(initial_pane_id)
    if success:
        print_success(f"Focused pane: {initial_pane_id}")
        active = model.get_active_pane()
        assert active and active.id == initial_pane_id
    else:
        print_error("Failed to focus pane")
        return False

    # Test 6: Change widget type
    print_header("Test 6: Change Widget Type")
    success = model.change_pane_widget(initial_pane_id, WidgetType.OUTPUT)
    if success:
        print_success("Changed widget type to OUTPUT")
        pane = model.get_pane(initial_pane_id)
        assert pane and pane.widget_type == WidgetType.OUTPUT
    else:
        print_error("Failed to change widget type")
        return False

    # Test 7: Close pane
    print_header("Test 7: Close Pane")
    success = model.close_pane(new_pane_id2)
    if success:
        print_success(f"Closed pane: {new_pane_id2}")
        all_panes = model.get_all_panes()
        assert len(all_panes) == 2, f"Should have 2 panes after closing, got {len(all_panes)}"
    else:
        print_error("Failed to close pane")
        return False

    # Test 8: Serialization
    print_header("Test 8: Serialization")
    state = model.serialize()
    print_success("State serialized")
    print_info(f"Serialized structure: {json.dumps(state, indent=2)[:500]}...")

    # Test 9: Deserialization
    print_header("Test 9: Deserialization")
    model2 = WorkspaceModel()
    model2.deserialize(state)
    print_success("State deserialized to new model")

    # Verify deserialized state
    assert len(model2.state.tabs) == 2, "Should have 2 tabs after deserialize"
    assert len(model2.get_all_panes()) == 2, "Should have 2 panes after deserialize"
    print_success("Deserialized state verified")

    # Test 10: Tab operations
    print_header("Test 10: Tab Operations")

    # Switch tabs
    success = model.set_active_tab(tab1_id)
    assert success and model.state.active_tab_id == tab1_id
    print_success(f"Switched to tab: {tab1_id}")

    # Rename tab
    success = model.rename_tab(tab1_id, "Renamed Tab")
    assert success
    tab = model._find_tab(tab1_id)
    assert tab and tab.name == "Renamed Tab"
    print_success("Tab renamed")

    # Try to close last tab (should fail)
    model.close_tab(tab2_id)  # Close tab 2
    success = model.close_tab(tab1_id)  # Try to close last tab
    assert not success, "Should not be able to close last tab"
    print_success("Prevented closing last tab")

    # Summary
    print_header("VALIDATION SUMMARY")
    print_success(f"Total events fired: {len(events)}")
    print_success("All tests passed! ✨")
    print_info("\nThe WorkspaceModel is fully functional and ready for use!")

    return True


if __name__ == "__main__":
    try:
        success = validate_model()
        if success:
            exit(0)
        else:
            exit(1)
    except Exception as e:
        print_error(f"Validation failed with error: {e}")
        import traceback

        traceback.print_exc()
        exit(1)
