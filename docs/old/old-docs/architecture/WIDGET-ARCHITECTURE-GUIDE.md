# Widget Architecture Guide

## Overview

This document provides a comprehensive guide to ViloxTerm's widget architecture, covering the complete system from conceptual patterns to practical implementation. This is the master reference that ties together all widget-related concepts.

**Navigation:**
- [AppWidgetManager Details](app-widget-manager.md) - Registry and metadata system
- [Widget Lifecycle](WIDGET_LIFECYCLE.md) - State management and lifecycle
- [Developer Guide](../dev-guides/widget-lifecycle-guide.md) - Practical implementation
- [Development Guide](../development/widget-development-guide.md) - Creating new widgets

## Core Architecture Concepts

### 1. Widget Identity System

ViloxTerm uses a three-tier identity system for widgets:

```
┌─────────────────────────────────────────────────────────────┐
│                    WIDGET IDENTITY SYSTEM                  │
├─────────────────┬─────────────────────┬───────────────────────┤
│   WIDGET_ID     │     WIDGET_TYPE     │    INSTANCE_ID        │
│  (Registration) │   (Categorical)     │     (Runtime)         │
├─────────────────┼─────────────────────┼───────────────────────┤
│ com.viloapp.    │ WidgetType.TERMINAL │ terminal_abc123       │
│ terminal        │                     │                       │
├─────────────────┼─────────────────────┼───────────────────────┤
│ com.viloapp.    │ WidgetType.SETTINGS │ com.viloapp.settings  │
│ settings        │                     │ (singleton = same)    │
└─────────────────┴─────────────────────┴───────────────────────┘
```

- **widget_id**: Unique registration identifier (reverse domain notation)
- **WidgetType**: Categorical enum for compatibility and grouping
- **instance_id**: Runtime instance identifier (unique per running instance)

### 2. Widget Lifecycle Patterns

The architecture supports four distinct lifecycle patterns:

#### Pattern 1: Multi-Instance Widgets
```
┌─────────────────────────────────────────────────────────────┐
│                    MULTI-INSTANCE                           │
│                   (Text Editor)                             │
├─────────────────────────────────────────────────────────────┤
│ • Multiple independent instances allowed                    │
│ • Each instance manages its own resources                   │
│ • No shared state between instances                         │
│ • Instance IDs: editor_abc123, editor_def456...            │
└─────────────────────────────────────────────────────────────┘

Example: Text Editor
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ Editor Tab 1│ │ Editor Tab 2│ │ Editor Tab 3│
│ file1.py    │ │ file2.js    │ │ file3.md    │
└─────────────┘ └─────────────┘ └─────────────┘
```

#### Pattern 2: Singleton Widgets
```
┌─────────────────────────────────────────────────────────────┐
│                      SINGLETON                              │
│                     (Settings)                              │
├─────────────────────────────────────────────────────────────┤
│ • Only one instance allowed                                 │
│ • Reuse existing if opened again                            │
│ • Instance ID same as widget_id                             │
│ • Created on-demand, destroyed when closed                  │
└─────────────────────────────────────────────────────────────┘

Example: Settings
┌─────────────┐
│ Settings    │ ← Only one can exist
│             │   Opening again switches to existing tab
└─────────────┘
```

#### Pattern 3: Service-Backed Widgets
```
┌─────────────────────────────────────────────────────────────┐
│                   SERVICE-BACKED                            │
│                    (Terminal)                               │
├─────────────────────────────────────────────────────────────┤
│ • Background service always running                         │
│ • Multiple UI instances share service                       │
│ • Service persists after UI instances close                 │
│ • Each UI instance has unique session                       │
└─────────────────────────────────────────────────────────────┘

Example: Terminal System
┌─────────────────────────────────────────────────────────────┐
│                  TerminalService                            │
│                (Background Service)                         │
├─────────────────────────────────────────────────────────────┤
│ Session 1 (PTY: bash)  │ Session 2 (PTY: zsh)   │ Session 3│
└─────────────────────────────────────────────────────────────┘
           ↑                      ↑                    ↑
    ┌─────────────┐        ┌─────────────┐     ┌─────────────┐
    │Terminal Tab1│        │Terminal Tab2│     │Terminal Tab3│
    │ (UI View)   │        │ (UI View)   │     │ (UI View)   │
    └─────────────┘        └─────────────┘     └─────────────┘
```

