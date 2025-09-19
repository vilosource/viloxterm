"""Terminal settings management."""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class TerminalSettings:
    """Terminal settings configuration."""

    # Shell settings
    shell_linux: str = "/bin/bash"
    shell_osx: str = "/bin/zsh"
    shell_windows: str = "powershell.exe"

    # Font settings
    font_family: str = "monospace"
    font_size: int = 14
    font_weight: str = "normal"
    line_height: float = 1.2

    # Cursor settings
    cursor_style: str = "block"  # block, underline, bar
    cursor_blink: bool = True

    # Colors (will be synced with theme)
    use_theme_colors: bool = True
    background: str = "#1e1e1e"
    foreground: str = "#d4d4d4"
    cursor_color: str = "#ffffff"
    selection_background: str = "#264f78"

    # Scrollback
    scrollback_lines: int = 1000

    # Bell
    bell_style: str = "none"  # none, visual, sound, both

    # Copy/Paste
    copy_on_select: bool = False
    paste_on_middle_click: bool = True

    # Performance
    renderer_type: str = "canvas"  # canvas, dom, webgl

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TerminalSettings":
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


class TerminalSettingsManager:
    """Manages terminal settings."""

    def __init__(self, config_service=None):
        self.config_service = config_service
        self.settings = TerminalSettings()
        self._load_settings()

    def _load_settings(self):
        """Load settings from configuration service."""
        if not self.config_service:
            return

        # Load each setting
        for field in TerminalSettings.__annotations__:
            key = f"terminal.{field}"
            value = self.config_service.get(key)
            if value is not None:
                setattr(self.settings, field, value)

    def save_settings(self):
        """Save settings to configuration service."""
        if not self.config_service:
            return

        for field, value in self.settings.to_dict().items():
            key = f"terminal.{field}"
            self.config_service.set(key, value)

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a specific setting."""
        return getattr(self.settings, key, default)

    def set_setting(self, key: str, value: Any):
        """Set a specific setting."""
        if hasattr(self.settings, key):
            setattr(self.settings, key, value)
            self.save_settings()

    def apply_to_terminal(self, terminal_widget):
        """Apply settings to a terminal widget."""
        if not terminal_widget or not terminal_widget.web_view:
            return

        # Create JavaScript configuration
        js_config = f"""
        (function() {{
            if (typeof term !== 'undefined') {{
                // Font settings
                term.options.fontFamily = '{self.settings.font_family}';
                term.options.fontSize = {self.settings.font_size};
                term.options.lineHeight = {self.settings.line_height};

                // Cursor settings
                term.options.cursorStyle = '{self.settings.cursor_style}';
                term.options.cursorBlink = {str(self.settings.cursor_blink).lower()};

                // Scrollback
                term.options.scrollback = {self.settings.scrollback_lines};

                // Renderer
                term.options.rendererType = '{self.settings.renderer_type}';

                // Colors (if not using theme)
                if (!{str(self.settings.use_theme_colors).lower()}) {{
                    term.options.theme = {{
                        background: '{self.settings.background}',
                        foreground: '{self.settings.foreground}',
                        cursor: '{self.settings.cursor_color}',
                        selection: '{self.settings.selection_background}'
                    }};
                }}

                // Refresh
                term.refresh(0, term.rows - 1);
            }}
        }})();
        """

        terminal_widget.web_view.page().runJavaScript(js_config)

    def sync_with_theme(self, theme_colors: Dict[str, str]):
        """Sync terminal colors with application theme."""
        if not self.settings.use_theme_colors:
            return

        # Map theme colors to terminal colors
        color_mapping = {
            "terminal.background": "background",
            "terminal.foreground": "foreground",
            "terminal.cursor": "cursor_color",
            "terminal.selection": "selection_background"
        }

        for theme_key, setting_key in color_mapping.items():
            if theme_key in theme_colors:
                setattr(self.settings, setting_key, theme_colors[theme_key])