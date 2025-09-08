"""Icon management system for the application."""

from PySide6.QtGui import QIcon
from PySide6.QtCore import QObject, Signal, QSize
from typing import Dict, Optional


class IconManager(QObject):
    """Manages application icons and theme switching."""
    
    theme_changed = Signal(str)  # Emitted when theme changes
    
    def __init__(self):
        super().__init__()
        self._theme = "light"  # Default theme
        self._icon_cache: Dict[str, QIcon] = {}
        
    @property
    def theme(self) -> str:
        """Get current theme."""
        return self._theme
        
    @theme.setter
    def theme(self, value: str):
        """Set theme and emit change signal."""
        if value in ["light", "dark"] and value != self._theme:
            self._theme = value
            self._icon_cache.clear()  # Clear cache on theme change
            self.theme_changed.emit(value)
            
    def get_icon(self, name: str) -> QIcon:
        """Get icon by name for current theme.
        
        Args:
            name: Icon name (explorer, search, git, settings)
            
        Returns:
            QIcon instance
        """
        cache_key = f"{self._theme}_{name}"
        
        if cache_key not in self._icon_cache:
            icon = QIcon()
            
            # Load icon for current theme
            icon_path = f":/icons/{self._theme}/{name}"
            icon.addFile(icon_path, QSize(), QIcon.Normal, QIcon.Off)
            
            # Add hover state (slightly different opacity)
            icon.addFile(icon_path, QSize(), QIcon.Active, QIcon.Off)
            
            # Add selected state (use opposite theme for contrast)
            opposite_theme = "dark" if self._theme == "light" else "light"
            selected_path = f":/icons/{opposite_theme}/{name}"
            icon.addFile(selected_path, QSize(), QIcon.Selected, QIcon.Off)
            
            self._icon_cache[cache_key] = icon
            
        return self._icon_cache[cache_key]
    
    def get_icon_with_states(self, name: str) -> QIcon:
        """Get icon with multiple states configured.
        
        Args:
            name: Icon name
            
        Returns:
            QIcon with states configured
        """
        icon = QIcon()
        
        # Normal state - current theme
        normal_path = f":/icons/{self._theme}/{name}"
        icon.addFile(normal_path, QSize(), QIcon.Normal, QIcon.Off)
        
        # Disabled state - same icon with reduced opacity (handled by Qt)
        icon.addFile(normal_path, QSize(), QIcon.Disabled, QIcon.Off)
        
        # Active/Hover state - current theme
        icon.addFile(normal_path, QSize(), QIcon.Active, QIcon.Off)
        
        # Selected state - opposite theme for contrast
        opposite_theme = "dark" if self._theme == "light" else "light"
        selected_path = f":/icons/{opposite_theme}/{name}"
        icon.addFile(selected_path, QSize(), QIcon.Selected, QIcon.Off)
        
        return icon
    
    def detect_system_theme(self):
        """Detect system theme preference (light/dark)."""
        # This is a simplified version
        # In production, you'd want to check the actual system theme
        # On Windows: Check registry
        # On macOS: Check system appearance
        # On Linux: Check desktop environment settings
        
        # For now, we'll just use light as default
        self.theme = "light"
        
    def toggle_theme(self):
        """Toggle between light and dark themes."""
        self.theme = "dark" if self._theme == "light" else "light"


# Global icon manager instance
_icon_manager = None


def get_icon_manager() -> IconManager:
    """Get the global icon manager instance."""
    global _icon_manager
    if _icon_manager is None:
        _icon_manager = IconManager()
    return _icon_manager