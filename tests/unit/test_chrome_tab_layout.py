#!/usr/bin/env python3
"""
Unit tests for Chrome tab bar layout changes.
Tests that the + button stays next to tabs with draggable space to window controls.
"""

import pytest
from unittest.mock import Mock, patch
from PySide6.QtWidgets import QWidget, QHBoxLayout, QSizePolicy
from PySide6.QtCore import Qt


class TestChromeTitleBarLayout:
    """Test Chrome title bar layout modifications."""
    
    def test_tab_container_has_maximum_size_policy(self, qtbot):
        """Test that tab container uses Maximum size policy to stay compact."""
        from ui.widgets.chrome_title_bar import ChromeTitleBar
        
        title_bar = ChromeTitleBar()
        qtbot.addWidget(title_bar)
        
        # Find the tab container widget
        tab_container = None
        for child in title_bar.children():
            if isinstance(child, QWidget) and hasattr(child, 'layout'):
                layout = child.layout()
                if layout and layout.count() >= 2:  # Has tab bar and + button
                    # Check if it contains the tab bar
                    for i in range(layout.count()):
                        item = layout.itemAt(i)
                        if item and item.widget() == title_bar.tab_bar:
                            tab_container = child
                            break
        
        assert tab_container is not None, "Tab container not found"
        
        # Verify size policy is Maximum (stays compact)
        size_policy = tab_container.sizePolicy()
        assert size_policy.horizontalPolicy() == QSizePolicy.Maximum, \
            f"Tab container should have Maximum horizontal policy, got {size_policy.horizontalPolicy()}"
        
        # Verify maximum width is set
        assert tab_container.maximumWidth() <= 1200, \
            f"Tab container max width should be limited, got {tab_container.maximumWidth()}"
    
    def test_spacer_between_tabs_and_controls(self, qtbot):
        """Test that there's an expanding spacer between tabs and window controls."""
        from ui.widgets.chrome_title_bar import ChromeTitleBar
        
        title_bar = ChromeTitleBar()
        qtbot.addWidget(title_bar)
        
        # Get main layout
        main_layout = title_bar.layout()
        assert main_layout is not None
        
        # Find the spacer widget
        spacer_found = False
        spacer_widget = None
        
        for i in range(main_layout.count()):
            item = main_layout.itemAt(i)
            if item:
                widget = item.widget()
                if widget and widget.objectName() == "dragSpacer":
                    spacer_found = True
                    spacer_widget = widget
                    break
        
        assert spacer_found, "Draggable spacer not found in layout"
        
        # Verify spacer has expanding policy
        size_policy = spacer_widget.sizePolicy()
        assert size_policy.horizontalPolicy() == QSizePolicy.Expanding, \
            f"Spacer should have Expanding policy, got {size_policy.horizontalPolicy()}"
        
        # Verify minimum width for dragging
        assert spacer_widget.minimumWidth() >= 80, \
            f"Spacer should have minimum width for dragging, got {spacer_widget.minimumWidth()}"
    
    def test_new_tab_button_next_to_tabs(self, qtbot):
        """Test that + button is positioned next to tab bar, not at fixed position."""
        from ui.widgets.chrome_title_bar import ChromeTitleBar
        
        title_bar = ChromeTitleBar()
        qtbot.addWidget(title_bar)
        
        # Add some tabs
        title_bar.add_tab("Tab 1")
        title_bar.add_tab("Tab 2")
        title_bar.add_tab("Tab 3")
        
        # Find tab container
        tab_container = None
        for child in title_bar.children():
            if isinstance(child, QWidget) and hasattr(child, 'layout'):
                layout = child.layout()
                if layout:
                    # Check if this container has both tab bar and + button
                    has_tab_bar = False
                    has_new_btn = False
                    for i in range(layout.count()):
                        item = layout.itemAt(i)
                        if item:
                            widget = item.widget()
                            if widget == title_bar.tab_bar:
                                has_tab_bar = True
                            elif widget == title_bar.new_tab_btn:
                                has_new_btn = True
                    
                    if has_tab_bar and has_new_btn:
                        tab_container = child
                        break
        
        assert tab_container is not None, "Tab container with both tab bar and + button not found"
        
        # Verify they're in the same container layout
        container_layout = tab_container.layout()
        assert container_layout is not None
        
        # Verify + button is right after tab bar in layout
        tab_bar_index = -1
        new_btn_index = -1
        
        for i in range(container_layout.count()):
            item = container_layout.itemAt(i)
            if item:
                widget = item.widget()
                if widget == title_bar.tab_bar:
                    tab_bar_index = i
                elif widget == title_bar.new_tab_btn:
                    new_btn_index = i
        
        assert tab_bar_index >= 0, "Tab bar not found in container layout"
        assert new_btn_index >= 0, "+ button not found in container layout"
        assert new_btn_index == tab_bar_index + 1, \
            f"+ button should be right after tab bar, but indices are {tab_bar_index} and {new_btn_index}"
    
    def test_layout_structure(self, qtbot):
        """Test overall layout structure of Chrome title bar."""
        from ui.widgets.chrome_title_bar import ChromeTitleBar
        
        title_bar = ChromeTitleBar()
        qtbot.addWidget(title_bar)
        
        main_layout = title_bar.layout()
        assert isinstance(main_layout, QHBoxLayout), "Main layout should be horizontal"
        
        # Expected structure (in order):
        # 1. Left spacer (8px)
        # 2. Tab container (with tab bar and + button)
        # 3. Draggable spacer (expanding)
        # 4. Window controls
        
        assert main_layout.count() >= 4, f"Expected at least 4 items in layout, got {main_layout.count()}"
        
        # Check each component
        components = []
        for i in range(main_layout.count()):
            item = main_layout.itemAt(i)
            if item:
                widget = item.widget()
                if widget:
                    components.append({
                        'widget': widget,
                        'class': widget.__class__.__name__,
                        'object_name': widget.objectName() or '',
                        'size_policy': widget.sizePolicy()
                    })
        
        # Verify we have the expected components
        assert len(components) >= 4, f"Expected at least 4 components, got {len(components)}"
        
        # Component 0: Left spacer
        assert components[0]['widget'].width() == 8 or components[0]['widget'].fixedWidth() == 8, \
            "First component should be 8px spacer"
        
        # Component 1: Tab container (Maximum policy)
        assert components[1]['size_policy'].horizontalPolicy() == QSizePolicy.Maximum, \
            "Second component should be tab container with Maximum policy"
        
        # Component 2: Draggable spacer (Expanding policy)
        assert components[2]['object_name'] == 'dragSpacer', \
            "Third component should be drag spacer"
        assert components[2]['size_policy'].horizontalPolicy() == QSizePolicy.Expanding, \
            "Drag spacer should have Expanding policy"
        
        # Component 3: Window controls
        assert components[3]['class'] == 'WindowControls', \
            "Fourth component should be window controls"
    
    def test_dynamic_width_with_tabs(self, qtbot):
        """Test that tab container width adjusts with number of tabs."""
        from ui.widgets.chrome_title_bar import ChromeTitleBar
        
        title_bar = ChromeTitleBar()
        qtbot.addWidget(title_bar)
        title_bar.resize(1000, 35)  # Give it a reasonable width
        
        # Measure with 1 tab
        title_bar.add_tab("Tab 1")
        qtbot.wait(10)  # Let layout update
        
        # Find tab container
        tab_container = None
        for child in title_bar.children():
            if isinstance(child, QWidget) and hasattr(child, 'layout'):
                layout = child.layout()
                if layout and layout.count() >= 2:
                    for i in range(layout.count()):
                        item = layout.itemAt(i)
                        if item and item.widget() == title_bar.tab_bar:
                            tab_container = child
                            break
        
        assert tab_container is not None
        
        width_1_tab = tab_container.width()
        
        # Add more tabs
        title_bar.add_tab("Tab 2")
        title_bar.add_tab("Tab 3")
        qtbot.wait(10)  # Let layout update
        
        width_3_tabs = tab_container.width()
        
        # Container should be wider with more tabs (but not full width)
        assert width_3_tabs > width_1_tab, \
            f"Container should grow with more tabs: {width_1_tab} -> {width_3_tabs}"
        
        # But should not take full title bar width (leaving space for dragging)
        assert width_3_tabs < title_bar.width() - 200, \
            f"Container should not take full width: {width_3_tabs} vs {title_bar.width()}"