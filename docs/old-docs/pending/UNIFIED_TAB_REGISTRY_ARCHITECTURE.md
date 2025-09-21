# Unified Tab Registry Architecture

## Current Situation

The application currently has a **mixed approach** for creating tabs with different widget types:

### 1. Specific Methods for Core Widget Types

The system has dedicated, hardcoded methods for Editor and Terminal tabs:

```python
# WorkspaceService methods
def add_editor_tab(self, name: Optional[str] = None) -> int
def add_terminal_tab(self, name: Optional[str] = None) -> int

# Workspace methods
def add_editor_tab(self, name: str = "Editor") -> int
def add_terminal_tab(self, name: str = "Terminal") -> int
```

These methods:
- Return `int` (tab index)
- Have specific implementation for each type
- Are called directly by commands like `file.newEditorTab` and `file.newTerminalTab`

### 2. Generic Method for Extended Widget Types

For the Settings widget (and future widgets), we added a generic method:

```python
# WorkspaceService method
def add_app_widget(self, widget_type, widget_id: str, name: Optional[str] = None) -> bool

# Workspace method
def add_app_widget_tab(self, widget_type, widget_id: str, name: str = None) -> bool
```

These methods:
- Return `bool` (success/failure)
- Work with any `WidgetType`
- Are more flexible but inconsistent with existing patterns

### 3. Partial Registry Pattern

The system already has a `WidgetRegistry` that:
- Stores configuration for each widget type
- Has factory methods for widget creation
- Manages widget properties (min size, styling, etc.)

However, the registry is **not fully utilized** for tab creation:
- Terminal uses `register_terminal_widget()` to register its factory
- Editor doesn't use the factory pattern
- Settings registers its factory on-demand in the command

### Problems with Current Architecture

1. **Code Duplication**: Similar logic repeated for each widget type
2. **Inconsistency**: Different return types and method signatures
3. **Limited Extensibility**: Adding new widget types requires new methods
4. **Mixed Patterns**: Some widgets use factories, others don't
5. **Maintenance Burden**: Multiple places to update when adding features

## Proposed Solution: Unified Registry-Based Tab System

### Overview

Migrate to a **fully registry-based system** where all tab creation goes through a unified path, leveraging the existing `WidgetRegistry` infrastructure.

### Architecture Components

#### 1. Enhanced Widget Registry

Extend `WidgetConfig` with tab-specific metadata:

```python
@dataclass
class WidgetConfig:
    # Existing fields...

    # New tab-related fields
    tab_name_template: str = "{type} {index}"  # e.g., "Editor 1", "Terminal 2"
    supports_tabs: bool = True  # Whether this widget can be opened in tabs
    requires_services: List[str] = None  # Services needed for initialization
    pre_creation_hook: Optional[Callable] = None  # Called before tab creation
    post_creation_hook: Optional[Callable] = None  # Called after tab creation
```

#### 2. Unified Tab Creation Method

Replace specific methods with a single, generic method:

```python
class WorkspaceService:
    def create_tab(self, widget_type: WidgetType, name: Optional[str] = None, **kwargs) -> TabResult:
        """
        Universal tab creation method.

        Args:
            widget_type: Type of widget to create
            name: Optional custom tab name
            **kwargs: Additional widget-specific parameters

        Returns:
            TabResult with success status, tab index, and any errors
        """
        # Get widget config from registry
        config = widget_registry.get_config(widget_type)
        if not config or not config.supports_tabs:
            return TabResult(success=False, error=f"{widget_type} doesn't support tabs")

        # Initialize required services
        if config.requires_services:
            for service_name in config.requires_services:
                service = self.get_service(service_name)
                if not service:
                    return TabResult(success=False, error=f"Required service {service_name} not available")

        # Pre-creation hook
        if config.pre_creation_hook:
            config.pre_creation_hook(widget_type, kwargs)

        # Generate name if not provided
        if not name:
            name = self._generate_tab_name(widget_type, config.tab_name_template)

        # Create the tab
        index = self._workspace.create_widget_tab(widget_type, name, **kwargs)

        # Post-creation hook
        if config.post_creation_hook:
            config.post_creation_hook(widget_type, index, kwargs)

        return TabResult(success=True, index=index, name=name)
```

#### 3. Backward Compatibility Layer

Keep existing methods as deprecated wrappers during transition:

