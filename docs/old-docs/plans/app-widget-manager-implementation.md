# AppWidget Manager Implementation Plan

## Executive Summary

This document outlines the implementation of a centralized AppWidgetManager to replace the current fragmented widget management system. The new system will provide a single source of truth for all widget metadata, enable dynamic widget discovery, and prepare the foundation for future plugin support.

## Current State Analysis

### Problems Identified

1. **Fragmented Widget Information**
   - Widget types defined in `widget_registry.py`
   - Display names hardcoded in `pane_header.py` (lines 239-248)
   - Widget categorization hardcoded in `pane_header.py` (lines 166-174)
   - Factory registration scattered across multiple files

2. **Inconsistent Registration Patterns**
   - Terminal: Registers at app startup in `main.py`
   - Settings/Shortcuts: Registers at module import in command files
   - Theme Editor: Uses `WidgetType.CUSTOM` instead of proper type
   - Editor: No factory, hardcoded in `SplitPaneModel`

3. **Limited Widget Metadata**
   - No capability information
   - No command associations
   - No category organization
   - No plugin readiness

4. **Hardcoded Widget Lists**
   - Menu generation manually lists widget types
   - No dynamic discovery mechanism
   - Cannot add new widgets without code changes

### Current Widget Flow

```
User Action → Command → WorkspaceService.add_app_widget()
→ Workspace.add_app_widget_tab() → SplitPaneWidget
→ SplitPaneModel.create_app_widget() → Factory/Direct Creation
```

## Proposed Solution

### Core Components

#### 1. AppWidgetMetadata Class

```python
@dataclass
class AppWidgetMetadata:
    """Complete metadata for an AppWidget"""
    # Identity
    widget_id: str  # Unique ID like "com.viloapp.terminal"
    widget_type: WidgetType  # Enum value for compatibility

    # Display
    display_name: str
    description: str
    icon: str
    category: WidgetCategory

    # Technical
    widget_class: Type['AppWidget']
    factory: Optional[Callable[[str], 'AppWidget']] = None

    # Commands
    open_command: Optional[str] = None
    associated_commands: List[str] = field(default_factory=list)

    # Behavior
    singleton: bool = False
    can_split: bool = True
    show_in_menu: bool = True
    show_in_palette: bool = True

    # Requirements & Capabilities
    requires_services: List[str] = field(default_factory=list)
    provides_capabilities: List[str] = field(default_factory=list)

    # Plugin preparation
    source: str = "builtin"
    plugin_id: Optional[str] = None
    version: str = "1.0.0"
```

#### 2. AppWidgetManager Singleton

```python
class AppWidgetManager:
    """Central registry for all AppWidget metadata and factories"""

    def register_widget(self, metadata: AppWidgetMetadata)
    def create_widget(self, widget_id: str, instance_id: str) -> Optional[AppWidget]
    def get_widget_by_type(self, widget_type: WidgetType) -> Optional[AppWidgetMetadata]
    def get_widgets_by_category(self, category: WidgetCategory) -> List[AppWidgetMetadata]
    def get_all_widgets(self) -> List[AppWidgetMetadata]
```

#### 3. Widget Categories

```python
class WidgetCategory(Enum):
    EDITOR = "editor"
    TERMINAL = "terminal"
    VIEWER = "viewer"
    TOOLS = "tools"
    DEVELOPMENT = "development"
    PLUGIN = "plugin"
```

### Implementation Phases

## Phase 1: Core Infrastructure (Week 1)

### Tasks
1. Create `core/app_widget_manager.py` with AppWidgetManager class
2. Create `core/app_widget_metadata.py` with metadata classes
3. Create `core/app_widget_registry.py` for built-in widget registration
4. Add AppWidgetManager to ServiceLocator
5. Write comprehensive unit tests

### Files to Create
- `core/app_widget_manager.py`
- `core/app_widget_metadata.py`
- `core/app_widget_registry.py`
- `tests/unit/test_app_widget_manager.py`
- `tests/gui/test_app_widget_integration.py`

## Phase 2: Widget Migration (Week 2)

### Tasks
1. Add new WidgetType entries (THEME_EDITOR, SHORTCUT_EDITOR)
2. Register all existing widgets with metadata
3. Update `SplitPaneModel.create_app_widget()` to use manager
4. Update `pane_header.py` to use manager for menu generation
5. Update commands to use manager

### Files to Modify
- `ui/widgets/widget_registry.py` - Add new WidgetType values
- `ui/widgets/split_pane_model.py` - Use AppWidgetManager
- `ui/widgets/pane_header.py` - Dynamic menu generation
- `core/commands/builtin/theme_commands.py` - Use proper widget type
- `core/commands/builtin/settings_commands.py` - Use proper widget type

## Phase 3: Testing & Documentation (Week 3)

### Testing Requirements
- Unit tests for AppWidgetManager
- GUI tests for widget creation and menu generation
- Integration tests for command execution
- No blocking or user interaction in tests
- Use pytest-qt fixtures properly

### Documentation Updates
- Update architecture documentation
- Create widget development guide
- Document migration from old system
- Add plugin preparation notes

## Migration Strategy

### Backward Compatibility
1. Keep existing `widget_registry` working
2. Add deprecation warnings
3. Bridge old factories to new system
4. Maintain existing APIs

