#!/usr/bin/env python3
"""
Built-in widget registration.

This module registers all built-in widgets with the AppWidgetManager
at application startup. It serves as the central location for defining
metadata for all built-in widgets.

🚨 IMPORTANT: Widget Registration Patterns

This file contains the complete registry of all built-in widgets.
When adding new widgets, follow these patterns exactly:

1. WIDGET LIFECYCLE PATTERNS:
   - Multi-Instance: Each command creates a new independent widget (Text Editor)
   - Singleton: Only one instance exists, reuse if exists (Settings, Theme Editor)
   - Service-Backed: Multiple UI widgets share a background service (Terminal)

2. WIDGET ID USAGE:
   - Registration: Use widget_id for AppWidgetMetadata ("com.viloapp.settings")
   - Commands: For singletons, use SAME widget_id as instance_id
   - Commands: For multi-instance, generate unique instance_id each time

3. WIDGETTYPE CONSISTENCY:
   - Registration: Set widget_type in AppWidgetMetadata
   - Commands: Use the SAME WidgetType when calling add_app_widget()
   - Multiple widgets can share the same WidgetType (e.g., all settings use SETTINGS)

4. COMMON MISTAKES TO AVOID:
   - ❌ Random instance_id for singletons (breaks singleton behavior)
   - ❌ Different WidgetType in registration vs command (causes mismatches)
   - ❌ Forgetting to set singleton=True for singleton widgets
   - ❌ Missing open_command (breaks menu integration)

See WIDGET-ARCHITECTURE-GUIDE.md for complete documentation.
"""

import logging
from typing import Optional

from viloapp.core.app_widget_manager import AppWidgetManager
from viloapp.core.app_widget_metadata import AppWidgetMetadata, WidgetCategory
from viloapp.core.widget_placement import WidgetPlacement

logger = logging.getLogger(__name__)


