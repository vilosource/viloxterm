# Architectural Improvement Plan

## Executive Summary

This document outlines the strategic plan to improve ViloApp's architecture based on the findings from the Architecture Review. The improvements will establish a solid foundation for implementing advanced features like keyboard shortcuts, command palette, and pane navigation.

## Current State vs Target State

### Current State
- **Actions scattered** across UI components
- **Business logic embedded** in view layers
- **No command abstraction** for operations
- **Limited testability** due to tight coupling
- **No context management** for state awareness

### Target State
- **Centralized command system** with registry
- **Service layer** separating business logic
- **Context-aware operations** with when clauses
- **Dependency injection** for loose coupling
- **Comprehensive keyboard management** system

## Implementation Phases

### Phase 1: Command System Foundation (3-4 days)

#### Objective
Establish the command pattern as the core mechanism for all application actions.

#### Directory Structure
```
core/
├── commands/
│   ├── __init__.py           # Public API
│   ├── base.py              # Command base classes
│   ├── registry.py          # Command registry
│   ├── executor.py          # Execution engine
│   ├── decorators.py        # @command decorator
│   └── context.py           # Command context
```

#### Core Components

##### 1. Command Base Class
```python
from abc import ABC, abstractmethod
from typing import Any, Optional, Dict
from dataclasses import dataclass

@dataclass
class CommandResult:
    """Result of command execution."""
    success: bool
    value: Any = None
    error: Optional[str] = None
    undo_data: Optional[Dict] = None

class Command(ABC):
    """Base class for all commands."""
    
    def __init__(self, 
                 id: str,
                 title: str,
                 category: str = "General",
                 description: str = "",
                 icon: Optional[str] = None,
                 shortcut: Optional[str] = None,
                 when: Optional[str] = None):
        self.id = id
        self.title = title
        self.category = category
        self.description = description
        self.icon = icon
        self.shortcut = shortcut
        self.when = when  # Context expression
        self._enabled = True
        
    @abstractmethod
    def execute(self, context: 'CommandContext') -> CommandResult:
        """Execute the command."""
        pass
        
    def can_execute(self, context: 'CommandContext') -> bool:
        """Check if command can be executed."""
        return self._enabled and self._evaluate_when_clause(context)
        
    def undo(self, context: 'CommandContext', undo_data: Dict) -> CommandResult:
        """Undo the command. Override for undo support."""
        return CommandResult(False, error="Undo not supported")
        
    def redo(self, context: 'CommandContext', undo_data: Dict) -> CommandResult:
        """Redo the command. Override for redo support."""
        return self.execute(context)
```

##### 2. Command Context
```python
@dataclass
class CommandContext:
    """Context passed to commands during execution."""
    
    # Application references
    main_window: Optional['MainWindow'] = None
    workspace: Optional['Workspace'] = None
    active_widget: Optional['QWidget'] = None
    
    # Services (will be added in Phase 2)
    services: Dict[str, Any] = field(default_factory=dict)
    
    # Context values for when clauses
    context_values: Dict[str, Any] = field(default_factory=dict)
    
    # Command arguments
    args: Dict[str, Any] = field(default_factory=dict)
    
    def get_service(self, service_type: Type[T]) -> Optional[T]:
        """Get a service instance."""
        return self.services.get(service_type.__name__)
```

##### 3. Command Registry
```python
class CommandRegistry:
    """Central registry for all commands."""
    
    def __init__(self):
        self._commands: Dict[str, Command] = {}
        self._categories: Dict[str, List[Command]] = {}
        self._shortcuts: Dict[str, str] = {}  # shortcut -> command_id
        
    def register(self, command: Command) -> None:
        """Register a command."""
        self._commands[command.id] = command
        
        # Index by category
        if command.category not in self._categories:
            self._categories[command.category] = []
        self._categories[command.category].append(command)
        
        # Register shortcut
        if command.shortcut:
            self._shortcuts[command.shortcut] = command.id
            
    def get_command(self, command_id: str) -> Optional[Command]:
        """Get command by ID."""
        return self._commands.get(command_id)
        
    def get_all_commands(self) -> List[Command]:
        """Get all registered commands."""
        return list(self._commands.values())
```

#### Migration Examples

##### Before (Current Code)
```python
# In MainWindow.create_menu_bar()
theme_action = QAction("Toggle Theme", self)
theme_action.setShortcut(QKeySequence("Ctrl+T"))
theme_action.triggered.connect(self.toggle_theme)

def toggle_theme(self):
    icon_manager = get_icon_manager()
    icon_manager.toggle_theme()
    current_theme = icon_manager.theme.capitalize()
    self.status_bar.set_message(f"Switched to {current_theme} theme", 2000)
```

