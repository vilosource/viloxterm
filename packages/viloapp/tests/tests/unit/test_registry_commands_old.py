#!/usr/bin/env python3
"""
Unit tests for widget registry management commands.

Tests that commands properly manage the widget registry instead of
direct service manipulation.
"""

from unittest.mock import MagicMock

import pytest

from viloapp.core.commands.base import CommandContext
from viloapp.core.commands.builtin.registry_commands import (
    get_widget_tab_index_command,
    is_widget_registered_command,
    register_widget_command,
    unregister_widget_command,
    update_registry_after_close_command,
)
from viloapp.services.workspace_service import WorkspaceService


class TestRegistryCommands:
    """Test suite for registry management commands."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_workspace_service = MagicMock(spec=WorkspaceService)
        self.mock_workspace_service._widget_registry = {}

        self.mock_context = MagicMock(spec=CommandContext)
        self.mock_context.get_service.return_value = self.mock_workspace_service

    def test_register_widget_command(self):
        """Test registering a widget in the registry."""
        # Set up context args
        self.mock_context.args = {"widget_id": "com.viloapp.settings", "tab_index": 2}

        # Register a widget
        result = register_widget_command._original_func(self.mock_context)

        assert result.success
        assert result.value == {"widget_id": "com.viloapp.settings", "tab_index": 2}
        assert self.mock_workspace_service._widget_registry["com.viloapp.settings"] == 2

    def test_register_widget_no_service(self):
        """Test registering when service is not available."""
        self.mock_context.get_service.return_value = None
        self.mock_context.args = {"widget_id": "com.viloapp.settings", "tab_index": 2}

        result = register_widget_command._original_func(self.mock_context)

        assert not result.success
        assert "WorkspaceService not available" in result.error

    def test_unregister_widget_command(self):
        """Test unregistering a widget from the registry."""
        # Setup: Add widget to registry
        self.mock_workspace_service._widget_registry["com.viloapp.settings"] = 2

        # Unregister the widget
        self.mock_context.args = {"widget_id": "com.viloapp.settings"}
        result = unregister_widget_command._original_func(self.mock_context)

        assert result.success
        assert "com.viloapp.settings" not in self.mock_workspace_service._widget_registry

    def test_unregister_nonexistent_widget(self):
        """Test unregistering a widget that doesn't exist."""
        self.mock_context.args = {"widget_id": "com.viloapp.nonexistent"}
        result = unregister_widget_command._original_func(self.mock_context)

        # Should succeed even if widget doesn't exist (idempotent)
        assert result.success

    def test_update_registry_after_close(self):
        """Test updating registry indices after tab close."""
        # Setup: Multiple widgets in registry
        self.mock_workspace_service._widget_registry = {
            "widget1": 0,
            "widget2": 1,
            "widget3": 2,
            "widget4": 3,
        }

        # Close tab at index 1 (widget2)
        self.mock_context.args = {"closed_index": 1, "widget_id": "widget2"}
        result = update_registry_after_close_command._original_func(self.mock_context)

        assert result.success
        assert result.value["closed_index"] == 1
        assert result.value["updated_count"] == 2

        # Check updated registry
        expected = {
            "widget1": 0,  # unchanged
            "widget3": 1,  # moved from 2 to 1
            "widget4": 2,  # moved from 3 to 2
        }
        assert self.mock_workspace_service._widget_registry == expected

    def test_update_registry_after_close_no_widget_id(self):
        """Test updating registry when no widget_id is provided."""
        # Setup: Multiple widgets in registry
        self.mock_workspace_service._widget_registry = {
            "widget1": 0,
            "widget2": 1,
            "widget3": 2,
        }

        # Close tab at index 0 without specifying widget_id
        self.mock_context.args = {"closed_index": 0, "widget_id": None}
        result = update_registry_after_close_command._original_func(self.mock_context)

        assert result.success
        # All widgets after index 0 should be updated
        expected = {
            "widget1": 0,  # Not removed (no widget_id provided)
            "widget2": 0,  # moved from 1 to 0
            "widget3": 1,  # moved from 2 to 1
        }
        assert self.mock_workspace_service._widget_registry == expected

    def test_get_widget_tab_index(self):
        """Test getting tab index for a registered widget."""
        # Setup: Add widget to registry
        self.mock_workspace_service._widget_registry["com.viloapp.settings"] = 3

        self.mock_context.args = {"widget_id": "com.viloapp.settings"}
        result = get_widget_tab_index_command._original_func(self.mock_context)

        assert result.success
        assert result.value == {"widget_id": "com.viloapp.settings", "tab_index": 3}

    def test_get_widget_tab_index_not_found(self):
        """Test getting tab index for unregistered widget."""
        self.mock_context.args = {"widget_id": "com.viloapp.nonexistent"}
        result = get_widget_tab_index_command._original_func(self.mock_context)

        assert not result.success
        assert "not found in registry" in result.error

    def test_is_widget_registered(self):
        """Test checking if a widget is registered."""
        # Setup: Add widget to registry
        self.mock_workspace_service._widget_registry["com.viloapp.settings"] = 2

        # Check registered widget
        self.mock_context.args = {"widget_id": "com.viloapp.settings"}
        result = is_widget_registered_command._original_func(self.mock_context)
        assert result.success
        assert result.value == {"widget_id": "com.viloapp.settings", "registered": True}

        # Check unregistered widget
        self.mock_context.args = {"widget_id": "com.viloapp.nonexistent"}
        result = is_widget_registered_command._original_func(self.mock_context)
        assert result.success
        assert result.value == {
            "widget_id": "com.viloapp.nonexistent",
            "registered": False,
        }

    def test_commands_handle_missing_registry(self):
        """Test that commands handle missing _widget_registry gracefully."""
        # Remove the registry attribute
        delattr(self.mock_workspace_service, "_widget_registry")

        # Register should create it
        self.mock_context.args = {"widget_id": "test", "tab_index": 0}
        result = register_widget_command._original_func(self.mock_context)
        assert result.success
        assert hasattr(self.mock_workspace_service, "_widget_registry")

        # Remove again for other tests
        delattr(self.mock_workspace_service, "_widget_registry")

        # Other commands should handle missing registry
        self.mock_context.args = {"widget_id": "test"}
        result = unregister_widget_command._original_func(self.mock_context)
        assert result.success

        self.mock_context.args = {"closed_index": 0}
        result = update_registry_after_close_command._original_func(self.mock_context)
        assert result.success

        self.mock_context.args = {"widget_id": "test"}
        result = get_widget_tab_index_command._original_func(self.mock_context)
        assert not result.success  # Widget not found

        self.mock_context.args = {"widget_id": "test"}
        result = is_widget_registered_command._original_func(self.mock_context)
        assert result.success
        assert not result.value["registered"]

    def test_exception_handling(self):
        """Test that commands handle exceptions gracefully."""
        # Make service raise exception
        self.mock_workspace_service._widget_registry = MagicMock()
        self.mock_workspace_service._widget_registry.__setitem__.side_effect = Exception(
            "Test error"
        )

        self.mock_context.args = {"widget_id": "test", "tab_index": 0}
        result = register_widget_command._original_func(self.mock_context)

        assert not result.success
        assert "Test error" in result.error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
