"""Unit tests for the icon manager component."""

import pytest
from unittest.mock import Mock, patch
from pytestqt.qt_compat import qt_api
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSize
from ui.icon_manager import IconManager, get_icon_manager


@pytest.mark.unit
class TestIconManager:
    """Test cases for IconManager class."""

    def test_icon_manager_initialization(self, qtbot):
        """Test icon manager initializes correctly."""
        manager = IconManager()
        #qtbot.addWidget(manager)  # For proper cleanup
        
        assert manager.theme == "light"
        assert isinstance(manager._icon_cache, dict)
        assert len(manager._icon_cache) == 0

    def test_theme_property_getter(self, qtbot):
        """Test theme property getter."""
        manager = IconManager()
        #qtbot.addWidget(manager)
        
        assert manager.theme == "light"
        
        # Change theme internally and check getter
        manager._theme = "dark"
        assert manager.theme == "dark"

    def test_theme_property_setter_valid_values(self, qtbot):
        """Test theme property setter with valid values."""
        manager = IconManager()
        #qtbot.addWidget(manager)
        
        # Test setting to dark
        with qtbot.waitSignal(manager.theme_changed, timeout=1000) as blocker:
            manager.theme = "dark"
            
        assert manager.theme == "dark"
        assert blocker.args == ["dark"]
        assert len(manager._icon_cache) == 0  # Cache should be cleared

    def test_theme_property_setter_invalid_values(self, qtbot):
        """Test theme property setter with invalid values."""
        manager = IconManager()
        #qtbot.addWidget(manager)
        
        initial_theme = manager.theme
        
        # Test invalid theme values
        manager.theme = "invalid"
        assert manager.theme == initial_theme  # Should not change
        
        manager.theme = "blue"
        assert manager.theme == initial_theme  # Should not change
        
        manager.theme = ""
        assert manager.theme == initial_theme  # Should not change

    def test_theme_property_setter_same_value(self, qtbot):
        """Test theme property setter with same value doesn't emit signal."""
        manager = IconManager()
        #qtbot.addWidget(manager)
        
        # Set same theme (should not emit signal)
        manager.theme = "light"
        
        # We can't easily test that signal was NOT emitted
        # but we can verify state is consistent
        assert manager.theme == "light"

    def test_get_icon_caches_icons(self, qtbot):
        """Test get_icon caches icons properly."""
        manager = IconManager()
        #qtbot.addWidget(manager)
        
        # Mock QIcon to avoid resource loading issues
        with patch('ui.icon_manager.QIcon') as mock_qicon:
            mock_icon = Mock()
            mock_qicon.return_value = mock_icon
            
            # Get icon first time
            icon1 = manager.get_icon("explorer")
            
            # Get same icon second time
            icon2 = manager.get_icon("explorer")
            
            # Should return cached version (same instance)
            assert icon1 is icon2
            assert "light_explorer" in manager._icon_cache

    def test_get_icon_different_themes(self, qtbot):
        """Test get_icon returns different icons for different themes."""
        manager = IconManager()
        #qtbot.addWidget(manager)
        
        with patch('ui.icon_manager.QIcon') as mock_qicon:
            mock_icon = Mock()
            mock_qicon.return_value = mock_icon
            
            # Get icon in light theme
            manager.theme = "light"
            light_icon = manager.get_icon("search")
            
            # Get icon in dark theme
            manager.theme = "dark"
            dark_icon = manager.get_icon("search")
            
            # Should be different instances due to theme change clearing cache
            assert light_icon is not dark_icon
            assert "dark_search" in manager._icon_cache

    def test_get_icon_creates_proper_paths(self, qtbot):
        """Test get_icon creates proper resource paths."""
        manager = IconManager()
        #qtbot.addWidget(manager)
        
        with patch('ui.icon_manager.QIcon') as mock_qicon:
            mock_icon = Mock()
            mock_qicon.return_value = mock_icon
            
            # Get icon
            manager.get_icon("git")
            
            # Check addFile was called with correct paths
            calls = mock_icon.addFile.call_args_list
            
            # Should have calls for Normal, Active, and Selected states
            assert len(calls) >= 2
            
            # Check paths contain correct theme and icon name
            for call in calls:
                path = call[0][0]  # First argument is the path
                assert "git" in path
                assert ("light" in path or "dark" in path)

    def test_get_icon_with_states(self, qtbot):
        """Test get_icon_with_states creates icon with multiple states."""
        manager = IconManager()
        #qtbot.addWidget(manager)
        
        with patch('ui.icon_manager.QIcon') as mock_qicon:
            mock_icon = Mock()
            mock_qicon.return_value = mock_icon
            
            # Get icon with states
            icon = manager.get_icon_with_states("settings")
            
            # Check addFile was called multiple times for different states
            calls = mock_icon.addFile.call_args_list
            assert len(calls) == 4  # Normal, Disabled, Active, Selected
            
            # Check that both themes are used (current and opposite)
            paths = [call[0][0] for call in calls]
            assert any("light" in path for path in paths)
            assert any("dark" in path for path in paths)

    def test_detect_system_theme(self, qtbot):
        """Test detect_system_theme sets theme to light."""
        manager = IconManager()
        #qtbot.addWidget(manager)
        
        # Set theme to dark first
        manager._theme = "dark"
        
        # Detect system theme
        manager.detect_system_theme()
        
        # Should set theme to light (current implementation)
        assert manager.theme == "light"

    def test_toggle_theme_light_to_dark(self, qtbot):
        """Test toggle_theme switches from light to dark."""
        manager = IconManager()
        #qtbot.addWidget(manager)
        
        # Start with light theme
        manager._theme = "light"
        
        # Toggle theme
        with qtbot.waitSignal(manager.theme_changed, timeout=1000) as blocker:
            manager.toggle_theme()
            
        assert manager.theme == "dark"
        assert blocker.args == ["dark"]

    def test_toggle_theme_dark_to_light(self, qtbot):
        """Test toggle_theme switches from dark to light."""
        manager = IconManager()
        #qtbot.addWidget(manager)
        
        # Start with dark theme
        manager._theme = "dark"
        
        # Toggle theme
        with qtbot.waitSignal(manager.theme_changed, timeout=1000) as blocker:
            manager.toggle_theme()
            
        assert manager.theme == "light"
        assert blocker.args == ["light"]

    def test_cache_clearing_on_theme_change(self, qtbot):
        """Test cache is cleared when theme changes."""
        manager = IconManager()
        #qtbot.addWidget(manager)
        
        with patch('ui.icon_manager.QIcon') as mock_qicon:
            mock_icon = Mock()
            mock_qicon.return_value = mock_icon
            
            # Add item to cache
            manager.get_icon("explorer")
            assert len(manager._icon_cache) == 1
            
            # Change theme
            manager.theme = "dark"
            
            # Cache should be cleared
            assert len(manager._icon_cache) == 0

    def test_theme_changed_signal_defined(self, qtbot):
        """Test theme_changed signal is properly defined."""
        manager = IconManager()
        #qtbot.addWidget(manager)
        
        assert hasattr(manager, 'theme_changed')
        # Signal should be connectable
        mock_slot = Mock()
        manager.theme_changed.connect(mock_slot)

    def test_icon_cache_keys(self, qtbot):
        """Test icon cache uses correct keys."""
        manager = IconManager()
        #qtbot.addWidget(manager)
        
        with patch('ui.icon_manager.QIcon') as mock_qicon:
            mock_icon = Mock()
            mock_qicon.return_value = mock_icon
            
            # Set light theme and get icon
            manager._theme = "light"
            manager.get_icon("search")
            
            # Check cache key format
            assert "light_search" in manager._icon_cache
            
            # Set dark theme and get icon
            manager._theme = "dark"
            manager._icon_cache.clear()  # Manually clear for test
            manager.get_icon("search")
            
            # Check cache key format
            assert "dark_search" in manager._icon_cache


@pytest.mark.unit
class TestGetIconManager:
    """Test cases for get_icon_manager function."""

    def test_get_icon_manager_returns_singleton(self):
        """Test get_icon_manager returns singleton instance."""
        # Clear global instance for test
        import ui.icon_manager
        ui.icon_manager._icon_manager = None
        
        # Get instance
        manager1 = get_icon_manager()
        manager2 = get_icon_manager()
        
        # Should be same instance
        assert manager1 is manager2
        assert isinstance(manager1, IconManager)

    def test_get_icon_manager_creates_instance(self):
        """Test get_icon_manager creates instance if none exists."""
        # Clear global instance
        import ui.icon_manager
        ui.icon_manager._icon_manager = None
        
        # Get instance
        manager = get_icon_manager()
        
        # Should create and return instance
        assert isinstance(manager, IconManager)
        assert ui.icon_manager._icon_manager is manager

    def test_get_icon_manager_preserves_existing_instance(self):
        """Test get_icon_manager preserves existing instance."""
        # Create instance directly
        import ui.icon_manager
        original_manager = IconManager()
        ui.icon_manager._icon_manager = original_manager
        
        # Get instance through function
        manager = get_icon_manager()
        
        # Should return existing instance
        assert manager is original_manager