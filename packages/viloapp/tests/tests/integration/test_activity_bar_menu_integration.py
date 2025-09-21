"""Integration tests for activity bar menu with main window."""

import pytest
from PySide6.QtWidgets import QMenu

from viloapp.ui.main_window import MainWindow


@pytest.mark.integration
class TestActivityBarMenuIntegration:
    """Test activity bar menu integration with main window."""

    def test_menu_icon_visible_in_activity_bar(self, qtbot):
        """Test menu icon is visible in the activity bar."""
        window = MainWindow()
        qtbot.addWidget(window)
        window.show()

        # Check menu action exists
        assert hasattr(window.activity_bar, "menu_action")
        assert window.activity_bar.menu_action.isVisible()
        assert window.activity_bar.menu_action.text() == "Menu"

    def test_use_activity_bar_menu_toggle(self, qtbot):
        """Test 'Use Activity Bar Menu' toggle in View menu."""
        window = MainWindow()
        qtbot.addWidget(window)
        window.show()

        # Check the action exists
        assert hasattr(window, "auto_hide_menubar_action")
        assert window.auto_hide_menubar_action.isCheckable()

        # Initially menu bar should be visible
        assert window.menuBar().isVisible()

        # Toggle the action
        window.auto_hide_menubar_action.setChecked(True)
        window.on_auto_hide_menubar_toggled(True)

        # Menu bar should now be hidden
        assert not window.menuBar().isVisible()

        # Toggle back
        window.auto_hide_menubar_action.setChecked(False)
        window.on_auto_hide_menubar_toggled(False)

        # Menu bar should be visible again
        assert window.menuBar().isVisible()

    def test_menu_popup_contains_all_menus(self, qtbot):
        """Test menu popup contains all menus from menu bar."""
        window = MainWindow()
        qtbot.addWidget(window)
        window.show()

        # Get menu bar menus
        menubar = window.menuBar()
        menubar_actions = menubar.actions()
        menubar_menu_names = [
            action.text() for action in menubar_actions if action.menu()
        ]

        # We should have File, View, Debug menus
        assert "File" in menubar_menu_names
        assert "View" in menubar_menu_names
        assert "Debug" in menubar_menu_names

        # Mock the exec method to prevent actual popup
        original_exec = QMenu.exec
        exec_called = False
        menu_instance = None

        def mock_exec(self, pos=None):
            nonlocal exec_called, menu_instance
            exec_called = True
            menu_instance = self
            return None

        QMenu.exec = mock_exec

        try:
            # Trigger menu click
            window.activity_bar.on_menu_clicked()

            # Verify exec was called
            assert exec_called, "Menu exec was not called"

            # Verify menu was created
            assert menu_instance is not None

            # Check menu contains expected submenus
            menu_actions = menu_instance.actions()
            menu_names = [action.text() for action in menu_actions if action.menu()]

            assert "File" in menu_names
            assert "View" in menu_names
            assert "Debug" in menu_names

        finally:
            # Restore original exec
            QMenu.exec = original_exec

    def test_menu_click_with_hidden_menubar(self, qtbot):
        """Test menu click works when menu bar is hidden."""
        window = MainWindow()
        qtbot.addWidget(window)
        window.show()

        # Hide menu bar
        window.menuBar().setVisible(False)

        # Mock exec to prevent popup
        original_exec = QMenu.exec
        exec_called = False

        def mock_exec(self, pos=None):
            nonlocal exec_called
            exec_called = True
            return None

        QMenu.exec = mock_exec

        try:
            # This should still work even with hidden menu bar
            window.activity_bar.on_menu_clicked()

            # Verify menu was shown
            assert exec_called, "Menu was not shown"

        finally:
            QMenu.exec = original_exec

    def test_menu_position_relative_to_button(self, qtbot):
        """Test menu appears at the correct position relative to button."""
        window = MainWindow()
        qtbot.addWidget(window)
        window.show()

        # Mock exec to capture position
        original_exec = QMenu.exec
        menu_position = None

        def mock_exec(self, pos):
            nonlocal menu_position
            menu_position = pos
            return None

        QMenu.exec = mock_exec

        try:
            # Trigger menu
            window.activity_bar.on_menu_clicked()

            # Verify position was set
            assert menu_position is not None

            # Position should be to the right of activity bar
            button_rect = window.activity_bar.actionGeometry(
                window.activity_bar.menu_action
            )
            expected_pos = window.activity_bar.mapToGlobal(button_rect.topRight())

            # The position should be close to expected
            # (allowing some tolerance for different platforms)
            assert abs(menu_position.x() - expected_pos.x()) < 10
            assert abs(menu_position.y() - expected_pos.y()) < 10

        finally:
            QMenu.exec = original_exec

    def test_theme_constants_defined(self, qtbot):
        """Test all theme constants used in stylesheet are defined."""
        window = MainWindow()
        qtbot.addWidget(window)
        window.show()

        # Import theme constants to check they exist
        from viloapp.ui.vscode_theme import (
            MENU_BACKGROUND,
            MENU_FOREGROUND,
            MENU_SELECTION_BACKGROUND,
            SPLITTER_BACKGROUND,
        )

        # These should all be defined
        assert MENU_BACKGROUND is not None
        assert MENU_FOREGROUND is not None
        assert SPLITTER_BACKGROUND is not None
        assert MENU_SELECTION_BACKGROUND is not None

        # Trigger menu to ensure no NameError
        original_exec = QMenu.exec
        QMenu.exec = lambda self, pos=None: None

        try:
            # This should not raise NameError
            window.activity_bar.on_menu_clicked()
        except NameError as e:
            pytest.fail(f"Theme constant not defined: {e}")
        finally:
            QMenu.exec = original_exec