### Migration Steps
1. **Stage 1**: Add AppWidgetManager alongside existing system
2. **Stage 2**: Migrate internal code to use manager
3. **Stage 3**: Deprecate old registration methods
4. **Stage 4**: Remove deprecated code (future release)

## Testing Strategy

### Unit Tests (`tests/unit/test_app_widget_manager.py`)
- Test widget registration
- Test widget creation
- Test category filtering
- Test metadata queries
- Test singleton behavior

### GUI Tests (`tests/gui/test_app_widget_integration.py`)
- Test menu generation
- Test widget creation in panes
- Test command integration
- Test dynamic discovery
- No user interaction required

### Test Fixtures
```python
@pytest.fixture
def app_widget_manager():
    """Provide clean AppWidgetManager instance"""
    manager = AppWidgetManager()
    # Register test widgets
    return manager

@pytest.fixture
def mock_widget_metadata():
    """Provide test widget metadata"""
    return AppWidgetMetadata(
        widget_id="test.widget",
        widget_type=WidgetType.CUSTOM,
        display_name="Test Widget",
        # ...
    )
```

## Success Criteria

### Phase 1 Complete
- [ ] AppWidgetManager implemented and tested
- [ ] All metadata classes created
- [ ] Unit tests passing with >90% coverage
- [ ] Added to ServiceLocator

### Phase 2 Complete
- [ ] All widgets migrated to new system
- [ ] Dynamic menu generation working
- [ ] Commands using manager
- [ ] GUI tests passing

### Phase 3 Complete
- [ ] All tests passing
- [ ] Documentation complete
- [ ] No hardcoded widget lists remain
- [ ] Backward compatibility maintained

## Future Enhancements

### Plugin Support (Future)
- Plugin discovery mechanism
- Plugin manifest parsing
- Security sandboxing
- Permission system
- Plugin marketplace

### Advanced Features (Future)
- Widget capability negotiation
- Service dependency injection
- Dynamic widget loading
- Hot reload support
- Widget templates

## Benefits

### Immediate
- **Single source of truth** for widget information
- **Dynamic discovery** of available widgets
- **Consistent registration** pattern
- **Rich metadata** for better UI
- **Command integration** built-in

### Long-term
- **Plugin ready** architecture
- **Extensible** without code changes
- **Maintainable** centralized system
- **Professional** following best practices
- **Scalable** to hundreds of widgets

## Risk Mitigation

### Risks
1. Breaking existing functionality
2. Performance impact
3. Complex migration
4. Test coverage gaps

### Mitigations
1. Comprehensive testing before migration
2. Lazy loading and caching
3. Phased migration approach
4. Automated test generation

## Implementation Checklist

### Pre-Implementation
- [x] Audit current system
- [x] Document findings
- [x] Design new architecture
- [x] Plan migration strategy
- [ ] Create feature branch

### Implementation
- [ ] Create core classes
- [ ] Write unit tests
- [ ] Migrate widgets
- [ ] Update UI components
- [ ] Write GUI tests

### Post-Implementation
- [ ] Update documentation
- [ ] Performance testing
- [ ] Code review
- [ ] Merge to develop
- [ ] Monitor for issues

## Appendix: Code Examples

### Widget Registration Example
```python
# In core/app_widget_registry.py
def register_builtin_widgets():
    manager = AppWidgetManager.get_instance()

    manager.register_widget(AppWidgetMetadata(
        widget_id="com.viloapp.terminal",
        widget_type=WidgetType.TERMINAL,
        display_name="Terminal",
        description="Integrated terminal emulator",
        icon="terminal",
        category=WidgetCategory.TERMINAL,
        widget_class=TerminalAppWidget,
        factory=create_terminal_widget,
        open_command="file.newTerminalTab",
        provides_capabilities=["shell_execution", "ansi_colors"]
    ))
```

### Dynamic Menu Generation Example
```python
# In pane_header.py
def show_widget_type_menu(self):
    menu = QMenu(self)
    manager = AppWidgetManager.get_instance()

    # Group by category
    for category in WidgetCategory:
        widgets = manager.get_widgets_by_category(category)
        if widgets:
            menu.addSection(category.value.title())
            for widget_meta in widgets:
                if widget_meta.show_in_menu:
                    action = QAction(
                        f"{widget_meta.icon} {widget_meta.display_name}",
                        self
                    )
                    action.triggered.connect(
                        lambda: execute_command(widget_meta.open_command)
                    )
                    menu.addAction(action)
```

### Test Example
```python
# In tests/unit/test_app_widget_manager.py
def test_widget_registration(app_widget_manager):
    """Test that widgets can be registered and retrieved"""
    metadata = AppWidgetMetadata(
        widget_id="test.widget",
        widget_type=WidgetType.CUSTOM,
        display_name="Test Widget",
        # ...
    )

    app_widget_manager.register_widget(metadata)

    # Verify retrieval
    retrieved = app_widget_manager.get_widget_metadata("test.widget")
    assert retrieved == metadata

    # Verify by type
    by_type = app_widget_manager.get_widget_by_type(WidgetType.CUSTOM)
    assert by_type == metadata
```

## Conclusion

The AppWidgetManager implementation will solve current architectural issues while preparing the codebase for future plugin support. The phased approach ensures minimal disruption while delivering immediate benefits.