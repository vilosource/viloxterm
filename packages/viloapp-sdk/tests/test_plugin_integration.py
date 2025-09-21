"""Integration tests for plugin implementations with new IWidget interface."""

import pytest
from PySide6.QtWidgets import QWidget

from viloapp_sdk import IWidget


class TestPluginIntegration:
    """Test that real plugin implementations work with new interface."""

    def test_terminal_widget_new_interface(self, qtbot):
        """Test ViloxTerm widget implements new interface correctly."""
        try:
            from viloxterm.widget import TerminalWidgetFactory
        except ImportError:
            pytest.skip("ViloxTerm not available")

        factory = TerminalWidgetFactory()

        # Test new interface methods
        assert factory.get_widget_id() == "terminal"
        assert factory.get_title() == "Terminal"
        assert factory.get_icon() == "terminal"

        # Test instance creation
        widget = factory.create_instance("test-instance")
        assert isinstance(widget, QWidget)
        qtbot.addWidget(widget)

        # Test command handling
        result = factory.handle_command("get_sessions", {})
        assert isinstance(result, dict)

        # Test state management
        state = factory.get_state()
        assert isinstance(state, dict)
        assert "session_count" in state

        # Test cleanup
        factory.destroy_instance("test-instance")

    def test_editor_widget_new_interface(self, qtbot):
        """Test ViloxEdit widget implements new interface correctly."""
        try:
            from viloedit.widget import EditorWidgetFactory
        except ImportError:
            pytest.skip("ViloxEdit not available")

        factory = EditorWidgetFactory()

        # Test new interface methods
        assert factory.get_widget_id() == "editor"
        assert factory.get_title() == "Editor"
        assert factory.get_icon() == "file-text"

        # Test instance creation
        widget = factory.create_instance("test-instance")
        assert isinstance(widget, QWidget)
        qtbot.addWidget(widget)

        # Test command handling
        result = factory.handle_command("get_instances", {})
        assert isinstance(result, dict)

        # Test text operations
        result = factory.handle_command("set_text", {
            "instance_id": "test-instance",
            "text": "Hello, World!"
        })
        assert result is True

        result = factory.handle_command("get_text", {
            "instance_id": "test-instance"
        })
        assert "Hello, World!" in str(result)

        # Test state management
        state = factory.get_state()
        assert isinstance(state, dict)
        assert "instance_count" in state

        # Test cleanup
        factory.destroy_instance("test-instance")

    def test_interface_compliance(self):
        """Test that plugin implementations comply with IWidget interface."""
        plugins_to_test = []

        try:
            from viloxterm.widget import TerminalWidgetFactory
            plugins_to_test.append(TerminalWidgetFactory())
        except ImportError:
            pass

        try:
            from viloedit.widget import EditorWidgetFactory
            plugins_to_test.append(EditorWidgetFactory())
        except ImportError:
            pass

        for factory in plugins_to_test:
            # Verify it's an IWidget implementation
            assert isinstance(factory, IWidget)

            # Test all required methods exist and return correct types
            widget_id = factory.get_widget_id()
            assert isinstance(widget_id, str)
            assert len(widget_id) > 0

            title = factory.get_title()
            assert isinstance(title, str)
            assert len(title) > 0

            icon = factory.get_icon()
            assert icon is None or isinstance(icon, str)

            state = factory.get_state()
            assert isinstance(state, dict)

            # Test command handling returns something
            result = factory.handle_command("unknown_command", {})
            # Should not raise exception

    def test_backward_compatibility_with_real_plugins(self):
        """Test that LegacyWidgetAdapter works with old plugin code patterns."""
        from viloapp_sdk.widget import LegacyWidgetAdapter, WidgetMetadata, WidgetPosition

        # Simulate an old-style plugin
        class OldStylePlugin:
            def get_metadata(self):
                return WidgetMetadata(
                    id="old-plugin",
                    title="Old Plugin",
                    position=WidgetPosition.MAIN,
                    icon="old-icon"
                )

            def create_widget(self, parent=None):
                from PySide6.QtWidgets import QLabel
                return QLabel("Old Plugin Widget", parent)

            def get_state(self):
                return {"old": "state"}

            def restore_state(self, state):
                pass

        old_plugin = OldStylePlugin()
        adapter = LegacyWidgetAdapter(old_plugin)

        # Test adapter provides new interface
        assert adapter.get_widget_id() == "old-plugin"
        assert adapter.get_title() == "Old Plugin"
        assert adapter.get_icon() == "old-icon"

        widget = adapter.create_instance("test-id")
        assert isinstance(widget, QWidget)

        # Commands should work (return None for unsupported)
        result = adapter.handle_command("any_command", {})
        assert result is None

        state = adapter.get_state()
        assert state == {"old": "state"}