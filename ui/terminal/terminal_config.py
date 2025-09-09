#!/usr/bin/env python3
"""
Terminal configuration system.
Manages terminal settings including shell, appearance, and behavior.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from PySide6.QtCore import QSettings
import platform
import os


@dataclass
class ColorScheme:
    """Terminal color scheme."""
    background: str = "#1e1e1e"
    foreground: str = "#d4d4d4"
    cursor: str = "#ffffff"
    cursor_accent: str = "#000000"
    selection: str = "#264f78"
    
    # ANSI colors
    black: str = "#000000"
    red: str = "#cd3131"
    green: str = "#0dbc79"
    yellow: str = "#e5e510"
    blue: str = "#2472c8"
    magenta: str = "#bc3fbc"
    cyan: str = "#11a8cd"
    white: str = "#e5e5e5"
    
    # Bright ANSI colors
    bright_black: str = "#666666"
    bright_red: str = "#f14c4c"
    bright_green: str = "#23d18b"
    bright_yellow: str = "#f5f543"
    bright_blue: str = "#3b8eea"
    bright_magenta: str = "#d670d6"
    bright_cyan: str = "#29b8db"
    bright_white: str = "#e5e5e5"
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for xterm.js theme."""
        return {
            'background': self.background,
            'foreground': self.foreground,
            'cursor': self.cursor,
            'cursorAccent': self.cursor_accent,
            'selection': self.selection,
            'black': self.black,
            'red': self.red,
            'green': self.green,
            'yellow': self.yellow,
            'blue': self.blue,
            'magenta': self.magenta,
            'cyan': self.cyan,
            'white': self.white,
            'brightBlack': self.bright_black,
            'brightRed': self.bright_red,
            'brightGreen': self.bright_green,
            'brightYellow': self.bright_yellow,
            'brightBlue': self.bright_blue,
            'brightMagenta': self.bright_magenta,
            'brightCyan': self.bright_cyan,
            'brightWhite': self.bright_white
        }


# Predefined color schemes
VSCODE_DARK_THEME = ColorScheme()

VSCODE_LIGHT_THEME = ColorScheme(
    background="#ffffff",
    foreground="#333333",
    cursor="#000000",
    cursor_accent="#ffffff",
    selection="#add6ff",
    black="#000000",
    red="#cd3131",
    green="#00bc00",
    yellow="#949800",
    blue="#0451a5",
    magenta="#bc05bc",
    cyan="#0598bc",
    white="#555555",
    bright_black="#666666",
    bright_red="#cd3131",
    bright_green="#14ce14",
    bright_yellow="#b5ba00",
    bright_blue="#0451a5",
    bright_magenta="#bc05bc",
    bright_cyan="#0598bc",
    bright_white="#a5a5a5"
)


