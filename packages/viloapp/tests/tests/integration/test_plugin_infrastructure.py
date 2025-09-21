#!/usr/bin/env python3
"""Integration tests for plugin infrastructure functionality."""

import pytest
from unittest.mock import Mock
import logging

logger = logging.getLogger(__name__)


class TestPluginInfrastructure:
    """Test plugin infrastructure integration."""

    def test_plugin_service_registration(self):
        """Test that PluginService can be created and registered."""
        from viloapp.services.plugin_service import PluginService
        from viloapp.core.plugin_system.plugin_manager import PluginManager

        # Create plugin service
        plugin_service = PluginService()
        assert plugin_service.name == "PluginService"

        # Create mock plugin manager
        mock_plugin_manager = Mock(spec=PluginManager)
        plugin_service.set_plugin_manager(mock_plugin_manager)

        # Verify plugin manager is set
        assert plugin_service.get_plugin_manager() == mock_plugin_manager

    def test_widget_factory_registration(self):
        """Test that plugin widgets can be registered and created."""
        from viloapp.services.workspace_service import WorkspaceService

        # Create workspace service
        workspace_service = WorkspaceService()

        # Register a test widget factory
        def test_factory(instance_id):
            return f'test_widget_{instance_id}'

        workspace_service.register_widget_factory('test_widget', test_factory)

        # Verify registration
        factories = workspace_service.get_widget_factories()
        assert 'test_widget' in factories

        # Test widget creation
        widget = workspace_service.create_widget('test_widget', 'instance1')
        assert widget == 'test_widget_instance1'

    def test_command_registration(self):
        """Test that plugin commands can be registered in command registry."""
        from viloapp.core.plugin_system.service_adapters import CommandServiceAdapter
        from viloapp.core.commands.registry import command_registry

        # Create adapter
        adapter = CommandServiceAdapter(None)

        # Register a test command
        def test_handler(args):
            return 'test result'

        adapter.register_command('plugin.test', test_handler)

        # Verify registration
        command = command_registry.get_command('plugin.test')
        assert command is not None
        assert command.id == 'plugin.test'
        assert command.category == 'Plugin'

        # Test unregistration
        adapter.unregister_command('plugin.test')
        command = command_registry.get_command('plugin.test')
        assert command is None

    def test_widget_bridge_registration(self):
        """Test that widget bridge can register plugin widgets."""
        from viloapp.core.plugin_system.widget_bridge import PluginWidgetBridge
        from viloapp.services.workspace_service import WorkspaceService

        # Create services
        workspace_service = WorkspaceService()
        bridge = PluginWidgetBridge(workspace_service)

        # Mock plugin widget
        mock_plugin_widget = Mock()
        mock_plugin_widget.get_widget_id.return_value = 'test.terminal'

        # Register widget
        bridge.register_plugin_widget(mock_plugin_widget)

        # Verify registration in workspace service
        factories = workspace_service.get_widget_factories()
        assert 'test.terminal' in factories

    def test_service_adapters_creation(self):
        """Test that service adapters can be created with service instances."""
        from viloapp.core.plugin_system.service_adapters import (
            CommandServiceAdapter,
            ConfigurationServiceAdapter,
            WorkspaceServiceAdapter,
            ThemeServiceAdapter,
            NotificationServiceAdapter,
            create_service_adapters
        )

        # Mock services
        mock_services = {
            'command_service': Mock(),
            'settings_service': Mock(),
            'workspace_service': Mock(),
            'theme_service': Mock(),
            'ui_service': Mock(),
        }

        # Create adapters
        adapters = create_service_adapters(mock_services)

        # Verify all adapters were created
        assert 'command' in adapters
        assert 'configuration' in adapters
        assert 'workspace' in adapters
        assert 'theme' in adapters
        assert 'notification' in adapters

        # Verify adapter types
        assert isinstance(adapters['command'], CommandServiceAdapter)
        assert isinstance(adapters['configuration'], ConfigurationServiceAdapter)
        assert isinstance(adapters['workspace'], WorkspaceServiceAdapter)
        assert isinstance(adapters['theme'], ThemeServiceAdapter)
        assert isinstance(adapters['notification'], NotificationServiceAdapter)

    def test_plugin_widget_adapter_determination(self):
        """Test widget type determination in PluginAppWidgetAdapter."""
        from viloapp.core.plugin_system.widget_bridge import PluginAppWidgetAdapter

        # We'll test the _determine_widget_type method directly
        # by creating a partial adapter that skips Qt initialization
        class TestAdapter(PluginAppWidgetAdapter):
            def __init__(self):
                # Skip parent init to avoid Qt widget creation
                pass

        adapter = TestAdapter()

        # Test terminal widget type determination
        from viloapp.ui.widgets.widget_registry import WidgetType
        if WidgetType:
            result = adapter._determine_widget_type('terminal')
            assert result == WidgetType.TERMINAL

            result = adapter._determine_widget_type('test.terminal.widget')
            assert result == WidgetType.TERMINAL

            result = adapter._determine_widget_type('editor')
            assert result == WidgetType.TEXT_EDITOR

            result = adapter._determine_widget_type('text.editor')
            assert result == WidgetType.TEXT_EDITOR

            result = adapter._determine_widget_type('unknown.widget')
            assert result == WidgetType.CUSTOM

    def test_split_pane_model_plugin_integration(self):
        """Test that split pane model can create plugin widgets."""
        # This test verifies the factory pattern integration
        # without actually creating Qt widgets

        from viloapp.services.workspace_service import WorkspaceService

        # Create workspace service and register a test factory
        workspace_service = WorkspaceService()

        def mock_terminal_factory(instance_id):
            mock_widget = Mock()
            mock_widget.widget_id = instance_id
            return mock_widget

        workspace_service.register_widget_factory('terminal', mock_terminal_factory)

        # Verify the factory works
        widget = workspace_service.create_widget('terminal', 'test_terminal')
        assert widget is not None
        assert widget.widget_id == 'test_terminal'

    def test_service_initialization_chain(self):
        """Test the full service initialization chain."""
        from viloapp.services.plugin_service import PluginService
        from viloapp.services.workspace_service import WorkspaceService
        from viloapp.core.plugin_system.widget_bridge import PluginWidgetBridge

        # Create services
        plugin_service = PluginService()
        workspace_service = WorkspaceService()

        # Create widget bridge
        widget_bridge = PluginWidgetBridge(workspace_service)

        # Connect bridge to plugin service
        plugin_service._widget_bridge = widget_bridge

        # Mock plugin widget
        mock_plugin_widget = Mock()
        mock_plugin_widget.get_widget_id.return_value = 'test.widget'

        # Register widget through plugin service
        plugin_service.register_widget(mock_plugin_widget)

        # Verify widget was registered in workspace service
        factories = workspace_service.get_widget_factories()
        assert 'test.widget' in factories


if __name__ == '__main__':
    pytest.main([__file__, '-v'])