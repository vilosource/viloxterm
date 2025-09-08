"""Icon management system for the application."""

from PySide6.QtGui import QIcon, QPixmap, QPainter, QFont, QColor
from PySide6.QtCore import QObject, Signal, QSize, Qt
from typing import Dict, Optional


class IconManager(QObject):
    """Manages application icons and theme switching."""
    
    theme_changed = Signal(str)  # Emitted when theme changes
    
    def __init__(self):
        super().__init__()
        self._theme = "dark"  # Default to dark theme to match our app
        self._icon_cache: Dict[str, QIcon] = {}
        
        # Icon text mapping for activity bar icons
        self._icon_symbols = {
            "explorer": "⊞",   # Squared plus (file manager)
            "search": "⌕",     # Search symbol
            "git": "⌘",        # Command symbol (version control)
            "settings": "⚙"    # Gear symbol (settings)
        }
        
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
            icon = self._create_text_icon(name)
            self._icon_cache[cache_key] = icon
            
        return self._icon_cache[cache_key]
    
    def _create_text_icon(self, name: str, size: int = 24) -> QIcon:
        """Create a text-based icon with proper contrast.
        
        Args:
            name: Icon name
            size: Icon size in pixels
            
        Returns:
            QIcon with text-based icon
        """
        icon = QIcon()
        
        # Get symbol for this icon
        symbol = self._icon_symbols.get(name, "?")
        
        # Create pixmaps for different states
        normal_pixmap = self._create_icon_pixmap(symbol, size, self._get_normal_color())
        hover_pixmap = self._create_icon_pixmap(symbol, size, self._get_hover_color())
        active_pixmap = self._create_icon_pixmap(symbol, size, self._get_active_color())
        
        # Add pixmaps to icon
        icon.addPixmap(normal_pixmap, QIcon.Normal, QIcon.Off)
        icon.addPixmap(hover_pixmap, QIcon.Active, QIcon.Off) 
        icon.addPixmap(active_pixmap, QIcon.Selected, QIcon.Off)
        
        return icon
    
    def _create_icon_pixmap(self, text: str, size: int, color: QColor) -> QPixmap:
        """Create a pixmap with text icon.
        
        Args:
            text: Text to render
            size: Size of the pixmap
            color: Text color
            
        Returns:
            QPixmap with rendered text
        """
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Set up font - try to use a font with good unicode support
        font = QFont("Arial Unicode MS, Segoe UI Symbol, DejaVu Sans")
        font.setPixelSize(int(size * 0.8))  # 80% of icon size
        font.setBold(True)  # Make icons more visible
        painter.setFont(font)
        
        # Set color
        painter.setPen(color)
        
        # Draw text centered
        painter.drawText(pixmap.rect(), Qt.AlignCenter, text)
        painter.end()
        
        return pixmap
    
    def _get_normal_color(self) -> QColor:
        """Get normal icon color for current theme."""
        # Light color for dark theme (our current theme)
        return QColor("#cccccc") if self._theme == "dark" else QColor("#333333")
    
    def _get_hover_color(self) -> QColor:
        """Get hover icon color for current theme."""
        # Brighter for hover
        return QColor("#ffffff") if self._theme == "dark" else QColor("#000000")
    
    def _get_active_color(self) -> QColor:
        """Get active/selected icon color for current theme."""
        # Blue accent for active state
        return QColor("#007acc")
    
    def get_icon_with_states(self, name: str) -> QIcon:
        """Get icon with multiple states configured.
        
        Args:
            name: Icon name
            
        Returns:
            QIcon with states configured
        """
        # Use the same method as get_icon now
        return self.get_icon(name)
    
    def detect_system_theme(self):
        """Detect system theme preference (light/dark)."""
        return self._detect_system_theme()
        
    def _detect_system_theme(self):
        """Internal method to detect system theme."""
        # This is a simplified version
        # In production, you'd want to check the actual system theme
        # On Windows: Check registry
        # On macOS: Check system appearance
        # On Linux: Check desktop environment settings
        
        # For now, we'll use dark as default to match our VSCode theme
        self.theme = "dark"
        return "dark"
        
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