def register_builtin_widgets():
    """
    Register all built-in widgets with the AppWidgetManager.

    This function should be called once at application startup
    to register all built-in widgets with their metadata.
    """
    manager = AppWidgetManager.get_instance()

    # ========================================
    # Terminal Widget - Now provided by viloxterm plugin
    # ========================================
    # Terminal functionality is now provided by the viloxterm plugin
    # which registers with widget_id="com.viloapp.terminal"

    # ========================================
    # Text Editor Widget - Now provided by viloedit plugin
    # ========================================
    # Editor functionality is now provided by the viloedit plugin
    # which registers with widget_id="com.viloapp.editor"

    # ========================================
    # Theme Editor Widget - Removed from core
    # ========================================
    # Theme Editor was removed from core - could be implemented as a plugin
    # if theme editing functionality is needed in the future

    # ========================================
    # SINGLETON PATTERN: Keyboard Shortcuts Widget
    # ========================================
    # Keyboard Shortcuts uses a singleton pattern (like Theme Editor):
    # - Only one instance allowed at a time
    # - Opening again switches to existing tab
    # - Uses widget_id as instance_id for consistency
    #
    # Instance ID Pattern: Use "com.viloapp.shortcuts" (same as widget_id)
    # Widget Commands: settings.openKeyboardShortcuts (reuses existing or creates new)
    # 🚨 CRITICAL: Commands must use widget_id as instance_id for singletons!
    try:
        from viloapp.ui.widgets.shortcut_config_app_widget import ShortcutConfigAppWidget

        def create_shortcut_config_widget(widget_id: str) -> "ShortcutConfigAppWidget":
            return ShortcutConfigAppWidget(widget_id)

        metadata = AppWidgetMetadata(
            widget_id="com.viloapp.shortcuts",
            display_name="Keyboard Shortcuts",
            description="Configure and customize keyboard shortcuts",
            icon="keyboard",
            category=WidgetCategory.TOOLS,
            widget_class=ShortcutConfigAppWidget,
            factory=create_shortcut_config_widget,
            open_command="settings.openKeyboardShortcuts",
            singleton=True,  # 🚨 CRITICAL: This makes it a singleton widget
            # Commands MUST use "com.viloapp.shortcuts" as instance_id
            provides_capabilities=["shortcut_configuration", "keybinding_editor"],
            requires_services=["keyboard_service", "command_service"],
            min_width=600,
            min_height=400,
            # Intent metadata
            default_placement=WidgetPlacement.SMART,
            supports_replacement=True,
            supports_new_tab=True,
        )

        # Add context-specific commands
        metadata.commands = {
            "open_new_tab": "settings.openKeyboardShortcuts",
            "replace_pane": "settings.replaceWithKeyboardShortcuts",
        }

        manager.register_widget(metadata)
        logger.debug("Registered Keyboard Shortcuts widget")
    except ImportError as e:
        logger.warning(f"Could not register Keyboard Shortcuts widget: {e}")

    # ========================================
    # UTILITY PATTERN: Placeholder Widget
    # ========================================
    # Placeholder is a utility widget for empty panes:
    # - Multiple instances allowed (each pane can be empty)
    # - Not singleton (each placeholder is independent)
    # - Hidden from menus by default (system widget)
    #
    # Instance ID Pattern: Generate unique IDs as needed
    # Widget Commands: Internal use mostly, not user-facing
    try:
        from viloapp.ui.widgets.placeholder_app_widget import PlaceholderAppWidget

        manager.register_widget(
            AppWidgetMetadata(
                widget_id="com.viloapp.placeholder",
                display_name="Empty Pane",
                description="Empty pane - right-click to change type",
                icon="layout",
                category=WidgetCategory.SYSTEM,
                widget_class=PlaceholderAppWidget,
                show_in_menu=True,  # Allow users to explicitly create empty panes
                show_in_palette=False,  # Don't show in command palette
                min_width=100,
                min_height=100,
            )
        )
        logger.debug("Registered Placeholder widget")
    except ImportError as e:
        logger.warning(f"Could not register Placeholder widget: {e}")

    # Register Output Widget (for future use)
    try:
        from viloapp.ui.widgets.placeholder_app_widget import PlaceholderAppWidget  # Temporary

        manager.register_widget(
            AppWidgetMetadata(
                widget_id="com.viloapp.output",
                display_name="Output Panel",
                description="Output and console messages",
                icon="message-square",
                category=WidgetCategory.TOOLS,
                widget_class=PlaceholderAppWidget,  # Using placeholder for now
                provides_capabilities=["output_display", "console_messages"],
                preserve_context_menu=True,
                min_width=300,
                min_height=150,
            )
        )
        logger.debug("Registered Output widget")
    except ImportError as e:
        logger.warning(f"Could not register Output widget: {e}")

    # Register File Explorer Widget (for future use)
    try:
        from viloapp.ui.widgets.placeholder_app_widget import PlaceholderAppWidget  # Temporary

        manager.register_widget(
            AppWidgetMetadata(
                widget_id="com.viloapp.explorer",
                display_name="File Explorer",
                description="Browse and manage files",
                icon="folder",
                category=WidgetCategory.VIEWER,
                widget_class=PlaceholderAppWidget,  # Using placeholder for now
                provides_capabilities=["file_browsing", "file_management"],
                requires_services=["file_service"],
                preserve_context_menu=True,
                min_width=200,
                min_height=300,
                show_in_menu=False,  # Hide until implemented
            )
        )
        logger.debug("Registered File Explorer widget")
    except ImportError as e:
        logger.warning(f"Could not register File Explorer widget: {e}")

    # ========================================
    # SINGLETON PATTERN: Settings Widget
    # ========================================
    # Settings uses a singleton pattern (like Theme Editor and Shortcuts):
    # - Only one instance allowed at a time
    # - Opening again switches to existing tab
    # - Uses widget_id as instance_id for consistency
    #
    # Instance ID Pattern: Use "com.viloapp.settings" (same as widget_id)
    # Widget Commands: Must check for existing instance before creating
    # 🚨 CRITICAL: Commands must use widget_id as instance_id for singletons!
    try:
        from viloapp.ui.widgets.settings_app_widget import SettingsAppWidget

        manager.register_widget(
            AppWidgetMetadata(
                widget_id="com.viloapp.settings",
                display_name="Settings",
                description="Configure application settings and preferences",
                icon="settings",
                category=WidgetCategory.EDITOR,
                widget_class=SettingsAppWidget,
                provides_capabilities=["settings_management", "preferences"],
                requires_services=["settings_service"],
                singleton=True,  # 🚨 CRITICAL: This makes it a singleton widget
                # Commands MUST use "com.viloapp.settings" as instance_id
                min_width=600,
                min_height=400,
                show_in_menu=True,
            )
        )
        logger.debug("Registered Settings widget")
    except ImportError as e:
        logger.warning(f"Could not register Settings widget: {e}")

    logger.info(f"Registered {len(manager)} built-in widgets")


