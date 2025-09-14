#!/usr/bin/env python3
"""
Unit tests for AppWidgetManager.

Tests the centralized widget management system including registration,
creation, and querying of widgets.
"""

import pytest
from unittest.mock import MagicMock, patch, call
from core.app_widget_manager import AppWidgetManager
from core.app_widget_metadata import AppWidgetMetadata, WidgetCategory
from ui.widgets.widget_registry import WidgetType
from ui.widgets.app_widget import AppWidget


@pytest.fixture
def manager():
    """Provide a clean AppWidgetManager instance for each test."""
    # Clear singleton instance
    AppWidgetManager._instance = None
    manager = AppWidgetManager.get_instance()
    manager.clear()
    return manager


@pytest.fixture
def mock_widget_class():
    """Mock AppWidget class that behaves like real widgets."""
    mock_class = MagicMock()
    # Create a mock instance that will be returned
    mock_instance = MagicMock(spec=AppWidget)
    # Configure the class to return the instance when called with just widget_id
    mock_class.return_value = mock_instance
    return mock_class


@pytest.fixture
def sample_metadata(mock_widget_class):
    """Sample widget metadata for testing."""
    return AppWidgetMetadata(
        widget_id="test.widget",
        widget_type=WidgetType.CUSTOM,
        display_name="Test Widget",
        description="A test widget",
        icon="test-icon",
        category=WidgetCategory.TOOLS,
        widget_class=mock_widget_class,
        open_command="test.open",
        provides_capabilities=["test_capability"],
        requires_services=["test_service"],
        source="test"  # Prevent auto-prefixing
    )


class TestAppWidgetManagerSingleton:
    """Test singleton behavior."""

    def test_singleton_instance(self):
        """Test that manager is a singleton."""
        manager1 = AppWidgetManager.get_instance()
        manager2 = AppWidgetManager.get_instance()
        assert manager1 is manager2

    def test_singleton_new(self):
        """Test that __new__ returns same instance."""
        manager1 = AppWidgetManager()
        manager2 = AppWidgetManager()
        assert manager1 is manager2


class TestWidgetRegistration:
    """Test widget registration functionality."""

    def test_register_widget(self, manager, sample_metadata):
        """Test registering a widget."""
        manager.register_widget(sample_metadata)

        assert "test.widget" in manager
        assert len(manager) == 1

        retrieved = manager.get_widget_metadata("test.widget")
        assert retrieved == sample_metadata

    def test_register_duplicate_widget(self, manager, sample_metadata):
        """Test registering duplicate widget updates existing."""
        manager.register_widget(sample_metadata)

        # Modify and re-register
        sample_metadata.description = "Updated description"
        manager.register_widget(sample_metadata)

        assert len(manager) == 1
        retrieved = manager.get_widget_metadata("test.widget")
        assert retrieved.description == "Updated description"

    def test_unregister_widget(self, manager, sample_metadata):
        """Test unregistering a widget."""
        manager.register_widget(sample_metadata)
        assert len(manager) == 1

        success = manager.unregister_widget("test.widget")
        assert success
        assert len(manager) == 0
        assert "test.widget" not in manager

    def test_unregister_nonexistent_widget(self, manager):
        """Test unregistering widget that doesn't exist."""
        success = manager.unregister_widget("nonexistent")
        assert not success

    def test_type_mapping(self, manager, sample_metadata):
        """Test that widget type mapping is maintained."""
        manager.register_widget(sample_metadata)

        by_type = manager.get_widget_by_type(WidgetType.CUSTOM)
        assert by_type == sample_metadata


class TestWidgetCreation:
    """Test widget creation functionality."""

    def test_create_widget_with_class(self, manager, sample_metadata, mock_widget_class):
        """Test creating widget using widget class."""
        manager.register_widget(sample_metadata)

        widget = manager.create_widget("test.widget", "instance_123")

        assert widget is not None
        mock_widget_class.assert_called_once_with("instance_123")

    def test_create_widget_with_factory(self, manager, mock_widget_class):
        """Test creating widget using factory function."""
        mock_factory = MagicMock(return_value=MagicMock(spec=AppWidget))

        metadata = AppWidgetMetadata(
            widget_id="factory.widget",
            widget_type=WidgetType.CUSTOM,
            display_name="Factory Widget",
            description="Widget with factory",
            icon="factory",
            category=WidgetCategory.TOOLS,
            widget_class=mock_widget_class,
            factory=mock_factory
        )

        manager.register_widget(metadata)
        widget = manager.create_widget("factory.widget", "instance_456")

        assert widget is not None
        mock_factory.assert_called_once_with("instance_456")
        mock_widget_class.assert_not_called()

    def test_create_widget_by_type(self, manager, sample_metadata, mock_widget_class):
        """Test creating widget by WidgetType enum."""
        manager.register_widget(sample_metadata)

        widget = manager.create_widget_by_type(WidgetType.CUSTOM, "instance_789")

        assert widget is not None
        mock_widget_class.assert_called_once_with("instance_789")

    def test_create_unregistered_widget(self, manager):
        """Test creating widget that isn't registered."""
        widget = manager.create_widget("unregistered", "instance")
        assert widget is None

    def test_create_widget_with_exception(self, manager, mock_widget_class):
        """Test widget creation when exception occurs."""
        mock_widget_class.side_effect = Exception("Creation failed")

        metadata = AppWidgetMetadata(
            widget_id="error.widget",
            widget_type=WidgetType.CUSTOM,
            display_name="Error Widget",
            description="Widget that fails",
            icon="error",
            category=WidgetCategory.TOOLS,
            widget_class=mock_widget_class
        )

        manager.register_widget(metadata)
        widget = manager.create_widget("error.widget", "instance")

        assert widget is None


