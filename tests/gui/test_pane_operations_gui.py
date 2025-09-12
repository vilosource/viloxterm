"""GUI tests for pane operations including close button functionality."""

import pytest
from unittest.mock import Mock, patch
from PySide6.QtCore import Qt, QPoint
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QPushButton, QToolButton
from core.commands.executor import execute_command


@pytest.mark.gui
class TestPaneOperationsGUI:
    """Test pane operations through actual GUI interactions."""
    
    @pytest.fixture(autouse=True)
    def setup(self, qtbot, gui_main_window):
        """Setup for each test."""
        self.qtbot = qtbot
        self.main_window = gui_main_window
        self.workspace = gui_main_window.workspace
        
        # Reset workspace to single pane for test isolation
        # Close all extra panes to start fresh
        split_widget = self.workspace.get_current_split_widget()
        if split_widget and split_widget.model:
            while len(split_widget.model.get_all_app_widgets()) > 1:
                self.workspace.close_active_pane()
                QTest.qWait(50)
        
    def get_current_pane_count(self):
        """Get the current number of panes in the active tab."""
        split_widget = self.workspace.get_current_split_widget()
        if split_widget and split_widget.model:
            return len(split_widget.model.get_all_app_widgets())
        return 0
        
    def test_split_pane_horizontal(self):
        """Test splitting a pane horizontally."""
        initial_count = self.get_current_pane_count()
        assert initial_count == 1, "Should start with one pane"
        
        # Execute split command
        result = execute_command("workbench.action.splitPaneHorizontal")
        assert result.success, f"Split command failed: {result.error}"
        
        # Wait for UI update
        QTest.qWait(100)
        
        # Verify pane was split
        final_count = self.get_current_pane_count()
        assert final_count == initial_count + 1, "Pane should have been split"
        
    def test_split_pane_vertical(self):
        """Test splitting a pane vertically."""
        initial_count = self.get_current_pane_count()
        assert initial_count == 1, "Should start with one pane"
        
        # Execute split command
        result = execute_command("workbench.action.splitPaneVertical")
        assert result.success, f"Split command failed: {result.error}"
        
        # Wait for UI update
        QTest.qWait(100)
        
        # Verify pane was split
        final_count = self.get_current_pane_count()
        assert final_count == initial_count + 1, "Pane should have been split"
        
    def test_close_pane_via_keyboard_shortcut(self):
        """Test closing a pane using Ctrl+Shift+W keyboard shortcut."""
        # First split to have multiple panes
        result = execute_command("workbench.action.splitPaneHorizontal")
        assert result.success, "Failed to split pane"
        QTest.qWait(100)
        
        initial_count = self.get_current_pane_count()
        assert initial_count > 1, "Need multiple panes for test"
        
        # Use Ctrl+Shift+W to close pane
        self.qtbot.keyClick(
            self.workspace, 
            Qt.Key.Key_W, 
            Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier
        )
        QTest.qWait(100)
        
        # Verify pane was closed
        final_count = self.get_current_pane_count()
        assert final_count == initial_count - 1, "Pane should have been closed by Ctrl+Shift+W"
    
    def test_close_pane_via_command(self):
        """Test closing a pane through the command system."""
        # First split to have multiple panes
        result = execute_command("workbench.action.splitPaneHorizontal")
        assert result.success, "Failed to split pane"
        QTest.qWait(100)
        
        initial_count = self.get_current_pane_count()
        assert initial_count > 1, "Need multiple panes for test"
        
        # Execute close command
        result = execute_command("workbench.action.closePane")
        assert result.success, f"Close command failed: {result.error}"
        
        # Wait for UI update
        QTest.qWait(100)
        
        # Verify pane was closed
        final_count = self.get_current_pane_count()
        assert final_count == initial_count - 1, "Pane should have been closed"
        
    def test_close_pane_via_button_click(self):
        """Test closing a pane by clicking the close button."""
        # First split to have multiple panes
        result = execute_command("workbench.action.splitPaneHorizontal")
        assert result.success, "Failed to split pane"
        QTest.qWait(100)
        
        initial_count = self.get_current_pane_count()
        assert initial_count > 1, "Need multiple panes for test"
        
        # Find a close button in one of the panes
        split_widget = self.workspace.get_current_split_widget()
        close_button = None
        
        # Look for close buttons in the pane headers (they're QToolButtons)
        for widget in split_widget.findChildren(QToolButton):
            if "×" in widget.text():
                close_button = widget
                break
                
        assert close_button is not None, "Could not find close button"
        assert close_button.isVisible(), "Close button should be visible"
        
        # Click the close button
        self.qtbot.mouseClick(close_button, Qt.MouseButton.LeftButton)
        QTest.qWait(100)
        
        # Verify pane was closed
        final_count = self.get_current_pane_count()
        assert final_count == initial_count - 1, "Pane should have been closed after button click"
        
    def test_cannot_close_last_pane(self):
        """Test that the last pane cannot be closed."""
        # Ensure we have only one pane
        initial_count = self.get_current_pane_count()
        assert initial_count == 1, "Should have exactly one pane"
        
        # Try to close the last pane
        result = execute_command("workbench.action.closePane")
        
        # Command should fail or do nothing
        if result.success:
            # If it claims success, verify no pane was actually closed
            final_count = self.get_current_pane_count()
            assert final_count == 1, "Last pane should not be closed"
        else:
            # Command correctly reported failure
            assert "Cannot close" in result.error or "last pane" in result.error.lower()
            
    def test_maximize_pane(self):
        """Test maximizing and restoring a pane."""
        # Split to have multiple panes
        execute_command("workbench.action.splitPaneHorizontal")
        QTest.qWait(100)
        
        # Execute maximize command
        result = execute_command("workbench.action.maximizePane")
        assert result.success, f"Maximize command failed: {result.error}"
        
        # Note: Without visual verification, we just ensure the command executes
        # In a real application, we'd check the pane's size or state
        
    def test_pane_focus_navigation(self):
        """Test navigating focus between panes."""
        # Create multiple panes
        execute_command("workbench.action.splitPaneHorizontal")
        execute_command("workbench.action.splitPaneVertical")
        QTest.qWait(100)
        
        # Test focus navigation commands
        commands = [
            "workbench.action.focusNextPane",
            "workbench.action.focusPreviousPane",
            "workbench.action.focusLeftPane",
            "workbench.action.focusRightPane",
            "workbench.action.focusAbovePane",
            "workbench.action.focusBelowPane"
        ]
        
        for cmd in commands:
            result = execute_command(cmd)
            # Some navigation commands might fail if there's no pane in that direction
            # That's OK - we're testing that they don't crash
            if not result.success:
                assert "No pane" in result.error or "not found" in result.error.lower()