##### After (With Command System)
```python
# In commands/view_commands.py
class ToggleThemeCommand(Command):
    def __init__(self):
        super().__init__(
            id="view.toggleTheme",
            title="Toggle Theme",
            category="View",
            description="Switch between light and dark theme",
            shortcut="ctrl+t"
        )
        
    def execute(self, context: CommandContext) -> CommandResult:
        icon_manager = get_icon_manager()
        icon_manager.toggle_theme()
        
        current_theme = icon_manager.theme.capitalize()
        if context.main_window:
            context.main_window.status_bar.set_message(
                f"Switched to {current_theme} theme", 2000
            )
        
        return CommandResult(success=True, value=current_theme)

# Registration
command_registry.register(ToggleThemeCommand())
```

### Phase 2: Service Layer (2-3 days)

#### Objective
Extract business logic from UI components into dedicated services.

#### Directory Structure
```
services/
├── __init__.py
├── base.py                  # ServiceBase class
├── service_locator.py       # Service registry
├── workspace_service.py     # Tab/pane management
├── editor_service.py        # Editor operations
├── terminal_service.py      # Terminal management
├── ui_service.py           # UI state management
└── file_service.py         # File operations
```

#### Core Components

##### Service Base Class
```python
class Service(ABC):
    """Base class for all services."""
    
    def __init__(self):
        self._observers = []
        
    def attach(self, observer):
        """Attach an observer."""
        self._observers.append(observer)
        
    def notify(self, event: str, data: Any = None):
        """Notify all observers."""
        for observer in self._observers:
            observer.update(event, data)
```

##### Service Locator
```python
class ServiceLocator:
    """Central registry for services."""
    
    _instance = None
    _services: Dict[Type, Any] = {}
    
    @classmethod
    def register(cls, service_type: Type[T], instance: T):
        """Register a service."""
        cls._services[service_type] = instance
        
    @classmethod
    def get(cls, service_type: Type[T]) -> Optional[T]:
        """Get a service instance."""
        return cls._services.get(service_type)
```

##### Example: Workspace Service
```python
class WorkspaceService(Service):
    """Manages workspace operations."""
    
    def __init__(self, workspace: Workspace):
        super().__init__()
        self._workspace = workspace
        
    def add_editor_tab(self, name: str = "Editor") -> int:
        """Add a new editor tab."""
        index = self._workspace.add_editor_tab(name)
        self.notify("tab_added", {"type": "editor", "name": name, "index": index})
        return index
        
    def split_active_pane(self, orientation: str = "horizontal"):
        """Split the active pane."""
        if orientation == "horizontal":
            self._workspace.split_active_pane_horizontal()
        else:
            self._workspace.split_active_pane_vertical()
        self.notify("pane_split", {"orientation": orientation})
```

### Phase 3: Context System (2 days)

#### Objective
Enable context-aware commands and shortcuts.

#### Directory Structure
```
core/context/
├── __init__.py
├── manager.py              # ContextManager
├── keys.py                # Context key definitions
├── evaluator.py           # When clause evaluation
└── providers.py           # Context providers
```

#### Context Keys
```python
class ContextKeys:
    """Standard context keys."""
    
    # Focus contexts
    EDITOR_FOCUS = "editorFocus"
    TERMINAL_FOCUS = "terminalFocus"
    SIDEBAR_FOCUS = "sidebarFocus"
    
    # Visibility contexts
    SIDEBAR_VISIBLE = "sidebarVisible"
    TERMINAL_VISIBLE = "terminalVisible"
    
    # State contexts
    HAS_OPEN_EDITORS = "hasOpenEditors"
    HAS_MULTIPLE_TABS = "hasMultipleTabs"
    CAN_SPLIT = "canSplit"
    
    # Mode contexts
    VIM_MODE = "vimMode"
    DEBUG_MODE = "debugMode"
```

#### Context Manager
```python
class ContextManager:
    """Manages application context."""
    
    def __init__(self):
        self._context: Dict[str, Any] = {}
        self._providers: List[ContextProvider] = []
        
    def set_context(self, key: str, value: Any):
        """Set a context value."""
        old_value = self._context.get(key)
        self._context[key] = value
        if old_value != value:
            self._notify_change(key, value)
            
    def evaluate_when_clause(self, when: str) -> bool:
        """Evaluate a when clause expression."""
        if not when:
            return True
        # Parse and evaluate expression
        return WhenClauseEvaluator.evaluate(when, self._context)
```

### Phase 4: Keyboard Service (2 days)

#### Objective
Centralize keyboard shortcut management.

#### Directory Structure
```
core/keyboard/
├── __init__.py
├── service.py             # KeyboardService
├── shortcuts.py           # Shortcut definitions
├── parser.py             # Key sequence parser
├── conflicts.py          # Conflict resolution
└── keymaps/
    ├── default.json      # Default keymap
    ├── vscode.json       # VSCode keymap
    └── vim.json          # Vim keymap
```

