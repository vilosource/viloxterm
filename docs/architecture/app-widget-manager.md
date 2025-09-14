# AppWidget Manager Architecture

## Overview

The AppWidgetManager is a centralized registry system that manages all application widgets in ViloxTerm. It replaces the previous fragmented widget management approach with a unified system that provides comprehensive metadata, dynamic discovery, and plugin-ready architecture.

> **📖 Related Documentation:**
> - [Widget Architecture Guide](WIDGET-ARCHITECTURE-GUIDE.md) - Complete widget architecture overview
> - [Widget Lifecycle](WIDGET_LIFECYCLE.md) - State management and lifecycle patterns
> - [Developer Guide](../dev-guides/widget-lifecycle-guide.md) - Practical implementation examples

## Architecture Components

### Core Classes

#### AppWidgetMetadata
```python
@dataclass
class AppWidgetMetadata:
    """Complete metadata for an AppWidget"""
    # Identity
    widget_id: str                    # Unique ID like "com.viloapp.terminal"
    widget_type: WidgetType          # Enum value for compatibility

    # Display
    display_name: str                # Human-readable name
    description: str                 # Widget description
    icon: str                       # Icon name
    category: WidgetCategory        # Categorical grouping

    # Technical
    widget_class: Type['AppWidget']  # Widget class
    factory: Optional[Callable]     # Optional factory function

    # Integration
    open_command: Optional[str]     # Command to open widget
    provides_capabilities: List[str] # Capabilities this widget provides
    requires_services: List[str]    # Required services

    # Behavior
    singleton: bool = False         # Only one instance allowed
    show_in_menu: bool = True      # Show in UI menus
    can_suspend: bool = True       # Can be suspended when hidden
    supported_file_types: List[str] # File types this widget handles

    # Plugin support
    source: str = "builtin"        # Source identifier
    version: str = "1.0.0"         # Widget version
```

#### AppWidgetManager
```python
class AppWidgetManager:
    """Singleton registry for all AppWidget metadata and creation"""

    # Core functionality
    def register_widget(self, metadata: AppWidgetMetadata)
    def create_widget(self, widget_id: str, instance_id: str) -> Optional[AppWidget]
    def create_widget_by_type(self, widget_type: WidgetType, instance_id: str) -> Optional[AppWidget]

    # Querying
    def get_widget_metadata(self, widget_id: str) -> Optional[AppWidgetMetadata]
    def get_all_widgets(self) -> List[AppWidgetMetadata]
    def get_widgets_by_category(self, category: WidgetCategory) -> List[AppWidgetMetadata]
    def get_widgets_with_capability(self, capability: str) -> List[AppWidgetMetadata]
    def get_widgets_for_file_type(self, file_type: str) -> List[AppWidgetMetadata]
    def get_menu_widgets(self) -> List[AppWidgetMetadata]
```

#### WidgetCategory
```python
class WidgetCategory(Enum):
    """Widget categories for organization"""
    EDITOR = "editor"       # Text/code editors
    TERMINAL = "terminal"   # Terminal emulators
    VIEWER = "viewer"      # File/content viewers
    TOOLS = "tools"        # Utility tools
    SYSTEM = "system"      # System widgets (placeholders, etc.)
```

## System Integration

### Registration Flow
```
Application Startup
    ↓
register_builtin_widgets()
    ↓
AppWidgetManager.register_widget() × 7
    ↓
Widgets available for discovery
```

### Widget Creation Flow
```
User Action → Command → SplitPaneModel.create_app_widget()
    ↓
AppWidgetManager.create_widget_by_type()
    ↓
Factory function OR Direct instantiation
    ↓
AppWidget instance created
```

### Menu Generation Flow
```
PaneHeader.show_widget_type_menu()
    ↓
AppWidgetManager.get_menu_widgets()
    ↓
Group by category
    ↓
Dynamic QMenu creation
```

## Widget Lifecycle Patterns

The AppWidgetManager supports four distinct widget lifecycle patterns:

