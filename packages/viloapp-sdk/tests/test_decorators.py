"""Tests for plugin decorators."""

import pytest
from unittest.mock import Mock

from viloapp_sdk.utils.decorators import (
    plugin,
    command,
    widget,
    service,
    activation_event,
    contribution,
    ActivationEventType,
    ContributionPointType,
    get_plugin_metadata,
    get_command_metadata,
    get_widget_metadata,
    get_service_metadata,
    get_activation_events,
    get_contributions,
    get_commands_from_class,
    create_manifest_from_decorators,
)
from viloapp_sdk.interfaces import IPlugin
from viloapp_sdk.widget import IWidget
from viloapp_sdk.service import IService
from viloapp_sdk.exceptions import PluginError


class TestPluginDecorator:
    """Test cases for @plugin decorator."""

    def test_plugin_decorator_basic(self):
        """Test basic plugin decoration."""

        @plugin(
            plugin_id="test-plugin",
            name="Test Plugin",
            version="1.0.0",
            description="A test plugin",
        )
        class TestPlugin(IPlugin):
            def get_metadata(self):
                return None

            def activate(self, context):
                pass

            def deactivate(self):
                pass

        metadata = get_plugin_metadata(TestPlugin)
        assert metadata is not None
        assert metadata.plugin_id == "test-plugin"
        assert metadata.name == "Test Plugin"
        assert metadata.version == "1.0.0"
        assert metadata.description == "A test plugin"

    def test_plugin_decorator_defaults(self):
        """Test plugin decorator with default values."""

        @plugin(name="Test Plugin")
        class TestPlugin(IPlugin):
            def get_metadata(self):
                return None

            def activate(self, context):
                pass

            def deactivate(self):
                pass

        metadata = get_plugin_metadata(TestPlugin)
        assert metadata.plugin_id == "test"  # derived from class name
        assert metadata.version == "1.0.0"
        assert metadata.license == "MIT"
        assert metadata.engines == {"viloapp": ">=2.0.0"}
        assert metadata.categories == ["Other"]

    def test_plugin_decorator_author_string(self):
        """Test plugin decorator with string author."""

        @plugin(name="Test Plugin", author="John Doe")
        class TestPlugin(IPlugin):
            def get_metadata(self):
                return None

            def activate(self, context):
                pass

            def deactivate(self):
                pass

        metadata = get_plugin_metadata(TestPlugin)
        assert metadata.author == {"name": "John Doe"}

    def test_plugin_decorator_author_dict(self):
        """Test plugin decorator with dict author."""

        @plugin(name="Test Plugin", author={"name": "John Doe", "email": "john@example.com"})
        class TestPlugin(IPlugin):
            def get_metadata(self):
                return None

            def activate(self, context):
                pass

            def deactivate(self):
                pass

        metadata = get_plugin_metadata(TestPlugin)
        assert metadata.author == {"name": "John Doe", "email": "john@example.com"}

    def test_plugin_decorator_validation_errors(self):
        """Test plugin decorator validation errors."""
        with pytest.raises(PluginError, match="Plugin name is required"):

            @plugin()
            class TestPlugin(IPlugin):
                pass

        with pytest.raises(PluginError, match="Invalid plugin ID format"):

            @plugin(name="Test Plugin", plugin_id="invalid@id")
            class TestPlugin2(IPlugin):
                pass

    def test_plugin_decorator_full_config(self):
        """Test plugin decorator with full configuration."""

        @plugin(
            plugin_id="my-awesome-plugin",
            name="My Awesome Plugin",
            version="2.1.0",
            description="An awesome plugin",
            author={"name": "Jane Doe", "email": "jane@example.com"},
            license="GPL-3.0",
            keywords=["terminal", "productivity"],
            engines={"viloapp": ">=2.1.0", "python": ">=3.8"},
            categories=["Programming Languages"],
            icon="my-icon",
            preview=True,
        )
        class AwesomePlugin(IPlugin):
            def get_metadata(self):
                return None

            def activate(self, context):
                pass

            def deactivate(self):
                pass

        metadata = get_plugin_metadata(AwesomePlugin)
        assert metadata.plugin_id == "my-awesome-plugin"
        assert metadata.name == "My Awesome Plugin"
        assert metadata.version == "2.1.0"
        assert metadata.keywords == ["terminal", "productivity"]
        assert metadata.engines == {"viloapp": ">=2.1.0", "python": ">=3.8"}
        assert metadata.categories == ["Programming Languages"]
        assert metadata.icon == "my-icon"
        assert metadata.preview is True


