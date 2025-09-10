#!/usr/bin/env python3
"""
Settings schema validation for type safety and data integrity.

This module defines JSON schemas for validating settings data and provides
validation functions to ensure settings conform to expected structure and types.
"""

from typing import Dict, Any, List, Optional, Union
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)

# ============= Schema Definitions =============

COMMAND_PALETTE_SCHEMA = {
    "type": "object",
    "properties": {
        "max_results": {"type": "integer", "minimum": 1, "maximum": 1000},
        "show_recent_commands": {"type": "boolean"},
        "recent_commands_count": {"type": "integer", "minimum": 0, "maximum": 50},
        "search_debounce_ms": {"type": "integer", "minimum": 0, "maximum": 1000},
        "auto_select_first": {"type": "boolean"},
        "show_shortcuts": {"type": "boolean"},
        "show_categories": {"type": "boolean"},
        "fuzzy_search_threshold": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        "remember_window_size": {"type": "boolean"},
        "window_width": {"type": "integer", "minimum": 300, "maximum": 2000},
        "window_height": {"type": "integer", "minimum": 200, "maximum": 1500}
    },
    "additionalProperties": False
}

KEYBOARD_SHORTCUTS_SCHEMA = {
    "type": "object",
    "patternProperties": {
        r"^[a-zA-Z][a-zA-Z0-9._]*$": {  # command_id pattern
            "type": "string",
            "pattern": r"^(ctrl\+|alt\+|shift\+|meta\+)*[a-zA-Z0-9\+\-\\\[\]\/;'`~,\.<>\?:\"{}|!@#$%^&*()_=]$|^$"
        }
    },
    "additionalProperties": False
}

THEME_SCHEMA = {
    "type": "object", 
    "properties": {
        "theme": {"type": "string", "enum": ["light", "dark", "auto"]},
        "accent_color": {"type": "string", "pattern": r"^#[0-9A-Fa-f]{6}$"},
        "font_family": {"type": "string", "minLength": 1},
        "font_size": {"type": "integer", "minimum": 8, "maximum": 72},
        "line_height": {"type": "number", "minimum": 0.5, "maximum": 3.0},
        "editor_theme": {"type": "string", "minLength": 1},
        "icon_theme": {"type": "string", "minLength": 1},
        "auto_detect_theme": {"type": "boolean"}
    },
    "additionalProperties": False
}

UI_SCHEMA = {
    "type": "object",
    "properties": {
        "show_activity_bar": {"type": "boolean"},
        "show_sidebar": {"type": "boolean"},
        "show_status_bar": {"type": "boolean"},
        "show_menu_bar": {"type": "boolean"},
        "sidebar_width": {"type": "integer", "minimum": 100, "maximum": 1000},
        "activity_bar_width": {"type": "integer", "minimum": 30, "maximum": 100},
        "status_bar_height": {"type": "integer", "minimum": 16, "maximum": 50},
        "tab_size": {"type": "integer", "minimum": 1, "maximum": 16},
        "word_wrap": {"type": "boolean"},
        "line_numbers": {"type": "boolean"},
        "minimap_enabled": {"type": "boolean"},
        "breadcrumbs_enabled": {"type": "boolean"}
    },
    "additionalProperties": False
}

WORKSPACE_SCHEMA = {
    "type": "object",
    "properties": {
        "auto_save": {"type": "boolean"},
        "auto_save_delay": {"type": "integer", "minimum": 100, "maximum": 10000},
        "restore_workspace": {"type": "boolean"},
        "restore_files": {"type": "boolean"},
        "max_recent_workspaces": {"type": "integer", "minimum": 0, "maximum": 50},
        "default_workspace_layout": {"type": "string", "minLength": 1},
        "enable_workspace_trust": {"type": "boolean"},
        "exclude_patterns": {
            "type": "array",
            "items": {"type": "string"},
            "maxItems": 100
        }
    },
    "additionalProperties": False
}

EDITOR_SCHEMA = {
    "type": "object",
    "properties": {
        "auto_indent": {"type": "boolean"},
        "smart_indent": {"type": "boolean"},
        "trim_whitespace": {"type": "boolean"},
        "insert_final_newline": {"type": "boolean"},
        "detect_indentation": {"type": "boolean"},
        "tab_completion": {"type": "boolean"},
        "bracket_matching": {"type": "boolean"},
        "code_folding": {"type": "boolean"},
        "highlight_current_line": {"type": "boolean"},
        "show_whitespace": {"type": "boolean"},
        "rulers": {
            "type": "array",
            "items": {"type": "integer", "minimum": 1, "maximum": 500},
            "maxItems": 10
        },
        "selection_highlight": {"type": "boolean"}
    },
    "additionalProperties": False
}