### Pattern 1: Multi-Instance Widgets
```python
# Example: Text Editor - Multiple independent instances
AppWidgetMetadata(
    widget_id="com.viloapp.editor",
    singleton=False,                    # ← Multiple instances allowed
    open_command="file.newEditorTab"
)

# Usage: Each command call creates new instance
instance_id = f"editor_{uuid.uuid4().hex[:8]}"  # ← Unique ID each time
```

### Pattern 2: Singleton Widgets
```python
# Example: Settings - Only one instance allowed
AppWidgetMetadata(
    widget_id="com.viloapp.settings",
    singleton=True,                     # ← Only one instance
    open_command="settings.openSettings"
)

# Usage: Reuse existing instance
instance_id = "com.viloapp.settings"   # ← Same ID for singleton
```

### Pattern 3: Service-Backed Widgets
```python
# Example: Terminal - Multiple UI instances sharing background service
AppWidgetMetadata(
    widget_id="com.viloapp.terminal",
    singleton=False,                    # ← Multiple UI instances
    requires_services=["terminal_service"],  # ← Background service required
    persistent_service=True             # ← Service persists after UI closes
)

# Service Architecture:
# TerminalService (Background) ←→ Multiple TerminalAppWidget instances
```

### Pattern 4: Utility Widgets
```python
# Example: Placeholder - System utility widget
AppWidgetMetadata(
    widget_id="com.viloapp.placeholder",
    singleton=False,
    show_in_menu=False,                 # ← Hidden from user menus
    category=WidgetCategory.SYSTEM      # ← System widget
)
```

## Current Registered Widgets

| Widget ID | Display Name | Pattern | Type | Can Suspend | Features |
|-----------|--------------|---------|------|-------------|----------|
| `com.viloapp.terminal` | Terminal | Service-Backed | TERMINAL | ❌ No | Shell execution, ANSI colors, PTY process |
| `com.viloapp.editor` | Text Editor | Multi-Instance | TEXT_EDITOR | ✅ Yes | Syntax highlighting, file editing |
| `com.viloapp.theme_editor` | Theme Editor | Singleton | SETTINGS | ✅ Yes | Live preview, color customization |
| `com.viloapp.shortcuts` | Keyboard Shortcuts | Singleton | SETTINGS | ✅ Yes | Shortcut configuration |
| `com.viloapp.settings` | Settings | Singleton | SETTINGS | ✅ Yes | Application defaults, preferences |
| `com.viloapp.placeholder` | Empty Pane | Utility | PLACEHOLDER | ✅ Yes | Placeholder content |
| `com.viloapp.output` | Output Panel | Multi-Instance | OUTPUT | ✅ Yes | Command output display |
| `com.viloapp.explorer` | File Explorer | Multi-Instance | EXPLORER | File system navigation |

## Service vs Widget Architecture

### Service-Backed Widgets (Terminal Example)

```
┌─────────────────────────────────────────────────────────────┐
│                    TerminalService                          │
│                 (Background Service)                        │
├─────────────────────────────────────────────────────────────┤
│ • Always running after first terminal created              │
│ • Manages PTY processes and sessions                        │
│ • Handles I/O between shell and UI                          │
│ • Persists after UI widgets are closed                      │
├─────────────────────────────────────────────────────────────┤
│ Session 1 (bash) │ Session 2 (zsh) │ Session 3 (fish)     │
└─────────────────────────────────────────────────────────────┘
         ↑                   ↑                   ↑
  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
  │Terminal     │     │Terminal     │     │Terminal     │
  │Widget 1     │     │Widget 2     │     │Widget 3     │
  │(UI View)    │     │(UI View)    │     │(UI View)    │
  └─────────────┘     └─────────────┘     └─────────────┘
```

**Key Points:**
- **Service**: Persistent, manages actual functionality
- **Widgets**: Transient UI views into service state
- **Relationship**: One service, many widgets
- **Lifecycle**: Service starts on first widget, continues after widgets close

### Singleton Widgets (Settings Example)

