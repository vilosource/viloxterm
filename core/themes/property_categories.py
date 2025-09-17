#!/usr/bin/env python3
"""
Theme property categorization.

Organizes theme properties into logical categories for the theme editor.
"""


from core.themes.constants import ThemeColors


class ThemePropertyCategories:
    """Organize theme properties into logical categories."""

    @staticmethod
    def get_categories() -> dict[str, dict[str, list[tuple[str, str]]]]:
        """
        Get hierarchical categorization of theme properties.

        Returns:
            Dict with category -> subcategory -> [(property_key, description)]
        """
        return {
            "Editor": {
                "General": [
                    (ThemeColors.EDITOR_BACKGROUND, "Editor background color"),
                    (ThemeColors.EDITOR_FOREGROUND, "Default text color"),
                    (ThemeColors.EDITOR_LINE_HIGHLIGHT, "Current line highlight"),
                    (ThemeColors.EDITOR_SELECTION, "Selected text background"),
                ],
                "Cursor & Guides": [
                    (ThemeColors.EDITOR_CURSOR, "Cursor color"),
                    (ThemeColors.EDITOR_WHITESPACE, "Whitespace characters"),
                    (ThemeColors.EDITOR_INDENT_GUIDE, "Indentation guides"),
                    (ThemeColors.EDITOR_INDENT_GUIDE_ACTIVE, "Active indentation guide"),
                ],
            },
            "Activity Bar": {
                "Background & Borders": [
                    (ThemeColors.ACTIVITY_BAR_BACKGROUND, "Activity bar background"),
                    (ThemeColors.ACTIVITY_BAR_BORDER, "Activity bar border"),
                    (ThemeColors.ACTIVITY_BAR_ACTIVE_BORDER, "Active item border"),
                    (ThemeColors.ACTIVITY_BAR_ACTIVE_BACKGROUND, "Active item background"),
                ],
                "Foreground": [
                    (ThemeColors.ACTIVITY_BAR_FOREGROUND, "Icon color"),
                    (ThemeColors.ACTIVITY_BAR_INACTIVE_FOREGROUND, "Inactive icon color"),
                ],
            },
            "Sidebar": {
                "General": [
                    (ThemeColors.SIDEBAR_BACKGROUND, "Sidebar background"),
                    (ThemeColors.SIDEBAR_FOREGROUND, "Sidebar text color"),
                    (ThemeColors.SIDEBAR_BORDER, "Sidebar border"),
                ],
                "Section Headers": [
                    (ThemeColors.SIDEBAR_SECTION_HEADER_BACKGROUND, "Section header background"),
                    (ThemeColors.SIDEBAR_SECTION_HEADER_FOREGROUND, "Section header text"),
                ],
            },
            "Status Bar": {
                "General": [
                    (ThemeColors.STATUS_BAR_BACKGROUND, "Status bar background"),
                    (ThemeColors.STATUS_BAR_FOREGROUND, "Status bar text"),
                    (ThemeColors.STATUS_BAR_BORDER, "Status bar border"),
                ],
                "Special States": [
                    (ThemeColors.STATUS_BAR_NO_FOLDER_BACKGROUND, "No folder background"),
                    (ThemeColors.STATUS_BAR_DEBUG_BACKGROUND, "Debug mode background"),
                    (ThemeColors.STATUS_BAR_DEBUG_FOREGROUND, "Debug mode text"),
                ],
            },
            "Title Bar": {
                "Active Window": [
                    (ThemeColors.TITLE_BAR_ACTIVE_BACKGROUND, "Active window title bar"),
                    (ThemeColors.TITLE_BAR_ACTIVE_FOREGROUND, "Active window title text"),
                ],
                "Inactive Window": [
                    (ThemeColors.TITLE_BAR_INACTIVE_BACKGROUND, "Inactive window title bar"),
                    (ThemeColors.TITLE_BAR_INACTIVE_FOREGROUND, "Inactive window title text"),
                ],
                "Border": [
                    (ThemeColors.TITLE_BAR_BORDER, "Title bar border"),
                ],
            },
            "Tabs": {
                "Active Tab": [
                    (ThemeColors.TAB_ACTIVE_BACKGROUND, "Active tab background"),
                    (ThemeColors.TAB_ACTIVE_FOREGROUND, "Active tab text"),
                    (ThemeColors.TAB_ACTIVE_BORDER, "Active tab border"),
                    (ThemeColors.TAB_ACTIVE_BORDER_TOP, "Active tab top border"),
                ],
                "Inactive Tab": [
                    (ThemeColors.TAB_INACTIVE_BACKGROUND, "Inactive tab background"),
                    (ThemeColors.TAB_INACTIVE_FOREGROUND, "Inactive tab text"),
                ],
                "General": [
                    (ThemeColors.TAB_BORDER, "Tab border"),
                ],
            },
            "Panel": {
                "General": [
                    (ThemeColors.PANEL_BACKGROUND, "Panel background"),
                    (ThemeColors.PANEL_BORDER, "Panel border"),
                ],
                "Title": [
                    (ThemeColors.PANEL_TITLE_ACTIVE_BORDER, "Active panel title border"),
                    (ThemeColors.PANEL_TITLE_ACTIVE_FOREGROUND, "Active panel title text"),
                    (ThemeColors.PANEL_TITLE_INACTIVE_FOREGROUND, "Inactive panel title text"),
                ],
            },
            "Input Controls": {
                "Input Fields": [
                    (ThemeColors.INPUT_BACKGROUND, "Input field background"),
                    (ThemeColors.INPUT_FOREGROUND, "Input field text"),
                    (ThemeColors.INPUT_BORDER, "Input field border"),
                    (ThemeColors.INPUT_PLACEHOLDER_FOREGROUND, "Placeholder text"),
                ],
                "Focus": [
                    (ThemeColors.FOCUS_BORDER, "Focused element border"),
                ],
            },
            "Buttons": {
                "Primary Button": [
                    (ThemeColors.BUTTON_BACKGROUND, "Button background"),
                    (ThemeColors.BUTTON_FOREGROUND, "Button text"),
                    (ThemeColors.BUTTON_HOVER_BACKGROUND, "Button hover background"),
                    (ThemeColors.BUTTON_BORDER, "Button border"),
                ],
                "Secondary Button": [
                    (ThemeColors.BUTTON_SECONDARY_BACKGROUND, "Secondary button background"),
                    (ThemeColors.BUTTON_SECONDARY_FOREGROUND, "Secondary button text"),
                ],
            },
            "Dropdowns": {
                "General": [
                    (ThemeColors.DROPDOWN_BACKGROUND, "Dropdown background"),
                    (ThemeColors.DROPDOWN_FOREGROUND, "Dropdown text"),
                    (ThemeColors.DROPDOWN_BORDER, "Dropdown border"),
                ],
            },
            "Lists & Trees": {
                "Selection": [
                    (ThemeColors.LIST_ACTIVE_SELECTION_BACKGROUND, "Active selection background"),
                    (ThemeColors.LIST_ACTIVE_SELECTION_FOREGROUND, "Active selection text"),
                    (ThemeColors.LIST_INACTIVE_SELECTION_BACKGROUND, "Inactive selection background"),
                    (ThemeColors.LIST_INACTIVE_SELECTION_FOREGROUND, "Inactive selection text"),
                ],
                "Hover": [
                    (ThemeColors.LIST_HOVER_BACKGROUND, "Hover background"),
                    (ThemeColors.LIST_HOVER_FOREGROUND, "Hover text"),
                ],
            },
            "Scrollbar": {
                "General": [
                    (ThemeColors.SCROLLBAR_SLIDER_BACKGROUND, "Scrollbar thumb"),
                    (ThemeColors.SCROLLBAR_SLIDER_HOVER_BACKGROUND, "Scrollbar thumb hover"),
                    (ThemeColors.SCROLLBAR_SLIDER_ACTIVE_BACKGROUND, "Scrollbar thumb active"),
                ],
            },
            "Menu": {
                "General": [
                    (ThemeColors.MENU_BACKGROUND, "Menu background"),
                    (ThemeColors.MENU_FOREGROUND, "Menu text"),
                    (ThemeColors.MENU_SEPARATOR_BACKGROUND, "Menu separator"),
                ],
                "Selection": [
                    (ThemeColors.MENU_SELECTION_BACKGROUND, "Selected item background"),
                    (ThemeColors.MENU_SELECTION_FOREGROUND, "Selected item text"),
                    (ThemeColors.MENU_SELECTION_BORDER, "Selected item border"),
                ],
            },
            "Terminal": {
                "General": [
                    (ThemeColors.TERMINAL_BACKGROUND, "Terminal background"),
                    (ThemeColors.TERMINAL_FOREGROUND, "Terminal text color"),
                    (ThemeColors.TERMINAL_SELECTION_BACKGROUND, "Selection background"),
                ],
                "Cursor": [
                    (ThemeColors.TERMINAL_CURSOR_BACKGROUND, "Cursor background"),
                    (ThemeColors.TERMINAL_CURSOR_FOREGROUND, "Cursor foreground"),
                ],
                "ANSI Colors": [
                    (ThemeColors.TERMINAL_ANSI_BLACK, "Black"),
                    (ThemeColors.TERMINAL_ANSI_RED, "Red"),
                    (ThemeColors.TERMINAL_ANSI_GREEN, "Green"),
                    (ThemeColors.TERMINAL_ANSI_YELLOW, "Yellow"),
                    (ThemeColors.TERMINAL_ANSI_BLUE, "Blue"),
                    (ThemeColors.TERMINAL_ANSI_MAGENTA, "Magenta"),
                    (ThemeColors.TERMINAL_ANSI_CYAN, "Cyan"),
                    (ThemeColors.TERMINAL_ANSI_WHITE, "White"),
                ],
                "ANSI Bright Colors": [
                    (ThemeColors.TERMINAL_ANSI_BRIGHT_BLACK, "Bright Black"),
                    (ThemeColors.TERMINAL_ANSI_BRIGHT_RED, "Bright Red"),
                    (ThemeColors.TERMINAL_ANSI_BRIGHT_GREEN, "Bright Green"),
                    (ThemeColors.TERMINAL_ANSI_BRIGHT_YELLOW, "Bright Yellow"),
                    (ThemeColors.TERMINAL_ANSI_BRIGHT_BLUE, "Bright Blue"),
                    (ThemeColors.TERMINAL_ANSI_BRIGHT_MAGENTA, "Bright Magenta"),
                    (ThemeColors.TERMINAL_ANSI_BRIGHT_CYAN, "Bright Cyan"),
                    (ThemeColors.TERMINAL_ANSI_BRIGHT_WHITE, "Bright White"),
                ],
            },
            "Accent Colors": {
                "General": [
                    (ThemeColors.ACCENT_COLOR, "Accent color"),
                ],
                "Status Colors": [
                    (ThemeColors.ERROR_FOREGROUND, "Error text"),
                    (ThemeColors.WARNING_FOREGROUND, "Warning text"),
                    (ThemeColors.INFO_FOREGROUND, "Info text"),
                    (ThemeColors.SUCCESS_FOREGROUND, "Success text"),
                ],
            },
            "Pane Headers": {
                "Background": [
                    (ThemeColors.PANE_HEADER_BACKGROUND, "Pane header background"),
                    (ThemeColors.PANE_HEADER_ACTIVE_BACKGROUND, "Active pane header"),
                ],
                "Foreground": [
                    (ThemeColors.PANE_HEADER_FOREGROUND, "Pane header text"),
                    (ThemeColors.PANE_HEADER_ACTIVE_FOREGROUND, "Active pane header text"),
                ],
                "Interactive": [
                    (ThemeColors.PANE_HEADER_BORDER, "Pane header border"),
                    (ThemeColors.PANE_HEADER_BUTTON_HOVER, "Button hover background"),
                    (ThemeColors.PANE_HEADER_CLOSE_HOVER, "Close button hover"),
                ],
            },
            "Splitters": {
                "General": [
                    (ThemeColors.SPLITTER_BACKGROUND, "Splitter background"),
                    (ThemeColors.SPLITTER_HOVER, "Splitter hover"),
                ],
            },
            "Icons": {
                "General": [
                    (ThemeColors.ICON_FOREGROUND, "Icon color"),
                    (ThemeColors.ICON_ACTIVE_FOREGROUND, "Active icon color"),
                ],
            },
        }

    @staticmethod
    def get_all_properties() -> list[tuple[str, str, str, str]]:
        """
        Get flat list of all properties with full categorization.

        Returns:
            List of (property_key, description, category, subcategory)
        """
        result = []
        categories = ThemePropertyCategories.get_categories()

        for category, subcategories in categories.items():
            for subcategory, properties in subcategories.items():
                for prop_key, description in properties:
                    result.append((prop_key, description, category, subcategory))

        return result

    @staticmethod
    def get_properties_by_category(category: str, subcategory: str = None) -> list[tuple[str, str]]:
        """
        Get properties for a specific category/subcategory.

        Args:
            category: Main category name
            subcategory: Optional subcategory name

        Returns:
            List of (property_key, description) tuples
        """
        categories = ThemePropertyCategories.get_categories()

        if category not in categories:
            return []

        if subcategory:
            return categories[category].get(subcategory, [])

        # Return all properties in category
        result = []
        for subcat_props in categories[category].values():
            result.extend(subcat_props)
        return result

    @staticmethod
    def search_properties(query: str) -> list[tuple[str, str, str, str]]:
        """
        Search properties by key or description.

        Args:
            query: Search query string

        Returns:
            List of matching (property_key, description, category, subcategory)
        """
        query = query.lower()
        result = []

        for prop_key, description, category, subcategory in ThemePropertyCategories.get_all_properties():
            if query in prop_key.lower() or query in description.lower():
                result.append((prop_key, description, category, subcategory))

        return result

    @staticmethod
    def get_required_properties() -> list[str]:
        """
        Get list of required theme properties.

        Returns:
            List of property keys that must be present in a valid theme
        """
        return [
            ThemeColors.EDITOR_BACKGROUND,
            ThemeColors.EDITOR_FOREGROUND,
            ThemeColors.ACTIVITY_BAR_BACKGROUND,
            ThemeColors.ACTIVITY_BAR_FOREGROUND,
            ThemeColors.SIDEBAR_BACKGROUND,
            ThemeColors.SIDEBAR_FOREGROUND,
            ThemeColors.STATUS_BAR_BACKGROUND,
            ThemeColors.STATUS_BAR_FOREGROUND,
        ]
