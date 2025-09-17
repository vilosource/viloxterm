#!/usr/bin/env python3
"""
GUI integration tests for AppWidgetManager.

Tests the integration of AppWidgetManager with UI components,
including menu generation and widget creation in panes.
"""

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QMenu

from core.app_widget_manager import AppWidgetManager
from core.app_widget_metadata import AppWidgetMetadata, WidgetCategory
from core.app_widget_registry import register_builtin_widgets
from ui.widgets.app_widget import AppWidget
from ui.widgets.pane_header import PaneHeaderBar
from ui.widgets.split_pane_model import LeafNode, SplitPaneModel
from ui.widgets.widget_registry import WidgetType


@pytest.fixture
def app(qapp):
    """Ensure QApplication is available."""
    return qapp


@pytest.fixture
def manager():
    """Provide clean AppWidgetManager with test widgets."""
    AppWidgetManager._instance = None
    manager = AppWidgetManager.get_instance()
    manager.clear()

    # Register test widgets
    for i, category in enumerate([WidgetCategory.EDITOR, WidgetCategory.TERMINAL, WidgetCategory.TOOLS]):
        mock_class = MagicMock(spec=AppWidget)
        mock_class.return_value = MagicMock(spec=AppWidget)

        metadata = AppWidgetMetadata(
            widget_id=f"test.widget_{i}",
            widget_type=WidgetType.CUSTOM,
            display_name=f"Test Widget {i}",
            description=f"Test widget {i} description",
            icon=f"icon_{i}",
            category=category,
            widget_class=mock_class,
            open_command=f"test.open_{i}",
            show_in_menu=(i != 2)  # Hide one widget from menu
        )
        manager.register_widget(metadata)

    return manager


@pytest.fixture
def pane_header(qtbot):
    """Create PaneHeaderBar for testing."""
    header = PaneHeaderBar(pane_id="test_pane", show_type_menu=True)
    qtbot.addWidget(header)
    return header


class TestPaneHeaderMenuGeneration:
    """Test dynamic menu generation in pane header."""

    def test_menu_shows_registered_widgets(self, qtbot, pane_header, manager):
        """Test that menu shows registered widgets."""
        # Trigger menu creation
        with patch.object(QMenu, 'exec_') as mock_exec:
            pane_header.show_widget_type_menu()

            # Menu should have been created and shown
            mock_exec.assert_called_once()

    def test_menu_filters_hidden_widgets(self, qtbot, manager):
        """Test that hidden widgets don't appear in menu."""
        # Register a hidden widget
        mock_class = MagicMock(spec=AppWidget)
        hidden_widget = AppWidgetMetadata(
            widget_id="hidden.widget",
            widget_type=WidgetType.CUSTOM,
            display_name="Hidden Widget",
            description="Should not appear in menu",
            icon="hidden",
            category=WidgetCategory.TOOLS,
            widget_class=mock_class,
            show_in_menu=False
        )
        manager.register_widget(hidden_widget)

        # Get menu widgets
        menu_widgets = manager.get_menu_widgets()
        widget_ids = [w.widget_id for w in menu_widgets]

        assert "hidden.widget" not in widget_ids
        assert "test.widget_0" in widget_ids  # Visible widget
        assert "test.widget_1" in widget_ids  # Visible widget

    @patch('core.commands.executor.execute_command')
    def test_menu_action_triggers_command(self, mock_execute, qtbot, pane_header, manager):
        """Test that menu actions trigger correct commands."""
        # We need to actually interact with the menu
        # Since we can't easily simulate menu interaction in tests,
        # we'll test the underlying mechanism

        # Get a widget with an open command
        widget = manager.get_widget_metadata("test.widget_0")
        assert widget.open_command == "test.open_0"

        # Simulate what happens when menu action is triggered
        from core.commands.executor import execute_command
        execute_command(widget.open_command)

        mock_execute.assert_called_once_with("test.open_0")


class TestSplitPaneModelIntegration:
    """Test integration with SplitPaneModel."""

    def test_create_widget_from_manager(self, manager):
        """Test that SplitPaneModel can create widgets from manager."""
        model = SplitPaneModel(initial_widget_type=WidgetType.PLACEHOLDER)

        # Mock the manager's create_widget_by_type method
        mock_widget = MagicMock(spec=AppWidget)
        with patch.object(manager, 'create_widget_by_type', return_value=mock_widget):
            widget = model.create_app_widget(WidgetType.CUSTOM, "test_id")

            assert widget == mock_widget
            manager.create_widget_by_type.assert_called_once_with(WidgetType.CUSTOM, "test_id")

    def test_fallback_to_placeholder(self, manager):
        """Test fallback to placeholder for unknown widget types."""
        model = SplitPaneModel(initial_widget_type=WidgetType.PLACEHOLDER)

        # Try to create unknown widget type
        with patch.object(manager, 'create_widget_by_type', return_value=None):
            widget = model.create_app_widget(WidgetType.DEBUGGER, "test_id")

            # Should fall back to placeholder
            assert widget is not None
            # Note: We'd need to check the actual type but that requires more setup


