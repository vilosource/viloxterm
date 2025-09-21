#!/usr/bin/env python3
"""
Test suite for the service layer implementation.
"""

from unittest.mock import Mock, patch

import pytest

from viloapp.services.base import Service
from viloapp.services.editor_service import EditorService
from viloapp.services.service_locator import ServiceLocator
from viloapp.services.terminal_service import TerminalService
from viloapp.services.ui_service import UIService
from viloapp.services.workspace_service import WorkspaceService


class TestServiceBase:
    """Test the base Service class."""

    def test_service_initialization(self):
        """Test service initialization."""

        # Create a concrete service class for testing
        class TestService(Service):
            def initialize(self, context):
                super().initialize(context)

            def cleanup(self):
                super().cleanup()

        service = TestService("TestService")
        assert service.name == "TestService"
        assert not service.is_initialized

        # Initialize the service
        context = {"test": "value"}
        service.initialize(context)
        assert service.is_initialized
        assert service.get_context_value("test") == "value"

        # Cleanup
        service.cleanup()
        assert not service.is_initialized

    def test_service_event_notification(self):
        """Test service event notification."""

        class TestService(Service):
            def initialize(self, context):
                super().initialize(context)

            def cleanup(self):
                super().cleanup()

        service = TestService()

        # Add observer
        received_events = []

        def observer(event):
            received_events.append(event)

        service.add_observer(observer)

        # Notify event
        service.notify("test_event", {"data": "test"})

        # Check event was received
        assert len(received_events) == 1
        assert received_events[0].name == "test_event"
        assert received_events[0].data == {"data": "test"}
        assert received_events[0].source == service.name

        # Remove observer
        service.remove_observer(observer)
        service.notify("another_event", {})
        assert len(received_events) == 1  # No new events


class TestServiceLocator:
    """Test the ServiceLocator singleton."""

    def test_singleton_pattern(self):
        """Test that ServiceLocator is a singleton."""
        locator1 = ServiceLocator.get_instance()
        locator2 = ServiceLocator.get_instance()
        assert locator1 is locator2

    def test_service_registration(self):
        """Test service registration and retrieval."""
        locator = ServiceLocator.get_instance()
        locator.clear()  # Clear any existing services

        # Create mock service
        mock_service = Mock(spec=WorkspaceService)
        mock_service.name = "WorkspaceService"

        # Register service
        locator.register(WorkspaceService, mock_service)

        # Retrieve by type
        retrieved = locator.get(WorkspaceService)
        assert retrieved is mock_service

        # Retrieve by name
        retrieved_by_name = locator.get_by_name("WorkspaceService")
        assert retrieved_by_name is mock_service

        # Check has_service
        assert locator.has_service(WorkspaceService)

        # Clear
        locator.clear()
        assert not locator.has_service(WorkspaceService)

    def test_required_service(self):
        """Test getting required service."""
        locator = ServiceLocator.get_instance()
        locator.clear()

        # Should raise when service not found
        with pytest.raises(RuntimeError, match="Required service not found"):
            locator.get_required(WorkspaceService)

        # Should return when service exists
        mock_service = Mock(spec=WorkspaceService)
        locator.register(WorkspaceService, mock_service)

        retrieved = locator.get_required(WorkspaceService)
        assert retrieved is mock_service

        locator.clear()


