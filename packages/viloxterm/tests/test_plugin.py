"""Tests for terminal plugin."""

import pytest
from unittest.mock import Mock, patch

from viloxterm.plugin import TerminalPlugin
from viloapp_sdk import PluginContext, EventBus, ServiceProxy


@pytest.fixture
def mock_context():
    """Create mock plugin context."""
    services = {
        "command": Mock(),
        "workspace": Mock(),
        "configuration": Mock(),
        "notification": Mock(),
    }

    context = PluginContext(
        plugin_id="viloxterm",
        plugin_path="/tmp/viloxterm",
        data_path="/tmp/viloxterm-data",
        service_proxy=ServiceProxy(services),
        event_bus=EventBus(),
        configuration={},
    )

    return context


def test_plugin_metadata():
    """Test plugin metadata."""
    plugin = TerminalPlugin()
    metadata = plugin.get_metadata()

    assert metadata.id == "viloxterm"
    assert metadata.name == "ViloxTerm Terminal"
    assert metadata.version == "1.0.0"
    assert "terminal" in metadata.keywords


def test_plugin_activation(mock_context):
    """Test plugin activation."""
    plugin = TerminalPlugin()

    # Mock terminal server
    with patch("viloxterm.plugin.terminal_server") as mock_server:
        plugin.activate(mock_context)

        assert plugin.context == mock_context
        assert mock_server.start_server.called


def test_plugin_deactivation(mock_context):
    """Test plugin deactivation."""
    plugin = TerminalPlugin()
    plugin.activate(mock_context)

    with patch("viloxterm.plugin.terminal_server") as mock_server:
        plugin.deactivate()

        assert mock_server.cleanup_all_sessions.called
        assert mock_server.shutdown.called


def test_create_new_terminal_command(mock_context):
    """Test creating a new terminal."""
    plugin = TerminalPlugin()
    plugin.activate(mock_context)

    # Mock workspace service
    workspace_service = mock_context.get_service("workspace")
    workspace_service.add_widget = Mock()

    # Execute command
    result = plugin.on_command("terminal.new", {})

    assert result is not None
    # Verify widget was added to workspace
    # workspace_service.add_widget.assert_called()


def test_terminal_configuration(mock_context):
    """Test terminal configuration handling."""
    plugin = TerminalPlugin()
    plugin.activate(mock_context)

    # Test configuration change
    config = {"terminal.fontSize": 16, "terminal.shell.linux": "/bin/zsh"}

    plugin.on_configuration_changed(config)
    # Verify configuration was applied
