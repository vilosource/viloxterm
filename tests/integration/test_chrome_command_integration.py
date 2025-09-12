#!/usr/bin/env python3
"""
Integration tests for Chrome mode with command pattern.
Tests that Chrome features properly integrate with the command system.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtCore import QSettings

from core.commands.base import CommandContext
from core.commands.executor import execute_command
# We'll execute commands through the command executor instead of directly
from services.ui_service import UIService
from services.workspace_service import WorkspaceService


class TestChromeCommandIntegration:
    """Test Chrome mode integration with command pattern."""
    
    @pytest.fixture
    def mock_context(self):
        """Create a mock command context with services."""
        context = Mock(spec=CommandContext)
        context.args = {}
        
        # Mock WorkspaceService
        workspace_service = Mock(spec=WorkspaceService)
        workspace_service.get_current_tab_index.return_value = 0
        workspace_service.get_tab_count.return_value = 3
        workspace_service.switch_to_tab.return_value = True
        
        # Mock UIService with Chrome support
        ui_service = Mock(spec=UIService)
        chrome_title_bar = Mock()
        chrome_title_bar.set_current_tab = Mock()
        chrome_title_bar.add_tab = Mock()
        chrome_title_bar.remove_tab = Mock()
        ui_service.get_chrome_title_bar.return_value = chrome_title_bar
        ui_service.is_chrome_mode_enabled.return_value = True
        
        # Setup service getter
        def get_service(service_class):
            if service_class == WorkspaceService:
                return workspace_service
            elif service_class == UIService:
                return ui_service
            return None
        
        context.get_service = get_service
        context.workspace_service = workspace_service
        context.ui_service = ui_service
        context.chrome_title_bar = chrome_title_bar
        
        return context
    
    def test_next_tab_command_updates_chrome(self, mock_context):
        """Test that next tab command updates Chrome title bar."""
        # Execute command
        result = next_tab_command(mock_context)
        
        # Verify command succeeded
        assert result.success
        assert result.value == {'tab_index': 1}
        
        # Verify workspace was updated
        mock_context.workspace_service.switch_to_tab.assert_called_with(1)
        
        # Verify Chrome title bar was updated
        mock_context.chrome_title_bar.set_current_tab.assert_called_with(1)
    
    def test_previous_tab_command_updates_chrome(self, mock_context):
        """Test that previous tab command updates Chrome title bar."""
        # Set current tab to 2
        mock_context.workspace_service.get_current_tab_index.return_value = 2
        
        # Execute command
        result = previous_tab_command(mock_context)
        
        # Verify command succeeded
        assert result.success
        assert result.value == {'tab_index': 1}
        
        # Verify workspace was updated
        mock_context.workspace_service.switch_to_tab.assert_called_with(1)
        
        # Verify Chrome title bar was updated
        mock_context.chrome_title_bar.set_current_tab.assert_called_with(1)
    
    def test_select_tab_command_updates_chrome(self, mock_context):
        """Test that select tab command updates Chrome title bar."""
        # Set target tab
        mock_context.args = {'tab_index': 2}
        
        # Execute command
        result = select_tab_command(mock_context)
        
        # Verify command succeeded
        assert result.success
        assert result.value == {'tab_index': 2}
        
        # Verify workspace was updated
        mock_context.workspace_service.switch_to_tab.assert_called_with(2)
        
        # Verify Chrome title bar was updated
        mock_context.chrome_title_bar.set_current_tab.assert_called_with(2)
    
    def test_commands_skip_chrome_when_disabled(self, mock_context):
        """Test that commands don't update Chrome when mode is disabled."""
        # Disable Chrome mode
        mock_context.ui_service.is_chrome_mode_enabled.return_value = False
        mock_context.ui_service.get_chrome_title_bar.return_value = None
        
        # Execute command
        result = next_tab_command(mock_context)
        
        # Verify command succeeded
        assert result.success
        
        # Verify workspace was updated
        mock_context.workspace_service.switch_to_tab.assert_called_with(1)
        
        # Verify Chrome title bar was NOT updated
        mock_context.chrome_title_bar.set_current_tab.assert_not_called()
    
    def test_command_with_invalid_tab_index(self, mock_context):
        """Test select tab command with invalid index."""
        # Set invalid tab index
        mock_context.args = {'tab_index': 10}  # Out of range
        
        # Execute command
        result = select_tab_command(mock_context)
        
        # Verify command failed
        assert not result.success
        assert "Invalid tab index" in result.error
        
        # Verify nothing was updated
        mock_context.workspace_service.switch_to_tab.assert_not_called()
        mock_context.chrome_title_bar.set_current_tab.assert_not_called()
    
    def test_tab_wrap_around(self, mock_context):
        """Test that tab navigation wraps around correctly."""
        # Test next tab from last position
        mock_context.workspace_service.get_current_tab_index.return_value = 2  # Last tab
        result = next_tab_command(mock_context)
        
        assert result.success
        assert result.value == {'tab_index': 0}  # Should wrap to first
        mock_context.chrome_title_bar.set_current_tab.assert_called_with(0)
        
        # Test previous tab from first position
        mock_context.workspace_service.get_current_tab_index.return_value = 0  # First tab
        result = previous_tab_command(mock_context)
        
        assert result.success
        assert result.value == {'tab_index': 2}  # Should wrap to last
        mock_context.chrome_title_bar.set_current_tab.assert_called_with(2)