class TestWidgetQuerying:
    """Test widget querying functionality."""

    def test_get_all_widgets(self, manager):
        """Test getting all widgets."""
        # Register multiple widgets
        for i in range(3):
            metadata = AppWidgetMetadata(
                widget_id=f"widget_{i}",
                widget_type=WidgetType.CUSTOM,
                display_name=f"Widget {i}",
                description=f"Description {i}",
                icon=f"icon_{i}",
                category=WidgetCategory.TOOLS,
                widget_class=MagicMock(),
                source="test"
            )
            manager.register_widget(metadata)

        all_widgets = manager.get_all_widgets()
        assert len(all_widgets) == 3

    def test_get_widgets_by_category(self, manager, mock_widget_class):
        """Test filtering widgets by category."""
        # Register widgets in different categories
        categories = [WidgetCategory.TOOLS, WidgetCategory.EDITOR, WidgetCategory.TOOLS]
        for i, category in enumerate(categories):
            metadata = AppWidgetMetadata(
                widget_id=f"widget_{i}",
                widget_type=WidgetType.CUSTOM,
                display_name=f"Widget {i}",
                description=f"Description {i}",
                icon=f"icon_{i}",
                category=category,
                widget_class=mock_widget_class
            )
            manager.register_widget(metadata)

        tools_widgets = manager.get_widgets_by_category(WidgetCategory.TOOLS)
        assert len(tools_widgets) == 2

        editor_widgets = manager.get_widgets_by_category(WidgetCategory.EDITOR)
        assert len(editor_widgets) == 1

    def test_get_widgets_by_source(self, manager, mock_widget_class):
        """Test filtering widgets by source."""
        # Register builtin widget
        builtin = AppWidgetMetadata(
            widget_id="builtin.widget",
            widget_type=WidgetType.CUSTOM,
            display_name="Builtin",
            description="Builtin widget",
            icon="builtin",
            category=WidgetCategory.TOOLS,
            widget_class=mock_widget_class,
            source="builtin"
        )
        manager.register_widget(builtin)

        # Register plugin widget
        plugin = AppWidgetMetadata(
            widget_id="plugin.widget",
            widget_type=WidgetType.CUSTOM,
            display_name="Plugin",
            description="Plugin widget",
            icon="plugin",
            category=WidgetCategory.TOOLS,
            widget_class=mock_widget_class,
            source="plugin"
        )
        manager.register_widget(plugin)

        builtin_widgets = manager.get_widgets_by_source("builtin")
        assert len(builtin_widgets) == 1
        assert builtin_widgets[0].widget_id == "builtin.widget"

        plugin_widgets = manager.get_widgets_by_source("plugin")
        assert len(plugin_widgets) == 1
        assert plugin_widgets[0].widget_id == "plugin.widget"

    def test_get_widgets_with_capability(self, manager, mock_widget_class):
        """Test filtering widgets by capability."""
        # Register widgets with different capabilities
        metadata1 = AppWidgetMetadata(
            widget_id="widget1",
            widget_type=WidgetType.CUSTOM,
            display_name="Widget 1",
            description="Description 1",
            icon="icon1",
            category=WidgetCategory.TOOLS,
            widget_class=mock_widget_class,
            provides_capabilities=["editing", "preview"]
        )
        manager.register_widget(metadata1)

        metadata2 = AppWidgetMetadata(
            widget_id="widget2",
            widget_type=WidgetType.CUSTOM,
            display_name="Widget 2",
            description="Description 2",
            icon="icon2",
            category=WidgetCategory.TOOLS,
            widget_class=mock_widget_class,
            provides_capabilities=["preview", "export"]
        )
        manager.register_widget(metadata2)

        preview_widgets = manager.get_widgets_with_capability("preview")
        assert len(preview_widgets) == 2

        editing_widgets = manager.get_widgets_with_capability("editing")
        assert len(editing_widgets) == 1
        assert editing_widgets[0].widget_id in ["widget1", "com.viloapp.widget1"]

    def test_get_widgets_for_file_type(self, manager, mock_widget_class):
        """Test filtering widgets by file type support."""
        metadata = AppWidgetMetadata(
            widget_id="editor",
            widget_type=WidgetType.TEXT_EDITOR,
            display_name="Editor",
            description="Text editor",
            icon="edit",
            category=WidgetCategory.EDITOR,
            widget_class=mock_widget_class,
            supported_file_types=["txt", "py", "js"]
        )
        manager.register_widget(metadata)

        # Test with extension
        py_widgets = manager.get_widgets_for_file_type(".py")
        assert len(py_widgets) == 1
        assert py_widgets[0].widget_id in ["editor", "com.viloapp.editor"]

        # Test without dot
        txt_widgets = manager.get_widgets_for_file_type("txt")
        assert len(txt_widgets) == 1

        # Test unsupported type
        exe_widgets = manager.get_widgets_for_file_type("exe")
        assert len(exe_widgets) == 0

    def test_get_menu_widgets(self, manager, mock_widget_class):
        """Test getting widgets for menu display."""
        # Widget shown in menu
        shown = AppWidgetMetadata(
            widget_id="shown",
            widget_type=WidgetType.CUSTOM,
            display_name="Shown",
            description="Shown in menu",
            icon="shown",
            category=WidgetCategory.TOOLS,
            widget_class=mock_widget_class,
            show_in_menu=True
        )
        manager.register_widget(shown)

        # Widget hidden from menu
        hidden = AppWidgetMetadata(
            widget_id="hidden",
            widget_type=WidgetType.CUSTOM,
            display_name="Hidden",
            description="Hidden from menu",
            icon="hidden",
            category=WidgetCategory.TOOLS,
            widget_class=mock_widget_class,
            show_in_menu=False
        )
        manager.register_widget(hidden)

        menu_widgets = manager.get_menu_widgets()
        assert len(menu_widgets) == 1
        assert menu_widgets[0].widget_id in ["shown", "com.viloapp.shown"]


