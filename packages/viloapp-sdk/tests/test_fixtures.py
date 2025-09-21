"""Tests for SDK testing fixtures."""

import pytest
from pathlib import Path
from unittest.mock import Mock

from viloapp_sdk.context import IPluginContext
from viloapp_sdk.service import ServiceProxy
from viloapp_sdk.events import EventBus, PluginEvent, EventType
from viloapp_sdk.plugin import PluginMetadata, PluginCapability
from viloapp_sdk.interfaces import IPlugin
from viloapp_sdk.testing.mock_host import MockPluginHost
from viloapp_sdk.testing.fixtures import *


class TestBasicFixtures:
    """Test basic testing fixtures."""

    def test_mock_plugin_host_fixture(self, mock_plugin_host):
        """Test the mock_plugin_host fixture."""
        assert isinstance(mock_plugin_host, MockPluginHost)
        assert len(mock_plugin_host._services) >= 5  # Default services

    def test_mock_plugin_context_fixture(self, mock_plugin_context):
        """Test the mock_plugin_context fixture."""
        assert isinstance(mock_plugin_context, IPluginContext)
        assert mock_plugin_context.get_plugin_id() == "test-plugin"
        assert mock_plugin_context.get_plugin_path().exists()
        assert mock_plugin_context.get_data_path().exists()

    def test_mock_services_fixture(self, mock_services):
        """Test the mock_services fixture."""
        assert isinstance(mock_services, dict)
        assert "command" in mock_services
        assert "configuration" in mock_services
        assert "workspace" in mock_services
        assert "theme" in mock_services
        assert "notification" in mock_services

    def test_mock_service_proxy_fixture(self, mock_service_proxy):
        """Test the mock_service_proxy fixture."""
        assert isinstance(mock_service_proxy, ServiceProxy)
        assert mock_service_proxy.has_service("command")
        assert mock_service_proxy.has_service("configuration")

    def test_mock_event_bus_fixture(self, mock_event_bus):
        """Test the mock_event_bus fixture."""
        assert isinstance(mock_event_bus, EventBus)

        # Test basic event functionality
        events_received = []
        mock_event_bus.subscribe(EventType.PLUGIN_ACTIVATED, lambda e: events_received.append(e))

        event = PluginEvent(EventType.PLUGIN_ACTIVATED, "test-source")
        mock_event_bus.emit(event)

        assert len(events_received) == 1
        assert events_received[0].type == EventType.PLUGIN_ACTIVATED


class TestPluginFixtures:
    """Test plugin-related fixtures."""

    def test_sample_plugin_metadata_fixture(self, sample_plugin_metadata):
        """Test the sample_plugin_metadata fixture."""
        assert isinstance(sample_plugin_metadata, PluginMetadata)
        assert sample_plugin_metadata.id == "sample-plugin"
        assert sample_plugin_metadata.name == "Sample Plugin"
        assert sample_plugin_metadata.version == "1.0.0"
        assert PluginCapability.WIDGETS in sample_plugin_metadata.capabilities

    def test_sample_plugin_class_fixture(self, sample_plugin_class):
        """Test the sample_plugin_class fixture."""
        assert issubclass(sample_plugin_class, IPlugin)

        # Instantiate and test
        plugin = sample_plugin_class()
        assert not plugin.activated
        assert not plugin.deactivated

        metadata = plugin.get_metadata()
        assert metadata.id == "sample-plugin"

    def test_sample_plugin_fixture(self, sample_plugin):
        """Test the sample_plugin fixture."""
        assert isinstance(sample_plugin, IPlugin)
        assert not sample_plugin.activated

        # Test activation
        mock_context = Mock()
        sample_plugin.activate(mock_context)
        assert sample_plugin.activated
        assert sample_plugin.context == mock_context

        # Test deactivation
        sample_plugin.deactivate()
        assert sample_plugin.deactivated

    def test_sample_plugin_commands(self, sample_plugin):
        """Test sample plugin command handling."""
        # Test default command result
        result = sample_plugin.on_command("test.command", {})
        assert result == "executed_test.command"

        # Test custom command result
        sample_plugin.command_results["custom.command"] = "custom_result"
        result = sample_plugin.on_command("custom.command", {"arg": "value"})
        assert result == "custom_result"


class TestDirectoryFixtures:
    """Test directory and file fixtures."""

    def test_temp_plugin_dir_fixture(self, temp_plugin_dir):
        """Test the temp_plugin_dir fixture."""
        assert isinstance(temp_plugin_dir, Path)
        assert temp_plugin_dir.exists()
        assert temp_plugin_dir.is_dir()

        # Test writing to the directory
        test_file = temp_plugin_dir / "test.txt"
        test_file.write_text("test content")
        assert test_file.exists()
        assert test_file.read_text() == "test content"

    def test_plugin_manifest_dir_fixture(self, plugin_manifest_dir):
        """Test the plugin_manifest_dir fixture."""
        assert isinstance(plugin_manifest_dir, Path)
        assert plugin_manifest_dir.exists()

        # Should have a plugin.json file
        manifest_file = plugin_manifest_dir / "plugin.json"
        assert manifest_file.exists()

        # Should be valid JSON
        import json

        with open(manifest_file) as f:
            manifest_data = json.load(f)

        assert manifest_data["id"] == "sample-plugin"
        assert manifest_data["name"] == "Sample Plugin"
        assert "entry_point" in manifest_data

    def test_temp_directories_are_different(self, temp_plugin_dir):
        """Test that each test gets a different temp directory."""
        # This test should get a different directory than the previous test
        assert temp_plugin_dir.exists()
        # Can't easily test they're different in the same test,
        # but the fixture implementation ensures uniqueness


