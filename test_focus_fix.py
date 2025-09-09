#!/usr/bin/env python3
"""
Test script for focus management fix.
Verifies that clicking on different panes properly updates the active pane.
"""

import sys
from PySide6.QtWidgets import QApplication
from ui.widgets.split_pane_model import SplitPaneModel
from ui.widgets.split_pane_widget import SplitPaneWidget
from ui.widgets.widget_registry import WidgetType

def test_focus_management():
    """Test that focus management works correctly."""
    print("🔧 Testing focus management fix...")
    
    # Create QApplication
    app = QApplication(sys.argv)
    
    # Create split widget with terminal
    split_widget = SplitPaneWidget(WidgetType.TERMINAL)
    
    print(f"✓ Initial active pane: {split_widget.active_pane_id}")
    initial_pane = split_widget.active_pane_id
    
    # Split horizontally to create second pane
    new_pane = split_widget.model.split_pane(initial_pane, "horizontal")
    split_widget.refresh_view()
    
    print(f"✓ After split, active pane: {split_widget.active_pane_id}")
    print(f"✓ New pane created: {new_pane}")
    print(f"✓ All panes: {split_widget.get_all_pane_ids()}")
    
    # Test focus change by directly calling set_active_pane
    print(f"\n--- Testing focus change ---")
    print(f"Before focus change - active: {split_widget.active_pane_id}")
    
    # Focus on the initial pane
    split_widget.set_active_pane(initial_pane)
    print(f"After focusing initial pane - active: {split_widget.active_pane_id}")
    
    # Focus on the new pane  
    split_widget.set_active_pane(new_pane)
    print(f"After focusing new pane - active: {split_widget.active_pane_id}")
    
    # Test simulated clicks by triggering focus_requested signals
    print(f"\n--- Testing simulated clicks ---")
    
    # Get the AppWidgets
    initial_leaf = split_widget.model.find_leaf(initial_pane)
    new_leaf = split_widget.model.find_leaf(new_pane)
    
    if initial_leaf and initial_leaf.app_widget:
        print(f"Simulating click on initial pane ({initial_pane})")
        initial_leaf.app_widget.request_focus()
        print(f"Active after initial click: {split_widget.active_pane_id}")
        
    if new_leaf and new_leaf.app_widget:
        print(f"Simulating click on new pane ({new_pane})")
        new_leaf.app_widget.request_focus()
        print(f"Active after new click: {split_widget.active_pane_id}")
        
    # Test that splits would target the correct pane now
    print(f"\n--- Testing split targeting ---")
    current_active = split_widget.active_pane_id
    print(f"Current active pane: {current_active}")
    
    # This should split the currently active pane
    third_pane = split_widget.model.split_pane(current_active, "vertical")
    split_widget.refresh_view()
    print(f"Split {current_active} vertically, created: {third_pane}")
    print(f"All panes now: {split_widget.get_all_pane_ids()}")
    
    # Clean up
    split_widget.cleanup()
    print(f"\n✅ Focus management test completed!")
    
if __name__ == "__main__":
    test_focus_management()