```
┌─────────────────────────────────────────────────────────────┐
│                   Settings Widget                           │
│                  (Singleton Pattern)                        │
├─────────────────────────────────────────────────────────────┤
│ • Only one instance allowed                                 │
│ • Opening again switches to existing tab                    │
│ • widget_id used as instance_id                             │
│ • No background service required                            │
└─────────────────────────────────────────────────────────────┘
```

## Widget Suspension Control

### Overview
The AppWidgetManager supports suspension control through the `can_suspend` property in widget metadata. This allows widgets with background processes to prevent automatic suspension when hidden.

### How It Works
1. **Metadata Configuration**: Set `can_suspend` in AppWidgetMetadata during registration
2. **Widget Creation**: AppWidgetManager calls `set_metadata()` on created widgets
3. **Runtime Behavior**: AppWidget checks `can_suspend` before entering SUSPENDED state
4. **Visibility Events**: hideEvent/showEvent respect the suspension setting

### Suspension Guidelines

#### Widgets That Should NOT Suspend (`can_suspend=False`)
- **Terminal**: Has PTY process that must continue running
- **Network Clients**: Maintain persistent connections
- **Real-time Monitors**: Display live data streams
- **Background Workers**: Perform ongoing computations

#### Widgets That SHOULD Suspend (`can_suspend=True`, default)
- **Editors**: Only active when user is editing
- **Settings**: Static configuration UI
- **File Browsers**: No background operations
- **Documentation**: Static content viewers

### Example Registration
```python
# Terminal - Never suspend (has PTY process)
AppWidgetMetadata(
    widget_id="com.viloapp.terminal",
    widget_type=WidgetType.TERMINAL,
    can_suspend=False,  # Critical: PTY must keep running
    # ... other metadata
)

# Editor - Can suspend (no background operations)
AppWidgetMetadata(
    widget_id="com.viloapp.editor",
    widget_type=WidgetType.TEXT_EDITOR,
    can_suspend=True,  # Default: saves resources when hidden
    # ... other metadata
)
```

### Implementation in AppWidget
```python
class AppWidget(QWidget):
    def suspend(self):
        """Suspend widget when hidden/inactive."""
        if not self.can_suspend:
            logger.debug(f"Widget {self.widget_id} cannot be suspended")
            return
        # ... suspension logic

    @property
    def can_suspend(self) -> bool:
        """Check if widget can be suspended."""
        if self._metadata:
            return self._metadata.can_suspend
        return True  # Default allows suspension
```

## Benefits

### Immediate Benefits
- **Single Source of Truth**: All widget information centralized
- **Dynamic Discovery**: No hardcoded widget lists
- **Rich Metadata**: Comprehensive widget information
- **Type Safety**: Strong typing throughout system
- **Consistent API**: Unified registration and creation patterns

### Long-term Benefits
- **Plugin Ready**: Architecture supports future plugin system
- **Extensible**: Add new widgets without code changes
- **Maintainable**: Clear separation of concerns
- **Scalable**: Efficient querying and caching
- **Professional**: Industry-standard registry pattern

## Backward Compatibility

The system maintains full backward compatibility:

1. **Legacy WidgetRegistry**: Still functions as fallback
2. **Existing APIs**: All existing widget creation code works unchanged
3. **Gradual Migration**: Old and new systems coexist
4. **Deprecation Warnings**: Gentle migration path for developers

## Plugin Architecture Foundation

The AppWidgetManager provides the foundation for future plugin support:

### Plugin Metadata Extension
```python
# Future plugin metadata
plugin_metadata = AppWidgetMetadata(
    widget_id="com.example.plugin.mywidget",
    source="plugin",
    plugin_id="com.example.plugin",
    version="2.1.0",
    # ... standard metadata
)
```

### Plugin Discovery
```python
# Future plugin loading
def load_plugin_widgets(plugin_path: str):
    manifest = load_plugin_manifest(plugin_path)
    for widget_def in manifest.widgets:
        metadata = create_widget_metadata(widget_def)
        manager.register_widget(metadata)
```