class TestWorkspaceService:
    """Test the WorkspaceService."""

    @pytest.fixture
    def workspace_service(self):
        """Create workspace service with mock workspace."""
        mock_workspace = Mock()
        mock_workspace.add_editor_tab = Mock(return_value=0)
        mock_workspace.add_terminal_tab = Mock(return_value=1)
        mock_workspace.tab_widget = Mock()
        mock_workspace.tab_widget.currentIndex = Mock(return_value=0)
        mock_workspace.tab_widget.count = Mock(return_value=2)

        service = WorkspaceService(mock_workspace)
        service.initialize({})
        return service, mock_workspace

    def test_add_editor_tab(self, workspace_service):
        """Test adding editor tab."""
        service, mock_workspace = workspace_service

        # Add tab without name
        index = service.add_editor_tab()
        assert index == 0
        mock_workspace.add_editor_tab.assert_called_once()

        # Add tab with name
        mock_workspace.add_editor_tab.reset_mock()
        mock_workspace.add_editor_tab.return_value = 1
        index = service.add_editor_tab("Custom Editor")
        assert index == 1
        mock_workspace.add_editor_tab.assert_called_with("Custom Editor")

    def test_add_terminal_tab(self, workspace_service):
        """Test adding terminal tab."""
        service, mock_workspace = workspace_service

        index = service.add_terminal_tab("Terminal 1")
        assert index == 1
        mock_workspace.add_terminal_tab.assert_called_with("Terminal 1")

    def test_get_tab_count(self, workspace_service):
        """Test getting tab count."""
        service, mock_workspace = workspace_service

        count = service.get_tab_count()
        assert count == 2
        mock_workspace.tab_widget.count.assert_called_once()

    def test_switch_to_tab(self, workspace_service):
        """Test switching tabs."""
        service, mock_workspace = workspace_service

        # Valid tab index
        success = service.switch_to_tab(1)
        assert success is True, "Failed to switch to valid tab index 1"
        mock_workspace.tab_widget.setCurrentIndex.assert_called_with(1)

        # Invalid tab index
        mock_workspace.tab_widget.setCurrentIndex.reset_mock()
        success = service.switch_to_tab(10)
        assert (
            success is False
        ), "Expected failure when switching to invalid tab index 10"
        mock_workspace.tab_widget.setCurrentIndex.assert_not_called()


class TestUIService:
    """Test the UIService."""

    @pytest.fixture
    def ui_service(self):
        """Create UI service with mock main window."""
        mock_main_window = Mock()
        mock_main_window.status_bar = Mock()
        mock_main_window.sidebar = Mock()
        mock_main_window.isFullScreen = Mock(return_value=False)

        service = UIService(mock_main_window)
        service.initialize({})
        return service, mock_main_window

    @patch("viloapp.ui.icon_manager.get_icon_manager")
    def test_toggle_theme(self, mock_get_icon_manager, ui_service):
        """Test theme toggling."""
        service, mock_main_window = ui_service

        # Setup mock icon manager
        mock_icon_manager = Mock()
        mock_icon_manager.theme = "dark"
        mock_get_icon_manager.return_value = mock_icon_manager

        # Toggle theme
        new_theme = service.toggle_theme()
        assert new_theme == "dark"
        mock_icon_manager.toggle_theme.assert_called_once()

    def test_set_sidebar_view(self, ui_service):
        """Test setting sidebar view."""
        service, mock_main_window = ui_service

        # Valid view
        success = service.set_sidebar_view("explorer")
        assert success is True, "Failed to set sidebar view to 'explorer'"
        mock_main_window.sidebar.set_current_view.assert_called_with("explorer")

        # Invalid view
        success = service.set_sidebar_view("invalid_view")
        assert success is False, "Expected failure when setting invalid sidebar view"

    def test_toggle_fullscreen(self, ui_service):
        """Test fullscreen toggling."""
        service, mock_main_window = ui_service

        # Enter fullscreen
        mock_main_window.isFullScreen.return_value = False
        is_fullscreen = service.toggle_fullscreen()
        assert is_fullscreen is True, "Expected fullscreen mode to be enabled"
        mock_main_window.showFullScreen.assert_called_once()

        # Exit fullscreen
        mock_main_window.isFullScreen.return_value = True
        is_fullscreen = service.toggle_fullscreen()
        assert is_fullscreen is False, "Expected fullscreen mode to be disabled"
        mock_main_window.showNormal.assert_called_once()


