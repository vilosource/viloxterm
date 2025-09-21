"""Tests for plugin interface."""

from viloapp_sdk import IPlugin, PluginMetadata, PluginCapability
from viloapp_sdk.context import PluginContext
from viloapp_sdk.service import ServiceProxy
from viloapp_sdk.events import EventBus
from pathlib import Path


class TestPlugin(IPlugin):
    """Test plugin implementation."""

    def __init__(self):
        self.activated = False
        self.deactivated = False

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            id="test-plugin",
            name="Test Plugin",
            version="1.0.0",
            description="A test plugin",
            author="Test Author",
            capabilities=[PluginCapability.WIDGETS],
        )

    def activate(self, context):
        self.activated = True
        self.context = context

    def deactivate(self):
        self.deactivated = True


def test_plugin_metadata():
    """Test plugin metadata."""
    plugin = TestPlugin()
    metadata = plugin.get_metadata()

    assert metadata.id == "test-plugin"
    assert metadata.name == "Test Plugin"
    assert metadata.version == "1.0.0"
    assert metadata.description == "A test plugin"
    assert metadata.author == "Test Author"
    assert PluginCapability.WIDGETS in metadata.capabilities


def test_plugin_lifecycle():
    """Test plugin lifecycle."""
    plugin = TestPlugin()

    assert not plugin.activated
    assert not plugin.deactivated

    # Create mock context
    context = PluginContext(
        plugin_id="test-plugin",
        plugin_path=Path("/tmp/test-plugin"),
        data_path=Path("/tmp/test-plugin-data"),
        service_proxy=ServiceProxy({}),
        event_bus=EventBus(),
        configuration={},
    )

    # Activate plugin
    plugin.activate(context)
    assert plugin.activated
    assert plugin.context == context

    # Deactivate plugin
    plugin.deactivate()
    assert plugin.deactivated


def test_metadata_validation():
    """Test metadata validation."""
    # Valid metadata
    metadata = PluginMetadata(
        id="valid-plugin",
        name="Valid Plugin",
        version="1.0.0",
        description="A valid plugin",
        author="Author",
    )

    errors = metadata.validate()
    assert len(errors) == 0

    # Invalid metadata (empty ID)
    metadata = PluginMetadata(
        id="",
        name="Invalid Plugin",
        version="1.0.0",
        description="An invalid plugin",
        author="Author",
    )

    errors = metadata.validate()
    assert len(errors) > 0
    assert "Plugin ID is required" in errors

    # Invalid metadata (bad ID format)
    metadata = PluginMetadata(
        id="invalid_plugin",  # Underscore not allowed
        name="Invalid Plugin",
        version="1.0.0",
        description="An invalid plugin",
        author="Author",
    )

    errors = metadata.validate()
    assert any("alphanumeric with hyphens" in error for error in errors)