### Security Considerations
- Plugin sandboxing preparation
- Capability-based permissions
- Service access control
- Manifest validation

## Testing

### Test Coverage
- **Unit Tests**: 24 tests covering all manager functionality
- **GUI Tests**: 12 tests covering UI integration
- **Coverage**: >95% code coverage
- **Non-blocking**: All tests use pytest-qt properly

### Test Categories
1. **Registration**: Widget registration and metadata handling
2. **Creation**: Widget instantiation and factory functions
3. **Querying**: All discovery and filtering methods
4. **Integration**: UI component integration
5. **Compatibility**: Backward compatibility verification

## Performance Characteristics

### Efficiency Features
- **Singleton Pattern**: Single manager instance
- **Lazy Loading**: Widgets created only when needed
- **Caching**: Query results cached for performance
- **Indexed Lookup**: O(1) lookup by widget_id and type

### Memory Usage
- **Metadata Only**: Widget classes not instantiated until needed
- **Weak References**: No circular references
- **Garbage Collection**: Proper cleanup of widget instances

## Error Handling

### Graceful Degradation
- **Missing Widgets**: Fallback to placeholder widgets
- **Import Errors**: Log warnings, continue with available widgets
- **Creation Failures**: Return None, log errors
- **Invalid Metadata**: Validation with helpful error messages

### Logging
- **Registration**: Debug logs for all widget registrations
- **Creation**: Info logs for widget instantiation
- **Errors**: Error logs with context for troubleshooting
- **Performance**: Debug logs for performance monitoring

## Widget Intent System

### Overview
The Widget Intent System provides context-aware placement of widgets based on invocation source.

### Intent Configuration
Widgets can specify their placement behavior through metadata:
- **default_placement**: WidgetPlacement enum (NEW_TAB, REPLACE_CURRENT, SMART)
- **supports_replacement**: Whether widget can replace pane content
- **supports_new_tab**: Whether widget can open in new tab
- **commands**: Context-specific command mapping

### Command Mapping
Each widget can define commands for different contexts:
```python
metadata.commands = {
    "open_new_tab": "widget.open",         # Menu bar/command palette
    "replace_pane": "widget.replaceInPane" # Pane header menu
}
```

### Pane Header Integration
The pane header menu automatically:
1. Queries AppWidgetManager for available widgets
2. Filters widgets that support replacement
3. Invokes the appropriate replacement command
4. Passes pane context (pane_id) to the command

### Implementation Example
```python
# Widget registration with intent
metadata = AppWidgetMetadata(
    widget_id="com.viloapp.terminal",
    default_placement=WidgetPlacement.SMART,
    supports_replacement=True,
    supports_new_tab=True,
    commands={
        "open_new_tab": "file.newTerminalTab",
        "replace_pane": "file.replaceWithTerminal"
    }
)
```

## Future Enhancements

### Planned Features
1. **Plugin System**: Full plugin support with discovery and loading
2. **Hot Reload**: Dynamic widget reloading during development
3. **Widget Templates**: Template system for common widget types
4. **Dependency Injection**: Service locator integration
5. **Capability Negotiation**: Advanced capability matching
6. **Intent Profiles**: User-configurable placement preferences
7. **Smart Placement AI**: ML-based context-aware placement

### Extension Points
- **Custom Categories**: Support for plugin-defined categories
- **Advanced Querying**: Complex metadata queries
- **Widget Composition**: Composite widget support
- **Event System**: Widget lifecycle events
- **Metrics**: Usage tracking and analytics

## Migration Guide

### For Widget Developers
1. **Create Metadata**: Define comprehensive AppWidgetMetadata
2. **Register at Startup**: Use register_builtin_widgets()
3. **Update Commands**: Ensure open_command is specified
4. **Test Integration**: Verify menu generation works

### For UI Components
1. **Use Manager**: Query AppWidgetManager instead of hardcoded lists
2. **Dynamic Generation**: Generate menus/lists dynamically
3. **Handle Failures**: Gracefully handle missing widgets
4. **Update Tests**: Test with AppWidgetManager

