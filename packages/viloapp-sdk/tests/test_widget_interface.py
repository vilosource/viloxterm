"""Tests for the new IWidget interface specification."""

import pytest
from abc import ABC
from typing import Optional, Dict, Any
from unittest.mock import Mock

from PySide6.QtWidgets import QWidget, QLabel

from viloapp_sdk.widget import IWidget


class TestIWidgetInterface:
    """Test the IWidget interface specification."""

    def test_iwidget_is_abstract(self):
        """Test that IWidget cannot be instantiated directly."""
        with pytest.raises(TypeError):
            IWidget()

    def test_abstract_methods_exist(self):
        """Test that all required abstract methods are defined."""
        # Get all abstract methods from IWidget
        abstract_methods = IWidget.__abstractmethods__

        # New interface has these abstract methods
        required_methods = {
            "get_widget_id", "get_title", "get_icon",
            "create_instance", "destroy_instance", "handle_command",
            "get_state", "restore_state"
        }

        # Check all required abstract methods exist
        for method in required_methods:
            assert method in abstract_methods, f"Missing abstract method: {method}"

        # Ensure we have exactly the expected methods
        assert abstract_methods == required_methods


class MockWidgetFactory(IWidget):
    """Mock implementation for testing the new interface methods."""

    def __init__(self):
        self.instances = {}
        self.commands_handled = []

    # New interface methods implementation
    def get_widget_id(self) -> str:
        """Get unique widget identifier."""
        return "test-widget"

    def get_title(self) -> str:
        """Get widget display title."""
        return "Test Widget"

    def get_icon(self) -> Optional[str]:
        """Get widget icon identifier."""
        return "test-icon"

    def create_instance(self, instance_id: str) -> QWidget:
        """Create widget instance with unique ID."""
        widget = QLabel(f"Test Widget {instance_id}")
        self.instances[instance_id] = widget
        return widget

    def destroy_instance(self, instance_id: str) -> None:
        """Destroy widget instance."""
        if instance_id in self.instances:
            widget = self.instances[instance_id]
            widget.deleteLater()
            del self.instances[instance_id]

    def handle_command(self, command: str, args: Dict[str, Any]) -> Any:
        """Handle widget-specific commands."""
        self.commands_handled.append((command, args))
        if command == "get_text":
            return "test response"
        elif command == "set_text":
            return f"Set text to: {args.get('text', '')}"
        return None

    def get_state(self) -> Dict[str, Any]:
        """Get widget state."""
        return {"test_state": "value"}

    def restore_state(self, state: Dict[str, Any]) -> None:
        """Restore widget state."""
        pass


class TestNewIWidgetMethods:
    """Test the new IWidget interface methods that will be added."""

    @pytest.fixture
    def widget_factory(self):
        """Create a mock widget factory for testing."""
        return MockWidgetFactory()

    def test_get_widget_id(self, widget_factory):
        """Test get_widget_id returns string identifier."""
        widget_id = widget_factory.get_widget_id()
        assert isinstance(widget_id, str)
        assert len(widget_id) > 0
        assert widget_id == "test-widget"

    def test_get_title(self, widget_factory):
        """Test get_title returns display title."""
        title = widget_factory.get_title()
        assert isinstance(title, str)
        assert len(title) > 0
        assert title == "Test Widget"

    def test_get_icon_optional(self, widget_factory):
        """Test get_icon returns optional icon identifier."""
        icon = widget_factory.get_icon()
        assert icon is None or isinstance(icon, str)
        if icon:
            assert len(icon) > 0

    def test_create_instance_with_id(self, widget_factory, qtbot):
        """Test create_instance creates widget with unique ID."""
        instance_id = "test-instance-1"
        widget = widget_factory.create_instance(instance_id)

        assert isinstance(widget, QWidget)
        assert instance_id in widget_factory.instances
        qtbot.addWidget(widget)

    def test_create_multiple_instances(self, widget_factory, qtbot):
        """Test creating multiple widget instances."""
        instance1 = widget_factory.create_instance("instance1")
        instance2 = widget_factory.create_instance("instance2")

        assert instance1 != instance2
        assert len(widget_factory.instances) == 2
        assert "instance1" in widget_factory.instances
        assert "instance2" in widget_factory.instances

        qtbot.addWidget(instance1)
        qtbot.addWidget(instance2)

    def test_destroy_instance(self, widget_factory, qtbot):
        """Test destroy_instance removes and cleans up widget."""
        instance_id = "destroy-test"
        widget = widget_factory.create_instance(instance_id)
        qtbot.addWidget(widget)

        assert instance_id in widget_factory.instances

        widget_factory.destroy_instance(instance_id)

        assert instance_id not in widget_factory.instances

    def test_destroy_nonexistent_instance(self, widget_factory):
        """Test destroying non-existent instance doesn't raise error."""
        # Should not raise exception
        widget_factory.destroy_instance("nonexistent")

    def test_handle_command_with_args(self, widget_factory):
        """Test handle_command processes commands and arguments."""
        result = widget_factory.handle_command("get_text", {})
        assert result == "test response"

        result = widget_factory.handle_command("set_text", {"text": "hello"})
        assert result == "Set text to: hello"

        # Check commands were recorded
        assert len(widget_factory.commands_handled) == 2
        assert widget_factory.commands_handled[0] == ("get_text", {})
        assert widget_factory.commands_handled[1] == ("set_text", {"text": "hello"})

    def test_handle_unknown_command(self, widget_factory):
        """Test handle_command with unknown command."""
        result = widget_factory.handle_command("unknown_command", {})
        assert result is None

    def test_get_state_returns_dict(self, widget_factory):
        """Test get_state returns serializable dictionary."""
        state = widget_factory.get_state()
        assert isinstance(state, dict)
        # Should be JSON serializable
        import json
        json.dumps(state)  # Should not raise

    def test_restore_state_accepts_dict(self, widget_factory):
        """Test restore_state accepts state dictionary."""
        state = {"test_key": "test_value"}
        # Should not raise exception
        widget_factory.restore_state(state)