class TestCommandDecorator:
    """Test cases for @command decorator."""

    def test_command_decorator_basic(self):
        """Test basic command decoration."""

        class TestPlugin:
            @command(command_id="test.hello", title="Say Hello")
            def hello_command(self):
                pass

        metadata = get_command_metadata(TestPlugin.hello_command)
        assert metadata is not None
        assert metadata.command_id == "test.hello"
        assert metadata.title == "Say Hello"
        assert metadata.handler == TestPlugin.hello_command

    def test_command_decorator_full_config(self):
        """Test command decorator with full configuration."""

        class TestPlugin:
            @command(
                command_id="test.openFile",
                title="Open File",
                category="File",
                description="Opens a file dialog",
                icon="file-open",
                shortcut="ctrl+o",
                when="editorFocus",
            )
            def open_file_command(self):
                pass

        metadata = get_command_metadata(TestPlugin.open_file_command)
        assert metadata.command_id == "test.openFile"
        assert metadata.title == "Open File"
        assert metadata.category == "File"
        assert metadata.description == "Opens a file dialog"
        assert metadata.icon == "file-open"
        assert metadata.shortcut == "ctrl+o"
        assert metadata.when == "editorFocus"

    def test_command_decorator_validation_errors(self):
        """Test command decorator validation errors."""
        with pytest.raises(PluginError, match="Command ID is required"):

            class TestPlugin:
                @command(command_id="", title="Test")
                def test_command(self):
                    pass

        with pytest.raises(PluginError, match="Invalid command ID format"):

            class TestPlugin2:
                @command(command_id="invalid@command", title="Test")
                def test_command(self):
                    pass

    def test_get_commands_from_class(self):
        """Test extracting all commands from a class."""

        class TestPlugin:
            @command(command_id="test.cmd1", title="Command 1")
            def command1(self):
                pass

            @command(command_id="test.cmd2", title="Command 2")
            def command2(self):
                pass

            def regular_method(self):
                pass

        commands = get_commands_from_class(TestPlugin)
        assert len(commands) == 2
        assert "test.cmd1" in commands
        assert "test.cmd2" in commands
        assert commands["test.cmd1"].title == "Command 1"
        assert commands["test.cmd2"].title == "Command 2"


class TestWidgetDecorator:
    """Test cases for @widget decorator."""

    def test_widget_decorator_basic(self):
        """Test basic widget decoration."""

        @widget(widget_id="test-widget", title="Test Widget")
        class TestWidget(IWidget):
            def get_widget_id(self):
                return "test-widget"

            def get_title(self):
                return "Test Widget"

            def get_icon(self):
                return None

            def create_instance(self, instance_id):
                return Mock()

            def destroy_instance(self, instance_id):
                pass

            def handle_command(self, command, args):
                pass

            def get_state(self):
                return {}

            def restore_state(self, state):
                pass

        metadata = get_widget_metadata(TestWidget)
        assert metadata is not None
        assert metadata.widget_id == "test-widget"
        assert metadata.title == "Test Widget"
        assert metadata.factory_class == TestWidget

    def test_widget_decorator_full_config(self):
        """Test widget decorator with full configuration."""

        @widget(
            widget_id="terminal",
            title="Terminal",
            icon="terminal",
            position="main",
            closable=True,
            singleton=False,
            group="editors",
        )
        class TerminalWidget(IWidget):
            def get_widget_id(self):
                return "terminal"

            def get_title(self):
                return "Terminal"

            def get_icon(self):
                return "terminal"

            def create_instance(self, instance_id):
                return Mock()

            def destroy_instance(self, instance_id):
                pass

            def handle_command(self, command, args):
                pass

            def get_state(self):
                return {}

            def restore_state(self, state):
                pass

        metadata = get_widget_metadata(TerminalWidget)
        assert metadata.widget_id == "terminal"
        assert metadata.title == "Terminal"
        assert metadata.icon == "terminal"
        assert metadata.position == "main"
        assert metadata.closable is True
        assert metadata.singleton is False
        assert metadata.group == "editors"

    def test_widget_decorator_validation_errors(self):
        """Test widget decorator validation errors."""
        with pytest.raises(PluginError, match="Widget ID is required"):

            @widget(widget_id="", title="Test")
            class TestWidget(IWidget):
                pass

        with pytest.raises(PluginError, match="Widget title is required"):

            @widget(widget_id="test", title="")
            class TestWidget2(IWidget):
                pass

        with pytest.raises(PluginError, match="Invalid widget position"):

            @widget(widget_id="test", title="Test", position="invalid")
            class TestWidget3(IWidget):
                pass


