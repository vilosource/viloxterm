"""Tests for editor plugin."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path

from viloedit.plugin import EditorPlugin
from viloedit.editor import CodeEditor


class TestEditorPlugin:
    """Test editor plugin functionality."""

    def setup_method(self):
        """Setup test environment."""
        self.plugin = EditorPlugin()
        self.mock_context = Mock()

    def test_plugin_metadata(self):
        """Test plugin metadata."""
        metadata = self.plugin.get_metadata()

        assert metadata.id == "viloedit"
        assert metadata.name == "ViloEdit"
        assert metadata.version == "1.0.0"
        assert "Editor" in metadata.categories
        assert len(metadata.contributes["commands"]) == 5
        assert len(metadata.contributes["languages"]) == 4

    def test_plugin_activation(self):
        """Test plugin activation."""
        # Mock services
        command_service = Mock()
        workspace_service = Mock()
        notification_service = Mock()

        self.mock_context.get_service.side_effect = lambda name: {
            "command": command_service,
            "workspace": workspace_service,
            "notification": notification_service
        }.get(name)

        # Activate plugin
        self.plugin.activate(self.mock_context)

        # Verify services were called
        assert self.mock_context.get_service.called
        assert self.plugin.context == self.mock_context

    @patch('viloedit.widget.CodeEditor')
    def test_new_file_command(self, mock_editor_class):
        """Test new file command."""
        # Setup mocks
        mock_editor = Mock()
        mock_editor_class.return_value = mock_editor

        workspace_service = Mock()
        self.mock_context.get_service.return_value = workspace_service
        self.plugin.context = self.mock_context

        # Execute command
        result = self.plugin._new_file({})

        # Verify result
        assert result["success"] is True
        workspace_service.add_widget.assert_called_once()

    @patch('viloedit.widget.CodeEditor')
    def test_open_file_command(self, mock_editor_class):
        """Test open file command."""
        # Setup mocks
        mock_editor = Mock()
        mock_editor_class.return_value = mock_editor

        # Create a test file
        test_file = Path("test_file.py")
        test_file.write_text("print('hello world')")

        try:
            # Setup mocks
            workspace_service = Mock()
            self.mock_context.get_service.return_value = workspace_service
            self.plugin.context = self.mock_context

            # Execute command
            result = self.plugin._open_file({"path": str(test_file)})

            # Verify result
            assert result["success"] is True
            assert result["path"] == str(test_file)
            workspace_service.add_widget.assert_called_once()
            mock_editor.load_file.assert_called_once_with(str(test_file))

        finally:
            if test_file.exists():
                test_file.unlink()

    def test_save_file_command(self):
        """Test save file command."""
        # Setup mocks
        workspace_service = Mock()
        editor = Mock(spec=CodeEditor)
        editor.save_file.return_value = True
        workspace_service.get_active_widget.return_value = editor

        self.mock_context.get_service.return_value = workspace_service
        self.plugin.context = self.mock_context

        # Execute command
        result = self.plugin._save_file({})

        # Verify result
        assert result["success"] is True
        editor.save_file.assert_called_once()

    def test_close_editor_command(self):
        """Test close editor command."""
        # Setup mocks
        workspace_service = Mock()
        editor = Mock(spec=CodeEditor)
        editor.document.return_value.isModified.return_value = False
        editor.file_path = None
        workspace_service.get_active_widget.return_value = editor

        self.mock_context.get_service.return_value = workspace_service
        self.plugin.context = self.mock_context

        # Execute command
        result = self.plugin._close_editor({})

        # Verify result
        assert result["success"] is True
        workspace_service.remove_widget.assert_called_once_with(editor)

    def test_command_routing(self):
        """Test command routing."""
        # Test each command ID
        commands = [
            "editor.new",
            "editor.open",
            "editor.save",
            "editor.saveAs",
            "editor.close"
        ]

        for cmd in commands:
            # Mock the specific command method
            method_name = f"_{cmd.replace('.', '_')}"
            if cmd == "editor.saveAs":
                method_name = "_save_file_as"
            elif cmd == "editor.close":
                method_name = "_close_editor"
            elif cmd == "editor.new":
                method_name = "_new_file"
            elif cmd == "editor.open":
                method_name = "_open_file"
            elif cmd == "editor.save":
                method_name = "_save_file"

            setattr(self.plugin, method_name, Mock(return_value={"success": True}))

            # Test command routing
            result = self.plugin.on_command(cmd, {})
            assert result["success"] is True