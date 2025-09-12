"""Unit tests for the activity bar menu functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import QMenu, QMenuBar, QMainWindow
from ui.activity_bar import ActivityBar


@pytest.mark.unit
class TestActivityBarMenu:
    """Test cases for ActivityBar menu functionality."""

    def test_menu_action_properties(self, qtbot):
        """Test menu action has correct properties."""
        with patch('ui.activity_bar.get_icon_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_icon = QIcon()
            mock_manager.get_icon.return_value = mock_icon
            mock_get_manager.return_value = mock_manager
            
            activity_bar = ActivityBar()
            qtbot.addWidget(activity_bar)
            
            # Check menu action properties
            assert hasattr(activity_bar, 'menu_action')
            assert activity_bar.menu_action.text() == "Menu"
            assert not activity_bar.menu_action.isCheckable()
            assert activity_bar.menu_action.toolTip() == "Application Menu"
    
    def test_menu_icon_at_bottom(self, qtbot):
        """Test menu icon is positioned at the bottom after a spacer."""
        with patch('ui.activity_bar.get_icon_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_icon = QIcon()
            mock_manager.get_icon.return_value = mock_icon
            mock_get_manager.return_value = mock_manager
            
            activity_bar = ActivityBar()
            qtbot.addWidget(activity_bar)
            
            # Get all widgets in the toolbar
            widgets = []
            for i in range(activity_bar.layout().count()):
                item = activity_bar.layout().itemAt(i)
                if item and item.widget():
                    widgets.append(item.widget())
            
            # There should be a spacer widget before the menu
            # The spacer has expanding size policy
            from PySide6.QtWidgets import QSizePolicy
            spacer_found = False
            for widget in widgets:
                if widget and hasattr(widget, 'sizePolicy'):
                    policy = widget.sizePolicy()
                    if (policy.verticalPolicy() == QSizePolicy.Expanding and
                        policy.horizontalPolicy() == QSizePolicy.Expanding):
                        spacer_found = True
                        break
            
            assert spacer_found, "No spacer widget found to push menu to bottom"
    
    def test_menu_click_creates_popup(self, qtbot, monkeypatch):
        """Test clicking menu creates a popup menu."""
        with patch('ui.activity_bar.get_icon_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_icon = QIcon()
            mock_manager.get_icon.return_value = mock_icon
            mock_get_manager.return_value = mock_manager
            
            # Create a mock main window with menu bar
            mock_main_window = MagicMock(spec=QMainWindow)
            mock_menubar = MagicMock(spec=QMenuBar)
            mock_main_window.menuBar.return_value = mock_menubar
            
            # Create mock menu actions
            file_action = MagicMock(spec=QAction)
            file_action.text.return_value = "File"
            file_action.menu.return_value = MagicMock(spec=QMenu)
            file_action.menu().actions.return_value = []
            
            mock_menubar.actions.return_value = [file_action]
            
            activity_bar = ActivityBar()
            qtbot.addWidget(activity_bar)
            
            # Mock the window() method to return our mock main window
            monkeypatch.setattr(activity_bar, 'window', lambda: mock_main_window)
            
            # Mock QMenu to track its creation
            with patch('PySide6.QtWidgets.QMenu') as mock_qmenu_class:
                mock_menu = MagicMock(spec=QMenu)
                mock_qmenu_class.return_value = mock_menu
                
                # Trigger menu click
                activity_bar.on_menu_clicked()
                
                # Verify QMenu was created
                mock_qmenu_class.assert_called_once_with(activity_bar)
                
                # Verify menu style was set (this would have caught our error!)
                mock_menu.setStyleSheet.assert_called_once()
                
                # Verify exec was called to show the menu
                mock_menu.exec.assert_called_once()
    
    def test_menu_stylesheet_valid(self, qtbot):
        """Test menu stylesheet doesn't throw NameError for undefined constants."""
        with patch('ui.activity_bar.get_icon_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_icon = QIcon()
            mock_manager.get_icon.return_value = mock_icon
            mock_get_manager.return_value = mock_manager
            
            # Create a real main window for more realistic test
            main_window = QMainWindow()
            menubar = main_window.menuBar()
            
            # Add a simple menu
            file_menu = menubar.addMenu("File")
            file_menu.addAction("Test Action")
            
            activity_bar = ActivityBar()
            main_window.setCentralWidget(activity_bar)
            qtbot.addWidget(main_window)
            
            # This should not raise NameError for undefined theme constants
            try:
                activity_bar.on_menu_clicked()
            except NameError as e:
                pytest.fail(f"Stylesheet contains undefined constant: {e}")
    
    def test_menu_copies_all_menus(self, qtbot, monkeypatch):
        """Test menu popup copies all menus from menu bar."""
        with patch('ui.activity_bar.get_icon_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_icon = QIcon()
            mock_manager.get_icon.return_value = mock_icon
            mock_get_manager.return_value = mock_manager
            
            # Create mock main window with multiple menus
            mock_main_window = MagicMock(spec=QMainWindow)
            mock_menubar = MagicMock(spec=QMenuBar)
            mock_main_window.menuBar.return_value = mock_menubar
            
            # Create mock menu actions
            file_action = MagicMock(spec=QAction)
            file_action.text.return_value = "File"
            file_action.menu.return_value = MagicMock(spec=QMenu)
            file_action.menu().actions.return_value = []
            
            view_action = MagicMock(spec=QAction)
            view_action.text.return_value = "View"
            view_action.menu.return_value = MagicMock(spec=QMenu)
            view_action.menu().actions.return_value = []
            
            mock_menubar.actions.return_value = [file_action, view_action]
            
            activity_bar = ActivityBar()
            qtbot.addWidget(activity_bar)
            
            # Mock the window() method
            monkeypatch.setattr(activity_bar, 'window', lambda: mock_main_window)
            
            with patch('ui.activity_bar.QMenu') as mock_qmenu_class:
                mock_menu = MagicMock(spec=QMenu)
                mock_qmenu_class.return_value = mock_menu
                
                # Trigger menu click
                activity_bar.on_menu_clicked()
                
                # Verify addMenu was called for each menu
                assert mock_menu.addMenu.call_count == 2
                mock_menu.addMenu.assert_any_call("File")
                mock_menu.addMenu.assert_any_call("View")
    
    def test_menu_handles_missing_menubar(self, qtbot):
        """Test menu handles case when menubar is not available."""
        with patch('ui.activity_bar.get_icon_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_icon = QIcon()
            mock_manager.get_icon.return_value = mock_icon
            mock_get_manager.return_value = mock_manager
            
            activity_bar = ActivityBar()
            qtbot.addWidget(activity_bar)
            
            # Set window to None to simulate missing main window
            activity_bar.setParent(None)
            
            # This should not crash
            with patch('ui.activity_bar.logger') as mock_logger:
                activity_bar.on_menu_clicked()
                
                # Verify warning was logged
                mock_logger.warning.assert_called_once_with(
                    "Could not access main window menu bar"
                )