#!/usr/bin/env python3
"""
Unit tests for Chrome mode tab synchronization.
Tests that tabs stay synchronized between Chrome title bar and workspace.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest

from ui.chrome_main_window import ChromeMainWindow
from ui.widgets.chrome_title_bar_fixed import ChromeTitleBarFixed


class TestChromeTabSynchronization:
    """Test tab synchronization between Chrome title bar and workspace."""
    
    @pytest.fixture
    def chrome_window_mock(self):
        """Create a mocked Chrome window for testing."""
        with patch('ui.main_window.MainWindow.__init__', return_value=None):
            window = ChromeMainWindow()
            
            # Set up Chrome mode
            window.chrome_mode_enabled = True
            
            # Mock workspace
            window.workspace = Mock()
            window.workspace.tab_widget = Mock()
            window.workspace.tab_widget.count.return_value = 3
            window.workspace.tab_widget.currentIndex.return_value = 0
            window.workspace.tab_widget.tabText.side_effect = lambda i: f"Tab {i+1}"
            window.workspace.tab_widget.setCurrentIndex = Mock()
            window.workspace.tab_widget.currentChanged = Mock()
            window.workspace.tab_widget.currentChanged.connect = Mock()
            
            # Mock Chrome title bar
            window.chrome_title_bar = Mock(spec=ChromeTitleBarFixed)
            window.chrome_title_bar.add_tab = Mock()
            window.chrome_title_bar.set_current_tab = Mock()
            window.chrome_title_bar.remove_tab = Mock()
            window.chrome_title_bar.current_tab = Mock(return_value=0)
            window.chrome_title_bar.tab_text = Mock(side_effect=lambda i: f"Tab {i+1}")
            window.chrome_title_bar.tab_count = Mock(return_value=3)
            
            return window
    
    def test_workspace_tab_change_updates_chrome(self, chrome_window_mock):
        """Test that changing workspace tab updates Chrome title bar."""
        window = chrome_window_mock
        
        # Simulate the connection that should be made in _transfer_tabs_to_chrome
        callback = None
        def capture_callback(cb):
            nonlocal callback
            callback = cb
        window.workspace.tab_widget.currentChanged.connect = capture_callback
        
        # Call the method that sets up the connection
        window._transfer_tabs_to_chrome()
        
        # Verify connection was made
        assert callback is not None, "Tab sync connection should be established"
        
        # Simulate workspace tab change
        callback(2)  # Change to tab index 2
        
        # Verify Chrome title bar was updated
        window.chrome_title_bar.set_current_tab.assert_called_with(2)
    
    def test_chrome_tab_change_updates_workspace(self, chrome_window_mock):
        """Test that clicking Chrome tab updates workspace."""
        window = chrome_window_mock
        
        # Simulate Chrome tab click (handled by on_chrome_tab_changed)
        window.on_chrome_tab_changed(1)
        
        # Verify workspace was updated
        window.workspace.tab_widget.setCurrentIndex.assert_called_with(1)
    
    def test_initial_tab_sync(self, chrome_window_mock):
        """Test that tabs are initially synchronized when Chrome mode is applied."""
        window = chrome_window_mock
        
        # Set up initial workspace state
        window.workspace.tab_widget.count.return_value = 3
        window.workspace.tab_widget.currentIndex.return_value = 1
        
        # Call transfer method
        window._transfer_tabs_to_chrome()
        
        # Verify all tabs were added to Chrome
        assert window.chrome_title_bar.add_tab.call_count == 3
        window.chrome_title_bar.add_tab.assert_any_call("Tab 1")
        window.chrome_title_bar.add_tab.assert_any_call("Tab 2")
        window.chrome_title_bar.add_tab.assert_any_call("Tab 3")
        
        # Verify current tab was set
        window.chrome_title_bar.set_current_tab.assert_called_with(1)
    
    def test_tab_close_synchronization(self, chrome_window_mock):
        """Test that closing a tab keeps both widgets synchronized."""
        window = chrome_window_mock
        
        # Set up multiple tabs
        window.workspace.tab_widget.count.return_value = 3
        
        # Simulate Chrome tab close request
        window.on_chrome_tab_close(1)
        
        # Verify workspace tab was closed
        window.workspace.close_tab.assert_called_with(1)
        
        # Verify Chrome tab was removed
        window.chrome_title_bar.remove_tab.assert_called_with(1)
    
    def test_new_tab_synchronization(self, chrome_window_mock):
        """Test that adding a new tab keeps both widgets synchronized."""
        window = chrome_window_mock
        
        # Mock workspace add_editor_tab to return new index
        window.workspace.add_editor_tab = Mock(return_value=3)
        
        # Simulate new tab request
        window.add_new_tab()
        
        # Verify workspace tab was added
        window.workspace.add_editor_tab.assert_called_with("New Tab")
        
        # Verify Chrome tab was added
        window.chrome_title_bar.add_tab.assert_called_with("New Tab")
        window.chrome_title_bar.set_current_tab.assert_called_with(3)
    
    def test_tab_sync_with_keyboard_shortcuts(self, chrome_window_mock):
        """Test that keyboard shortcuts maintain tab synchronization."""
        window = chrome_window_mock
        
        # Set up the sync connection
        callback = None
        def capture_callback(cb):
            nonlocal callback
            callback = cb
        window.workspace.tab_widget.currentChanged.connect = capture_callback
        window._transfer_tabs_to_chrome()
        
        # Simulate keyboard shortcut changing workspace tab (e.g., Ctrl+PgDown)
        # This would trigger currentChanged signal
        callback(1)
        window.chrome_title_bar.set_current_tab.assert_called_with(1)
        
        # Simulate another keyboard shortcut (e.g., Ctrl+PgUp)
        callback(0)
        window.chrome_title_bar.set_current_tab.assert_called_with(0)
    
    def test_no_close_last_tab(self, chrome_window_mock):
        """Test that the last tab cannot be closed."""
        window = chrome_window_mock
        
        # Set up only one tab
        window.workspace.tab_widget.count.return_value = 1
        
        # Try to close the last tab
        window.on_chrome_tab_close(0)
        
        # Verify tab was NOT closed
        assert not window.workspace.close_tab.called
        assert not window.chrome_title_bar.remove_tab.called


class TestChromeTabSyncIntegration:
    """Integration tests for Chrome tab synchronization with commands."""
    
    def test_next_tab_command_updates_chrome(self):
        """Test that workbench.action.nextTab command updates Chrome tabs."""
        # This would test integration with the command system
        # Currently marked as a placeholder for when we refactor to use commands
        pytest.skip("Command integration not yet implemented")
    
    def test_previous_tab_command_updates_chrome(self):
        """Test that workbench.action.previousTab command updates Chrome tabs."""
        pytest.skip("Command integration not yet implemented")
    
    def test_close_tab_command_updates_chrome(self):
        """Test that file.closeTab command updates Chrome tabs."""
        pytest.skip("Command integration not yet implemented")