class TestServiceDecorator:
    """Test cases for @service decorator."""

    def test_service_decorator_basic(self):
        """Test basic service decoration."""

        @service(service_id="test-service", name="Test Service")
        class TestService(IService):
            def get_service_id(self):
                return "test-service"

            def get_service_version(self):
                return "1.0.0"

        metadata = get_service_metadata(TestService)
        assert metadata is not None
        assert metadata.service_id == "test-service"
        assert metadata.name == "Test Service"
        assert metadata.version == "1.0.0"
        assert metadata.singleton is True
        assert metadata.lazy is False

    def test_service_decorator_full_config(self):
        """Test service decorator with full configuration."""

        @service(
            service_id="my-service",
            name="My Service",
            description="A custom service",
            version="2.0.0",
            singleton=False,
            lazy=True,
        )
        class MyService(IService):
            def get_service_id(self):
                return "my-service"

            def get_service_version(self):
                return "2.0.0"

        metadata = get_service_metadata(MyService)
        assert metadata.service_id == "my-service"
        assert metadata.name == "My Service"
        assert metadata.description == "A custom service"
        assert metadata.version == "2.0.0"
        assert metadata.singleton is False
        assert metadata.lazy is True

    def test_service_decorator_validation_errors(self):
        """Test service decorator validation errors."""
        with pytest.raises(PluginError, match="Service ID is required"):

            @service(service_id="", name="Test")
            class TestService(IService):
                pass

        with pytest.raises(PluginError, match="Service name is required"):

            @service(service_id="test", name="")
            class TestService2(IService):
                pass


class TestActivationEventDecorator:
    """Test cases for @activation_event decorator."""

    def test_activation_event_decorator_enum(self):
        """Test activation event decorator with enum."""

        @activation_event(ActivationEventType.ON_STARTUP)
        class TestPlugin(IPlugin):
            def get_metadata(self):
                return None

            def activate(self, context):
                pass

            def deactivate(self):
                pass

        events = get_activation_events(TestPlugin)
        assert "onStartup" in events

    def test_activation_event_decorator_with_parameter(self):
        """Test activation event decorator with parameter."""

        @activation_event(ActivationEventType.ON_COMMAND, "test.command")
        class TestPlugin(IPlugin):
            def get_metadata(self):
                return None

            def activate(self, context):
                pass

            def deactivate(self):
                pass

        events = get_activation_events(TestPlugin)
        assert "onCommand:test.command" in events

    def test_activation_event_decorator_string(self):
        """Test activation event decorator with string."""

        @activation_event("onLanguage", "python")
        class TestPlugin(IPlugin):
            def get_metadata(self):
                return None

            def activate(self, context):
                pass

            def deactivate(self):
                pass

        events = get_activation_events(TestPlugin)
        assert "onLanguage:python" in events

    def test_multiple_activation_events(self):
        """Test multiple activation event decorators."""

        @activation_event(ActivationEventType.ON_STARTUP)
        @activation_event(ActivationEventType.ON_COMMAND, "test.command")
        @activation_event("onLanguage", "python")
        class TestPlugin(IPlugin):
            def get_metadata(self):
                return None

            def activate(self, context):
                pass

            def deactivate(self):
                pass

        events = get_activation_events(TestPlugin)
        assert len(events) == 3
        assert "onStartup" in events
        assert "onCommand:test.command" in events
        assert "onLanguage:python" in events

    def test_duplicate_activation_events(self):
        """Test duplicate activation events are not added twice."""

        @activation_event(ActivationEventType.ON_STARTUP)
        @activation_event(ActivationEventType.ON_STARTUP)
        class TestPlugin(IPlugin):
            def get_metadata(self):
                return None

            def activate(self, context):
                pass

            def deactivate(self):
                pass

        events = get_activation_events(TestPlugin)
        assert events.count("onStartup") == 1