@dataclass
class TerminalConfig:
    """Terminal configuration."""
    
    # Shell settings
    shell: str = field(default_factory=lambda: TerminalConfig._get_default_shell())
    shell_args: str = ""
    custom_shell_path: Optional[str] = None
    
    # Appearance
    font_family: str = 'Consolas, "Courier New", monospace'
    font_size: int = 14
    line_height: float = 1.2
    cursor_style: str = "block"  # block, underline, bar
    cursor_blink: bool = True
    scrollback: int = 1000
    
    # Color scheme
    theme: str = "dark"  # dark, light, auto
    color_scheme_dark: ColorScheme = field(default_factory=lambda: VSCODE_DARK_THEME)
    color_scheme_light: ColorScheme = field(default_factory=lambda: VSCODE_LIGHT_THEME)
    
    # Behavior
    copy_on_select: bool = False
    right_click_paste: bool = True
    confirm_on_exit: bool = True
    bell_style: str = "visual"  # none, visual, sound
    max_terminals: int = 10
    
    # Window settings
    default_cols: int = 80
    default_rows: int = 24
    
    @staticmethod
    def _get_default_shell() -> str:
        """Get the default shell for the current platform."""
        if platform.system() == "Windows":
            # Try PowerShell first, fall back to cmd
            if os.path.exists("C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe"):
                return "powershell.exe"
            return "cmd.exe"
        else:
            # Unix-like systems
            shell = os.environ.get('SHELL', '/bin/bash')
            if os.path.exists(shell):
                return shell
            # Fallback options
            for shell in ['/bin/bash', '/bin/zsh', '/bin/sh']:
                if os.path.exists(shell):
                    return shell
            return 'bash'  # Last resort
    
    def get_shell_command(self) -> str:
        """Get the shell command to execute."""
        if self.custom_shell_path and os.path.exists(self.custom_shell_path):
            return self.custom_shell_path
        return self.shell
    
    def get_initial_directory(self) -> str:
        """Get the initial directory for new terminal sessions."""
        # Default to current working directory
        return os.getcwd()
    
    def get_color_scheme(self, is_dark_theme: bool = True) -> ColorScheme:
        """Get the appropriate color scheme based on theme."""
        if self.theme == "auto":
            return self.color_scheme_dark if is_dark_theme else self.color_scheme_light
        elif self.theme == "light":
            return self.color_scheme_light
        else:
            return self.color_scheme_dark
    
    def save_to_settings(self, settings: QSettings, prefix: str = "terminal"):
        """Save configuration to QSettings."""
        settings.beginGroup(prefix)
        
        # Shell settings
        settings.setValue("shell", self.shell)
        settings.setValue("shell_args", self.shell_args)
        settings.setValue("custom_shell_path", self.custom_shell_path)
        
        # Appearance
        settings.setValue("font_family", self.font_family)
        settings.setValue("font_size", self.font_size)
        settings.setValue("line_height", self.line_height)
        settings.setValue("cursor_style", self.cursor_style)
        settings.setValue("cursor_blink", self.cursor_blink)
        settings.setValue("scrollback", self.scrollback)
        
        # Theme
        settings.setValue("theme", self.theme)
        
        # Behavior
        settings.setValue("copy_on_select", self.copy_on_select)
        settings.setValue("right_click_paste", self.right_click_paste)
        settings.setValue("confirm_on_exit", self.confirm_on_exit)
        settings.setValue("bell_style", self.bell_style)
        settings.setValue("max_terminals", self.max_terminals)
        
        # Window
        settings.setValue("default_cols", self.default_cols)
        settings.setValue("default_rows", self.default_rows)
        
        settings.endGroup()
    
    @classmethod
    def load_from_settings(cls, settings: QSettings, prefix: str = "terminal") -> 'TerminalConfig':
        """Load configuration from QSettings."""
        config = cls()
        
        settings.beginGroup(prefix)
        
        # Shell settings
        config.shell = settings.value("shell", config.shell)
        config.shell_args = settings.value("shell_args", config.shell_args)
        config.custom_shell_path = settings.value("custom_shell_path", config.custom_shell_path)
        
        # Appearance
        config.font_family = settings.value("font_family", config.font_family)
        config.font_size = int(settings.value("font_size", config.font_size))
        config.line_height = float(settings.value("line_height", config.line_height))
        config.cursor_style = settings.value("cursor_style", config.cursor_style)
        config.cursor_blink = settings.value("cursor_blink", config.cursor_blink, type=bool)
        config.scrollback = int(settings.value("scrollback", config.scrollback))
        
        # Theme
        config.theme = settings.value("theme", config.theme)
        
        # Behavior
        config.copy_on_select = settings.value("copy_on_select", config.copy_on_select, type=bool)
        config.right_click_paste = settings.value("right_click_paste", config.right_click_paste, type=bool)
        config.confirm_on_exit = settings.value("confirm_on_exit", config.confirm_on_exit, type=bool)
        config.bell_style = settings.value("bell_style", config.bell_style)
        config.max_terminals = int(settings.value("max_terminals", config.max_terminals))
        
        # Window
        config.default_cols = int(settings.value("default_cols", config.default_cols))
        config.default_rows = int(settings.value("default_rows", config.default_rows))
        
        settings.endGroup()
        
        return config
    
    def to_xterm_config(self, is_dark_theme: bool = True) -> Dict[str, Any]:
        """Convert to xterm.js configuration object."""
        color_scheme = self.get_color_scheme(is_dark_theme)
        
        return {
            'cursorBlink': self.cursor_blink,
            'cursorStyle': self.cursor_style,
            'fontFamily': self.font_family,
            'fontSize': self.font_size,
            'lineHeight': self.line_height,
            'scrollback': self.scrollback,
            'theme': color_scheme.to_dict(),
            'macOptionIsMeta': True,
            'rightClickSelectsWord': not self.right_click_paste,
            'bellStyle': self.bell_style if self.bell_style != 'visual' else 'both'
        }


# Global configuration instance
terminal_config = TerminalConfig()