class TestTerminalService:
    """Test the TerminalService."""

    @pytest.fixture
    def terminal_service(self):
        """Create terminal service."""
        service = TerminalService()
        # Don't initialize with real terminal server
        service._terminal_server = Mock()
        service._terminal_server.is_running = Mock(return_value=False)
        service._terminal_server.port = 5000
        service._initialized = True
        return service

    def test_start_server(self, terminal_service):
        """Test starting terminal server."""
        service = terminal_service

        # Start server
        success = service.start_server()
        assert success is True, "Failed to start terminal server"
        service._terminal_server.start_server.assert_called_once()

    def test_create_session(self, terminal_service):
        """Test creating terminal session."""
        service = terminal_service
        service._terminal_server.is_running.return_value = True

        # Create session
        session_id = service.create_session(command="bash")
        assert (
            isinstance(session_id, str) and len(session_id) > 0
        ), f"Expected valid session ID string, got {session_id}"
        assert session_id in service._sessions

        # Check session info
        info = service.get_session_info(session_id)
        assert info["command"] == "bash"
        assert info["active"]

    def test_close_session(self, terminal_service):
        """Test closing terminal session."""
        service = terminal_service
        service._terminal_server.is_running.return_value = True

        # Create and close session
        session_id = service.create_session()
        assert session_id in service._sessions

        success = service.close_session(session_id)
        assert success is True, f"Failed to close terminal session {session_id}"
        assert session_id not in service._sessions


class TestEditorService:
    """Test the EditorService."""

    @pytest.fixture
    def editor_service(self):
        """Create editor service with mock editor."""
        service = EditorService()
        service.initialize({})

        # Create mock editor widget
        mock_editor = Mock()
        mock_editor.toPlainText = Mock(return_value="test content")
        mock_editor.setPlainText = Mock()
        mock_editor.insertPlainText = Mock()
        mock_editor.cut = Mock()
        mock_editor.copy = Mock()
        mock_editor.paste = Mock()
        mock_editor.selectAll = Mock()
        mock_editor.undo = Mock()
        mock_editor.redo = Mock()

        # Register the editor
        service.register_editor("editor1", mock_editor)

        return service, mock_editor

    def test_register_editor(self, editor_service):
        """Test editor registration."""
        service, mock_editor = editor_service

        assert service.get_editor_count() == 1
        assert "editor1" in service.get_all_editor_ids()
        assert service.get_active_editor() is mock_editor

    def test_text_operations(self, editor_service):
        """Test text operations."""
        service, mock_editor = editor_service

        # Get text
        text = service.get_text()
        assert text == "test content"

        # Set text
        success = service.set_text("new content")
        assert success is True, "Failed to set editor text"
        mock_editor.setPlainText.assert_called_with("new content")

        # Insert text
        success = service.insert_text("inserted")
        assert success is True, "Failed to insert text into editor"
        mock_editor.insertPlainText.assert_called_with("inserted")

    def test_clipboard_operations(self, editor_service):
        """Test clipboard operations."""
        service, mock_editor = editor_service

        # Cut
        success = service.cut()
        assert success is True, "Failed to cut text from editor"
        mock_editor.cut.assert_called_once()

        # Copy
        success = service.copy()
        assert success is True, "Failed to copy text from editor"
        mock_editor.copy.assert_called_once()

        # Paste
        success = service.paste()
        assert success is True, "Failed to paste text into editor"
        mock_editor.paste.assert_called_once()

    def test_undo_redo(self, editor_service):
        """Test undo/redo operations."""
        service, mock_editor = editor_service

        # Undo
        success = service.undo()
        assert success is True, "Failed to undo in editor"
        mock_editor.undo.assert_called_once()

        # Redo
        success = service.redo()
        assert success is True, "Failed to redo in editor"
        mock_editor.redo.assert_called_once()


class TestServiceIntegration:
    """Test service integration with commands."""

    def test_command_context_service_access(self):
        """Test accessing services through CommandContext."""
        from viloapp.core.commands.base import CommandContext

        # Create context
        context = CommandContext()

        # Mock ServiceLocator
        with patch("viloapp.services.service_locator.ServiceLocator") as MockServiceLocator:
            mock_locator = Mock()
            MockServiceLocator.get_instance.return_value = mock_locator

            # Mock service
            mock_service = Mock(spec=WorkspaceService)
            mock_locator.get.return_value = mock_service

            # Get service through context
            service = context.get_service(WorkspaceService)
            assert service is mock_service
            mock_locator.get.assert_called_with(WorkspaceService)

            # Get required service
            required_service = context.get_required_service(WorkspaceService)
            assert required_service is mock_service

            # Test missing required service
            mock_locator.get.return_value = None
            with pytest.raises(RuntimeError, match="Required service not found"):
                context.get_required_service(UIService)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