#### Pattern 4: Persistent Singleton Services
```
┌─────────────────────────────────────────────────────────────┐
│               PERSISTENT SINGLETON                          │
│              (Background Services)                          │
├─────────────────────────────────────────────────────────────┤
│ • One instance, starts with application                     │
│ • Always running, no UI required                            │
│ • Provides services to other widgets                        │
│ • Never destroyed until app shutdown                        │
└─────────────────────────────────────────────────────────────┘

Example: Not a widget, but services like TerminalService
```

## Widget Registration Architecture

### Registration Flow

```mermaid
graph TB
    A[Application Startup] --> B[register_builtin_widgets()]
    B --> C[AppWidgetManager.register_widget()]
    C --> D[Store AppWidgetMetadata]
    D --> E[Widget Available for Creation]

    F[User Action] --> G[Command Execution]
    G --> H[workspace_service.add_app_widget()]
    H --> I[AppWidgetManager.create_widget()]
    I --> J[Widget Instance Created]
```

### Metadata Structure

Each widget must be registered with complete metadata:

```python
AppWidgetMetadata(
    # Identity
    widget_id="com.viloapp.terminal",           # Unique registration ID
    widget_type=WidgetType.TERMINAL,            # Categorical type
    display_name="Terminal",                    # Human-readable name

    # Lifecycle Management
    singleton=False,                            # Multiple instances allowed
    persistent_service="TerminalService",       # Background service required
    can_suspend=False,                         # Cannot suspend (has PTY process)

    # UI Integration
    category=WidgetCategory.TERMINAL,           # Menu grouping
    icon="terminal",                            # Icon identifier
    show_in_menu=True,                         # Show in pane menus

    # Commands
    open_command="file.newTerminalTab",         # Command to open

    # Technical
    widget_class=TerminalAppWidget,             # Implementation class
    min_width=300,                             # Minimum dimensions
    min_height=200,

    # Capabilities
    provides_capabilities=["shell_execution", "ansi_display"],
    requires_services=["terminal_service"],
)
```

## Service vs Widget Distinction

Understanding the difference between services and widgets is crucial:

### Services (Background)
- **Purpose**: Provide functionality and manage resources
- **Lifecycle**: Start with application, persist throughout
- **Examples**: TerminalService, ThemeService, FileService
- **Location**: `services/` directory
- **Management**: ServiceLocator

### Widgets (UI)
- **Purpose**: Provide user interface for functionality
- **Lifecycle**: Created on demand, destroyed when closed
- **Examples**: TerminalAppWidget, SettingsAppWidget
- **Location**: `ui/widgets/` directory
- **Management**: AppWidgetManager

### Service-Widget Relationship

```
Service (Background)          Widget (UI)
┌─────────────────────┐      ┌─────────────────────┐
│ TerminalService     │ ←──→ │ TerminalAppWidget   │
│ • Manages PTY       │      │ • Displays terminal │
│ • Handles I/O       │      │ • Handles input     │
│ • Session lifecycle │      │ • Renders output    │
└─────────────────────┘      └─────────────────────┘
         │                            │
         │ Persistent                 │ Multiple instances
         │ (Always running)           │ (Created/destroyed)
         ↓                            ↓
    ┌─────────────┐              ┌─────────────┐
    │ Session 1   │              │ Tab 1       │
    │ Session 2   │              │ Tab 2       │
    │ Session 3   │              │ Tab 3       │
    └─────────────┘              └─────────────┘
```

## Widget Creation Patterns

### Pattern 1: Multi-Instance Widget Creation

```python
# Text Editor - Multiple instances allowed
def create_editor_tab(context):
    """Each call creates a new independent editor instance."""

    # Generate unique instance ID
    instance_id = f"editor_{uuid.uuid4().hex[:8]}"

    # Create new instance
    success = workspace_service.add_app_widget(
        widget_type=WidgetType.TEXT_EDITOR,
        widget_id=instance_id,      # ← Unique each time
        name="Text Editor"
    )

    # Result: New editor tab created
```

### Pattern 2: Singleton Widget Creation

```python
# Settings - Only one instance allowed
def open_settings(context):
    """First call creates, subsequent calls switch to existing."""

    # Use widget_id as instance_id for singletons
    widget_metadata = manager.get_widget_metadata("com.viloapp.settings")
    instance_id = widget_metadata.widget_id  # ← Always same for singleton

    # Check if already exists
    existing = workspace_service.find_widget_tab(instance_id)
    if existing:
        workspace_service.switch_to_tab(existing.index)
        return  # Switch to existing tab

    # Create singleton instance
    success = workspace_service.add_app_widget(
        widget_type=WidgetType.SETTINGS,
        widget_id=instance_id,      # ← Always same
        name="Settings"
    )

    # Result: Settings tab created or switched to existing
```