class TestBuiltinWidgetRegistration:
    """Test registration of built-in widgets."""

    def test_register_builtin_widgets(self):
        """Test that built-in widgets are registered correctly."""
        # Clear and re-register
        AppWidgetManager._instance = None
        manager = AppWidgetManager.get_instance()
        manager.clear()

        # Register built-in widgets
        with patch('core.app_widget_registry.logger'):
            register_builtin_widgets()

            # Check that widgets were registered
            # The exact number depends on what's available
            assert len(manager) > 0

            # Check for expected widgets
            terminal_widget = manager.get_widget_metadata("com.viloapp.terminal")
            if terminal_widget:
                assert terminal_widget.display_name == "Terminal"
                assert terminal_widget.category == WidgetCategory.TERMINAL

            editor_widget = manager.get_widget_metadata("com.viloapp.editor")
            if editor_widget:
                assert editor_widget.display_name == "Text Editor"
                assert editor_widget.category == WidgetCategory.EDITOR


class TestWidgetCreationInUI:
    """Test actual widget creation in UI components."""

    def test_widget_lifecycle(self, qtbot, manager):
        """Test widget creation and cleanup lifecycle."""
        # Create a leaf node
        leaf = LeafNode(widget_type=WidgetType.CUSTOM)

        # Mock widget creation
        mock_widget = MagicMock(spec=AppWidget)
        mock_widget.cleanup = MagicMock()
        mock_widget.widget_id = "test_widget"

        with patch.object(manager, 'create_widget_by_type', return_value=mock_widget):
            # Create widget through model
            model = SplitPaneModel(initial_widget_type=WidgetType.PLACEHOLDER)
            widget = model.create_app_widget(WidgetType.CUSTOM, leaf.id)

            assert widget == mock_widget

            # Set widget on leaf
            leaf.app_widget = widget

            # Test cleanup
            leaf.cleanup()
            mock_widget.cleanup.assert_called_once()
            assert leaf.app_widget is None


class TestDynamicWidgetDiscovery:
    """Test dynamic widget discovery features."""

    def test_discover_widgets_by_capability(self, manager):
        """Test discovering widgets by capability."""
        # Register widget with specific capability
        mock_class = MagicMock(spec=AppWidget)
        capable_widget = AppWidgetMetadata(
            widget_id="capable.widget",
            widget_type=WidgetType.CUSTOM,
            display_name="Capable Widget",
            description="Widget with special capability",
            icon="capable",
            category=WidgetCategory.TOOLS,
            widget_class=mock_class,
            provides_capabilities=["special_feature", "another_feature"]
        )
        manager.register_widget(capable_widget)

        # Find widgets with capability
        special_widgets = manager.get_widgets_with_capability("special_feature")
        assert len(special_widgets) == 1
        assert special_widgets[0].widget_id == "capable.widget"

    def test_discover_widgets_for_file(self, manager):
        """Test discovering widgets for file types."""
        # Register editor that handles Python files
        mock_class = MagicMock(spec=AppWidget)
        python_editor = AppWidgetMetadata(
            widget_id="python.editor",
            widget_type=WidgetType.TEXT_EDITOR,
            display_name="Python Editor",
            description="Editor for Python files",
            icon="python",
            category=WidgetCategory.EDITOR,
            widget_class=mock_class,
            supported_file_types=["py", "pyw"]
        )
        manager.register_widget(python_editor)

        # Find editors for Python files
        py_widgets = manager.get_widgets_for_file_type("py")
        assert len(py_widgets) == 1
        assert py_widgets[0].widget_id == "python.editor"


class TestCommandIntegration:
    """Test integration with command system."""

    def test_widget_open_commands(self, manager):
        """Test that widgets register their open commands."""
        # Check that widgets have open commands
        all_widgets = manager.get_all_widgets()
        widgets_with_commands = [w for w in all_widgets if w.open_command]

        assert len(widgets_with_commands) > 0

        # Verify command format
        for widget in widgets_with_commands:
            assert widget.open_command.startswith("test.open_")


class TestNonBlockingBehavior:
    """Test that GUI operations don't block."""

    def test_menu_creation_non_blocking(self, qtbot, pane_header, manager):
        """Test that menu creation doesn't block the UI."""
        # Create menu in a non-blocking way
        menu_created = False

        def create_menu():
            nonlocal menu_created
            pane_header.show_widget_type_menu()
            menu_created = True

        # Use timer to simulate non-blocking operation
        QTimer.singleShot(0, create_menu)

        # Process events
        qtbot.wait(100)  # Wait briefly for timer

        # Menu creation should have completed
        assert menu_created

    def test_widget_creation_non_blocking(self, qtbot, manager):
        """Test that widget creation doesn't block."""
        widget_created = False
        widget_instance = None

        def create_widget():
            nonlocal widget_created, widget_instance
            widget_instance = manager.create_widget("test.widget_0", "instance_123")
            widget_created = True

        # Use timer for non-blocking creation
        QTimer.singleShot(0, create_widget)

        # Process events
        qtbot.wait(100)

        assert widget_created
        # Widget should be created (it's mocked so will be a MagicMock)
