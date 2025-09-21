"""Plugin Test Harness for comprehensive plugin testing."""

import unittest
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Type, Callable
from unittest.mock import Mock, MagicMock

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtTest import QTest

from ..interfaces import IPlugin
from ..widget import IWidget
from ..service import IService
from ..context import PluginContext
from .mock_host import MockPluginHost
from .fixtures import (
    mock_plugin_context,
    mock_services,
    mock_event_bus,
    temp_plugin_dir,
)


class PluginTestCase(unittest.TestCase):
    """Base test case for plugin testing."""

    def setUp(self) -> None:
        """Set up test environment."""
        super().setUp()

        # Ensure QApplication exists for Qt tests
        if not QApplication.instance():
            self.app = QApplication(sys.argv)
            self.app_created = True
        else:
            self.app = QApplication.instance()
            self.app_created = False

        # Create mock host and context
        self.mock_host = MockPluginHost()
        self.plugin_context = self.mock_host.create_context("test.plugin")

        # Store original plugin instance
        self.plugin: Optional[IPlugin] = None

    def tearDown(self) -> None:
        """Clean up test environment."""
        # Deactivate plugin if it was activated
        if self.plugin and hasattr(self.plugin, 'deactivate'):
            try:
                self.plugin.deactivate()
            except Exception:
                pass

        # Clean up QApplication if we created it
        if self.app_created and self.app:
            self.app.quit()

        super().tearDown()

    def create_plugin(self, plugin_class: Type[IPlugin], **kwargs) -> IPlugin:
        """Create and activate a plugin for testing.

        Args:
            plugin_class: Plugin class to instantiate
            **kwargs: Additional arguments for plugin constructor

        Returns:
            Activated plugin instance
        """
        self.plugin = plugin_class(**kwargs)
        self.plugin.activate(self.plugin_context)
        return self.plugin

    def assert_plugin_activated(self, plugin: IPlugin) -> None:
        """Assert that a plugin is properly activated.

        Args:
            plugin: Plugin to check
        """
        self.assertIsNotNone(plugin)
        # Check if plugin has a context (indicating activation)
        if hasattr(plugin, '_context'):
            self.assertIsNotNone(plugin._context)

    def assert_plugin_deactivated(self, plugin: IPlugin) -> None:
        """Assert that a plugin is properly deactivated.

        Args:
            plugin: Plugin to check
        """
        self.assertIsNotNone(plugin)
        # Check if plugin context is cleared
        if hasattr(plugin, '_context'):
            self.assertIsNone(plugin._context)

    def get_mock_service(self, service_type: Type) -> Mock:
        """Get a mock service from the plugin context.

        Args:
            service_type: Type of service to get

        Returns:
            Mock service instance
        """
        return self.plugin_context.get_service(service_type)

    def simulate_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Simulate an event being fired.

        Args:
            event_type: Type of event
            data: Event data
        """
        event_bus = self.plugin_context.get_event_bus()
        event_bus.emit(event_type, data)

    def wait_for_signal(self, signal, timeout: int = 1000) -> bool:
        """Wait for a Qt signal to be emitted.

        Args:
            signal: Qt signal to wait for
            timeout: Timeout in milliseconds

        Returns:
            True if signal was emitted within timeout
        """
        from PySide6.QtTest import QSignalSpy
        spy = QSignalSpy(signal)
        return spy.wait(timeout)


class WidgetTestCase(PluginTestCase):
    """Specialized test case for widget testing."""

    def setUp(self) -> None:
        """Set up widget test environment."""
        super().setUp()
        self.widget_factory: Optional[IWidget] = None
        self.widget_instances: Dict[str, QWidget] = {}

    def tearDown(self) -> None:
        """Clean up widget test environment."""
        # Destroy all widget instances
        for instance_id, widget in self.widget_instances.items():
            try:
                if self.widget_factory:
                    self.widget_factory.destroy_instance(instance_id)
                widget.deleteLater()
            except Exception:
                pass

        super().tearDown()

    def create_widget_factory(self, factory_class: Type[IWidget], **kwargs) -> IWidget:
        """Create a widget factory for testing.

        Args:
            factory_class: Widget factory class
            **kwargs: Additional arguments for factory constructor

        Returns:
            Widget factory instance
        """
        self.widget_factory = factory_class(**kwargs)
        return self.widget_factory

    def create_widget_instance(self, instance_id: str = "test-widget") -> QWidget:
        """Create a widget instance for testing.

        Args:
            instance_id: Unique instance identifier

        Returns:
            Widget instance
        """
        if not self.widget_factory:
            raise ValueError("Widget factory not created. Call create_widget_factory first.")

        widget = self.widget_factory.create_instance(instance_id)
        self.widget_instances[instance_id] = widget
        return widget

    def assert_widget_created(self, widget: QWidget) -> None:
        """Assert that a widget was created properly.

        Args:
            widget: Widget to check
        """
        self.assertIsNotNone(widget)
        self.assertIsInstance(widget, QWidget)

    def assert_widget_visible(self, widget: QWidget) -> None:
        """Assert that a widget is visible.

        Args:
            widget: Widget to check
        """
        self.assertTrue(widget.isVisible())

    def assert_widget_hidden(self, widget: QWidget) -> None:
        """Assert that a widget is hidden.

        Args:
            widget: Widget to check
        """
        self.assertFalse(widget.isVisible())

    def click_widget(self, widget: QWidget) -> None:
        """Simulate clicking a widget.

        Args:
            widget: Widget to click
        """
        QTest.mouseClick(widget, 1)  # Left click

    def type_text(self, widget: QWidget, text: str) -> None:
        """Simulate typing text into a widget.

        Args:
            widget: Widget to type into
            text: Text to type
        """
        QTest.keyClicks(widget, text)

    def wait_for_widget_update(self, timeout: int = 100) -> None:
        """Wait for widget updates to complete.

        Args:
            timeout: Timeout in milliseconds
        """
        QTest.qWait(timeout)


class ServiceTestCase(PluginTestCase):
    """Specialized test case for service testing."""

    def setUp(self) -> None:
        """Set up service test environment."""
        super().setUp()
        self.service: Optional[IService] = None

    def tearDown(self) -> None:
        """Clean up service test environment."""
        if self.service and hasattr(self.service, 'dispose'):
            try:
                self.service.dispose()
            except Exception:
                pass
        super().tearDown()

    def create_service(self, service_class: Type[IService], **kwargs) -> IService:
        """Create a service for testing.

        Args:
            service_class: Service class
            **kwargs: Additional arguments for service constructor

        Returns:
            Service instance
        """
        self.service = service_class(**kwargs)
        return self.service

    def register_service(self, service: IService, interface_type: Type) -> None:
        """Register a service in the mock context.

        Args:
            service: Service instance
            interface_type: Service interface type
        """
        self.mock_host.register_service(interface_type, service)

    def assert_service_available(self, service_type: Type) -> None:
        """Assert that a service is available.

        Args:
            service_type: Service type to check
        """
        service = self.plugin_context.get_service(service_type)
        self.assertIsNotNone(service)


class CommandTestCase(PluginTestCase):
    """Specialized test case for command testing."""

    def setUp(self) -> None:
        """Set up command test environment."""
        super().setUp()
        self.command_results: Dict[str, Any] = {}

    def execute_command(self, command_id: str, **args) -> Any:
        """Execute a command and store the result.

        Args:
            command_id: Command identifier
            **args: Command arguments

        Returns:
            Command execution result
        """
        # Mock command execution
        result = self.mock_host.execute_command(command_id, args)
        self.command_results[command_id] = result
        return result

    def assert_command_success(self, command_id: str) -> None:
        """Assert that a command executed successfully.

        Args:
            command_id: Command identifier
        """
        result = self.command_results.get(command_id)
        self.assertIsNotNone(result)
        if hasattr(result, 'success'):
            self.assertTrue(result.success)

    def assert_command_failed(self, command_id: str) -> None:
        """Assert that a command failed.

        Args:
            command_id: Command identifier
        """
        result = self.command_results.get(command_id)
        self.assertIsNotNone(result)
        if hasattr(result, 'success'):
            self.assertFalse(result.success)

    def get_command_result(self, command_id: str) -> Any:
        """Get the result of a command execution.

        Args:
            command_id: Command identifier

        Returns:
            Command result
        """
        return self.command_results.get(command_id)


class IntegrationTestCase(PluginTestCase):
    """Test case for plugin integration testing."""

    def setUp(self) -> None:
        """Set up integration test environment."""
        super().setUp()
        self.plugins: Dict[str, IPlugin] = {}

    def tearDown(self) -> None:
        """Clean up integration test environment."""
        # Deactivate all plugins
        for plugin in self.plugins.values():
            try:
                plugin.deactivate()
            except Exception:
                pass
        super().tearDown()

    def load_plugin(self, plugin_id: str, plugin_class: Type[IPlugin], **kwargs) -> IPlugin:
        """Load a plugin for integration testing.

        Args:
            plugin_id: Plugin identifier
            plugin_class: Plugin class
            **kwargs: Plugin constructor arguments

        Returns:
            Loaded plugin instance
        """
        context = self.mock_host.create_context(plugin_id)
        plugin = plugin_class(**kwargs)
        plugin.activate(context)
        self.plugins[plugin_id] = plugin
        return plugin

    def assert_plugins_compatible(self, plugin_id_1: str, plugin_id_2: str) -> None:
        """Assert that two plugins are compatible.

        Args:
            plugin_id_1: First plugin ID
            plugin_id_2: Second plugin ID
        """
        plugin1 = self.plugins.get(plugin_id_1)
        plugin2 = self.plugins.get(plugin_id_2)

        self.assertIsNotNone(plugin1, f"Plugin {plugin_id_1} not loaded")
        self.assertIsNotNone(plugin2, f"Plugin {plugin_id_2} not loaded")

        # Basic compatibility check - both plugins should be active
        self.assert_plugin_activated(plugin1)
        self.assert_plugin_activated(plugin2)

    def simulate_plugin_interaction(
        self,
        source_plugin_id: str,
        target_plugin_id: str,
        interaction_type: str,
        data: Dict[str, Any]
    ) -> None:
        """Simulate interaction between plugins.

        Args:
            source_plugin_id: Source plugin ID
            target_plugin_id: Target plugin ID
            interaction_type: Type of interaction
            data: Interaction data
        """
        # Simulate event-based interaction
        event_type = f"{source_plugin_id}.{interaction_type}"
        self.simulate_event(event_type, {
            "source": source_plugin_id,
            "target": target_plugin_id,
            "data": data
        })


# Utility functions for test setup

def create_test_plugin_manifest(plugin_id: str, **overrides) -> Dict[str, Any]:
    """Create a test plugin manifest.

    Args:
        plugin_id: Plugin identifier
        **overrides: Override values

    Returns:
        Plugin manifest dictionary
    """
    manifest = {
        "id": plugin_id,
        "name": f"Test Plugin {plugin_id}",
        "version": "1.0.0",
        "description": "Test plugin for unit testing",
        "author": {"name": "Test Author"},
        "license": "MIT",
        "main": f"{plugin_id}.plugin:TestPlugin",
        "activation": "onStartup",
        "contributes": {
            "commands": [],
            "widgets": [],
            "services": []
        },
        "dependencies": {},
        "permissions": ["ui.read"]
    }

    manifest.update(overrides)
    return manifest


def assert_plugin_interface_compliance(plugin: IPlugin) -> None:
    """Assert that a plugin properly implements the IPlugin interface.

    Args:
        plugin: Plugin to check

    Raises:
        AssertionError: If plugin doesn't comply with interface
    """
    # Check required methods exist
    required_methods = [
        'activate', 'deactivate', 'get_id', 'get_name', 'get_version'
    ]

    for method_name in required_methods:
        assert hasattr(plugin, method_name), f"Plugin missing required method: {method_name}"
        method = getattr(plugin, method_name)
        assert callable(method), f"Plugin method {method_name} is not callable"


def assert_widget_interface_compliance(widget_factory: IWidget) -> None:
    """Assert that a widget factory properly implements the IWidget interface.

    Args:
        widget_factory: Widget factory to check

    Raises:
        AssertionError: If widget doesn't comply with interface
    """
    required_methods = [
        'get_widget_id', 'get_title', 'get_icon', 'create_instance',
        'destroy_instance', 'handle_command', 'get_state', 'restore_state'
    ]

    for method_name in required_methods:
        assert hasattr(widget_factory, method_name), f"Widget missing required method: {method_name}"
        method = getattr(widget_factory, method_name)
        assert callable(method), f"Widget method {method_name} is not callable"


def assert_service_interface_compliance(service: IService) -> None:
    """Assert that a service properly implements the IService interface.

    Args:
        service: Service to check

    Raises:
        AssertionError: If service doesn't comply with interface
    """
    required_methods = ['get_service_id']

    for method_name in required_methods:
        assert hasattr(service, method_name), f"Service missing required method: {method_name}"
        method = getattr(service, method_name)
        assert callable(method), f"Service method {method_name} is not callable"