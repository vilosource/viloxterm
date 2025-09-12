#!/usr/bin/env python3
"""
GUI tests for Chrome mode functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtCore import Qt, QSettings, QPoint, QTimer
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtTest import QTest
import time

from tests.gui.base import GUITestBase
from ui.widgets.window_controls import WindowControls
from ui.widgets.chrome_title_bar import ChromeTitleBar
from ui.chrome_main_window import ChromeMainWindow


class TestChromeModeGUI(GUITestBase):
    """GUI tests for Chrome mode functionality."""
    
    @pytest.fixture
    def chrome_window(self, qtbot):
        """Create a Chrome main window for testing."""
        # Mock settings to enable Chrome mode
        with patch('ui.chrome_main_window.QSettings') as mock_settings:
            mock_instance = Mock()
            mock_instance.value.return_value = True  # Chrome mode enabled
            mock_settings.return_value = mock_instance
            
            # Create Chrome window
            window = ChromeMainWindow()
            qtbot.addWidget(window)
            window.show()
            qtbot.waitForWindowShown(window)
            
            yield window
            
            # Cleanup
            window.close()
    
    def test_chrome_title_bar_visible(self, chrome_window, qtbot):
        """Test that Chrome title bar is visible when Chrome mode is enabled."""
        # Check that Chrome title bar exists
        assert hasattr(chrome_window, 'chrome_title_bar')
        assert chrome_window.chrome_title_bar.isVisible()
        
        # Check that it has the correct height
        assert chrome_window.chrome_title_bar.height() == 35
    
    def test_window_controls_functional(self, chrome_window, qtbot):
        """Test that window control buttons are functional."""
        title_bar = chrome_window.chrome_title_bar
        
        # Test minimize
        assert chrome_window.isVisible()
        title_bar.window_controls.minimize_btn.click()
        qtbot.wait(100)  # Give it time to minimize
        assert chrome_window.isMinimized()
        
        # Restore for further testing
        chrome_window.showNormal()
        qtbot.waitForWindowShown(chrome_window)
        
        # Test maximize
        assert not chrome_window.isMaximized()
        title_bar.window_controls.maximize_btn.click()
        qtbot.wait(100)
        assert chrome_window.isMaximized()
        
        # Test restore
        title_bar.window_controls.maximize_btn.click()
        qtbot.wait(100)
        assert not chrome_window.isMaximized()
    
    def test_tab_operations_in_title_bar(self, chrome_window, qtbot):
        """Test tab operations in the Chrome title bar."""
        title_bar = chrome_window.chrome_title_bar
        
        # Initially should have at least one tab
        initial_count = title_bar.tab_count()
        assert initial_count >= 1
        
        # Add a new tab via button click
        title_bar.new_tab_btn.click()
        qtbot.wait(100)
        
        # Should have one more tab
        assert title_bar.tab_count() == initial_count + 1
        
        # Switch between tabs
        if title_bar.tab_count() > 1:
            title_bar.set_current_tab(0)
            assert title_bar.current_tab() == 0
            
            title_bar.set_current_tab(1)
            assert title_bar.current_tab() == 1
    
    def test_window_dragging(self, chrome_window, qtbot):
        """Test window dragging via title bar."""
        if chrome_window.isMaximized():
            chrome_window.showNormal()
            qtbot.wait(100)
        
        title_bar = chrome_window.chrome_title_bar
        initial_pos = chrome_window.pos()
        
        # Simulate drag on title bar
        drag_start = QPoint(100, 15)  # Middle of title bar
        drag_end = QPoint(150, 25)
        
        # Start drag
        QTest.mousePress(title_bar, Qt.LeftButton, Qt.NoModifier, drag_start)
        
        # Move mouse
        QTest.mouseMove(title_bar, drag_end)
        
        # Release
        QTest.mouseRelease(title_bar, Qt.LeftButton, Qt.NoModifier, drag_end)
        
        qtbot.wait(100)
        
        # Window should have moved (approximately)
        final_pos = chrome_window.pos()
        # The window should have moved roughly by the drag delta
        # (exact movement depends on window manager)
        assert final_pos != initial_pos
    
    def test_window_resizing(self, chrome_window, qtbot):
        """Test window resizing from edges."""
        if chrome_window.isMaximized():
            chrome_window.showNormal()
            qtbot.wait(100)
        
        initial_size = chrome_window.size()
        
        # Test resize from right edge
        right_edge = QPoint(chrome_window.width() - 5, chrome_window.height() // 2)
        
        # Start resize
        QTest.mousePress(chrome_window, Qt.LeftButton, Qt.NoModifier, right_edge)
        
        # Drag to resize
        new_pos = QPoint(chrome_window.width() + 50, chrome_window.height() // 2)
        QTest.mouseMove(chrome_window, new_pos)
        
        # Release
        QTest.mouseRelease(chrome_window, Qt.LeftButton, Qt.NoModifier, new_pos)
        
        qtbot.wait(100)
        
        # Window should be wider
        final_size = chrome_window.size()
        assert final_size.width() > initial_size.width()
    
    def test_double_click_maximize(self, chrome_window, qtbot):
        """Test double-click on title bar to maximize/restore."""
        if chrome_window.isMaximized():
            chrome_window.showNormal()
            qtbot.wait(100)
        
        title_bar = chrome_window.chrome_title_bar
        
        # Double-click on empty area of title bar
        empty_pos = QPoint(200, 15)  # Should be empty space
        
        # First double-click should maximize
        QTest.mouseDClick(title_bar, Qt.LeftButton, Qt.NoModifier, empty_pos)
        qtbot.wait(100)
        assert chrome_window.isMaximized()
        
        # Second double-click should restore
        QTest.mouseDClick(title_bar, Qt.LeftButton, Qt.NoModifier, empty_pos)
        qtbot.wait(100)
        assert not chrome_window.isMaximized()
    
    def test_frameless_window_property(self, chrome_window):
        """Test that window has frameless property when Chrome mode is enabled."""
        flags = chrome_window.windowFlags()
        assert flags & Qt.FramelessWindowHint
    
    def test_menu_bar_hidden_in_chrome_mode(self, chrome_window):
        """Test that menu bar is hidden in Chrome mode."""
        # In Chrome mode, the menu bar should be hidden by default
        assert chrome_window.menuBar() is not None
        assert not chrome_window.menuBar().isVisible()
    
    def test_state_persistence(self, chrome_window, qtbot, tmp_path):
        """Test that Chrome mode state is persisted."""
        # Mock QSettings to use temp path
        with patch('ui.chrome_main_window.QSettings') as mock_settings:
            mock_instance = Mock()
            mock_settings.return_value = mock_instance
            
            # Save state
            chrome_window.save_state()
            
            # Check that Chrome mode setting was saved
            mock_instance.setValue.assert_any_call("UI/ChromeMode", True)
    
    def test_tab_close_functionality(self, chrome_window, qtbot):
        """Test closing tabs via close button."""
        title_bar = chrome_window.chrome_title_bar
        
        # Add multiple tabs
        title_bar.add_tab("Tab 1")
        title_bar.add_tab("Tab 2")
        title_bar.add_tab("Tab 3")
        
        initial_count = title_bar.tab_count()
        assert initial_count >= 3
        
        # Close a tab (simulate close button click)
        if title_bar.tab_bar.tabsClosable():
            # Emit the signal directly since we can't easily click the close button
            title_bar.tab_bar.tabCloseRequested.emit(1)
            qtbot.wait(100)
            
            # Should have one less tab
            assert title_bar.tab_count() == initial_count - 1


class TestChromeModeFallback(GUITestBase):
    """Test fallback to traditional mode when Chrome mode is disabled."""
    
    def test_traditional_mode_when_disabled(self, qtbot):
        """Test that traditional window is created when Chrome mode is disabled."""
        # Mock settings to disable Chrome mode
        with patch('main.QSettings') as mock_settings:
            mock_instance = Mock()
            mock_instance.value.return_value = False  # Chrome mode disabled
            mock_settings.return_value = mock_instance
            
            # Import and create main window
            from ui.main_window import MainWindow
            
            window = MainWindow()
            qtbot.addWidget(window)
            window.show()
            qtbot.waitForWindowShown(window)
            
            # Should not have Chrome title bar
            assert not hasattr(window, 'chrome_title_bar')
            
            # Should have normal window decorations (not frameless)
            flags = window.windowFlags()
            assert not (flags & Qt.FramelessWindowHint)
            
            # Menu bar should be visible
            assert window.menuBar().isVisible()
            
            window.close()


class TestChromeUICommands(GUITestBase):
    """Test Chrome mode UI commands."""
    
    def test_toggle_chrome_mode_command(self, main_window, qtbot):
        """Test the toggle Chrome mode command."""
        from core.commands.builtin.ui_commands import toggle_chrome_mode
        from core.commands.base import CommandContext
        
        # Create command context
        context = CommandContext(
            main_window=main_window,
            workspace=main_window.workspace,
            active_widget=None
        )
        
        # Mock QSettings and QMessageBox
        with patch('core.commands.builtin.ui_commands.QSettings') as mock_settings:
            with patch('core.commands.builtin.ui_commands.QMessageBox') as mock_msgbox:
                mock_instance = Mock()
                mock_instance.value.return_value = False  # Currently disabled
                mock_settings.return_value = mock_instance
                
                # User chooses not to restart
                mock_msgbox.information.return_value = mock_msgbox.No
                
                # Execute command
                result = toggle_chrome_mode(context)
                
                # Check that it succeeded
                assert result.success
                assert "enabled" in result.message
                
                # Check that setting was toggled
                mock_instance.setValue.assert_called_with("UI/ChromeMode", True)
    
    def test_chrome_mode_menu_item(self, main_window, qtbot):
        """Test that Chrome mode menu item exists and is functional."""
        # Find the View menu
        view_menu = None
        for action in main_window.menuBar().actions():
            if action.text() == "View":
                view_menu = action.menu()
                break
        
        assert view_menu is not None
        
        # Find Chrome mode action
        chrome_action = None
        for action in view_menu.actions():
            if "Chrome" in action.text():
                chrome_action = action
                break
        
        assert chrome_action is not None
        assert chrome_action.isCheckable()
        
        # Check that it reflects current state
        settings = QSettings()
        current_state = settings.value("UI/ChromeMode", False, type=bool)
        assert chrome_action.isChecked() == current_state


if __name__ == '__main__':
    pytest.main([__file__, '-v'])