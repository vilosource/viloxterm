"""Settings migration tool for ViloxTerm plugin architecture."""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class SettingsMigrator:
    """Migrates settings from old format to new plugin-compatible format."""

    def __init__(self):
        self.old_settings_path = Path.home() / ".viloxterm" / "settings.json"
        self.new_settings_path = Path.home() / ".config" / "viloxterm" / "settings.json"

    def needs_migration(self) -> bool:
        """Check if settings migration is needed."""
        return (
            self.old_settings_path.exists() and
            not self.new_settings_path.exists()
        )

    def migrate_settings(self) -> bool:
        """Migrate settings from old to new format."""
        if not self.needs_migration():
            return False

        try:
            # Load old settings
            with open(self.old_settings_path, 'r') as f:
                old_settings = json.load(f)

            # Transform to new format
            new_settings = self._transform_settings(old_settings)

            # Ensure new directory exists
            self.new_settings_path.parent.mkdir(parents=True, exist_ok=True)

            # Save new settings
            with open(self.new_settings_path, 'w') as f:
                json.dump(new_settings, f, indent=2)

            logger.info(f"Successfully migrated settings from {self.old_settings_path} to {self.new_settings_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to migrate settings: {e}")
            return False

    def _transform_settings(self, old_settings: Dict[str, Any]) -> Dict[str, Any]:
        """Transform old settings format to new plugin-compatible format."""
        new_settings = {
            "version": "2.0",
            "core": {
                "theme": old_settings.get("theme", "dark"),
                "language": old_settings.get("language", "en"),
                "window": {
                    "width": old_settings.get("window_width", 1200),
                    "height": old_settings.get("window_height", 800),
                    "maximized": old_settings.get("window_maximized", False)
                }
            },
            "plugins": {
                "viloxterm": {
                    "enabled": True,
                    "settings": self._extract_terminal_settings(old_settings)
                },
                "viloedit": {
                    "enabled": True,
                    "settings": self._extract_editor_settings(old_settings)
                }
            }
        }

        return new_settings

    def _extract_terminal_settings(self, old_settings: Dict[str, Any]) -> Dict[str, Any]:
        """Extract terminal-specific settings."""
        return {
            "shell": old_settings.get("default_shell", "/bin/bash"),
            "font_family": old_settings.get("terminal_font", "monospace"),
            "font_size": old_settings.get("terminal_font_size", 12),
            "colors": {
                "background": old_settings.get("terminal_bg", "#1e1e1e"),
                "foreground": old_settings.get("terminal_fg", "#ffffff"),
                "cursor": old_settings.get("terminal_cursor", "#ffffff")
            },
            "scrollback_lines": old_settings.get("scrollback_lines", 1000),
            "cursor_blink": old_settings.get("cursor_blink", True)
        }

    def _extract_editor_settings(self, old_settings: Dict[str, Any]) -> Dict[str, Any]:
        """Extract editor-specific settings."""
        return {
            "font_family": old_settings.get("editor_font", "monospace"),
            "font_size": old_settings.get("editor_font_size", 12),
            "tab_width": old_settings.get("tab_width", 4),
            "word_wrap": old_settings.get("word_wrap", False),
            "line_numbers": old_settings.get("show_line_numbers", True),
            "syntax_highlighting": old_settings.get("syntax_highlighting", True),
            "auto_indent": old_settings.get("auto_indent", True),
            "auto_save": old_settings.get("auto_save", False)
        }

    def backup_old_settings(self) -> bool:
        """Create a backup of old settings."""
        if not self.old_settings_path.exists():
            return False

        backup_path = self.old_settings_path.with_suffix('.json.backup')
        try:
            backup_path.write_bytes(self.old_settings_path.read_bytes())
            logger.info(f"Created backup at {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return False


def main():
    """Main migration function."""
    migrator = SettingsMigrator()

    if migrator.needs_migration():
        print("Old settings detected. Starting migration...")

        # Create backup
        if migrator.backup_old_settings():
            print("✓ Old settings backed up")

        # Migrate
        if migrator.migrate_settings():
            print("✓ Settings migrated successfully")
            print(f"New settings location: {migrator.new_settings_path}")
        else:
            print("✗ Settings migration failed")
    else:
        print("No migration needed")


if __name__ == "__main__":
    main()