TERMINAL_SCHEMA = {
    "type": "object",
    "properties": {
        "shell": {"type": "string", "enum": ["auto", "bash", "zsh", "fish", "cmd", "powershell"]},
        "font_family": {"type": "string", "minLength": 1},
        "font_size": {"type": "integer", "minimum": 8, "maximum": 72},
        "cursor_style": {"type": "string", "enum": ["block", "line", "underline"]},
        "cursor_blink": {"type": "boolean"},
        "scrollback_lines": {"type": "integer", "minimum": 100, "maximum": 100000},
        "bell": {"type": "boolean"},
        "copy_on_select": {"type": "boolean"},
        "paste_on_right_click": {"type": "boolean"},
        "confirm_on_exit": {"type": "boolean"}
    },
    "additionalProperties": False
}

PERFORMANCE_SCHEMA = {
    "type": "object",
    "properties": {
        "max_file_size_mb": {"type": "integer", "minimum": 1, "maximum": 1000},
        "max_search_results": {"type": "integer", "minimum": 10, "maximum": 10000},
        "indexing_enabled": {"type": "boolean"},
        "file_watcher_enabled": {"type": "boolean"},
        "git_integration": {"type": "boolean"},
        "language_server_timeout": {"type": "integer", "minimum": 1000, "maximum": 300000},
        "ui_animation_duration": {"type": "integer", "minimum": 0, "maximum": 1000},
        "debounce_typing": {"type": "integer", "minimum": 0, "maximum": 2000}
    },
    "additionalProperties": False
}

PRIVACY_SCHEMA = {
    "type": "object",
    "properties": {
        "telemetry_enabled": {"type": "boolean"},
        "crash_reporting": {"type": "boolean"},
        "usage_analytics": {"type": "boolean"},
        "error_reporting": {"type": "boolean"},
        "improvement_program": {"type": "boolean"}
    },
    "additionalProperties": False
}

# ============= Master Schema =============

SETTINGS_SCHEMA = {
    "type": "object",
    "properties": {
        "command_palette": COMMAND_PALETTE_SCHEMA,
        "keyboard_shortcuts": KEYBOARD_SHORTCUTS_SCHEMA,
        "theme": THEME_SCHEMA,
        "ui": UI_SCHEMA,
        "workspace": WORKSPACE_SCHEMA,
        "editor": EDITOR_SCHEMA,
        "terminal": TERMINAL_SCHEMA,
        "performance": PERFORMANCE_SCHEMA,
        "privacy": PRIVACY_SCHEMA,
        "settings_version": {"type": "string"},
        "last_migration": {"type": ["string", "null"]}
    },
    "additionalProperties": False
}


