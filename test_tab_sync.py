#!/usr/bin/env python3
"""
Test script to verify Chrome tab synchronization with keyboard shortcuts.
"""

import sys
import time
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSettings, QTimer, Qt
from PySide6.QtGui import QKeyEvent
from ui.chrome_main_window import ChromeMainWindow
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = QApplication(sys.argv)

# Enable Chrome mode - must be done after QApplication is created
settings = QSettings("ViloApp", "ViloApp")
settings.setValue("UI/ChromeMode", True)

# Create Chrome window
window = ChromeMainWindow()
window.setWindowTitle("Tab Sync Test")
window.resize(900, 600)
window.show()

# Add some tabs for testing
if hasattr(window, 'workspace'):
    window.workspace.add_editor_tab("Tab 2")
    window.workspace.add_editor_tab("Tab 3")
    window.workspace.tab_widget.setCurrentIndex(0)  # Start at first tab

def log_tab_states():
    """Log the current state of both tab widgets."""
    if not hasattr(window, 'chrome_title_bar'):
        logger.warning("Chrome mode not active - chrome_title_bar not found")
        return
        
    if hasattr(window, 'workspace') and hasattr(window, 'chrome_title_bar'):
        workspace_index = window.workspace.tab_widget.currentIndex()
        workspace_tab = window.workspace.tab_widget.tabText(workspace_index) if workspace_index >= 0 else "None"
        
        chrome_index = window.chrome_title_bar.current_tab()
        chrome_tab = window.chrome_title_bar.tab_text(chrome_index) if chrome_index >= 0 else "None"
        
        logger.info(f"Workspace: Tab {workspace_index} '{workspace_tab}' | Chrome: Tab {chrome_index} '{chrome_tab}'")
        
        if workspace_index != chrome_index:
            logger.error("❌ TABS NOT SYNCHRONIZED!")
        else:
            logger.info("✅ Tabs synchronized")

def simulate_tab_navigation():
    """Simulate keyboard shortcuts for tab navigation."""
    logger.info("\n" + "="*60)
    logger.info("TESTING TAB SYNCHRONIZATION")
    logger.info("="*60)
    
    # Log initial state
    logger.info("\nInitial state:")
    log_tab_states()
    
    # Test Ctrl+PgDown (next tab)
    logger.info("\nPressing Ctrl+PgDown (next tab)...")
    event = QKeyEvent(QKeyEvent.KeyPress, Qt.Key_PageDown, Qt.ControlModifier)
    QApplication.sendEvent(window.workspace.tab_widget, event)
    QTimer.singleShot(100, log_tab_states)
    
    # Test Ctrl+PgDown again
    QTimer.singleShot(500, lambda: logger.info("\nPressing Ctrl+PgDown again..."))
    QTimer.singleShot(600, lambda: QApplication.sendEvent(window.workspace.tab_widget, 
                                                          QKeyEvent(QKeyEvent.KeyPress, Qt.Key_PageDown, Qt.ControlModifier)))
    QTimer.singleShot(700, log_tab_states)
    
    # Test Ctrl+PgUp (previous tab)
    QTimer.singleShot(1000, lambda: logger.info("\nPressing Ctrl+PgUp (previous tab)..."))
    QTimer.singleShot(1100, lambda: QApplication.sendEvent(window.workspace.tab_widget,
                                                           QKeyEvent(QKeyEvent.KeyPress, Qt.Key_PageUp, Qt.ControlModifier)))
    QTimer.singleShot(1200, log_tab_states)
    
    # Test clicking Chrome tab directly
    QTimer.singleShot(1500, lambda: logger.info("\nClicking Chrome tab 0..."))
    QTimer.singleShot(1600, lambda: window.chrome_title_bar.set_current_tab(0) if hasattr(window, 'chrome_title_bar') else None)
    QTimer.singleShot(1700, log_tab_states)
    
    # Final summary
    QTimer.singleShot(2000, lambda: logger.info("\n" + "="*60))
    QTimer.singleShot(2000, lambda: logger.info("TEST COMPLETE - Check logs above for sync status"))
    QTimer.singleShot(2000, lambda: logger.info("="*60 + "\n"))

# Start testing after window is shown
QTimer.singleShot(500, simulate_tab_navigation)

# Keep window open for manual testing
logger.info("\nWindow will stay open for manual testing.")
logger.info("Use Ctrl+PgUp/PgDown to navigate tabs.")
logger.info("Both workspace and Chrome tabs should stay in sync.\n")

sys.exit(app.exec())