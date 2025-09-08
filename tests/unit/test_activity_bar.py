"""Unit tests for the activity bar component."""

import pytest
from unittest.mock import Mock, patch
from pytestqt.qt_compat import qt_api
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction, QIcon
from ui.activity_bar import ActivityBar


@pytest.mark.unit
class TestActivityBar:
    """Test cases for ActivityBar class."""

    def test_activity_bar_initialization(self, qtbot):
        """Test activity bar initializes correctly."""
        with patch('ui.activity_bar.get_icon_manager') as mock_get_manager:
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
        with patch('ui.activity_bar.get_icon_manager') as mock_get_manager:
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
        with patch('ui.activity_bar.get_icon_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_icon = QIcon()
            mock_manager.get_icon.return_value = mock_icon
            mock_get_manager.return_value = mock_manager
            
            activity_bar = ActivityBar()
            qtbot.addWidget(activity_bar)
            
            # Check actions exist
            assert hasattr(activity_bar, 'explorer_action')
            assert hasattr(activity_bar, 'search_action')
            assert hasattr(activity_bar, 'git_action')
            assert hasattr(activity_bar, 'settings_action')
            
            # Check actions are added to toolbar
            actions = activity_bar.actions()
            action_texts = [action.text() for action in actions if not action.isSeparator()]
            assert "Explorer" in action_texts
            assert "Search" in action_texts
            assert "Git" in action_texts
            assert "Settings" in action_texts

    def test_on_view_selected_new_view(self, qtbot):
        """Test selecting a new view."""
        with patch('ui.activity_bar.get_icon_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_icon = QIcon()
            mock_manager.get_icon.return_value = mock_icon
            mock_get_manager.return_value = mock_manager
            
            activity_bar = ActivityBar()
            qtbot.addWidget(activity_bar)
            
            # Connect signal for testing
            with qtbot.waitSignal(activity_bar.view_changed, timeout=1000) as blocker:
                activity_bar.on_view_selected("search")
                
            # Check signal was emitted with correct value
            assert blocker.args == ["search"]
            
            # Check current view updated
            assert activity_bar.current_view == "search"
            
            # Check action states
            assert not activity_bar.explorer_action.isChecked()
            assert activity_bar.search_action.isChecked()
            assert not activity_bar.git_action.isChecked()
            assert not activity_bar.settings_action.isChecked()

    def test_on_view_selected_same_view(self, qtbot):
        """Test selecting the same view toggles sidebar."""
        with patch('ui.activity_bar.get_icon_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_icon = QIcon()
            mock_manager.get_icon.return_value = mock_icon
            mock_get_manager.return_value = mock_manager
            
            activity_bar = ActivityBar()
            qtbot.addWidget(activity_bar)
            
            # Connect signal for testing
            with qtbot.waitSignal(activity_bar.toggle_sidebar, timeout=1000):
                activity_bar.on_view_selected("explorer")  # Same as current_view

    def test_update_icons_on_theme_change(self, qtbot):
        """Test icons are updated when theme changes."""
        with patch('ui.activity_bar.get_icon_manager') as mock_get_manager:
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
            
            # Verify get_icon was called for each icon
            expected_calls = ["explorer", "search", "git", "settings"]
            actual_calls = [call[0][0] for call in mock_manager.get_icon.call_args_list]
            assert set(expected_calls) == set(actual_calls)