class TestInterfaceContracts:
    """Test the interface contracts and requirements."""

    @pytest.fixture
    def widget_factory(self):
        return MockWidgetFactory()

    def test_widget_id_is_unique_identifier(self, widget_factory):
        """Test widget ID serves as unique identifier."""
        id1 = widget_factory.get_widget_id()
        id2 = widget_factory.get_widget_id()

        # Should be consistent
        assert id1 == id2

        # Should be valid identifier format
        assert isinstance(id1, str)
        assert len(id1) > 0
        # Could add more validation like no spaces, etc.

    def test_instance_lifecycle_management(self, widget_factory, qtbot):
        """Test complete instance lifecycle."""
        instance_id = "lifecycle-test"

        # Create instance
        widget = widget_factory.create_instance(instance_id)
        qtbot.addWidget(widget)
        assert instance_id in widget_factory.instances

        # Instance should be findable
        stored_widget = widget_factory.instances[instance_id]
        assert stored_widget is widget

        # Destroy instance
        widget_factory.destroy_instance(instance_id)
        assert instance_id not in widget_factory.instances

    def test_command_handling_is_extensible(self, widget_factory):
        """Test command handling supports extensibility."""
        # Commands should be strings
        result = widget_factory.handle_command("custom_command", {"param": "value"})

        # Should handle gracefully even if unknown
        assert result is None  # Or whatever the implementation returns

        # Should record all commands for debugging/testing
        assert ("custom_command", {"param": "value"}) in widget_factory.commands_handled


class TestBackwardCompatibility:
    """Test requirements for backward compatibility."""

    def test_legacy_adapter_works(self):
        """Test that LegacyWidgetAdapter provides backward compatibility."""
        from viloapp_sdk.widget import LegacyWidgetAdapter, WidgetMetadata, WidgetPosition

        # Create a mock legacy widget with old interface
        class LegacyWidget:
            def get_metadata(self):
                return WidgetMetadata(
                    id="legacy-widget",
                    title="Legacy Widget",
                    position=WidgetPosition.MAIN,
                    icon="legacy-icon"
                )

            def create_widget(self, parent=None):
                return QLabel("Legacy Widget", parent)

            def get_state(self):
                return {"legacy": "state"}

            def restore_state(self, state):
                pass

        legacy = LegacyWidget()
        adapter = LegacyWidgetAdapter(legacy)

        # New interface should work through adapter
        assert adapter.get_widget_id() == "legacy-widget"
        assert adapter.get_title() == "Legacy Widget"
        assert adapter.get_icon() == "legacy-icon"

        widget = adapter.create_instance("test-id")
        assert isinstance(widget, QWidget)

        state = adapter.get_state()
        assert isinstance(state, dict)
        assert state == {"legacy": "state"}

        # Should not raise
        adapter.restore_state({"test": "data"})


class TestInterfaceEvolution:
    """Test how the interface will evolve from old to new."""

    def test_migration_path_exists(self):
        """Test that migration from old to new interface is possible."""
        from viloapp_sdk.widget import LegacyWidgetAdapter, WidgetMetadata, WidgetPosition

        # Create a legacy widget implementation
        class LegacyWidget:
            def get_metadata(self):
                return WidgetMetadata(
                    id="migration-test",
                    title="Migration Test",
                    position=WidgetPosition.MAIN
                )

            def create_widget(self, parent=None):
                return QLabel("Migration Test", parent)

            def get_state(self):
                return {}

            def restore_state(self, state):
                pass

        legacy = LegacyWidget()

        # Old way - using metadata
        metadata = legacy.get_metadata()

        # New way - through adapter
        adapter = LegacyWidgetAdapter(legacy)
        assert adapter.get_widget_id() == metadata.id
        assert adapter.get_title() == metadata.title

        # Old create_widget adapted to create_instance
        old_widget = legacy.create_widget()
        new_widget = adapter.create_instance("test-id")

        # Both should create valid widgets
        assert isinstance(old_widget, QWidget)
        assert isinstance(new_widget, QWidget)