```python
class WorkspaceService:
    @deprecated("Use create_tab(WidgetType.TEXT_EDITOR) instead")
    def add_editor_tab(self, name: Optional[str] = None) -> int:
        result = self.create_tab(WidgetType.TEXT_EDITOR, name)
        return result.index if result.success else -1

    @deprecated("Use create_tab(WidgetType.TERMINAL) instead")
    def add_terminal_tab(self, name: Optional[str] = None) -> int:
        result = self.create_tab(WidgetType.TERMINAL, name)
        return result.index if result.success else -1
```

#### 4. Dynamic Command Registration

Register tab creation commands based on widget registry:

```python
def register_tab_commands():
    """Dynamically register tab creation commands for all tab-capable widgets."""
    for widget_type in WidgetType:
        config = widget_registry.get_config(widget_type)
        if config and config.supports_tabs:
            # Create command dynamically
            @command(
                id=f"file.new{widget_type.value.title()}Tab",
                title=f"New {widget_type.value.title()} Tab",
                category="File",
                description=f"Create a new {widget_type.value} tab",
                icon=config.icon or "file-plus"
            )
            def create_tab_command(context: CommandContext, wt=widget_type):
                workspace_service = context.get_service(WorkspaceService)
                if not workspace_service:
                    return CommandResult(success=False, error="WorkspaceService not available")

                result = workspace_service.create_tab(wt, context.args.get('name'))
                return CommandResult(
                    success=result.success,
                    value={'index': result.index, 'name': result.name},
                    error=result.error
                )
```

#### 5. Registry Configuration Examples

```python
# Editor configuration
widget_registry.register_widget_type(
    WidgetType.TEXT_EDITOR,
    WidgetConfig(
        widget_class=QPlainTextEdit,
        tab_name_template="Editor {index}",
        supports_tabs=True,
        requires_services=[],
        # ... other config
    )
)

# Terminal configuration
widget_registry.register_widget_type(
    WidgetType.TERMINAL,
    WidgetConfig(
        widget_class=TerminalWidget,
        factory=create_terminal_widget,
        tab_name_template="Terminal {index}",
        supports_tabs=True,
        requires_services=["TerminalService"],
        pre_creation_hook=ensure_terminal_server_running,
        # ... other config
    )
)

# Settings configuration
widget_registry.register_widget_type(
    WidgetType.SETTINGS,
    WidgetConfig(
        widget_class=QWidget,
        factory=create_settings_widget,
        tab_name_template="Settings",
        supports_tabs=True,
        requires_services=[],
        # ... other config
    )
)
```

### Migration Plan

#### Phase 1: Preparation (No Breaking Changes)
1. Extend `WidgetConfig` with new fields (defaults maintain current behavior)
2. Implement `create_tab()` method alongside existing methods
3. Add `TabResult` class for better return type handling

#### Phase 2: Migration (Deprecation Warnings)
1. Update existing commands to use `create_tab()`
2. Add deprecation warnings to old methods
3. Update documentation to recommend new approach
4. Ensure all tests pass with both old and new methods

#### Phase 3: Cleanup (Next Major Version)
1. Remove deprecated methods
2. Remove duplicate code
3. Simplify command registration
4. Update all documentation

### Benefits

1. **Consistency**: Single path for all tab creation
2. **Extensibility**: New widget types automatically get tab support
3. **Maintainability**: Configuration-driven behavior
4. **DRY Principle**: No duplicate tab creation logic
5. **Type Safety**: Better return types with `TabResult`
6. **Service Integration**: Automatic service initialization
7. **Hooks System**: Extensible pre/post creation logic
8. **Dynamic UI**: Menus can be generated from registry

### Considerations

1. **Backward Compatibility**: Phased migration ensures no breaking changes
2. **Testing**: Need comprehensive tests for migration period
3. **Documentation**: Clear migration guide for plugin developers
4. **Performance**: Registry lookups are negligible overhead
5. **Type Safety**: Consider using TypedDict or dataclasses for kwargs

### Future Enhancements

Once the unified system is in place, we could add:

1. **Tab Templates**: Predefined configurations for common scenarios
2. **Tab Presets**: User-defined widget configurations
3. **Lazy Loading**: Only load widget code when first tab is created
4. **Tab Persistence**: Save/restore tab configurations
5. **Plugin System**: Third-party widgets can register themselves
6. **Context-Aware Tabs**: Different widget types based on file type or context

### Conclusion

The migration to a unified, registry-based tab system would:
- Eliminate code duplication
- Provide a consistent interface for all widget types
- Make the system more maintainable and extensible
- Preserve backward compatibility during transition
- Set up the architecture for future enhancements

This approach leverages the existing `WidgetRegistry` infrastructure while addressing the current inconsistencies in tab creation methods.