class TestChromeUICommands:
    """Test Chrome-specific UI commands."""
    
    @patch('core.commands.builtin.ui_commands.QSettings')
    @patch('core.commands.builtin.ui_commands.QMessageBox')
    def test_toggle_chrome_mode_command(self, mock_msgbox, mock_settings):
        """Test the Chrome mode toggle command."""
        from core.commands.builtin.ui_commands import toggle_chrome_mode_command
        
        # Mock settings
        mock_settings_instance = Mock()
        mock_settings_instance.value.return_value = False  # Chrome mode off initially
        mock_settings.return_value = mock_settings_instance
        
        # Create context
        context = Mock(spec=CommandContext)
        context.args = {}
        
        # Execute command
        result = toggle_chrome_mode_command(context)
        
        # Verify success
        assert result.success
        assert result.value == "Chrome mode toggled. Restart required."
        
        # Verify settings were updated
        mock_settings_instance.setValue.assert_called_with("UI/ChromeMode", True)
        
        # Verify message box was shown
        mock_msgbox.information.assert_called_once()


class TestChromeTabSyncRegressions:
    """Regression tests for tab synchronization issues."""
    
    def test_keyboard_shortcut_sync_regression(self, mock_context):
        """
        Regression test for the bug where Ctrl+PgUp/PgDown didn't update Chrome tabs.
        This was the original issue that prompted the refactoring.
        """
        # Simulate the keyboard shortcut scenario
        mock_context.workspace_service.get_current_tab_index.return_value = 0
        
        # User presses Ctrl+PgDown
        result = next_tab_command(mock_context)
        assert result.success
        
        # Verify BOTH workspace and Chrome were updated
        mock_context.workspace_service.switch_to_tab.assert_called_with(1)
        mock_context.chrome_title_bar.set_current_tab.assert_called_with(1)
        
        # Reset mocks
        mock_context.workspace_service.switch_to_tab.reset_mock()
        mock_context.chrome_title_bar.set_current_tab.reset_mock()
        mock_context.workspace_service.get_current_tab_index.return_value = 1
        
        # User presses Ctrl+PgUp
        result = previous_tab_command(mock_context)
        assert result.success
        
        # Verify BOTH were updated again
        mock_context.workspace_service.switch_to_tab.assert_called_with(0)
        mock_context.chrome_title_bar.set_current_tab.assert_called_with(0)
    
    def test_chrome_click_uses_command(self):
        """Test that Chrome tab clicks go through the command system."""
        # This verifies that on_chrome_tab_changed uses execute_command
        # rather than directly manipulating the workspace
        
        from ui.chrome_main_window import ChromeMainWindow
        
        with patch('ui.main_window.MainWindow.__init__', return_value=None):
            with patch('ui.chrome_main_window.execute_command') as mock_execute:
                window = ChromeMainWindow()
                window.chrome_mode_enabled = True
                
                # Simulate Chrome tab click
                window.on_chrome_tab_changed(2)
                
                # Verify command was executed
                mock_execute.assert_called_with("workbench.action.selectTab", tab_index=2)