class TestBackwardCompatibility:
    """Test backward compatibility features."""

    def test_register_factory_compat(self, manager, mock_widget_class):
        """Test backward compatible factory registration."""
        # First register widget
        metadata = AppWidgetMetadata(
            widget_id="compat.widget",
            widget_type=WidgetType.TERMINAL,
            display_name="Compat Widget",
            description="Backward compatible",
            icon="compat",
            category=WidgetCategory.TERMINAL,
            widget_class=mock_widget_class
        )
        manager.register_widget(metadata)

        # Use backward compatible factory registration
        mock_factory = MagicMock()
        with pytest.warns(DeprecationWarning):
            manager.register_factory_compat(WidgetType.TERMINAL, mock_factory)

        # Verify factory was updated
        updated = manager.get_widget_metadata("compat.widget")
        assert updated.factory == mock_factory

    def test_register_factory_compat_unknown_type(self, manager):
        """Test backward compatible factory registration with unknown type."""
        mock_factory = MagicMock()

        # Should warn but not crash
        with pytest.warns(DeprecationWarning):
            manager.register_factory_compat(WidgetType.DEBUGGER, mock_factory)


class TestUtilityMethods:
    """Test utility methods."""

    def test_clear(self, manager, sample_metadata):
        """Test clearing all widgets."""
        manager.register_widget(sample_metadata)
        assert len(manager) == 1

        manager.clear()
        assert len(manager) == 0
        assert "test.widget" not in manager

    def test_len(self, manager):
        """Test __len__ method."""
        assert len(manager) == 0

        for i in range(5):
            metadata = AppWidgetMetadata(
                widget_id=f"widget_{i}",
                widget_type=WidgetType.CUSTOM,
                display_name=f"Widget {i}",
                description=f"Description {i}",
                icon=f"icon_{i}",
                category=WidgetCategory.TOOLS,
                widget_class=MagicMock(),
                source="test"
            )
            manager.register_widget(metadata)

        assert len(manager) == 5

    def test_contains(self, manager, sample_metadata):
        """Test __contains__ method."""
        assert "test.widget" not in manager

        manager.register_widget(sample_metadata)
        assert "test.widget" in manager

    def test_repr(self, manager, sample_metadata):
        """Test __repr__ method."""
        repr_str = repr(manager)
        assert "AppWidgetManager" in repr_str
        assert "0 widgets" in repr_str

        manager.register_widget(sample_metadata)
        repr_str = repr(manager)
        assert "1 widgets" in repr_str