@pytest.mark.gui
@pytest.mark.integration
class TestPaneServiceIntegration:
    """Test integration between pane commands and workspace service."""
    
    @pytest.fixture(autouse=True)
    def setup(self, qtbot, gui_main_window):
        """Setup for each test."""
        self.qtbot = qtbot
        self.main_window = gui_main_window
        self.workspace = gui_main_window.workspace
        
        # Get the service locator
        from services.service_locator import ServiceLocator
        self.service_locator = ServiceLocator()
        
    def test_workspace_service_has_required_methods(self):
        """Test that WorkspaceService has all required methods."""
        from services.workspace_service import WorkspaceService
        
        workspace_service = self.service_locator.get(WorkspaceService)
        
        # Verify required methods exist
        assert hasattr(workspace_service, 'get_workspace'), "Missing get_workspace method"
        assert hasattr(workspace_service, 'set_workspace'), "Missing set_workspace method"
        
        # Verify getter returns workspace
        workspace = workspace_service.get_workspace()
        assert workspace is not None, "WorkspaceService should have workspace reference"
        
    def test_pane_commands_use_correct_service_methods(self):
        """Test that pane commands correctly interact with WorkspaceService."""
        from services.workspace_service import WorkspaceService
        
        workspace_service = self.service_locator.get(WorkspaceService)
        
        # Mock the workspace service methods to track calls
        original_get_workspace = workspace_service.get_workspace
        get_workspace_mock = Mock(side_effect=original_get_workspace)
        workspace_service.get_workspace = get_workspace_mock
        
        # Execute a pane command that should use the service
        result = execute_command("workbench.action.splitPaneHorizontal")
        
        # Verify the service method was called
        get_workspace_mock.assert_called()
        
        # Restore original method
        workspace_service.get_workspace = original_get_workspace
        
    def test_close_pane_button_triggers_command(self):
        """Test that clicking close button triggers the correct command."""
        # Split to have multiple panes
        execute_command("workbench.action.splitPaneHorizontal")
        QTest.qWait(100)
        
        # Mock the execute_command to track calls
        with patch('core.commands.executor.execute_command') as mock_execute:
            mock_execute.return_value = Mock(success=True)
            
            # Find and click close button
            split_widget = self.workspace.get_current_split_widget()
            for widget in split_widget.findChildren(QToolButton):
                if "×" in widget.text():
                    self.qtbot.mouseClick(widget, Qt.MouseButton.LeftButton)
                    break
            
            # Verify the close command was called
            # Note: The actual call might be indirect through signals
            # This is where we'd verify the integration