class TestContributionDecorator:
    """Test cases for @contribution decorator."""

    def test_contribution_decorator_enum(self):
        """Test contribution decorator with enum."""

        @contribution(
            ContributionPointType.COMMANDS, commands=[{"command": "test.hello", "title": "Hello"}]
        )
        class TestPlugin(IPlugin):
            def get_metadata(self):
                return None

            def activate(self, context):
                pass

            def deactivate(self):
                pass

        contributions = get_contributions(TestPlugin)
        assert len(contributions) == 1
        assert contributions[0].contribution_point == "commands"
        assert contributions[0].contribution_type == ContributionPointType.COMMANDS
        assert contributions[0].configuration == {
            "commands": [{"command": "test.hello", "title": "Hello"}]
        }

    def test_contribution_decorator_string(self):
        """Test contribution decorator with string."""

        @contribution("menus", menus={"editor/context": []})
        class TestPlugin(IPlugin):
            def get_metadata(self):
                return None

            def activate(self, context):
                pass

            def deactivate(self):
                pass

        contributions = get_contributions(TestPlugin)
        assert len(contributions) == 1
        assert contributions[0].contribution_point == "menus"
        assert contributions[0].contribution_type == ContributionPointType.MENUS

    def test_contribution_decorator_unknown_point(self):
        """Test contribution decorator with unknown contribution point."""
        with pytest.raises(PluginError, match="Unknown contribution point"):

            @contribution("unknown")
            class TestPlugin(IPlugin):
                pass

    def test_multiple_contributions(self):
        """Test multiple contribution decorators."""

        @contribution(ContributionPointType.COMMANDS, commands=[])
        @contribution(ContributionPointType.MENUS, menus={})
        class TestPlugin(IPlugin):
            def get_metadata(self):
                return None

            def activate(self, context):
                pass

            def deactivate(self):
                pass

        contributions = get_contributions(TestPlugin)
        assert len(contributions) == 2
        contribution_points = [c.contribution_point for c in contributions]
        assert "commands" in contribution_points
        assert "menus" in contribution_points


class TestManifestCreation:
    """Test cases for manifest creation from decorators."""

    def test_create_manifest_complete(self):
        """Test creating complete manifest from decorators."""

        @plugin(
            plugin_id="my-plugin",
            name="My Plugin",
            version="1.0.0",
            description="A test plugin",
            author={"name": "John Doe", "email": "john@example.com"},
            keywords=["test", "example"],
            categories=["Other"],
        )
        @activation_event(ActivationEventType.ON_STARTUP)
        @activation_event(ActivationEventType.ON_COMMAND, "myPlugin.hello")
        @contribution(ContributionPointType.COMMANDS)
        class MyPlugin(IPlugin):
            def get_metadata(self):
                return None

            def activate(self, context):
                pass

            def deactivate(self):
                pass

            @command(command_id="myPlugin.hello", title="Say Hello", category="Test")
            def hello_command(self):
                pass

        manifest = create_manifest_from_decorators(MyPlugin)

        # Check plugin metadata
        assert manifest["name"] == "my-plugin"
        assert manifest["displayName"] == "My Plugin"
        assert manifest["version"] == "1.0.0"
        assert manifest["description"] == "A test plugin"
        assert manifest["author"] == {"name": "John Doe", "email": "john@example.com"}
        assert manifest["keywords"] == ["test", "example"]
        assert manifest["categories"] == ["Other"]

        # Check activation events
        assert "activationEvents" in manifest
        assert "onStartup" in manifest["activationEvents"]
        assert "onCommand:myPlugin.hello" in manifest["activationEvents"]

        # Check commands contribution
        assert "contributes" in manifest
        assert "commands" in manifest["contributes"]
        commands = manifest["contributes"]["commands"]
        assert len(commands) == 1
        assert commands[0]["command"] == "myPlugin.hello"
        assert commands[0]["title"] == "Say Hello"
        assert commands[0]["category"] == "Test"

    def test_create_manifest_minimal(self):
        """Test creating minimal manifest from decorators."""

        @plugin(name="Minimal Plugin")
        class MinimalPlugin(IPlugin):
            def get_metadata(self):
                return None

            def activate(self, context):
                pass

            def deactivate(self):
                pass

        manifest = create_manifest_from_decorators(MinimalPlugin)

        assert manifest["name"] == "minimal"
        assert manifest["displayName"] == "Minimal Plugin"
        assert manifest["version"] == "1.0.0"
        assert manifest["license"] == "MIT"
        assert manifest["engines"] == {"viloapp": ">=2.0.0"}
        assert manifest["categories"] == ["Other"]

    def test_create_manifest_no_decorators(self):
        """Test creating manifest from class without decorators."""

        class PlainPlugin(IPlugin):
            def get_metadata(self):
                return None

            def activate(self, context):
                pass

            def deactivate(self):
                pass

        manifest = create_manifest_from_decorators(PlainPlugin)
        # Should return empty manifest
        assert manifest == {}
