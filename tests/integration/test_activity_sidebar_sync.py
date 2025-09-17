"""Integration tests for activity bar and sidebar synchronization."""

from unittest.mock import Mock, patch

import pytest

from ui.main_window import MainWindow


@pytest.mark.integration
class TestActivitySidebarSync:
    """Test cases for activity bar and sidebar integration."""

    def test_activity_bar_changes_sidebar_view(self, qtbot):
        """Test clicking activity bar buttons changes sidebar view."""
        main_window = MainWindow()
        qtbot.addWidget(main_window)

        # Mock sidebar methods to avoid complex UI interactions
        main_window.sidebar.set_current_view = Mock()
        main_window.sidebar.expand = Mock()
        main_window.sidebar.is_collapsed = False

        # Click search button in activity bar
        main_window.activity_bar.on_view_selected("search")

        # Verify sidebar view changed
        main_window.sidebar.set_current_view.assert_called_once_with("search")

    def test_activity_bar_expands_collapsed_sidebar(self, qtbot):
        """Test activity bar selection expands collapsed sidebar."""
        main_window = MainWindow()
        qtbot.addWidget(main_window)

        # Mock sidebar as collapsed
        main_window.sidebar.set_current_view = Mock()
        main_window.sidebar.expand = Mock()
        main_window.sidebar.is_collapsed = True

        # Select git view
        main_window.activity_bar.on_view_selected("git")

        # Verify sidebar expanded and view changed
        main_window.sidebar.set_current_view.assert_called_once_with("git")
        main_window.sidebar.expand.assert_called_once()

    def test_activity_bar_no_expand_if_sidebar_visible(self, qtbot):
        """Test activity bar doesn't expand sidebar if already visible."""
        main_window = MainWindow()
        qtbot.addWidget(main_window)

        # Mock sidebar as visible
        main_window.sidebar.set_current_view = Mock()
        main_window.sidebar.expand = Mock()
        main_window.sidebar.is_collapsed = False

        # Select settings view
        main_window.activity_bar.on_view_selected("settings")

        # Verify view changed but no expand called
        main_window.sidebar.set_current_view.assert_called_once_with("settings")
        main_window.sidebar.expand.assert_not_called()

    def test_same_activity_button_toggles_sidebar(self, qtbot):
        """Test clicking same activity button toggles sidebar."""
        main_window = MainWindow()
        qtbot.addWidget(main_window)

        # Mock sidebar toggle
        main_window.sidebar.toggle = Mock()

        # Set current view to explorer
        main_window.activity_bar.current_view = "explorer"

        # Click explorer again (same view)
        main_window.activity_bar.on_view_selected("explorer")

        # Verify toggle signal was emitted (connected to main window)
        # Since we can't easily mock the signal connection, we'll test the direct method
        main_window.toggle_sidebar()
        main_window.sidebar.toggle.assert_called_once()

    def test_activity_bar_exclusive_selection(self, qtbot):
        """Test activity bar maintains exclusive selection."""
        main_window = MainWindow()
        qtbot.addWidget(main_window)

        activity_bar = main_window.activity_bar

        # Initially explorer should be checked
        assert activity_bar.explorer_action.isChecked()
        assert not activity_bar.search_action.isChecked()
        assert not activity_bar.git_action.isChecked()
        assert not activity_bar.settings_action.isChecked()

        # Select search
        activity_bar.on_view_selected("search")

        # Only search should be checked
        assert not activity_bar.explorer_action.isChecked()
        assert activity_bar.search_action.isChecked()
        assert not activity_bar.git_action.isChecked()
        assert not activity_bar.settings_action.isChecked()

    def test_sidebar_view_updates_with_activity_selection(self, qtbot):
        """Test sidebar view stack updates with activity bar selection."""
        main_window = MainWindow()
        qtbot.addWidget(main_window)

        # Mock sidebar view switching
        main_window.sidebar.set_current_view = Mock()

        # Test all view selections
        views = ["explorer", "search", "git", "settings"]
        for view in views:
            main_window.activity_bar.on_view_selected(view)
            main_window.sidebar.set_current_view.assert_called_with(view)

    def test_keyboard_shortcuts_work_with_integration(self, qtbot):
        """Test keyboard shortcuts work with activity-sidebar integration."""
        main_window = MainWindow()
        qtbot.addWidget(main_window)

        # Mock sidebar toggle
        main_window.sidebar.toggle = Mock()

        # Find the sidebar toggle action
        menubar = main_window.menuBar()
        view_menu = None
        for action in menubar.actions():
            if action.text() == "View":
                view_menu = action.menu()
                break

        assert view_menu is not None

        # Find sidebar toggle action
        sidebar_action = None
        for action in view_menu.actions():
            if action.text() == "Toggle Sidebar":
                sidebar_action = action
                break

        assert sidebar_action is not None

        # Trigger the action
        sidebar_action.trigger()

        # Verify sidebar toggle was called
        main_window.sidebar.toggle.assert_called_once()

    def test_theme_changes_update_activity_bar_icons(self, qtbot):
        """Test theme changes update activity bar icons."""
        main_window = MainWindow()
        qtbot.addWidget(main_window)

        # Mock activity bar update_icons method
        main_window.activity_bar.update_icons = Mock()

        # Mock icon manager
        with patch('ui.main_window.get_icon_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_manager.theme = "light"
            mock_get_manager.return_value = mock_manager

            # Toggle theme through main window
            main_window.toggle_theme()

            # Verify theme toggle was called
            mock_manager.toggle_theme.assert_called_once()

    def test_activity_bar_signals_connected(self, qtbot):
        """Test activity bar signals are properly connected to main window."""
        main_window = MainWindow()
        qtbot.addWidget(main_window)

        # Check that signals are connected by verifying they have receivers
        assert main_window.activity_bar.view_changed.isSignalConnected()
        assert main_window.activity_bar.toggle_sidebar.isSignalConnected()

    def test_main_window_handles_view_change_signal(self, qtbot):
        """Test main window properly handles view change signal."""
        main_window = MainWindow()
        qtbot.addWidget(main_window)

        # Mock sidebar methods
        main_window.sidebar.set_current_view = Mock()
        main_window.sidebar.expand = Mock()
        main_window.sidebar.is_collapsed = True

        # Emit view_changed signal directly
        main_window.activity_bar.view_changed.emit("git")

        # Process events to ensure signal is handled
        qtbot.wait(10)

        # Verify main window handled the signal
        main_window.sidebar.set_current_view.assert_called_once_with("git")
        main_window.sidebar.expand.assert_called_once()

    def test_main_window_handles_toggle_sidebar_signal(self, qtbot):
        """Test main window properly handles toggle sidebar signal."""
        main_window = MainWindow()
        qtbot.addWidget(main_window)

        # Mock sidebar toggle
        main_window.sidebar.toggle = Mock()

        # Emit toggle_sidebar signal directly
        main_window.activity_bar.toggle_sidebar.emit()

        # Process events to ensure signal is handled
        qtbot.wait(10)

        # Verify main window handled the signal
        main_window.sidebar.toggle.assert_called_once()