### Pattern 3: Service-Backed Widget Creation

```python
# Terminal - Service must be running first
def create_terminal_tab(context):
    """Creates UI instance backed by persistent service."""

    # 1. Ensure service is running
    terminal_service = service_locator.get(TerminalService)
    if not terminal_service.is_running():
        terminal_service.start()

    # 2. Create session in service
    session_id = terminal_service.create_session()

    # 3. Create UI instance with session reference
    instance_id = f"terminal_{session_id}"
    success = workspace_service.add_app_widget(
        widget_type=WidgetType.TERMINAL,
        widget_id=instance_id,
        name=f"Terminal {len(terminal_service.sessions)}"
    )

    # Result: Terminal tab created, connected to service session
```

## Widget Suspension Patterns

### Understanding Suspension Control

The `can_suspend` property determines whether a widget enters the SUSPENDED state when hidden. This is critical for widgets with background operations.

#### Pattern: Non-Suspendable Widget (Terminal)
```python
class TerminalAppWidget(AppWidget):
    """Terminal with background PTY process."""

    # Registration includes:
    # can_suspend=False  # PTY must keep running

    def on_suspend(self):
        # This will NEVER be called due to can_suspend=False
        pass

    def hideEvent(self, event):
        # Widget stays in READY state even when hidden
        # PTY process continues running
        super().hideEvent(event)
```

#### Pattern: Suspendable Widget (Editor)
```python
class EditorAppWidget(AppWidget):
    """Editor with no background operations."""

    # Registration includes:
    # can_suspend=True  # Default, saves resources

    def on_suspend(self):
        # Called when widget is hidden
        self.pause_syntax_highlighting()
        self.clear_undo_redo_stack()

    def on_resume(self):
        # Called when widget is shown again
        self.restore_syntax_highlighting()
        self.rebuild_undo_redo_stack()
```

### Suspension Decision Matrix

| Widget Type | Background Process | Network Connection | Real-time Data | can_suspend |
|-------------|-------------------|--------------------|----------------|-------------|
| Terminal | ✅ PTY | ❌ | ✅ Output stream | **False** |
| Editor | ❌ | ❌ | ❌ | **True** |
| Chat Client | ❌ | ✅ WebSocket | ✅ Messages | **False** |
| File Browser | ❌ | ❌ | ❌ | **True** |
| Log Monitor | ❌ | ❌ | ✅ Log tailing | **False** |
| Settings | ❌ | ❌ | ❌ | **True** |

## Common Patterns and Anti-Patterns

### ✅ Correct Patterns

#### Singleton Widget Command
```python
@command(id="settings.open")
def open_settings(context):
    # Use registered widget_id for singletons
    widget_id = "com.viloapp.settings"  # ← Consistent with registration

    # Check for existing instance
    if workspace_service.has_widget(widget_id):
        workspace_service.focus_widget(widget_id)
        return

    # Create singleton instance
    workspace_service.add_app_widget(WidgetType.SETTINGS, widget_id, "Settings")
```

#### Multi-Instance Widget Command
```python
@command(id="file.newEditor")
def new_editor(context):
    # Generate unique instance ID
    instance_id = f"editor_{uuid.uuid4().hex[:8]}"  # ← Unique each time

    workspace_service.add_app_widget(WidgetType.TEXT_EDITOR, instance_id, "Editor")
```

### ❌ Anti-Patterns (What Not To Do)

#### ❌ Random IDs for Singletons
```python
# WRONG - Breaks singleton behavior
def open_settings(context):
    widget_id = str(uuid.uuid4())[:8]  # ← Creates new instance each time!
    workspace_service.add_app_widget(WidgetType.SETTINGS, widget_id, "Settings")
```

#### ❌ WidgetType Mismatches
```python
# WRONG - Registration vs usage mismatch
# Registration:
widget_type=WidgetType.SETTINGS

# Command:
workspace_service.add_app_widget(WidgetType.CUSTOM, ...)  # ← Different type!
```