class SettingsSchema:
    """Settings schema validator with detailed error reporting."""
    
    def __init__(self):
        """Initialize schema validator."""
        self.schemas = {
            "command_palette": COMMAND_PALETTE_SCHEMA,
            "keyboard_shortcuts": KEYBOARD_SHORTCUTS_SCHEMA,
            "theme": THEME_SCHEMA,
            "ui": UI_SCHEMA,
            "workspace": WORKSPACE_SCHEMA,
            "editor": EDITOR_SCHEMA,
            "terminal": TERMINAL_SCHEMA,
            "performance": PERFORMANCE_SCHEMA,
            "privacy": PRIVACY_SCHEMA,
            "root": SETTINGS_SCHEMA
        }
        
        # Try to import jsonschema for validation
        try:
            import jsonschema
            self.validator = jsonschema.Draft7Validator
            self._jsonschema_available = True
        except ImportError:
            logger.warning("jsonschema not available, using basic validation")
            self.validator = None
            self._jsonschema_available = False
    
    def validate_settings(self, settings: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate complete settings dictionary.
        
        Args:
            settings: Settings dictionary to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        if self._jsonschema_available:
            return self._validate_with_jsonschema(settings, SETTINGS_SCHEMA)
        else:
            return self._validate_basic(settings)
    
    def validate_category(self, category: str, data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate settings for a specific category.
        
        Args:
            category: Category name
            data: Settings data for category
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        if category not in self.schemas:
            return False, [f"Unknown settings category: {category}"]
        
        schema = self.schemas[category]
        
        if self._jsonschema_available:
            return self._validate_with_jsonschema(data, schema)
        else:
            return self._validate_category_basic(category, data)
    
    def _validate_with_jsonschema(self, data: Dict[str, Any], schema: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Validate using jsonschema library."""
        try:
            import jsonschema
            validator = jsonschema.Draft7Validator(schema)
            errors = list(validator.iter_errors(data))
            
            if not errors:
                return True, []
            
            error_messages = []
            for error in errors:
                path = ".".join(str(p) for p in error.path) if error.path else "root"
                error_messages.append(f"{path}: {error.message}")
            
            return False, error_messages
            
        except Exception as e:
            logger.error(f"Schema validation error: {e}")
            return False, [f"Validation error: {e}"]
    
    def _validate_basic(self, settings: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Basic validation without jsonschema."""
        errors = []
        
        # Check required structure
        if not isinstance(settings, dict):
            return False, ["Settings must be a dictionary"]
        
        # Validate each category
        for category, data in settings.items():
            if category in ["settings_version", "last_migration"]:
                continue  # Skip meta fields
                
            if category not in self.schemas:
                errors.append(f"Unknown category: {category}")
                continue
            
            is_valid, category_errors = self._validate_category_basic(category, data)
            if not is_valid:
                errors.extend(f"{category}.{err}" for err in category_errors)
        
        return len(errors) == 0, errors
    
    def _validate_category_basic(self, category: str, data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Basic category validation."""
        errors = []
        
        if not isinstance(data, dict):
            return False, ["Category data must be a dictionary"]
        
        # Basic type checking for known critical settings
        if category == "command_palette":
            if "max_results" in data and not isinstance(data["max_results"], int):
                errors.append("max_results must be an integer")
            if "show_recent_commands" in data and not isinstance(data["show_recent_commands"], bool):
                errors.append("show_recent_commands must be a boolean")
                
        elif category == "theme":
            if "theme" in data and data["theme"] not in ["light", "dark", "auto"]:
                errors.append("theme must be 'light', 'dark', or 'auto'")
            if "font_size" in data and not isinstance(data["font_size"], int):
                errors.append("font_size must be an integer")
                
        elif category == "keyboard_shortcuts":
            if not isinstance(data, dict):
                errors.append("keyboard_shortcuts must be a dictionary")
            else:
                for cmd_id, shortcut in data.items():
                    if not isinstance(shortcut, str):
                        errors.append(f"{cmd_id}: shortcut must be a string")
        
        return len(errors) == 0, errors


def validate_settings(settings: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    Validate settings dictionary against schema.
    
    Args:
        settings: Settings to validate
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    schema = SettingsSchema()
    return schema.validate_settings(settings)


def validate_keyboard_shortcut(shortcut: str) -> bool:
    """
    Validate a keyboard shortcut string.
    
    Args:
        shortcut: Shortcut string to validate
        
    Returns:
        True if shortcut is valid
    """
    if not shortcut or shortcut.strip() == "":
        return True  # Empty shortcuts are valid (disabled)
    
    # Basic validation - should contain only valid key combinations
    import re
    pattern = r"^(ctrl\+|alt\+|shift\+|meta\+)*[a-zA-Z0-9\+\-\\\[\]\/;'`~,\.<>\?:\"{}|!@#$%^&*()_=]$"
    return re.match(pattern, shortcut.lower()) is not None


def get_schema_for_category(category: str) -> Optional[Dict[str, Any]]:
    """
    Get JSON schema for a specific category.
    
    Args:
        category: Category name
        
    Returns:
        Schema dictionary or None if not found
    """
    schema_obj = SettingsSchema()
    return schema_obj.schemas.get(category)


def export_schemas_json(output_path: Union[str, Path]) -> bool:
    """
    Export all schemas to JSON file for documentation.
    
    Args:
        output_path: Path to output JSON file
        
    Returns:
        True if export successful
    """
    try:
        schema_obj = SettingsSchema()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(schema_obj.schemas, f, indent=2, sort_keys=True)
        
        logger.info(f"Schemas exported to {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to export schemas: {e}")
        return False


if __name__ == "__main__":
    # Test schema validation
    from .defaults import DEFAULT_SETTINGS
    
    schema = SettingsSchema()
    is_valid, errors = schema.validate_settings(DEFAULT_SETTINGS)
    
    print(f"Default settings validation: {'PASS' if is_valid else 'FAIL'}")
    if errors:
        for error in errors:
            print(f"  - {error}")
    
    # Test individual categories
    print("\nCategory validation:")
    for category, data in DEFAULT_SETTINGS.items():
        if category in ["settings_version", "last_migration"]:
            continue
        
        is_valid, errors = schema.validate_category(category, data)
        status = "PASS" if is_valid else "FAIL"
        print(f"  {category}: {status}")
        if errors:
            for error in errors:
                print(f"    - {error}")