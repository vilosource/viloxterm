"""Tests for plugin system."""

import pytest
from pathlib import Path
from unittest.mock import Mock

from core.plugin_system import PluginManager, PluginRegistry
from viloapp_sdk import IPlugin, PluginMetadata, EventBus

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
            description="Test plugin",
            author="Test"
        )

    def activate(self, context):
        self.activated = True

    def deactivate(self):
        self.deactivated = True

@pytest.fixture
def plugin_manager():
    """Create plugin manager for testing."""
    event_bus = EventBus()
    services = {
        'command': Mock(),
        'configuration': Mock(),
        'workspace': Mock()
    }
    return PluginManager(event_bus, services)

def test_plugin_discovery(plugin_manager):
    """Test plugin discovery."""
    # Mock discovery
    plugin_manager.discovery.discover_all = Mock(return_value=[])

    # Discover plugins
    plugins = plugin_manager.discover_plugins()
    assert isinstance(plugins, list)

def test_plugin_loading(plugin_manager):
    """Test plugin loading."""
    # Register test plugin
    from core.plugin_system.plugin_registry import PluginInfo
    from viloapp_sdk import LifecycleState

    plugin_info = PluginInfo(
        metadata=PluginMetadata(
            id="test-plugin",
            name="Test Plugin",
            version="1.0.0",
            description="Test",
            author="Test"
        ),
        path=Path("test"),
        state=LifecycleState.DISCOVERED
    )

    plugin_manager.registry.register(plugin_info)

    # Mock loader
    plugin_manager.loader.load_plugin = Mock(return_value=True)

    # Load plugin
    assert plugin_manager.load_plugin("test-plugin")

def test_plugin_activation(plugin_manager):
    """Test plugin activation."""
    # Setup test plugin
    test_plugin = TestPlugin()

    # Mock getting plugin
    plugin_manager.get_plugin = Mock(return_value=test_plugin)
    plugin_manager.loader.activate_plugin = Mock(return_value=True)

    # Activate
    assert plugin_manager.activate_plugin("test-plugin")

def test_dependency_resolution():
    """Test dependency resolution."""
    from core.plugin_system import DependencyResolver

    registry = PluginRegistry()
    resolver = DependencyResolver(registry)

    # Create plugins with dependencies
    from core.plugin_system.plugin_registry import PluginInfo
    from viloapp_sdk import LifecycleState

    plugin_a = PluginInfo(
        metadata=PluginMetadata(
            id="plugin-a",
            name="Plugin A",
            version="1.0.0",
            description="A",
            author="Test",
            dependencies=[]
        ),
        path=Path("a"),
        state=LifecycleState.DISCOVERED
    )

    plugin_b = PluginInfo(
        metadata=PluginMetadata(
            id="plugin-b",
            name="Plugin B",
            version="1.0.0",
            description="B",
            author="Test",
            dependencies=["plugin-a@>=1.0.0"]
        ),
        path=Path("b"),
        state=LifecycleState.DISCOVERED
    )

    registry.register(plugin_a)
    registry.register(plugin_b)

    # Resolve dependencies
    load_order, unmet = resolver.resolve_dependencies()

    # Check load order (A should come before B)
    assert load_order.index("plugin-a") < load_order.index("plugin-b")
    assert len(unmet) == 0