#### ❌ Service-Widget Confusion
```python
# WRONG - Creating service instead of widget
def new_terminal(context):
    terminal_service = TerminalService()  # ← This is a service, not a widget!
    workspace_service.add_tab(terminal_service)  # ← Won't work
```

## Decision Tree: Choosing Widget Patterns

```
┌─────────────────────────────────────────────────────────────┐
│                  WIDGET PATTERN DECISION TREE              │
└─────────────────────────────────────────────────────────────┘

1. Does this widget need a background service?
   ├─ YES → Does the service need to persist after UI closes?
   │  ├─ YES → SERVICE-BACKED PATTERN (Terminal)
   │  └─ NO → MULTI-INSTANCE or SINGLETON with service
   └─ NO → Continue to question 2

2. Should only one instance exist at a time?
   ├─ YES → SINGLETON PATTERN (Settings, Theme Editor)
   └─ NO → MULTI-INSTANCE PATTERN (Editor, File Viewer)

3. Service Requirements:
   ├─ Always Running → Start service at app startup
   ├─ On Demand → Start service when first widget created
   └─ No Service → Widget manages its own resources

4. Instance Management:
   ├─ Singleton → Use widget_id as instance_id
   ├─ Multi-Instance → Generate unique instance_id
   └─ Service-Backed → Use session/connection ID

5. Suspension Control:
   ├─ Has background process? → can_suspend = False (Terminal)
   ├─ Network connections? → can_suspend = False
   ├─ Real-time data? → can_suspend = False
   └─ UI-only widget? → can_suspend = True (Editor, Settings)
```

## Registration Checklist

When registering a new widget, complete this checklist:

### Identity
- [ ] Choose unique widget_id (reverse domain notation)
- [ ] Select appropriate WidgetType (or create new one)
- [ ] Decide on display_name and description

### Lifecycle Pattern
- [ ] Determine lifecycle pattern (singleton/multi-instance/service-backed)
- [ ] Set singleton flag correctly
- [ ] Identify service dependencies
- [ ] Define persistence requirements
- [ ] Set can_suspend based on background operations

### Integration
- [ ] Create open_command
- [ ] Set category for menu grouping
- [ ] Choose appropriate icon
- [ ] Define capabilities and requirements

### Implementation
- [ ] Implement AppWidget subclass
- [ ] Handle cleanup properly
- [ ] Implement serialization if needed
- [ ] Add proper error handling

### Testing
- [ ] Test widget creation
- [ ] Test lifecycle transitions
- [ ] Test singleton behavior (if applicable)
- [ ] Test service integration (if applicable)

## Troubleshooting Guide

### Common Issues and Solutions

#### Issue: "Multiple Settings tabs created"
**Cause**: Command generates random widget_id instead of using registered ID
**Solution**: Use `com.viloapp.settings` as both widget_id and instance_id

#### Issue: "Widget not found in menu"
**Cause**: Widget metadata not registered or `show_in_menu=False`
**Solution**: Check registration in `core/app_widget_registry.py`

#### Issue: "Service not available when widget created"
**Cause**: Service not started before widget creation
**Solution**: Ensure service is running in command before creating widget

#### Issue: "Widget crashes on creation"
**Cause**: Missing service dependency or incorrect WidgetType
**Solution**: Check `requires_services` and verify WidgetType matches

#### Issue: "Singleton widget creates multiple instances"
**Cause**: Different instance_id used each time
**Solution**: Use consistent instance_id (typically same as widget_id)

## Architecture Migration Path

For existing widgets that don't follow these patterns:

### Phase 1: Metadata Registration
1. Add complete AppWidgetMetadata
2. Set correct lifecycle flags
3. Add open_command

### Phase 2: Command Updates
1. Fix widget_id usage in commands
2. Implement proper singleton logic
3. Add service dependency checks

### Phase 3: Service Separation
1. Extract services from widgets
2. Update widget-service communication
3. Implement proper lifecycle management

## See Also

- [AppWidgetManager Implementation](app-widget-manager.md) - Detailed manager implementation
- [Widget Lifecycle States](WIDGET_LIFECYCLE.md) - State machine details
- [Developer Guide](../dev-guides/widget-lifecycle-guide.md) - Practical examples
- [Widget Development](../development/widget-development-guide.md) - Creating new widgets
- [Service Architecture](../architecture/SERVICES.md) - Service layer details

---

**Last Updated**: January 2025
**Status**: Complete
**Next Review**: When adding new widget patterns