#### Keyboard Service
```python
class KeyboardService:
    """Manages keyboard shortcuts."""
    
    def __init__(self, command_registry: CommandRegistry):
        self._registry = command_registry
        self._shortcuts: Dict[str, str] = {}  # key -> command_id
        self._keymap: str = "default"
        
    def register_shortcut(self, key: str, command_id: str, when: str = None):
        """Register a keyboard shortcut."""
        shortcut = Shortcut(key, command_id, when)
        self._shortcuts[key] = shortcut
        
    def handle_key_event(self, event: QKeyEvent) -> bool:
        """Handle a key event."""
        key = self._parse_key_event(event)
        if key in self._shortcuts:
            command_id = self._shortcuts[key].command_id
            # Execute command
            return True
        return False
```

### Phase 5: Dependency Injection (1 day)

#### Objective
Enable loose coupling and testability.

#### Implementation
```python
# In main.py
def initialize_services():
    """Initialize and register all services."""
    
    # Create services
    workspace_service = WorkspaceService(main_window.workspace)
    editor_service = EditorService()
    terminal_service = TerminalService()
    
    # Register with locator
    ServiceLocator.register(WorkspaceService, workspace_service)
    ServiceLocator.register(EditorService, editor_service)
    ServiceLocator.register(TerminalService, terminal_service)
    
    # Register with command context
    context.services = {
        'workspace': workspace_service,
        'editor': editor_service,
        'terminal': terminal_service
    }
```

### Phase 6: Focus Management (2 days)

#### Objective
Enable keyboard navigation between UI elements.

#### Directory Structure
```
core/focus/
├── __init__.py
├── manager.py            # FocusManager
├── groups.py            # Focus group definitions
├── navigation.py        # Navigation logic
└── indicators.py        # Visual focus indicators
```

## Migration Strategy

### 1. Parallel Implementation
- Build new system alongside existing code
- No breaking changes initially
- Feature flag to enable/disable

### 2. Incremental Migration
```python
# Step 1: Create command
class NewTabCommand(Command):
    def execute(self, context):
        # Call existing method initially
        context.main_window.workspace.add_editor_tab()

# Step 2: Move logic to service
class NewTabCommand(Command):
    def execute(self, context):
        workspace_service = context.get_service(WorkspaceService)
        workspace_service.add_editor_tab()

# Step 3: Remove old code
# Delete the direct QAction creation
```

### 3. Testing Strategy
- Unit tests for each command
- Integration tests for command execution
- E2E tests for keyboard shortcuts

## Success Metrics

1. **Code Quality**
   - Reduced coupling (measure with tools)
   - Increased test coverage (>80%)
   - Cleaner separation of concerns

2. **Developer Experience**
   - Easier to add new commands
   - Clear where to put code
   - Better debugging capability

3. **User Experience**
   - All actions discoverable
   - Customizable shortcuts
   - Consistent behavior

## Risk Mitigation

### Risk 1: Breaking Existing Functionality
**Mitigation**: 
- Parallel implementation
- Comprehensive testing
- Feature flags

### Risk 2: Performance Impact
**Mitigation**:
- Profile command execution
- Lazy loading
- Caching strategies

### Risk 3: Complexity Increase
**Mitigation**:
- Clear documentation
- Code examples
- Developer guide

## Timeline

| Phase | Duration | Dependencies | Deliverables |
|-------|----------|--------------|--------------|
| Phase 1: Command System | 3-4 days | None | Command infrastructure, basic commands |
| Phase 2: Service Layer | 2-3 days | Phase 1 | Services, business logic extraction |
| Phase 3: Context System | 2 days | Phase 1 | Context manager, when clauses |
| Phase 4: Keyboard Service | 2 days | Phases 1-3 | Centralized keyboard handling |
| Phase 5: Dependency Injection | 1 day | Phase 2 | Service locator, DI container |
| Phase 6: Focus Management | 2 days | Phases 1-4 | Focus manager, navigation |

**Total: 12-14 days**

## Next Steps

1. **Review and approve** this plan
2. **Create feature branch** for implementation
3. **Start Phase 1** with command system
4. **Daily progress updates** with working examples
5. **Integration testing** after each phase

## Conclusion

This architectural improvement plan addresses the critical gaps identified in the Architecture Review. By implementing these changes before adding new features, we ensure:

1. **Solid Foundation** - New features built on proper architecture
2. **Maintainability** - Clear separation of concerns
3. **Extensibility** - Easy to add new functionality
4. **Testability** - Comprehensive test coverage possible
5. **User Experience** - Consistent, discoverable interface

The phased approach allows for incremental improvement while maintaining system stability. Each phase delivers value independently while building toward the complete architectural vision.