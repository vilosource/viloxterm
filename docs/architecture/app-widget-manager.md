# AppWidget Manager Architecture

## Overview

The AppWidgetManager is a centralized registry system that manages all application widgets in ViloxTerm. It replaces the previous fragmented widget management approach with a unified system that provides comprehensive metadata, dynamic discovery, and plugin-ready architecture.

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

## Current Registered Widgets

| Widget ID | Display Name | Category | Type | Features |
|-----------|--------------|----------|------|----------|
| `com.viloapp.terminal` | Terminal | terminal | TERMINAL | Shell execution, ANSI colors |
| `com.viloapp.editor` | Text Editor | editor | TEXT_EDITOR | Syntax highlighting, file editing |
| `com.viloapp.theme_editor` | Theme Editor | tools | SETTINGS | Live preview, color customization |
| `com.viloapp.shortcuts` | Keyboard Shortcuts | tools | SETTINGS | Shortcut configuration |
| `com.viloapp.placeholder` | Empty Pane | system | PLACEHOLDER | Placeholder content |
| `com.viloapp.output` | Output Panel | tools | OUTPUT | Command output display |
| `com.viloapp.explorer` | File Explorer | viewer | FILE_EXPLORER | File system navigation |

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

## Future Enhancements

### Planned Features
1. **Plugin System**: Full plugin support with discovery and loading
2. **Hot Reload**: Dynamic widget reloading during development
3. **Widget Templates**: Template system for common widget types
4. **Dependency Injection**: Service locator integration
5. **Capability Negotiation**: Advanced capability matching

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

## Best Practices

### Widget Registration
- Use reverse domain naming: `com.company.widget`
- Provide complete metadata
- Include meaningful descriptions
- Specify all capabilities and requirements

### Widget Implementation
- Follow AppWidget base class contract
- Handle cleanup properly
- Emit appropriate signals
- Support serialization if needed

### Error Handling
- Check widget creation success
- Provide fallbacks for missing widgets
- Log errors with context
- Don't crash on widget failures

## Conclusion

The AppWidgetManager represents a significant architectural improvement that centralizes widget management while preparing for future plugin support. The system maintains backward compatibility while providing modern, extensible architecture suitable for long-term growth.