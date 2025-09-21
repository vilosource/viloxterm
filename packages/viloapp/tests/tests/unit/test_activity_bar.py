"""Unit tests for the activity bar component."""

from unittest.mock import Mock, patch

import pytest
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon

from viloapp.ui.activity_bar import ActivityBar


@pytest.mark.unit
class TestActivityBar:
    """Test cases for ActivityBar class."""

    def test_activity_bar_initialization(self, qtbot):
        """Test activity bar initializes correctly."""
        with patch("viloapp.ui.activity_bar.get_icon_manager") as mock_get_manager:
            mock_manager = Mock()
            mock_icon = QIcon()  # Use real QIcon instead of Mock
            mock_manager.get_icon.return_value = mock_icon
            mock_get_manager.return_value = mock_manager

            activity_bar = ActivityBar()
            qtbot.addWidget(activity_bar)

            assert activity_bar.current_view == "explorer"
            assert activity_bar.orientation() == Qt.Vertical
            assert not activity_bar.isMovable()
            assert not activity_bar.isFloatable()
            assert activity_bar.iconSize() == QSize(24, 24)
            assert activity_bar.width() == 48

    def test_ui_setup(self, qtbot):
        """Test UI setup is correct."""
        with patch("viloapp.ui.activity_bar.get_icon_manager") as mock_get_manager:
            mock_manager = Mock()
            mock_icon = QIcon()
            mock_manager.get_icon.return_value = mock_icon
            mock_get_manager.return_value = mock_manager

            activity_bar = ActivityBar()
            qtbot.addWidget(activity_bar)

            assert activity_bar.objectName() == "activityBar"
            assert activity_bar.property("type") == "activitybar"

    def test_actions_created(self, qtbot):
        """Test all actions are created."""
        with patch("viloapp.ui.activity_bar.get_icon_manager") as mock_get_manager:
            mock_manager = Mock()
            mock_icon = QIcon()
            mock_manager.get_icon.return_value = mock_icon
            mock_get_manager.return_value = mock_manager

            activity_bar = ActivityBar()
            qtbot.addWidget(activity_bar)

            # Check actions exist
            assert hasattr(activity_bar, "explorer_action")
            assert hasattr(activity_bar, "search_action")
            assert hasattr(activity_bar, "git_action")
            assert hasattr(activity_bar, "settings_action")
            assert hasattr(activity_bar, "menu_action")  # Check menu action exists

            # Check actions are added to toolbar
            actions = activity_bar.actions()
            action_texts = [action.text() for action in actions if not action.isSeparator()]
            assert "Explorer" in action_texts
            assert "Search" in action_texts
            assert "Git" in action_texts
            assert "Settings" in action_texts
            assert "Menu" in action_texts  # Check menu action is added

    def test_on_view_selected_new_view(self, qtbot):
        """Test selecting a new view."""
        with (
            patch("viloapp.ui.activity_bar.get_icon_manager") as mock_get_manager,
            patch("viloapp.ui.activity_bar.execute_command") as mock_execute,
        ):
            mock_manager = Mock()
            mock_icon = QIcon()
            mock_manager.get_icon.return_value = mock_icon
            mock_get_manager.return_value = mock_manager

            activity_bar = ActivityBar()
            qtbot.addWidget(activity_bar)

            # Connect signal for testing
            with qtbot.waitSignal(activity_bar.view_changed, timeout=1000) as blocker:
                activity_bar.show_view("search")

            # Check signal was emitted with correct value
            assert blocker.args == ["search"]

            # Check current view updated
            assert activity_bar.current_view == "search"

            # Check action states
            assert not activity_bar.explorer_action.isChecked()
            assert activity_bar.search_action.isChecked()
            assert not activity_bar.git_action.isChecked()
            assert not activity_bar.settings_action.isChecked()

            # Verify command was executed
            mock_execute.assert_called_with("workbench.view.search")

    def test_on_view_selected_same_view(self, qtbot):
        """Test selecting the same view toggles sidebar."""
        with (
            patch("viloapp.ui.activity_bar.get_icon_manager") as mock_get_manager,
            patch("viloapp.ui.activity_bar.execute_command"),
        ):
            mock_manager = Mock()
            mock_icon = QIcon()
            mock_manager.get_icon.return_value = mock_icon
            mock_get_manager.return_value = mock_manager

            activity_bar = ActivityBar()
            qtbot.addWidget(activity_bar)

            # Connect signal for testing
            with qtbot.waitSignal(activity_bar.toggle_sidebar, timeout=1000):
                activity_bar.show_view("explorer")  # Same as current_view

    def test_update_icons_on_theme_change(self, qtbot):
        """Test icons are updated when theme changes."""
        with patch("viloapp.ui.activity_bar.get_icon_manager") as mock_get_manager:
            mock_manager = Mock()
            mock_icon = QIcon()
            mock_manager.get_icon.return_value = mock_icon
            mock_get_manager.return_value = mock_manager

            activity_bar = ActivityBar()
            qtbot.addWidget(activity_bar)

            # Reset mock to track update_icons calls
            mock_manager.get_icon.reset_mock()

            # Call update_icons
            activity_bar.update_icons()

            # Verify get_icon was called for each icon including menu
            expected_calls = ["explorer", "search", "git", "settings", "menu"]
            actual_calls = [call[0][0] for call in mock_manager.get_icon.call_args_list]
            assert set(expected_calls) == set(actual_calls)