# ============================================================================
# WIDGET REGISTRATION PATTERNS AND EXAMPLES
# ============================================================================
"""
When adding a new widget, follow these exact patterns:

1. DETERMINE YOUR WIDGET'S LIFECYCLE PATTERN:

   a) MULTI-INSTANCE (like Text Editor):
      - Each command creates a NEW independent widget
      - Generate unique instance_id each time: f"widget_{uuid4().hex[:8]}"
      - singleton=False in metadata

   b) SINGLETON (like Settings, Theme Editor):
      - Only ONE instance allowed
      - Use widget_id as instance_id: "com.viloapp.mywidget"
      - singleton=True in metadata
      - Commands must check for existing instance

   c) SERVICE-BACKED (like Terminal):
      - Background service manages functionality
      - Multiple UI widgets connect to service
      - Service starts once, persists after UI closes
      - Generate unique instance_id for each UI widget

2. REGISTRATION TEMPLATE:

   manager.register_widget(AppWidgetMetadata(
       widget_id="com.viloapp.mywidget",        # Unique reverse-domain ID
       # widget_id is the unique identifier
       display_name="My Widget",                # User-visible name
       description="What this widget does",     # Tooltip/help text
       icon="icon-name",                        # Icon identifier
       category=WidgetCategory.APPROPRIATE,     # Menu grouping
       widget_class=MyWidgetClass,              # Implementation class
       open_command="mywidget.open",            # Command to open widget
       singleton=False,                         # True for singleton pattern
       # ... other metadata fields
   ))

3. COMMAND IMPLEMENTATION PATTERNS:

   a) MULTI-INSTANCE COMMAND:

   @command(id="mywidget.open")
   def open_my_widget(context: CommandContext) -> CommandResult:
       # Generate unique instance ID
       instance_id = f"mywidget_{uuid.uuid4().hex[:8]}"

       workspace_service = context.get_service(WorkspaceService)
       success = workspace_service.add_app_widget(
           widget_id="com.viloapp.mywidget",
           widget_id=instance_id,  # ← Unique each time
           name="My Widget"
       )
       return CommandResult(status=CommandStatus.SUCCESS if success else CommandStatus.FAILURE)

   b) SINGLETON COMMAND:

   @command(id="mywidget.open")
   def open_my_widget(context: CommandContext) -> CommandResult:
       widget_id = "com.viloapp.mywidget"  # ← Same as registration

       workspace_service = context.get_service(WorkspaceService)

       # Check for existing instance
       if workspace_service.has_widget(widget_id):
           workspace_service.focus_widget(widget_id)
           return CommandResult(status=CommandStatus.SUCCESS)

       # Create singleton instance
       success = workspace_service.add_app_widget(
           widget_id="com.viloapp.mywidget",
           widget_id=widget_id,  # ← Always same for singleton
           name="My Widget"
       )
       return CommandResult(status=CommandStatus.SUCCESS if success else CommandStatus.FAILURE)

   c) SERVICE-BACKED COMMAND:

   @command(id="mywidget.open")
   def open_my_widget(context: CommandContext) -> CommandResult:
       # Ensure service is running
       my_service = context.get_service(MyService)
       if not my_service.is_running():
           my_service.start()

       # Create session in service
       session_id = my_service.create_session()

       # Create UI widget with session reference
       instance_id = f"mywidget_{session_id}"
       workspace_service = context.get_service(WorkspaceService)
       success = workspace_service.add_app_widget(
           widget_id="com.viloapp.mywidget",
           widget_id=instance_id,
           name="My Widget"
       )
       return CommandResult(status=CommandStatus.SUCCESS if success else CommandStatus.FAILURE)

4. COMMON MISTAKES TO AVOID:

   ❌ Using random instance_id for singletons:
      # WRONG - creates multiple Settings instances
      instance_id = f"settings_{uuid4().hex[:8]}"

   ✅ Use consistent instance_id for singletons:
      # CORRECT - singleton behavior
      instance_id = "com.viloapp.settings"

   ❌ WidgetType mismatch between registration and command:
      # Registration: SETTINGS
      # Command: "plugin.unknown"  ← Different type!

   ✅ Use same WidgetType everywhere:
      # Both registration and command use SETTINGS

   ❌ Forgetting singleton flag:
      # Settings registered with singleton=False
      # But command assumes singleton behavior

   ✅ Set singleton flag correctly in registration:
      singleton=True  # For Settings, Theme Editor, etc.

5. TESTING YOUR WIDGET:

   a) Test Registration:
      manager = AppWidgetManager.get_instance()
      metadata = manager.get_widget_metadata("com.viloapp.mywidget")
      assert metadata is not None

   b) Test Widget Creation:
      widget = manager.create_widget("com.viloapp.mywidget", "test_instance")
      assert widget is not None
      assert isinstance(widget, MyWidgetClass)

   c) Test Singleton Behavior (if applicable):
      widget1 = manager.create_widget("com.viloapp.mywidget", "same_id")
      widget2 = manager.create_widget("com.viloapp.mywidget", "same_id")
      # Should reuse same instance for singletons

6. WIDGET ID NAMING CONVENTION:

   Use reverse domain notation:
   - "com.viloapp.terminal"      ← Built-in widgets
   - "com.viloapp.editor"
   - "com.company.plugin_name"   ← Future plugins
   - "org.project.widget_name"   ← Third-party

   This prevents naming conflicts and supports future plugin system.

For complete documentation, see:
- WIDGET-ARCHITECTURE-GUIDE.md - Complete architecture overview
- app-widget-manager.md - AppWidgetManager implementation details
- WIDGET_LIFECYCLE.md - Widget lifecycle and state management
"""


def get_widget_for_command(command_id: str) -> Optional[AppWidgetMetadata]:
    """
    Get the widget associated with a command.

    Args:
        command_id: Command identifier

    Returns:
        Widget metadata if found, None otherwise
    """
    manager = AppWidgetManager.get_instance()
    for widget in manager.get_all_widgets():
        if widget.open_command == command_id:
            return widget
        if command_id in widget.associated_commands:
            return widget
    return None


def get_default_widget_for_file(file_path: str) -> Optional[AppWidgetMetadata]:
    """
    Get the default widget for opening a file.

    Args:
        file_path: Path to the file

    Returns:
        Best matching widget metadata or None
    """
    import os

    _, ext = os.path.splitext(file_path)
    ext = ext.lstrip(".")

    if not ext:
        return None

    manager = AppWidgetManager.get_instance()
    widgets = manager.get_widgets_for_file_type(ext)

    # Prefer editors over viewers
    for widget in widgets:
        if widget.category == WidgetCategory.EDITOR:
            return widget

    # Return first available widget
    return widgets[0] if widgets else None
