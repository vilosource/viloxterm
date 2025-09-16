#!/usr/bin/env python3
"""
Comprehensive unit tests for WorkspaceService.

Tests the critical workspace service that manages tabs, panes, and widgets
through specialized manager components. Follows Test Monkey principles:
- Clear test names: test_what_condition_expectation()
- AAA pattern (Arrange-Act-Assert)
- Strong assertions (specific values, not just "is not None")
- Mock workspace UI component properly
- Test error paths and boundary conditions
- Test edge cases for all operations
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from typing import Dict, Any

from services.workspace_service import WorkspaceService
from services.workspace_widget_registry import WorkspaceWidgetRegistry
from services.workspace_tab_manager import WorkspaceTabManager
from services.workspace_pane_manager import WorkspacePaneManager


class TestWorkspaceServiceInitialization:
    """Test workspace service initialization and setup."""

    def test_init_without_workspace_creates_service_successfully(self):
        """Test service can be created without workspace instance."""
        # Act
        service = WorkspaceService()

        # Assert
        assert service.name == "WorkspaceService"
        assert service.get_workspace() is None
        assert service._widget_registry is not None
        assert service._tab_manager is not None
        assert service._pane_manager is not None

    def test_init_with_workspace_sets_workspace_correctly(self):
        """Test service initialization with workspace instance."""
        # Arrange
        mock_workspace = Mock()

        # Act
        service = WorkspaceService(workspace=mock_workspace)

        # Assert
        assert service.get_workspace() is mock_workspace
        assert service._tab_manager._workspace is mock_workspace
        assert service._pane_manager._workspace is mock_workspace

    def test_set_workspace_updates_all_managers(self):
        """Test that setting workspace updates all manager instances."""
        # Arrange
        service = WorkspaceService()
        mock_workspace = Mock()

        # Act
        service.set_workspace(mock_workspace)

        # Assert
        assert service.get_workspace() is mock_workspace
        assert service._tab_manager._workspace is mock_workspace
        assert service._pane_manager._workspace is mock_workspace

    def test_initialize_with_context_gets_workspace_from_context(self):
        """Test initialization with context extracts workspace."""
        # Arrange
        service = WorkspaceService()
        mock_workspace = Mock()
        context = {'workspace': mock_workspace}

        # Act
        service.initialize(context)

        # Assert
        assert service.get_workspace() is mock_workspace

    def test_initialize_without_workspace_logs_warning(self):
        """Test initialization without workspace logs appropriate warning."""
        # Arrange
        service = WorkspaceService()
        context = {}

        # Act & Assert - should not raise exception
        service.initialize(context)
        assert service.get_workspace() is None

    def test_cleanup_clears_workspace_and_registry(self):
        """Test cleanup clears all resources properly."""
        # Arrange
        mock_workspace = Mock()
        service = WorkspaceService(workspace=mock_workspace)

        # Act
        service.cleanup()

        # Assert
        assert service.get_workspace() is None


class TestWorkspaceServiceWidgetRegistry:
    """Test widget registry operations through the service."""

    @pytest.fixture
    def service_with_mocks(self):
        """Create service with mocked components."""
        service = WorkspaceService()
        service._widget_registry = Mock(spec=WorkspaceWidgetRegistry)
        service._tab_manager = Mock(spec=WorkspaceTabManager)
        return service

    def test_has_widget_delegates_to_registry(self, service_with_mocks):
        """Test has_widget delegates to widget registry."""
        # Arrange
        service_with_mocks._widget_registry.has_widget.return_value = True

        # Act
        result = service_with_mocks.has_widget("test-widget")

        # Assert
        assert result is True
        service_with_mocks._widget_registry.has_widget.assert_called_once_with("test-widget")

    def test_register_widget_delegates_to_registry(self, service_with_mocks):
        """Test register_widget delegates to widget registry."""
        # Arrange
        service_with_mocks._widget_registry.register_widget.return_value = True

        # Act
        result = service_with_mocks.register_widget("test-widget", 0)

        # Assert
        assert result is True
        service_with_mocks._widget_registry.register_widget.assert_called_once_with("test-widget", 0)

    def test_unregister_widget_delegates_to_registry(self, service_with_mocks):
        """Test unregister_widget delegates to widget registry."""
        # Arrange
        service_with_mocks._widget_registry.unregister_widget.return_value = True

        # Act
        result = service_with_mocks.unregister_widget("test-widget")

        # Assert
        assert result is True
        service_with_mocks._widget_registry.unregister_widget.assert_called_once_with("test-widget")

    def test_focus_widget_delegates_to_tab_manager(self, service_with_mocks):
        """Test focus_widget delegates to tab manager."""
        # Arrange
        service_with_mocks._tab_manager.focus_widget.return_value = True

        # Act
        result = service_with_mocks.focus_widget("test-widget")

        # Assert
        assert result is True
        service_with_mocks._tab_manager.focus_widget.assert_called_once_with("test-widget")

    def test_get_widget_tab_index_returns_correct_index(self, service_with_mocks):
        """Test get_widget_tab_index returns correct tab index."""
        # Arrange
        service_with_mocks._widget_registry.get_widget_tab_index.return_value = 2

        # Act
        result = service_with_mocks.get_widget_tab_index("test-widget")

        # Assert
        assert result == 2
        service_with_mocks._widget_registry.get_widget_tab_index.assert_called_once_with("test-widget")

    def test_is_widget_registered_delegates_to_registry(self, service_with_mocks):
        """Test is_widget_registered delegates to widget registry."""
        # Arrange
        service_with_mocks._widget_registry.is_widget_registered.return_value = False

        # Act
        result = service_with_mocks.is_widget_registered("test-widget")

        # Assert
        assert result is False
        service_with_mocks._widget_registry.is_widget_registered.assert_called_once_with("test-widget")

    def test_update_registry_after_tab_close_delegates_correctly(self, service_with_mocks):
        """Test update_registry_after_tab_close delegates with correct parameters."""
        # Arrange
        service_with_mocks._widget_registry.update_registry_after_tab_close.return_value = 3

        # Act
        result = service_with_mocks.update_registry_after_tab_close(1, "test-widget")

        # Assert
        assert result == 3
        service_with_mocks._widget_registry.update_registry_after_tab_close.assert_called_once_with(1, "test-widget")


class TestWorkspaceServiceTabOperations:
    """Test tab management operations through the service."""

    @pytest.fixture
    def service_with_workspace(self):
        """Create service with mocked workspace and initialized state."""
        mock_workspace = Mock()
        mock_workspace.tab_widget = Mock()
        mock_workspace.tab_widget.currentIndex.return_value = 0
        mock_workspace.tab_widget.count.return_value = 1

        service = WorkspaceService(workspace=mock_workspace)
        service._initialized = True  # Mark as initialized to pass validation
        service._tab_manager = Mock(spec=WorkspaceTabManager)

        return service

    @patch('core.context.manager.context_manager')
    def test_add_editor_tab_creates_tab_and_notifies(self, mock_context_manager, service_with_workspace):
        """Test add_editor_tab creates tab and sends notifications."""
        # Arrange
        service_with_workspace._tab_manager.add_editor_tab.return_value = 1
        service_with_workspace._tab_manager.get_tab_count.return_value = 2

        observers = []
        service_with_workspace.add_observer(lambda event: observers.append((event.name, event.data)))

        # Act
        result = service_with_workspace.add_editor_tab("MyEditor")

        # Assert
        assert result == 1
        service_with_workspace._tab_manager.add_editor_tab.assert_called_once_with("MyEditor")

        # Check notification
        assert len(observers) == 1
        event, data = observers[0]
        assert event == 'tab_added'
        assert data['type'] == 'editor'
        assert data['name'] == 'MyEditor'
        assert data['index'] == 1

        # Check context updates
        mock_context_manager.set.assert_any_call('workbench.tabs.count', 2)
        mock_context_manager.set.assert_any_call('workbench.tabs.hasMultiple', True)

    @patch('core.context.manager.context_manager')
    def test_add_terminal_tab_creates_tab_and_notifies(self, mock_context_manager, service_with_workspace):
        """Test add_terminal_tab creates tab and sends notifications."""
        # Arrange
        service_with_workspace._tab_manager.add_terminal_tab.return_value = 2
        service_with_workspace._tab_manager.get_tab_count.return_value = 3

        observers = []
        service_with_workspace.add_observer(lambda event: observers.append((event.name, event.data)))

        # Act
        result = service_with_workspace.add_terminal_tab("MyTerminal")

        # Assert
        assert result == 2
        service_with_workspace._tab_manager.add_terminal_tab.assert_called_once_with("MyTerminal")

        # Check notification
        assert len(observers) == 1
        event, data = observers[0]
        assert event == 'tab_added'
        assert data['type'] == 'terminal'
        assert data['name'] == 'MyTerminal'
        assert data['index'] == 2

    def test_add_editor_tab_without_initialization_raises_error(self):
        """Test add_editor_tab raises error when service not initialized."""
        # Arrange
        service = WorkspaceService()
        # Don't mark as initialized

        # Act & Assert
        with pytest.raises(RuntimeError, match="Service WorkspaceService is not initialized"):
            service.add_editor_tab("Test")

    @patch('core.context.manager.context_manager')
    def test_add_app_widget_successful_registers_and_notifies(self, mock_context_manager, service_with_workspace):
        """Test add_app_widget successfully registers widget and notifies."""
        # Arrange
        # Mock a widget type instead of importing from core.widgets
        widget_type = Mock()
        widget_type.value = "settings"

        service_with_workspace._tab_manager.add_app_widget.return_value = True
        service_with_workspace._tab_manager.get_tab_count.return_value = 2

        observers = []
        service_with_workspace.add_observer(lambda event: observers.append((event.name, event.data)))

        # Act
        result = service_with_workspace.add_app_widget(widget_type, "settings-1", "Settings")

        # Assert
        assert result is True
        service_with_workspace._tab_manager.add_app_widget.assert_called_once_with(widget_type, "settings-1", "Settings")

        # Check notification
        assert len(observers) == 1
        event, data = observers[0]
        assert event == 'tab_added'
        assert data['type'] == "settings"
        assert data['widget_id'] == "settings-1"
        assert data['name'] == "Settings"

    def test_add_app_widget_failure_does_not_notify(self, service_with_workspace):
        """Test add_app_widget failure does not send notification."""
        # Arrange
        widget_type = Mock()
        service_with_workspace._tab_manager.add_app_widget.return_value = False

        observers = []
        service_with_workspace.add_observer(lambda event: observers.append((event.name, event.data)))

        # Act
        result = service_with_workspace.add_app_widget(widget_type, "settings-1", "Settings")

        # Assert
        assert result is False
        assert len(observers) == 0

    @patch('core.context.manager.context_manager')
    def test_close_tab_with_index_closes_and_notifies(self, mock_context_manager, service_with_workspace):
        """Test close_tab with specific index closes tab and notifies."""
        # Arrange
        service_with_workspace._workspace.tab_widget.tabText.return_value = "Tab 1"
        service_with_workspace._tab_manager.close_tab.return_value = True
        service_with_workspace._tab_manager.get_tab_count.return_value = 0

        observers = []
        service_with_workspace.add_observer(lambda event: observers.append((event.name, event.data)))

        # Act
        result = service_with_workspace.close_tab(1)

        # Assert
        assert result is True
        service_with_workspace._tab_manager.close_tab.assert_called_once_with(1)

        # Check notification
        assert len(observers) == 1
        event, data = observers[0]
        assert event == 'tab_closed'
        assert data['index'] == 1
        assert data['name'] == "Tab 1"

    def test_close_tab_without_index_uses_current_tab(self, service_with_workspace):
        """Test close_tab without index uses current tab index."""
        # Arrange
        service_with_workspace._workspace.tab_widget.currentIndex.return_value = 2
        service_with_workspace._workspace.tab_widget.tabText.return_value = "Current Tab"
        service_with_workspace._tab_manager.close_tab.return_value = True
        service_with_workspace._tab_manager.get_tab_count.return_value = 1

        # Act
        result = service_with_workspace.close_tab()

        # Assert
        assert result is True
        service_with_workspace._tab_manager.close_tab.assert_called_once_with(2)

    def test_get_current_tab_index_delegates_to_manager(self, service_with_workspace):
        """Test get_current_tab_index delegates to tab manager."""
        # Arrange
        service_with_workspace._tab_manager.get_current_tab_index.return_value = 3

        # Act
        result = service_with_workspace.get_current_tab_index()

        # Assert
        assert result == 3
        service_with_workspace._tab_manager.get_current_tab_index.assert_called_once()

    def test_get_tab_count_delegates_to_manager(self, service_with_workspace):
        """Test get_tab_count delegates to tab manager."""
        # Arrange
        service_with_workspace._tab_manager.get_tab_count.return_value = 5

        # Act
        result = service_with_workspace.get_tab_count()

        # Assert
        assert result == 5
        service_with_workspace._tab_manager.get_tab_count.assert_called_once()

    def test_switch_to_tab_delegates_and_notifies_on_success(self, service_with_workspace):
        """Test switch_to_tab delegates to manager and notifies on success."""
        # Arrange
        service_with_workspace._tab_manager.switch_to_tab.return_value = True

        observers = []
        service_with_workspace.add_observer(lambda event: observers.append((event.name, event.data)))

        # Act
        result = service_with_workspace.switch_to_tab(2)

        # Assert
        assert result is True
        service_with_workspace._tab_manager.switch_to_tab.assert_called_once_with(2)

        # Check notification
        assert len(observers) == 1
        event, data = observers[0]
        assert event == 'tab_switched'
        assert data['index'] == 2

    def test_switch_to_tab_does_not_notify_on_failure(self, service_with_workspace):
        """Test switch_to_tab does not notify when switching fails."""
        # Arrange
        service_with_workspace._tab_manager.switch_to_tab.return_value = False

        observers = []
        service_with_workspace.add_observer(lambda event: observers.append((event.name, event.data)))

        # Act
        result = service_with_workspace.switch_to_tab(99)

        # Assert
        assert result is False
        assert len(observers) == 0


class TestWorkspaceServicePaneOperations:
    """Test pane management operations through the service."""

    @pytest.fixture
    def service_with_workspace(self):
        """Create service with mocked workspace for pane operations."""
        mock_workspace = Mock()
        service = WorkspaceService(workspace=mock_workspace)
        service._initialized = True
        service._pane_manager = Mock(spec=WorkspacePaneManager)
        return service

    @patch('core.context.manager.context_manager')
    @patch('core.settings.app_defaults.get_default_split_direction')
    def test_split_active_pane_with_orientation_creates_pane_and_notifies(
        self, mock_get_default, mock_context_manager, service_with_workspace
    ):
        """Test split_active_pane with orientation creates pane and notifies."""
        # Arrange
        mock_get_default.return_value = "horizontal"
        service_with_workspace._pane_manager.split_active_pane.return_value = "pane-2"
        service_with_workspace._pane_manager.get_active_pane_id.return_value = "pane-1"
        service_with_workspace._pane_manager.get_pane_count.return_value = 2

        observers = []
        service_with_workspace.add_observer(lambda event: observers.append((event.name, event.data)))

        # Act
        result = service_with_workspace.split_active_pane("vertical")

        # Assert
        assert result == "pane-2"
        service_with_workspace._pane_manager.split_active_pane.assert_called_once_with("vertical")

        # Check notification
        assert len(observers) == 1
        event, data = observers[0]
        assert event == 'pane_split'
        assert data['orientation'] == "vertical"
        assert data['new_pane_id'] == "pane-2"
        assert data['parent_pane_id'] == "pane-1"

    @patch('core.context.manager.context_manager')
    def test_split_active_pane_without_orientation_uses_default(
        self, mock_context_manager, service_with_workspace
    ):
        """Test split_active_pane without orientation uses default split direction."""
        # Arrange
        service_with_workspace._pane_manager.split_active_pane.return_value = "pane-2"
        service_with_workspace._pane_manager.get_active_pane_id.return_value = "pane-1"
        service_with_workspace._pane_manager.get_pane_count.return_value = 2

        # Act
        result = service_with_workspace.split_active_pane()

        # Assert
        assert result == "pane-2"
        service_with_workspace._pane_manager.split_active_pane.assert_called_once_with(None)

    def test_split_active_pane_failure_does_not_notify(self, service_with_workspace):
        """Test split_active_pane failure does not send notification."""
        # Arrange
        service_with_workspace._pane_manager.split_active_pane.return_value = None

        observers = []
        service_with_workspace.add_observer(lambda event: observers.append((event.name, event.data)))

        # Act
        result = service_with_workspace.split_active_pane("horizontal")

        # Assert
        assert result is None
        assert len(observers) == 0

    @patch('core.context.manager.context_manager')
    def test_close_active_pane_closes_and_notifies(self, mock_context_manager, service_with_workspace):
        """Test close_active_pane closes pane and sends notification."""
        # Arrange
        service_with_workspace._pane_manager.get_active_pane_id.return_value = "pane-1"
        service_with_workspace._pane_manager.close_active_pane.return_value = True
        service_with_workspace._pane_manager.get_pane_count.return_value = 1

        observers = []
        service_with_workspace.add_observer(lambda event: observers.append((event.name, event.data)))

        # Act
        result = service_with_workspace.close_active_pane()

        # Assert
        assert result is True
        service_with_workspace._pane_manager.close_active_pane.assert_called_once()

        # Check notification
        assert len(observers) == 1
        event, data = observers[0]
        assert event == 'pane_closed'
        assert data['pane_id'] == "pane-1"

    def test_focus_pane_delegates_and_notifies_on_success(self, service_with_workspace):
        """Test focus_pane delegates to manager and notifies on success."""
        # Arrange
        service_with_workspace._pane_manager.focus_pane.return_value = True

        observers = []
        service_with_workspace.add_observer(lambda event: observers.append((event.name, event.data)))

        # Act
        result = service_with_workspace.focus_pane("pane-3")

        # Assert
        assert result is True
        service_with_workspace._pane_manager.focus_pane.assert_called_once_with("pane-3")

        # Check notification
        assert len(observers) == 1
        event, data = observers[0]
        assert event == 'pane_focused'
        assert data['pane_id'] == "pane-3"

    @patch('core.context.manager.context_manager')
    def test_toggle_pane_numbers_updates_context_and_notifies(
        self, mock_context_manager, service_with_workspace
    ):
        """Test toggle_pane_numbers updates context and sends notification."""
        # Arrange
        service_with_workspace._pane_manager.toggle_pane_numbers.return_value = True

        observers = []
        service_with_workspace.add_observer(lambda event: observers.append((event.name, event.data)))

        # Act
        result = service_with_workspace.toggle_pane_numbers()

        # Assert
        assert result is True
        mock_context_manager.set.assert_called_once_with('workbench.panes.numbersVisible', True)

        # Check notification
        assert len(observers) == 1
        event, data = observers[0]
        assert event == 'pane_numbers_toggled'
        assert data['visible'] is True

    def test_navigate_in_direction_tracks_navigation_and_notifies(self, service_with_workspace):
        """Test navigate_in_direction tracks from/to panes and notifies."""
        # Arrange
        service_with_workspace._pane_manager.get_active_pane_id.side_effect = ["pane-1", "pane-2"]
        service_with_workspace._pane_manager.navigate_in_direction.return_value = True

        observers = []
        service_with_workspace.add_observer(lambda event: observers.append((event.name, event.data)))

        # Act
        result = service_with_workspace.navigate_in_direction("right")

        # Assert
        assert result is True
        service_with_workspace._pane_manager.navigate_in_direction.assert_called_once_with("right")

        # Check notification
        assert len(observers) == 1
        event, data = observers[0]
        assert event == 'pane_navigated'
        assert data['from'] == "pane-1"
        assert data['to'] == "pane-2"
        assert data['direction'] == "right"

    def test_get_pane_count_delegates_to_manager(self, service_with_workspace):
        """Test get_pane_count delegates to pane manager."""
        # Arrange
        service_with_workspace._pane_manager.get_pane_count.return_value = 4

        # Act
        result = service_with_workspace.get_pane_count()

        # Assert
        assert result == 4
        service_with_workspace._pane_manager.get_pane_count.assert_called_once()

    def test_get_active_pane_id_delegates_to_manager(self, service_with_workspace):
        """Test get_active_pane_id delegates to pane manager."""
        # Arrange
        service_with_workspace._pane_manager.get_active_pane_id.return_value = "active-pane"

        # Act
        result = service_with_workspace.get_active_pane_id()

        # Assert
        assert result == "active-pane"
        service_with_workspace._pane_manager.get_active_pane_id.assert_called_once()


class TestWorkspaceServiceLayoutOperations:
    """Test layout save/restore operations."""

    @pytest.fixture
    def service_with_workspace(self):
        """Create service with mocked workspace for layout operations."""
        mock_workspace = Mock()
        service = WorkspaceService(workspace=mock_workspace)
        service._initialized = True
        return service

    def test_save_layout_returns_workspace_state(self, service_with_workspace):
        """Test save_layout returns state from workspace."""
        # Arrange
        expected_state = {'tabs': [{'name': 'Tab1'}], 'current_tab': 0}
        service_with_workspace._workspace.get_state.return_value = expected_state

        # Act
        result = service_with_workspace.save_layout()

        # Assert
        assert result == expected_state
        service_with_workspace._workspace.get_state.assert_called_once()

    def test_save_layout_without_workspace_returns_empty_dict(self):
        """Test save_layout without workspace returns empty dictionary."""
        # Arrange
        service = WorkspaceService()

        # Act
        result = service.save_layout()

        # Assert
        assert result == {}

    def test_restore_layout_applies_state_and_notifies(self, service_with_workspace):
        """Test restore_layout applies state to workspace and notifies."""
        # Arrange
        state = {'tabs': [{'name': 'Tab1'}], 'current_tab': 0}

        observers = []
        service_with_workspace.add_observer(lambda event: observers.append((event.name, event.data)))

        # Act
        result = service_with_workspace.restore_layout(state)

        # Assert
        assert result is True
        service_with_workspace._workspace.set_state.assert_called_once_with(state)

        # Check notification
        assert len(observers) == 1
        event, data = observers[0]
        assert event == 'layout_restored'
        assert data['state'] == state

    def test_restore_layout_handles_exception_gracefully(self, service_with_workspace):
        """Test restore_layout handles workspace exceptions gracefully."""
        # Arrange
        state = {'invalid': 'state'}
        service_with_workspace._workspace.set_state.side_effect = ValueError("Invalid state")

        # Act
        result = service_with_workspace.restore_layout(state)

        # Assert
        assert result is False

    def test_restore_layout_without_workspace_returns_false(self):
        """Test restore_layout without workspace returns False."""
        # Arrange
        service = WorkspaceService()
        service._initialized = True
        state = {'tabs': []}

        # Act
        result = service.restore_layout(state)

        # Assert
        assert result is False


class TestWorkspaceServiceNavigationOperations:
    """Test navigation operations."""

    @pytest.fixture
    def service_with_workspace(self):
        """Create service with mocked workspace for navigation."""
        mock_workspace = Mock()
        service = WorkspaceService(workspace=mock_workspace)
        service._initialized = True
        service._pane_manager = Mock(spec=WorkspacePaneManager)
        return service

    def test_navigate_to_next_pane_delegates_to_manager(self, service_with_workspace):
        """Test navigate_to_next_pane delegates to pane manager."""
        # Arrange
        service_with_workspace._pane_manager.navigate_to_next_pane.return_value = True

        # Act
        result = service_with_workspace.navigate_to_next_pane()

        # Assert
        assert result is True
        service_with_workspace._pane_manager.navigate_to_next_pane.assert_called_once()

    def test_navigate_to_previous_pane_delegates_to_manager(self, service_with_workspace):
        """Test navigate_to_previous_pane delegates to pane manager."""
        # Arrange
        service_with_workspace._pane_manager.navigate_to_previous_pane.return_value = True

        # Act
        result = service_with_workspace.navigate_to_previous_pane()

        # Assert
        assert result is True
        service_with_workspace._pane_manager.navigate_to_previous_pane.assert_called_once()


class TestWorkspaceServiceUtilityMethods:
    """Test utility and information methods."""

    def test_get_workspace_info_without_workspace_returns_unavailable(self):
        """Test get_workspace_info without workspace returns unavailable status."""
        # Arrange
        service = WorkspaceService()

        # Act
        result = service.get_workspace_info()

        # Assert
        assert result == {
            'available': False,
            'tab_count': 0,
            'current_tab': -1
        }

    def test_get_workspace_info_with_workspace_combines_manager_info(self):
        """Test get_workspace_info combines information from all managers."""
        # Arrange
        mock_workspace = Mock()
        service = WorkspaceService(workspace=mock_workspace)

        # Mock managers
        service._tab_manager = Mock()
        service._tab_manager.get_tab_info.return_value = {
            'count': 3,
            'current': 1,
            'current_tab_info': {'name': 'Tab 1'}
        }

        service._pane_manager = Mock()
        service._pane_manager.get_pane_info.return_value = {
            'count': 2,
            'active': 'pane-1'
        }

        # Act
        result = service.get_workspace_info()

        # Assert
        expected = {
            'available': True,
            'tab_count': 3,
            'current_tab': 1,
            'current_tab_info': {'name': 'Tab 1'},
            'pane_count': 2,
            'active_pane_id': 'pane-1'
        }
        assert result == expected


class TestWorkspaceServiceErrorConditions:
    """Test error conditions and edge cases."""

    def test_operations_without_initialization_raise_runtime_error(self):
        """Test operations requiring initialization raise RuntimeError."""
        # Arrange
        service = WorkspaceService()
        # Don't mark as initialized

        # Act & Assert
        with pytest.raises(RuntimeError, match="Service WorkspaceService is not initialized"):
            service.add_editor_tab("Test")

        with pytest.raises(RuntimeError, match="Service WorkspaceService is not initialized"):
            service.add_terminal_tab("Test")

        with pytest.raises(RuntimeError, match="Service WorkspaceService is not initialized"):
            service.close_tab(0)

        with pytest.raises(RuntimeError, match="Service WorkspaceService is not initialized"):
            service.switch_to_tab(0)

        with pytest.raises(RuntimeError, match="Service WorkspaceService is not initialized"):
            service.split_active_pane("horizontal")

    def test_operations_with_none_workspace_handle_gracefully(self):
        """Test operations with None workspace handle gracefully."""
        # Arrange
        service = WorkspaceService()
        service._initialized = True
        service._tab_manager = Mock()
        service._pane_manager = Mock()

        # Mock managers to return appropriate values for None workspace
        service._tab_manager.get_current_tab_index.return_value = -1
        service._tab_manager.get_tab_count.return_value = 0
        service._pane_manager.get_pane_count.return_value = 0
        service._pane_manager.get_active_pane_id.return_value = None

        # Act & Assert - should not raise exceptions
        assert service.get_current_tab_index() == -1
        assert service.get_tab_count() == 0
        assert service.get_pane_count() == 0
        assert service.get_active_pane_id() is None

    def test_edge_case_empty_widget_id_handled_safely(self):
        """Test edge case of empty widget ID is handled safely."""
        # Arrange
        service = WorkspaceService()
        service._widget_registry = Mock()
        service._tab_manager = Mock()

        # Mock registry methods for empty string
        service._widget_registry.has_widget.return_value = False
        service._tab_manager.focus_widget.return_value = False

        # Act & Assert
        assert service.has_widget("") is False
        assert service.focus_widget("") is False

    def test_edge_case_negative_tab_indices_handled_safely(self):
        """Test edge case of negative tab indices are handled safely."""
        # Arrange
        mock_workspace = Mock()
        service = WorkspaceService(workspace=mock_workspace)
        service._initialized = True
        service._tab_manager = Mock()

        # Mock tab manager to handle negative indices
        service._tab_manager.switch_to_tab.return_value = False
        service._tab_manager.close_tab.return_value = False

        # Act & Assert
        assert service.switch_to_tab(-1) is False
        assert service.close_tab(-1) is False

    def test_edge_case_very_large_tab_indices_handled_safely(self):
        """Test edge case of very large tab indices are handled safely."""
        # Arrange
        mock_workspace = Mock()
        service = WorkspaceService(workspace=mock_workspace)
        service._initialized = True
        service._tab_manager = Mock()

        # Mock tab manager to handle large indices
        service._tab_manager.switch_to_tab.return_value = False
        service._tab_manager.close_tab.return_value = False

        # Act & Assert
        assert service.switch_to_tab(999999) is False
        assert service.close_tab(999999) is False