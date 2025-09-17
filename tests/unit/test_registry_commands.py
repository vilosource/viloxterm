#!/usr/bin/env python3
"""
Unit tests for registry commands using proper service methods.
"""

from unittest.mock import MagicMock

from core.commands.base import CommandContext
from core.commands.builtin.registry_commands import (
    get_widget_tab_index_command,
    is_widget_registered_command,
    register_widget_command,
    unregister_widget_command,
    update_registry_after_close_command,
)
from services.workspace_service import WorkspaceService


class TestRegistryCommands:
    """Test registry commands using service methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_workspace_service = MagicMock(spec=WorkspaceService)

        # Mock the new service methods
        self.mock_workspace_service.register_widget = MagicMock(return_value=True)
        self.mock_workspace_service.unregister_widget = MagicMock(return_value=True)
        self.mock_workspace_service.update_registry_after_tab_close = MagicMock(
            return_value=2
        )
        self.mock_workspace_service.get_widget_tab_index = MagicMock(return_value=3)
        self.mock_workspace_service.is_widget_registered = MagicMock(return_value=True)

        self.mock_context = MagicMock(spec=CommandContext)
        self.mock_context.get_service.return_value = self.mock_workspace_service

    def test_register_widget_command(self):
        """Test registering a widget using service method."""
        # Set up context args
        self.mock_context.args = {"widget_id": "com.viloapp.settings", "tab_index": 2}

        # Register a widget
        result = register_widget_command._original_func(self.mock_context)

        assert result.success
        assert result.value == {"widget_id": "com.viloapp.settings", "tab_index": 2}
        # Verify service method was called
        self.mock_workspace_service.register_widget.assert_called_once_with(
            "com.viloapp.settings", 2
        )

    def test_register_widget_no_service(self):
        """Test register command when service is not available."""
        self.mock_context.get_service.return_value = None
        self.mock_context.args = {"widget_id": "com.viloapp.settings", "tab_index": 2}

        result = register_widget_command._original_func(self.mock_context)
        assert not result.success
        assert "WorkspaceService not available" in result.error

    def test_unregister_widget_command(self):
        """Test unregistering a widget using service method."""
        # Setup: Widget will be unregistered successfully
        self.mock_workspace_service.unregister_widget.return_value = True

        # Unregister the widget
        self.mock_context.args = {"widget_id": "com.viloapp.settings"}
        result = unregister_widget_command._original_func(self.mock_context)

        assert result.success
        assert result.value == {
            "widget_id": "com.viloapp.settings",
            "unregistered": True,
        }
        # Verify service method was called
        self.mock_workspace_service.unregister_widget.assert_called_once_with(
            "com.viloapp.settings"
        )

    def test_unregister_nonexistent_widget(self):
        """Test unregistering a widget that doesn't exist."""
        # Widget doesn't exist, service returns False
        self.mock_workspace_service.unregister_widget.return_value = False

        self.mock_context.args = {"widget_id": "com.viloapp.nonexistent"}
        result = unregister_widget_command._original_func(self.mock_context)

        # Command still succeeds but value shows unregistered=False
        assert result.success
        assert result.value == {
            "widget_id": "com.viloapp.nonexistent",
            "unregistered": False,
        }

    def test_update_registry_after_close(self):
        """Test updating registry indices after tab close."""
        # Service will return that 2 widgets were updated
        self.mock_workspace_service.update_registry_after_tab_close.return_value = 2

        self.mock_context.args = {"closed_index": 1, "widget_id": "widget2"}

        result = update_registry_after_close_command._original_func(self.mock_context)

        assert result.success
        assert result.value["closed_index"] == 1
        assert result.value["updated_count"] == 2

        # Verify service method was called
        self.mock_workspace_service.update_registry_after_tab_close.assert_called_once_with(
            1, "widget2"
        )

    def test_update_registry_after_close_no_widget_id(self):
        """Test updating registry when no widget_id is provided."""
        # Service will return that 1 widget was updated
        self.mock_workspace_service.update_registry_after_tab_close.return_value = 1

        self.mock_context.args = {"closed_index": 1}
        result = update_registry_after_close_command._original_func(self.mock_context)

        assert result.success
        assert result.value["updated_count"] == 1

        # Verify service method was called with None for widget_id
        self.mock_workspace_service.update_registry_after_tab_close.assert_called_once_with(
            1, None
        )

    def test_get_widget_tab_index(self):
        """Test getting tab index for a registered widget."""
        # Service returns tab index 3
        self.mock_workspace_service.get_widget_tab_index.return_value = 3

        self.mock_context.args = {"widget_id": "com.viloapp.settings"}
        result = get_widget_tab_index_command._original_func(self.mock_context)

        assert result.success
        assert result.value == {"widget_id": "com.viloapp.settings", "tab_index": 3}

        # Verify service method was called
        self.mock_workspace_service.get_widget_tab_index.assert_called_once_with(
            "com.viloapp.settings"
        )

    def test_get_widget_tab_index_not_found(self):
        """Test getting tab index for non-existent widget."""
        # Service returns None for non-existent widget
        self.mock_workspace_service.get_widget_tab_index.return_value = None

        self.mock_context.args = {"widget_id": "com.viloapp.nonexistent"}
        result = get_widget_tab_index_command._original_func(self.mock_context)

        assert not result.success
        assert "not found in registry" in result.error

    def test_is_widget_registered(self):
        """Test checking if a widget is registered."""
        # Check registered widget (returns True)
        self.mock_workspace_service.is_widget_registered.return_value = True
        self.mock_context.args = {"widget_id": "com.viloapp.settings"}
        result = is_widget_registered_command._original_func(self.mock_context)

        assert result.success
        assert result.value == {"widget_id": "com.viloapp.settings", "registered": True}

        # Check non-registered widget (returns False)
        self.mock_workspace_service.is_widget_registered.return_value = False
        self.mock_context.args = {"widget_id": "com.viloapp.nonexistent"}
        result = is_widget_registered_command._original_func(self.mock_context)

        assert result.success
        assert result.value == {
            "widget_id": "com.viloapp.nonexistent",
            "registered": False,
        }

    def test_register_with_failed_service_method(self):
        """Test when service method fails."""
        # Service method returns False (failure)
        self.mock_workspace_service.register_widget.return_value = False

        self.mock_context.args = {"widget_id": "com.viloapp.test", "tab_index": 0}

        result = register_widget_command._original_func(self.mock_context)

        assert not result.success
        assert "Failed to register widget" in result.error

    def test_exception_handling(self):
        """Test exception handling in commands."""
        # Make service method raise an exception
        self.mock_workspace_service.register_widget.side_effect = Exception(
            "Test error"
        )

        self.mock_context.args = {"widget_id": "test", "tab_index": 0}

        result = register_widget_command._original_func(self.mock_context)

        assert not result.success
        assert "Test error" in result.error

    def test_missing_required_args(self):
        """Test commands with missing required arguments."""
        # Test register without widget_id
        self.mock_context.args = {"tab_index": 0}
        result = register_widget_command._original_func(self.mock_context)
        assert not result.success
        assert "widget_id and tab_index are required" in result.error

        # Test register without tab_index
        self.mock_context.args = {"widget_id": "test"}
        result = register_widget_command._original_func(self.mock_context)
        assert not result.success
        assert "widget_id and tab_index are required" in result.error

        # Test unregister without widget_id
        self.mock_context.args = {}
        result = unregister_widget_command._original_func(self.mock_context)
        assert not result.success
        assert "widget_id is required" in result.error
