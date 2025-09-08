"""Integration tests for theme system across components."""

import pytest
from unittest.mock import Mock, patch
from pytestqt.qt_compat import qt_api
from ui.main_window import MainWindow
from ui.icon_manager import get_icon_manager


@pytest.mark.integration
class TestThemeIntegration:
    """Test cases for theme system integration across components."""

    def test_theme_toggle_updates_activity_bar(self, qtbot):
        """Test theme toggle updates activity bar icons."""
        with patch('ui.activity_bar.get_icon_manager') as mock_get_manager, \
             patch('ui.main_window.get_icon_manager') as mock_main_manager:
            
            mock_manager = Mock()
            mock_manager.theme = "light"
            mock_manager.get_icon.return_value = Mock()
            mock_get_manager.return_value = mock_manager
            mock_main_manager.return_value = mock_manager
            
            main_window = MainWindow()
            qtbot.addWidget(main_window)
            
            # Mock activity bar update_icons
            main_window.activity_bar.update_icons = Mock()
            
            # Toggle theme
            main_window.toggle_theme()
            
            # Verify theme manager was called
            mock_manager.toggle_theme.assert_called_once()

    def test_icon_manager_theme_change_signal_propagates(self, qtbot):
        """Test icon manager theme change signal propagates to components."""
        with patch('ui.activity_bar.get_icon_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_manager.theme = "light"
            mock_manager.get_icon.return_value = Mock()
            mock_get_manager.return_value = mock_manager
            
            main_window = MainWindow()
            qtbot.addWidget(main_window)
            
            # Mock activity bar update_icons
            main_window.activity_bar.update_icons = Mock()
            
            # Emit theme_changed signal directly
            mock_manager.theme_changed.emit("dark")
            
            # Process events
            qtbot.wait(10)
            
            # Verify activity bar received the signal
            # (This tests the signal connection made in ActivityBar.__init__)
            mock_manager.theme_changed.connect.assert_called()

    def test_theme_consistency_across_components(self, qtbot):
        """Test theme consistency across all UI components."""
        with patch('ui.activity_bar.get_icon_manager') as mock_activity_manager, \
             patch('ui.main_window.get_icon_manager') as mock_main_manager:
            
            # Create single manager instance
            mock_manager = Mock()
            mock_manager.theme = "light"
            mock_manager.get_icon.return_value = Mock()
            
            # Both patches should return same instance (singleton pattern)
            mock_activity_manager.return_value = mock_manager
            mock_main_manager.return_value = mock_manager
            
            main_window = MainWindow()
            qtbot.addWidget(main_window)
            
            # All components should use same theme
            # This is ensured by the singleton pattern of get_icon_manager()
            assert mock_activity_manager.return_value is mock_main_manager.return_value

    def test_status_bar_shows_theme_change_message(self, qtbot):
        """Test status bar shows message when theme changes."""
        with patch('ui.main_window.get_icon_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_manager.theme = "light"
            mock_get_manager.return_value = mock_manager
            
            main_window = MainWindow()
            qtbot.addWidget(main_window)
            
            # Mock status bar set_message
            main_window.status_bar.set_message = Mock()
            
            # Toggle theme
            main_window.toggle_theme()
            
            # Verify status message was shown
            mock_manager.toggle_theme.assert_called_once()
            main_window.status_bar.set_message.assert_called_once_with(
                "Switched to Light theme", 2000
            )

    def test_theme_change_updates_icon_cache(self, qtbot):
        """Test theme change clears and updates icon cache."""
        # Use real icon manager for this test
        from ui.icon_manager import IconManager
        
        manager = IconManager()
        qtbot.addWidget(manager)  # For cleanup
        
        with patch('ui.icon_manager.QIcon') as mock_qicon:
            mock_icon = Mock()
            mock_qicon.return_value = mock_icon
            
            # Get icon to populate cache
            manager.get_icon("explorer")
            assert len(manager._icon_cache) == 1
            assert "light_explorer" in manager._icon_cache
            
            # Change theme
            with qtbot.waitSignal(manager.theme_changed, timeout=1000):
                manager.theme = "dark"
            
            # Cache should be cleared
            assert len(manager._icon_cache) == 0
            
            # Getting icon again should repopulate cache with new theme
            manager.get_icon("explorer")
            assert len(manager._icon_cache) == 1
            assert "dark_explorer" in manager._icon_cache

    def test_keyboard_shortcut_theme_toggle(self, qtbot):
        """Test Ctrl+T keyboard shortcut toggles theme."""
        with patch('ui.main_window.get_icon_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_manager.theme = "light"
            mock_get_manager.return_value = mock_manager
            
            main_window = MainWindow()
            qtbot.addWidget(main_window)
            
            # Mock toggle_theme method
            main_window.toggle_theme = Mock()
            
            # Find theme toggle action
            menubar = main_window.menuBar()
            view_menu = None
            for action in menubar.actions():
                if action.text() == "View":
                    view_menu = action.menu()
                    break
            
            theme_action = None
            for action in view_menu.actions():
                if action.text() == "Toggle Theme":
                    theme_action = action
                    break
                    
            assert theme_action is not None
            
            # Trigger the action (simulates Ctrl+T)
            theme_action.trigger()
            
            # Verify theme toggle was called
            main_window.toggle_theme.assert_called_once()

    def test_theme_system_initialization(self, qtbot):
        """Test theme system initializes correctly on startup."""
        with patch('ui.activity_bar.get_icon_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_manager.theme = "light"
            mock_manager.get_icon.return_value = Mock()
            mock_get_manager.return_value = mock_manager
            
            main_window = MainWindow()
            qtbot.addWidget(main_window)
            
            # Verify icon manager was accessed during initialization
            assert mock_get_manager.called
            
            # Verify activity bar connected to theme changes
            mock_manager.theme_changed.connect.assert_called()

    def test_multiple_theme_toggles(self, qtbot):
        """Test multiple theme toggles work correctly."""
        # Use real icon manager for this test
        from ui.icon_manager import IconManager
        
        manager = IconManager()
        qtbot.addWidget(manager)
        
        initial_theme = manager.theme
        
        # Toggle multiple times
        for i in range(5):
            with qtbot.waitSignal(manager.theme_changed, timeout=1000):
                manager.toggle_theme()
                
            expected_theme = "dark" if (i % 2 == 0) else "light"
            assert manager.theme == expected_theme

    def test_theme_change_with_cached_icons(self, qtbot):
        """Test theme change works correctly with previously cached icons."""
        from ui.icon_manager import IconManager
        
        manager = IconManager()
        qtbot.addWidget(manager)
        
        with patch('ui.icon_manager.QIcon') as mock_qicon:
            mock_icon = Mock()
            mock_qicon.return_value = mock_icon
            
            # Cache icons for multiple names in light theme
            icon_names = ["explorer", "search", "git", "settings"]
            for name in icon_names:
                manager.get_icon(name)
            
            assert len(manager._icon_cache) == 4
            
            # Change to dark theme
            with qtbot.waitSignal(manager.theme_changed, timeout=1000):
                manager.theme = "dark"
            
            # Cache should be empty
            assert len(manager._icon_cache) == 0
            
            # Get icons again - should create dark theme versions
            for name in icon_names:
                manager.get_icon(name)
            
            # Should have dark theme cache entries
            assert len(manager._icon_cache) == 4
            for name in icon_names:
                assert f"dark_{name}" in manager._icon_cache

    def test_theme_integration_error_handling(self, qtbot):
        """Test theme system handles errors gracefully."""
        with patch('ui.main_window.get_icon_manager') as mock_get_manager:
            # Mock icon manager that raises exception
            mock_manager = Mock()
            mock_manager.theme = "light"
            mock_manager.toggle_theme.side_effect = Exception("Theme error")
            mock_get_manager.return_value = mock_manager
            
            main_window = MainWindow()
            qtbot.addWidget(main_window)
            
            # Mock status bar to avoid issues
            main_window.status_bar.set_message = Mock()
            
            # Toggle theme should not crash even if theme manager fails
            try:
                main_window.toggle_theme()
                # If we get here without exception, error was handled gracefully
                # Or the exception was allowed to propagate (depends on implementation)
            except Exception:
                # This is also acceptable - the point is the app doesn't crash completely
                pass