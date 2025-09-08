"""Unit tests for the main window component."""

import pytest
from unittest.mock import Mock, patch
from pytestqt.qt_compat import qt_api
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QKeySequence
from ui.main_window import MainWindow


@pytest.mark.unit
class TestMainWindow:
    """Test cases for MainWindow class."""

    def test_main_window_initialization(self, qtbot):
        """Test main window initializes correctly."""
        window = MainWindow()
        qtbot.addWidget(window)
        
        assert window.windowTitle() == "ViloApp"
        assert window.size().width() == 1200
        assert window.size().height() == 800
        
    def test_ui_components_created(self, qtbot):
        """Test all UI components are created."""
        window = MainWindow()
        qtbot.addWidget(window)
        
        assert hasattr(window, 'activity_bar')
        assert hasattr(window, 'sidebar')
        assert hasattr(window, 'workspace')
        assert hasattr(window, 'status_bar')
        assert hasattr(window, 'main_splitter')
        assert window.activity_bar is not None
        assert window.sidebar is not None
        assert window.workspace is not None
        assert window.status_bar is not None

    def test_menu_bar_created(self, qtbot):
        """Test menu bar is created with correct actions."""
        window = MainWindow()
        qtbot.addWidget(window)
        
        menubar = window.menuBar()
        assert menubar is not None
        
        # Check menu exists
        menus = [action.text() for action in menubar.actions()]
        assert "File" in menus
        assert "View" in menus
        
    def test_global_shortcuts_created(self, qtbot):
        """Test global shortcuts are created."""
        window = MainWindow()
        qtbot.addWidget(window)
        
        # Check menu toggle shortcut exists
        assert hasattr(window, 'menu_toggle_shortcut')
        assert window.menu_toggle_shortcut.key() == QKeySequence("Ctrl+Shift+M")

    def test_splitter_initial_sizes(self, qtbot):
        """Test splitter has correct initial sizes."""
        window = MainWindow()
        qtbot.addWidget(window)
        
        sizes = window.main_splitter.sizes()
        assert len(sizes) == 2
        assert sizes[0] == 250  # Sidebar width
        assert sizes[1] == 950  # Workspace width

    def test_activity_view_changed_signal(self, qtbot):
        """Test activity bar view change updates sidebar."""
        window = MainWindow()
        qtbot.addWidget(window)
        
        # Mock sidebar methods
        window.sidebar.set_current_view = Mock()
        window.sidebar.expand = Mock()
        window.sidebar.is_collapsed = True
        
        # Trigger signal
        window.on_activity_view_changed("search")
        
        # Verify calls
        window.sidebar.set_current_view.assert_called_once_with("search")
        window.sidebar.expand.assert_called_once()

    def test_activity_view_changed_no_expand_if_not_collapsed(self, qtbot):
        """Test activity view change doesn't expand if sidebar not collapsed."""
        window = MainWindow()
        qtbot.addWidget(window)
        
        # Mock sidebar methods
        window.sidebar.set_current_view = Mock()
        window.sidebar.expand = Mock()
        window.sidebar.is_collapsed = False
        
        # Trigger signal
        window.on_activity_view_changed("git")
        
        # Verify calls
        window.sidebar.set_current_view.assert_called_once_with("git")
        window.sidebar.expand.assert_not_called()

    def test_toggle_sidebar(self, qtbot):
        """Test sidebar toggle functionality."""
        window = MainWindow()
        qtbot.addWidget(window)
        
        # Mock sidebar toggle
        window.sidebar.toggle = Mock()
        
        # Call toggle
        window.toggle_sidebar()
        
        # Verify call
        window.sidebar.toggle.assert_called_once()

    def test_toggle_theme(self, qtbot):
        """Test theme toggle functionality."""
        window = MainWindow()
        qtbot.addWidget(window)
        
        # Mock icon manager
        with patch('ui.main_window.get_icon_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_manager.theme = "light"
            mock_get_manager.return_value = mock_manager
            
            # Mock status bar
            window.status_bar.set_message = Mock()
            
            # Call toggle theme
            window.toggle_theme()
            
            # Verify calls
            mock_manager.toggle_theme.assert_called_once()
            window.status_bar.set_message.assert_called_once_with("Switched to Light theme", 2000)

    def test_toggle_menu_bar_hide(self, qtbot):
        """Test menu bar toggle hides when visible."""
        window = MainWindow()
        qtbot.addWidget(window)
        
        # Ensure menu bar is visible
        menubar = window.menuBar()
        menubar.show()
        assert menubar.isVisible()
        
        # Mock status bar
        window.status_bar.set_message = Mock()
        
        # Toggle menu bar
        window.toggle_menu_bar()
        
        # Verify hidden and status message
        assert not menubar.isVisible()
        window.status_bar.set_message.assert_called_once_with(
            "Menu bar hidden. Press Ctrl+Shift+M to show", 3000
        )

    def test_toggle_menu_bar_show(self, qtbot):
        """Test menu bar toggle shows when hidden."""
        window = MainWindow()
        qtbot.addWidget(window)
        
        # Hide menu bar first
        menubar = window.menuBar()
        menubar.hide()
        assert not menubar.isVisible()
        
        # Mock status bar
        window.status_bar.set_message = Mock()
        
        # Toggle menu bar
        window.toggle_menu_bar()
        
        # Verify shown and status message
        assert menubar.isVisible()
        window.status_bar.set_message.assert_called_once_with("Menu bar shown", 2000)

    @patch('ui.main_window.QSettings')
    def test_save_state(self, mock_settings_class, qtbot):
        """Test state saving functionality."""
        mock_settings = Mock()
        mock_settings_class.return_value = mock_settings
        
        window = MainWindow()
        qtbot.addWidget(window)
        
        # Mock methods
        window.saveGeometry = Mock(return_value=b'geometry_data')
        window.saveState = Mock(return_value=b'state_data')
        window.main_splitter.saveState = Mock(return_value=b'splitter_data')
        window.menuBar().isVisible = Mock(return_value=True)
        
        # Call save state
        window.save_state()
        
        # Verify QSettings calls
        mock_settings.beginGroup.assert_called_once_with("MainWindow")
        mock_settings.setValue.assert_any_call("geometry", b'geometry_data')
        mock_settings.setValue.assert_any_call("windowState", b'state_data')
        mock_settings.setValue.assert_any_call("splitterSizes", b'splitter_data')
        mock_settings.setValue.assert_any_call("menuBarVisible", True)
        mock_settings.endGroup.assert_called_once()

    @patch('ui.main_window.QSettings')
    def test_restore_state(self, mock_settings_class, qtbot):
        """Test state restoration functionality."""
        mock_settings = Mock()
        mock_settings_class.return_value = mock_settings
        
        # Mock settings values
        mock_settings.value.side_effect = lambda key, default=None, type=None: {
            "geometry": b'geometry_data',
            "windowState": b'state_data',
            "splitterSizes": b'splitter_data',
            "menuBarVisible": True
        }.get(key, default)
        
        window = MainWindow()
        qtbot.addWidget(window)
        
        # Mock methods
        window.restoreGeometry = Mock()
        window.restoreState = Mock()
        window.main_splitter.restoreState = Mock()
        window.menuBar().setVisible = Mock()
        
        # Call restore state
        window.restore_state()
        
        # Verify restoration calls
        window.restoreGeometry.assert_called_once_with(b'geometry_data')
        window.restoreState.assert_called_once_with(b'state_data')
        window.main_splitter.restoreState.assert_called_once_with(b'splitter_data')
        window.menuBar().setVisible.assert_called_once_with(True)

    @patch('ui.main_window.QSettings')
    def test_restore_state_no_saved_data(self, mock_settings_class, qtbot):
        """Test state restoration with no saved data."""
        mock_settings = Mock()
        mock_settings_class.return_value = mock_settings
        
        # Mock settings to return None for all values
        mock_settings.value.return_value = None
        
        window = MainWindow()
        qtbot.addWidget(window)
        
        # Mock methods
        window.restoreGeometry = Mock()
        window.restoreState = Mock()
        window.main_splitter.restoreState = Mock()
        
        # Call restore state
        window.restore_state()
        
        # Verify no restoration calls made
        window.restoreGeometry.assert_not_called()
        window.restoreState.assert_not_called()
        window.main_splitter.restoreState.assert_not_called()

    def test_close_event_saves_state(self, qtbot):
        """Test close event triggers state saving."""
        window = MainWindow()
        qtbot.addWidget(window)
        
        # Mock save_state method
        window.save_state = Mock()
        
        # Create mock close event
        close_event = Mock()
        close_event.accept = Mock()
        
        # Call close event
        window.closeEvent(close_event)
        
        # Verify save state called and event accepted
        window.save_state.assert_called_once()
        close_event.accept.assert_called_once()

    def test_signal_connections(self, qtbot):
        """Test signal connections are established."""
        window = MainWindow()
        qtbot.addWidget(window)
        
        # Verify activity bar signals connected
        assert window.activity_bar.view_changed.isSignalConnected()
        assert window.activity_bar.toggle_sidebar.isSignalConnected()
        
    def test_menu_actions_shortcuts(self, qtbot):
        """Test menu actions have correct shortcuts."""
        window = MainWindow()
        qtbot.addWidget(window)
        
        menubar = window.menuBar()
        view_menu = None
        
        # Find view menu
        for action in menubar.actions():
            if action.text() == "View":
                view_menu = action.menu()
                break
                
        assert view_menu is not None
        
        # Check shortcuts exist
        actions = {action.text(): action for action in view_menu.actions()}
        
        assert "Toggle Theme" in actions
        assert actions["Toggle Theme"].shortcut() == QKeySequence("Ctrl+T")
        
        assert "Toggle Sidebar" in actions
        assert actions["Toggle Sidebar"].shortcut() == QKeySequence("Ctrl+B")

    def test_debug_menu_exists(self, qtbot):
        """Test that debug menu exists with reset action."""
        window = MainWindow()
        qtbot.addWidget(window)
        
        # Find debug menu
        menubar = window.menuBar()
        debug_menu = None
        for action in menubar.actions():
            if action.text() == "Debug":
                debug_menu = action.menu()
                break
        
        assert debug_menu is not None
        
        # Check reset action exists
        actions = {action.text(): action for action in debug_menu.actions()}
        assert "Reset App State" in actions
        assert actions["Reset App State"].shortcut() == QKeySequence("Ctrl+Shift+R")

    @patch('ui.main_window.QMessageBox.question')
    @patch('ui.main_window.QSettings')
    def test_reset_app_state_user_confirms(self, mock_settings_class, mock_question, qtbot):
        """Test reset app state when user confirms."""
        # Mock user clicking Yes
        mock_question.return_value = QMessageBox.Yes
        
        # Mock settings to return appropriate values during restore
        mock_settings = Mock()
        mock_settings.value.side_effect = lambda key, default=None, type=None: default
        mock_settings_class.return_value = mock_settings
        
        window = MainWindow()
        qtbot.addWidget(window)
        
        # Mock the _reset_to_defaults method
        window._reset_to_defaults = Mock()
        
        # Call reset
        window.reset_app_state()
        
        # Verify confirmation dialog was shown
        mock_question.assert_called_once()
        call_args = mock_question.call_args[0]
        assert "Reset Application State" in call_args[1]
        assert "default state" in call_args[2]
        
        # Verify settings were cleared
        mock_settings.clear.assert_called_once()
        
        # Verify defaults were reset
        window._reset_to_defaults.assert_called_once()

    @patch('ui.main_window.QMessageBox.question')
    @patch('ui.main_window.QSettings')
    def test_reset_app_state_user_cancels(self, mock_settings_class, mock_question, qtbot):
        """Test reset app state when user cancels."""
        # Mock user clicking No
        mock_question.return_value = QMessageBox.No
        
        # Mock settings to return appropriate values during restore  
        mock_settings = Mock()
        mock_settings.value.side_effect = lambda key, default=None, type=None: default
        mock_settings_class.return_value = mock_settings
        
        window = MainWindow()
        qtbot.addWidget(window)
        
        # Call reset
        window.reset_app_state()
        
        # Verify confirmation dialog was shown
        mock_question.assert_called_once()
        
        # Verify settings were NOT cleared
        mock_settings.clear.assert_not_called()

    @patch('ui.main_window.QMessageBox.critical')
    @patch('ui.main_window.QMessageBox.question')
    @patch('ui.main_window.QSettings')
    def test_reset_app_state_handles_error(self, mock_settings_class, mock_question, mock_critical, qtbot):
        """Test reset app state handles errors gracefully."""
        # Mock user clicking Yes
        mock_question.return_value = QMessageBox.Yes
        
        # Mock settings to return appropriate values during restore, but raise exception on clear
        mock_settings = Mock()
        mock_settings.value.side_effect = lambda key, default=None, type=None: default
        mock_settings.clear.side_effect = Exception("Settings error")
        mock_settings_class.return_value = mock_settings
        
        window = MainWindow()
        qtbot.addWidget(window)
        
        # Call reset
        window.reset_app_state()
        
        # Verify error dialog was shown
        mock_critical.assert_called_once()
        call_args = mock_critical.call_args[0]
        assert "Reset Failed" in call_args[1]
        assert "Settings error" in call_args[2]

    def test_reset_to_defaults(self, qtbot):
        """Test _reset_to_defaults method."""
        window = MainWindow()
        qtbot.addWidget(window)
        
        # Mock methods to avoid Qt operations in tests
        window.resize = Mock()
        window.move = Mock()
        window.screen = Mock()
        window.screen.return_value.geometry.return_value.width.return_value = 1920
        window.screen.return_value.geometry.return_value.height.return_value = 1080
        window.geometry = Mock()
        window.geometry.return_value.width.return_value = 1200
        window.geometry.return_value.height.return_value = 800
        window.main_splitter.setSizes = Mock()
        window.menuBar().setVisible = Mock()
        window.sidebar.is_collapsed = False
        window.sidebar.expand = Mock()
        window.workspace.reset_to_default_layout = Mock()
        
        # Mock icon manager
        with patch('ui.main_window.get_icon_manager') as mock_icon_manager:
            mock_manager = Mock()
            mock_manager._detect_system_theme.return_value = "light"
            mock_icon_manager.return_value = mock_manager
            
            # Call reset to defaults
            window._reset_to_defaults()
            
            # Verify window was reset
            window.resize.assert_called_once_with(1200, 800)
            window.move.assert_called_once()
            window.main_splitter.setSizes.assert_called_once_with([250, 950])
            window.menuBar().setVisible.assert_called_once_with(True)
            window.workspace.reset_to_default_layout.assert_called_once()
            
            # Verify theme was reset
            assert mock_manager.theme == "light"