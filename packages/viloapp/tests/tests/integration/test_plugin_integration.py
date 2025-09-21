"""Integration tests for plugin interactions."""

from unittest.mock import Mock, patch
import tempfile
from pathlib import Path

# Mock the SDK imports to avoid dependency issues in tests
with patch.dict('sys.modules', {
    'viloapp_sdk': Mock(),
    'viloapp_sdk.base': Mock(),
    'viloapp_sdk.interfaces': Mock(),
    'viloapp_sdk.metadata': Mock(),
    'viloapp_sdk.context': Mock(),
}):
    from packages.viloxterm.src.viloxterm.plugin import TerminalPlugin
    from packages.viloedit.src.viloedit.plugin import EditorPlugin


class TestPluginIntegration:
    """Test integration between terminal and editor plugins."""

    def setup_method(self):
        """Setup test environment."""
        self.terminal_plugin = TerminalPlugin()
        self.editor_plugin = EditorPlugin()
        self.mock_context = Mock()

        # Mock workspace service
        self.mock_workspace = Mock()
        self.mock_context.get_service.return_value = self.mock_workspace

    def test_terminal_opening_file_in_editor(self):
        """Test terminal plugin opening a file in editor."""
        # Setup plugins
        self.terminal_plugin.context = self.mock_context
        self.editor_plugin.context = self.mock_context

        # Create a test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("print('Hello from terminal')")
            test_file = f.name

        try:
            # Simulate terminal command to open file in editor
            result = self.editor_plugin._open_file({"path": test_file})

            # Verify file was opened
            assert result["success"] is True
            assert result["path"] == test_file

            # Verify workspace was called to add widget
            self.mock_workspace.add_widget.assert_called_once()

        finally:
            Path(test_file).unlink()

    def test_workspace_integration(self):
        """Test plugins working together in workspace."""
        # Setup plugins
        self.terminal_plugin.context = self.mock_context
        self.editor_plugin.context = self.mock_context

        # Test that both plugins can register widgets
        terminal_result = self.terminal_plugin._create_new_terminal({})
        editor_result = self.editor_plugin._new_file({})

        assert terminal_result["success"] is True
        assert editor_result["success"] is True

        # Verify workspace service was called for both
        assert self.mock_workspace.add_widget.call_count == 2

    def test_plugin_metadata_compatibility(self):
        """Test plugin metadata compatibility."""
        terminal_plugin = TerminalPlugin()
        editor_plugin = EditorPlugin()

        terminal_meta = terminal_plugin.get_metadata()
        editor_meta = editor_plugin.get_metadata()

        # Both plugins should target the same viloapp version
        assert terminal_meta.engines["viloapp"] == editor_meta.engines["viloapp"]

        # Both should have valid metadata
        assert terminal_meta.id is not None
        assert editor_meta.id is not None
        assert terminal_meta.version is not None
        assert editor_meta.version is not None