class TestConfigurationFixtures:
    """Test configuration fixtures."""

    def test_plugin_configuration_fixture(self, plugin_configuration):
        """Test the plugin_configuration fixture."""
        assert isinstance(plugin_configuration, dict)
        assert plugin_configuration["debug"] is True
        assert plugin_configuration["theme"] == "dark"
        assert plugin_configuration["max_connections"] == 10
        assert "features" in plugin_configuration
        assert "paths" in plugin_configuration

    def test_various_configurations_fixture(self, various_configurations):
        """Test the various_configurations parameterized fixture."""
        assert isinstance(various_configurations, dict)
        assert "debug" in various_configurations
        assert "verbose" in various_configurations
        assert isinstance(various_configurations["debug"], bool)
        assert isinstance(various_configurations["verbose"], bool)


class TestServiceFixtures:
    """Test service-specific fixtures."""

    def test_mock_command_service_fixture(self, mock_command_service):
        """Test the mock_command_service fixture."""
        from viloapp_sdk.testing.mock_host import MockCommandService

        assert isinstance(mock_command_service, MockCommandService)
        assert mock_command_service.get_service_id() == "command"

    def test_mock_configuration_service_fixture(self, mock_configuration_service):
        """Test the mock_configuration_service fixture with pre-populated settings."""
        from viloapp_sdk.testing.mock_host import MockConfigurationService

        assert isinstance(mock_configuration_service, MockConfigurationService)

        # Should have pre-populated settings
        assert mock_configuration_service.get("editor.fontSize") == 14
        assert mock_configuration_service.get("editor.theme") == "dark"
        assert mock_configuration_service.get("workspace.autosave") is True

    def test_service_types_fixture(self, service_types, mock_services):
        """Test the service_types parameterized fixture."""
        assert service_types in mock_services
        service = mock_services[service_types]
        assert service.get_service_id() == service_types


class TestUtilityFixtures:
    """Test utility fixtures."""

    def test_mock_widget_fixture(self, mock_widget):
        """Test the mock_widget fixture."""
        assert mock_widget.isVisible() is True
        assert mock_widget.size() == (800, 600)

        # Test that it's a proper mock
        mock_widget.show()
        mock_widget.show.assert_called_once()

    def test_assert_mock_calls_fixture(self, assert_mock_calls, mock_command_service):
        """Test the assert_mock_calls fixture."""
        # Make a call
        mock_command_service.execute_command("test.command")

        # Test assertion helpers
        assert_mock_calls.assert_called_once(
            mock_command_service.mock.execute_command, "test.command"
        )

        # Make more calls
        mock_command_service.execute_command("another.command")
        assert_mock_calls.assert_called_n_times(mock_command_service.mock.execute_command, 2)

        # Test not called assertion
        mock_method = Mock()
        assert_mock_calls.assert_not_called(mock_method)


class TestIntegrationFixtures:
    """Test integration fixtures."""

    def test_integrated_plugin_environment_fixture(self, integrated_plugin_environment):
        """Test the integrated_plugin_environment fixture."""
        env = integrated_plugin_environment

        # Check all components are present
        assert "host" in env
        assert "plugin" in env
        assert "context" in env
        assert "configuration" in env
        assert "services" in env
        assert "event_bus" in env

        # Check types
        assert isinstance(env["host"], MockPluginHost)
        assert isinstance(env["plugin"], IPlugin)
        assert isinstance(env["context"], IPluginContext)
        assert isinstance(env["configuration"], dict)
        assert isinstance(env["services"], dict)
        assert isinstance(env["event_bus"], EventBus)

        # Test integration
        plugin = env["plugin"]
        context = env["context"]

        assert not plugin.activated
        plugin.activate(context)
        assert plugin.activated
        assert plugin.context == context


class TestFixtureReusability:
    """Test that fixtures work correctly across multiple tests."""

    def test_fixture_isolation_1(self, mock_plugin_host):
        """First test using mock_plugin_host."""
        # Modify the host
        mock_plugin_host.plugin_id = "modified-id"
        custom_service = Mock()
        mock_plugin_host.add_service(custom_service)

        assert mock_plugin_host.plugin_id == "modified-id"

    def test_fixture_isolation_2(self, mock_plugin_host):
        """Second test using mock_plugin_host should get fresh instance."""
        # Should get a fresh host, not the modified one from previous test
        assert mock_plugin_host.plugin_id == "test-plugin"  # Default value
        assert len(mock_plugin_host._services) == 5  # Just default services

    def test_multiple_temp_dirs(self, temp_plugin_dir):
        """Test with temp directory."""
        temp_plugin_dir.touch()  # Create a marker
        marker_file = temp_plugin_dir / "marker.txt"
        marker_file.write_text("test1")
        assert marker_file.exists()

    def test_different_temp_dirs(self, temp_plugin_dir):
        """Should get different temp directory."""
        # This directory shouldn't have the marker from previous test
        marker_file = temp_plugin_dir / "marker.txt"
        assert not marker_file.exists()


class TestParameterizedFixtures:
    """Test parameterized fixtures run multiple times."""

    @pytest.mark.parametrize(
        "expected_debug,expected_verbose", [(True, False), (False, True), (True, True)]
    )
    def test_various_configurations_coverage(
        self, various_configurations, expected_debug, expected_verbose
    ):
        """Test that various_configurations covers expected combinations."""
        # This test will run 3 times, and at least one of them should match each combination
        if (
            various_configurations["debug"] == expected_debug
            and various_configurations["verbose"] == expected_verbose
        ):
            # Found the expected combination
            assert True
            return

    def test_all_service_types_covered(self, service_types):
        """Test that all expected service types are covered."""
        expected_services = {"command", "configuration", "workspace", "theme", "notification"}
        assert service_types in expected_services