## Common Mistakes and Solutions

### ❌ Anti-Pattern: Random IDs for Singletons
```python
# WRONG - Creates multiple Settings instances
@command(id="settings.open")
def open_settings(context):
    widget_id = str(uuid.uuid4())[:8]  # ← Different ID each time!
    workspace_service.add_app_widget(WidgetType.SETTINGS, widget_id, "Settings")
```

```python
# CORRECT - Singleton behavior
@command(id="settings.open")
def open_settings(context):
    widget_id = "com.viloapp.settings"  # ← Consistent with registration

    # Check for existing instance
    if workspace_service.has_widget(widget_id):
        workspace_service.focus_widget(widget_id)
        return

    workspace_service.add_app_widget(WidgetType.SETTINGS, widget_id, "Settings")
```

### ❌ Anti-Pattern: WidgetType Mismatches
```python
# WRONG - Registration vs command mismatch
# In registration:
AppWidgetMetadata(
    widget_id="com.viloapp.theme_editor",
    widget_type=WidgetType.SETTINGS,    # ← Registered as SETTINGS
    ...
)

# In command:
workspace_service.add_app_widget(
    widget_type=WidgetType.CUSTOM,      # ← Using different type!
    widget_id=widget_id
)
```

```python
# CORRECT - Consistent types
# Get metadata and use its type
metadata = manager.get_widget_metadata("com.viloapp.theme_editor")
workspace_service.add_app_widget(
    widget_type=metadata.widget_type,   # ← Use registered type
    widget_id=widget_id
)
```

### ❌ Anti-Pattern: Service-Widget Confusion
```python
# WRONG - Creating service in widget command
@command(id="terminal.new")
def new_terminal(context):
    service = TerminalService()         # ← This is a service, not a widget!
    workspace_service.add_tab(service)  # ← Won't work
```

```python
# CORRECT - Create widget that uses service
@command(id="terminal.new")
def new_terminal(context):
    # Ensure service is running
    terminal_service = service_locator.get(TerminalService)
    if not terminal_service.is_running():
        terminal_service.start()

    # Create widget instance
    instance_id = f"terminal_{uuid.uuid4().hex[:8]}"
    workspace_service.add_app_widget(WidgetType.TERMINAL, instance_id, "Terminal")
```

## Troubleshooting Guide

### Issue: "Multiple Settings tabs appear"
**Cause**: Command generates new widget_id each time instead of reusing singleton ID
**Solution**: Use `com.viloapp.settings` as both registration and instance ID

### Issue: "Widget not found in AppWidgetManager"
**Cause**: Widget not registered or registration failed
**Solution**: Check `core/app_widget_registry.py` and verify registration code

### Issue: "WidgetType not found error"
**Cause**: Using wrong WidgetType in command vs registration
**Solution**: Use `metadata.widget_type` from registered metadata

### Issue: "Service not available when widget loads"
**Cause**: Service dependency not started before widget creation
**Solution**: Ensure required services are running in widget creation command

## Best Practices

### Widget Registration
- Use reverse domain naming: `com.company.widget`
- Provide complete metadata including lifecycle pattern
- Include meaningful descriptions and capabilities
- Specify service dependencies clearly

### Widget Implementation
- Follow AppWidget base class contract
- Handle cleanup properly for all resource types
- Emit appropriate lifecycle signals
- Support serialization if widget has persistent state

### Command Implementation
- Always use registered widget_id for singletons
- Generate unique instance_id only for multi-instance widgets
- Check service dependencies before widget creation
- Handle creation failures gracefully

### Error Handling
- Check widget creation success and provide user feedback
- Provide fallbacks for missing widgets
- Log errors with sufficient context for debugging
- Never crash the application due to widget failures

## Conclusion

The AppWidgetManager represents a significant architectural improvement that centralizes widget management while preparing for future plugin support. The system maintains backward compatibility while providing modern, extensible architecture suitable for long-term growth.