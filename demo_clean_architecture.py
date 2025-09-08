#!/usr/bin/env python3
"""Clean demo of the tab and pane architecture."""

import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtCore import Qt
from ui.workspace_new import Workspace


class CleanDemoWindow(QMainWindow):
    """Clean demo window showing the architecture clearly."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Clean Architecture Demo - Tabs at Root, Panes Inside")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create workspace directly as central widget
        self.workspace = Workspace()
        self.setCentralWidget(self.workspace)
        
        # Set up the demo layout
        self.setup_demo()
        
        # Apply clean styling
        self.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #3c3c3c;
                background: #1e1e1e;
            }
            QTabBar::tab {
                background: #2d2d30;
                color: #cccccc;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #007acc;
                color: white;
            }
            QSplitter::handle {
                background: #3c3c3c;
            }
            QSplitter::handle:horizontal {
                width: 2px;
            }
            QSplitter::handle:vertical {
                height: 2px;
            }
        """)
    
    def setup_demo(self):
        """Set up a demo layout."""
        # First tab is already created (Welcome)
        workspace = self.workspace.get_current_tab_workspace()
        if workspace:
            # Set initial widget to editor
            active_pane = workspace.get_active_pane_id()
            if active_pane:
                workspace.set_pane_widget(active_pane, "editor")
            
            # Split horizontally and add terminal
            new_pane = workspace.split_horizontal()
            if new_pane:
                workspace.set_pane_widget(new_pane, "terminal")
        
        # Add a second tab for database work
        self.workspace.add_new_tab("Database")
        db_workspace = self.workspace.get_current_tab_workspace()
        if db_workspace:
            # Set SQL editor in main pane
            active_pane = db_workspace.get_active_pane_id()
            if active_pane:
                db_workspace.set_pane_widget(active_pane, "editor")
            
            # Split vertically for results
            new_pane = db_workspace.split_vertical()
            if new_pane:
                db_workspace.set_pane_widget(new_pane, "output")
        
        # Add a third tab for debugging
        self.workspace.add_new_tab("Debug")
        debug_workspace = self.workspace.get_current_tab_workspace()
        if debug_workspace:
            # Complex layout: editor on left, variables/output on right
            active_pane = debug_workspace.get_active_pane_id()
            if active_pane:
                debug_workspace.set_pane_widget(active_pane, "editor")
            
            # Split right for variables
            right_pane = debug_workspace.split_horizontal()
            if right_pane:
                debug_workspace.set_pane_widget(right_pane, "variables")
                
                # Split variables pane down for call stack
                bottom_pane = debug_workspace.split_vertical(right_pane)
                if bottom_pane:
                    debug_workspace.set_pane_widget(bottom_pane, "callstack")
        
        # Switch back to first tab
        self.workspace.tab_widget.setCurrentIndex(0)
    
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts."""
        workspace = self.workspace.get_current_tab_workspace()
        if not workspace:
            return
        
        if event.modifiers() == Qt.ControlModifier:
            if event.key() == Qt.Key_Backslash:
                # Split horizontal
                active = workspace.get_active_pane_id()
                if active:
                    new_pane = workspace.split_horizontal(active)
                    if new_pane:
                        print(f"Split horizontal: created {new_pane}")
            elif event.key() == Qt.Key_Minus:
                # Split vertical
                active = workspace.get_active_pane_id()
                if active:
                    new_pane = workspace.split_vertical(active)
                    if new_pane:
                        print(f"Split vertical: created {new_pane}")
            elif event.key() == Qt.Key_W:
                # Close pane
                active = workspace.get_active_pane_id()
                if active:
                    if workspace.close_pane(active):
                        print(f"Closed pane: {active}")
                    else:
                        print("Cannot close last pane")
        
        super().keyPressEvent(event)


def main():
    """Run the clean demo."""
    app = QApplication(sys.argv)
    
    # Set dark fusion style
    app.setStyle("Fusion")
    from PySide6.QtGui import QPalette, QColor
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(30, 30, 30))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(45, 45, 45))
    palette.setColor(QPalette.AlternateBase, QColor(60, 60, 60))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(45, 45, 45))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(palette)
    
    window = CleanDemoWindow()
    window.show()
    
    print("\n" + "="*60)
    print("CLEAN ARCHITECTURE DEMO")
    print("="*60)
    print("\nStructure:")
    print("  - ROOT LEVEL: Tab bar with [Welcome] [Database] [Debug] tabs")
    print("  - INSIDE TABS: Content panes (NO nested tabs)")
    print("  - Each pane shows its widget directly (Editor, Terminal, etc.)")
    print("\nKeyboard Shortcuts:")
    print("  Ctrl+\\  : Split current pane horizontally")
    print("  Ctrl+-  : Split current pane vertically")
    print("  Ctrl+W  : Close current pane")
    print("\nMouse Actions:")
    print("  - Right-click any pane for context menu")
    print("  - Click '+' button to add new tabs")
    print("  - Click 'X' on tabs to close them")
    print("\n" + "="*60 + "\n")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()