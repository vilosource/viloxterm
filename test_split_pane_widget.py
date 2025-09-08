#!/usr/bin/env python3
"""
Test application demonstrating SplitPaneWidget integrated with tabs.
Shows how each tab can have its own independent split layout.
"""

import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QPushButton,
    QVBoxLayout, QWidget, QToolBar, QStatusBar
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction

from ui.widgets.split_pane_widget import SplitPaneWidget
from ui.widgets.widget_registry import WidgetType


class TestMainWindow(QMainWindow):
    """Main window with tabs containing split pane widgets."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Split Pane Widget Test - Tabs with Independent Layouts")
        self.setGeometry(100, 100, 1400, 900)
        
        # Apply dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QTabWidget::pane {
                border: 1px solid #3c3c3c;
                background-color: #1e1e1e;
            }
            QTabBar::tab {
                background-color: #2d2d30;
                color: #cccccc;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #1e1e1e;
                border-bottom: 2px solid #007ACC;
            }
            QTabBar::tab:hover {
                background-color: #3c3c3c;
            }
            QToolBar {
                background-color: #2d2d30;
                border: none;
                spacing: 5px;
                padding: 5px;
            }
            QToolBar QToolButton {
                background-color: #3c3c3c;
                color: #cccccc;
                border: 1px solid #555555;
                padding: 5px;
                margin: 2px;
                min-width: 80px;
            }
            QToolBar QToolButton:hover {
                background-color: #484848;
                border: 1px solid #007ACC;
            }
            QToolBar QToolButton:pressed {
                background-color: #007ACC;
            }
            QStatusBar {
                background-color: #007ACC;
                color: white;
            }
        """)
        
        self.setup_statusbar()
        self.setup_toolbar()
        self.setup_ui()
    
    def setup_ui(self):
        """Initialize the UI."""
        # Create tab widget as central widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        
        self.setCentralWidget(self.tab_widget)
        
        # Create initial tabs with different layouts
        self.create_editor_tab()
        self.create_terminal_tab()
        self.create_debug_tab()
    
    def setup_toolbar(self):
        """Setup toolbar with actions."""
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)
        
        # Add new tab action
        new_tab_action = QAction("New Tab", self)
        new_tab_action.setShortcut("Ctrl+T")
        new_tab_action.triggered.connect(self.create_editor_tab)
        toolbar.addAction(new_tab_action)
        
        toolbar.addSeparator()
        
        # Split actions for current tab
        split_h_action = QAction("Split Horizontal", self)
        split_h_action.setShortcut("Ctrl+Shift+H")
        split_h_action.triggered.connect(self.split_current_horizontal)
        toolbar.addAction(split_h_action)
        
        split_v_action = QAction("Split Vertical", self)
        split_v_action.setShortcut("Ctrl+Shift+V")
        split_v_action.triggered.connect(self.split_current_vertical)
        toolbar.addAction(split_v_action)
        
        toolbar.addSeparator()
        
        # Info action
        info_action = QAction("Tab Info", self)
        info_action.triggered.connect(self.show_current_tab_info)
        toolbar.addAction(info_action)
    
    def setup_statusbar(self):
        """Setup status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
    
    def create_editor_tab(self):
        """Create a new editor tab with split pane widget."""
        split_widget = SplitPaneWidget(initial_widget_type=WidgetType.TEXT_EDITOR)
        
        # Connect signals
        split_widget.pane_added.connect(lambda pid: self.update_status())
        split_widget.pane_removed.connect(lambda pid: self.update_status())
        split_widget.active_pane_changed.connect(lambda pid: self.on_active_pane_changed(pid))
        
        tab_index = self.tab_widget.addTab(split_widget, "Editor")
        self.tab_widget.setCurrentIndex(tab_index)
        
        self.update_status()
        return split_widget
    
    def create_terminal_tab(self):
        """Create a terminal tab with split pane widget."""
        split_widget = SplitPaneWidget(initial_widget_type=WidgetType.TERMINAL)
        
        # Connect signals
        split_widget.pane_added.connect(lambda pid: self.update_status())
        split_widget.pane_removed.connect(lambda pid: self.update_status())
        
        # Pre-split the terminal tab to show multiple terminals
        first_pane_id = split_widget.get_all_pane_ids()[0]
        split_widget.split_horizontal(first_pane_id)
        
        tab_index = self.tab_widget.addTab(split_widget, "Terminal")
        
        self.update_status()
        return split_widget
    
    def create_debug_tab(self):
        """Create a debug tab with mixed widget types."""
        split_widget = SplitPaneWidget(initial_widget_type=WidgetType.DEBUGGER)
        
        # Connect signals
        split_widget.pane_added.connect(lambda pid: self.update_status())
        split_widget.pane_removed.connect(lambda pid: self.update_status())
        
        # Create a complex layout: debugger on left, output on top-right, terminal on bottom-right
        first_pane_id = split_widget.get_all_pane_ids()[0]
        split_widget.split_horizontal(first_pane_id)  # Split horizontally first
        
        # Get the new pane and split it vertically
        all_panes = split_widget.get_all_pane_ids()
        right_pane_id = [p for p in all_panes if p != first_pane_id][0]
        split_widget.split_vertical(right_pane_id)
        
        # Change widget types for the panes
        all_panes = split_widget.get_all_pane_ids()
        if len(all_panes) >= 3:
            # Keep first as debugger
            # Make second one output
            if right_pane_id in split_widget.widgets:
                widget = split_widget.widgets[right_pane_id]
                if hasattr(widget, 'change_widget_type'):
                    widget.change_widget_type(WidgetType.OUTPUT)
            
            # Make third one terminal
            third_pane = [p for p in all_panes if p != first_pane_id and p != right_pane_id][0]
            if third_pane in split_widget.widgets:
                widget = split_widget.widgets[third_pane]
                if hasattr(widget, 'change_widget_type'):
                    widget.change_widget_type(WidgetType.TERMINAL)
        
        tab_index = self.tab_widget.addTab(split_widget, "Debug")
        
        self.update_status()
        return split_widget
    
    def close_tab(self, index):
        """Close a tab."""
        if self.tab_widget.count() > 1:
            self.tab_widget.removeTab(index)
            self.update_status()
    
    def split_current_horizontal(self):
        """Split the active pane in the current tab horizontally."""
        current_widget = self.tab_widget.currentWidget()
        if isinstance(current_widget, SplitPaneWidget):
            active_pane = current_widget.active_pane_id
            if active_pane:
                current_widget.split_horizontal(active_pane)
    
    def split_current_vertical(self):
        """Split the active pane in the current tab vertically."""
        current_widget = self.tab_widget.currentWidget()
        if isinstance(current_widget, SplitPaneWidget):
            active_pane = current_widget.active_pane_id
            if active_pane:
                current_widget.split_vertical(active_pane)
    
    def show_current_tab_info(self):
        """Show information about the current tab."""
        current_widget = self.tab_widget.currentWidget()
        if isinstance(current_widget, SplitPaneWidget):
            pane_count = current_widget.get_pane_count()
            active_pane = current_widget.active_pane_id
            all_panes = current_widget.get_all_pane_ids()
            
            info = f"Panes: {pane_count}, Active: {active_pane}, All: {all_panes}"
            self.status_bar.showMessage(info, 5000)
    
    def on_active_pane_changed(self, pane_id):
        """Handle active pane change."""
        current_widget = self.tab_widget.currentWidget()
        if isinstance(current_widget, SplitPaneWidget):
            pane_count = current_widget.get_pane_count()
            tab_name = self.tab_widget.tabText(self.tab_widget.currentIndex())
            self.status_bar.showMessage(f"{tab_name} - Active: {pane_id} ({pane_count} panes)")
    
    def update_status(self):
        """Update status bar."""
        current_widget = self.tab_widget.currentWidget()
        if isinstance(current_widget, SplitPaneWidget):
            pane_count = current_widget.get_pane_count()
            tab_name = self.tab_widget.tabText(self.tab_widget.currentIndex())
            self.status_bar.showMessage(f"{tab_name} - {pane_count} pane(s)")
        else:
            self.status_bar.showMessage("Ready")


def main():
    """Run the test application."""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = TestMainWindow()
    window.show()
    
    print("=" * 70)
    print("SPLIT PANE WIDGET TEST APPLICATION")
    print("=" * 70)
    print("\n📋 FEATURES:")
    print("  • Each tab has its own independent split layout")
    print("  • Header bar at top of each pane with split/close controls")
    print("  • Native context menus preserved for text editors")
    print("  • Click on any pane to make it active (blue header)")
    print("  • Drag splitters to resize panes")
    
    print("\n🎯 TABS:")
    print("  • Editor tab    - For editing code")
    print("  • Terminal tab  - Pre-split with two terminals")
    print("  • Debug tab     - Complex layout (debugger, output, terminal)")
    
    print("\n⌨️  KEYBOARD SHORTCUTS:")
    print("  • Ctrl+T         - New editor tab")
    print("  • Ctrl+Shift+H   - Split active pane horizontally")
    print("  • Ctrl+Shift+V   - Split active pane vertically")
    
    print("\n🎮 HEADER BAR CONTROLS (visible on each pane):")
    print("  • [≡] Type menu     - Change widget type")  
    print("  • [↔] Split H       - New pane on the right")
    print("  • [↕] Split V       - New pane below")
    print("  • [×] Close         - Remove pane (promotes sibling)")
    
    print("\n🖱️  CONTEXT MENUS:")
    print("  • Text editors keep their native copy/paste menu")
    print("  • Other widgets show split/close options on right-click")
    
    print("\n💡 TIP: The status bar shows the active pane ID and total pane count")
    print("=" * 70)
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()