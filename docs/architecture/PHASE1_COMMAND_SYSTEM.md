# Phase 1: Command System Implementation

## Overview
This document details the implementation of the Command System, the foundational phase of the architectural improvements for ViloApp.

## Goals
- Create a centralized command pattern for all application actions
- Decouple actions from UI components
- Enable future command palette and keyboard customization
- Improve testability and maintainability

## Timeline: 3-4 Days

### Day 1: Core Infrastructure
Build the foundational classes and patterns.

### Day 2: Example Commands
Migrate existing actions to demonstrate the pattern.

### Day 3: Integration
Connect the command system to the existing UI.

### Day 4: Testing & Polish
Ensure quality and documentation.

## Directory Structure

```
core/
├── commands/
│   ├── __init__.py           # Public API exports
│   ├── base.py              # Command abstract class, CommandResult
│   ├── context.py           # CommandContext for execution
│   ├── registry.py          # CommandRegistry singleton
│   ├── executor.py          # CommandExecutor for running commands
│   ├── decorators.py        # @command decorator for easy creation
│   └── builtin/             # Built-in commands
│       ├── __init__.py
│       ├── file_commands.py    # File menu commands
│       ├── view_commands.py    # View menu commands
│       └── debug_commands.py   # Debug menu commands
```

## Component Specifications

### 1. Command Base Class (`base.py`)

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
        self.when = when  # Context expression (future)
        self._enabled = True
        
    @abstractmethod
    def execute(self, context: 'CommandContext') -> CommandResult:
        """Execute the command."""
        pass
        
    def can_execute(self, context: 'CommandContext') -> bool:
        """Check if command can be executed."""
        return self._enabled
        
    def undo(self, context: 'CommandContext', undo_data: Dict) -> CommandResult:
        """Undo the command. Override for undo support."""
        return CommandResult(False, error="Undo not supported")
        
    def redo(self, context: 'CommandContext', undo_data: Dict) -> CommandResult:
        """Redo the command. Override for redo support."""
        return self.execute(context)
```

### 2. Command Context (`context.py`)

```python
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Type, TypeVar

T = TypeVar('T')

@dataclass
class CommandContext:
    """Context passed to commands during execution."""
    
    # Application references
    main_window: Optional['MainWindow'] = None
    workspace: Optional['Workspace'] = None
    active_widget: Optional['QWidget'] = None
    
    # Services (will be added in Phase 2)
    services: Dict[str, Any] = field(default_factory=dict)
    
    # Context values for when clauses (future)
    context_values: Dict[str, Any] = field(default_factory=dict)
    
    # Command arguments
    args: Dict[str, Any] = field(default_factory=dict)
    
    def get_service(self, service_type: Type[T]) -> Optional[T]:
        """Get a service instance."""
        return self.services.get(service_type.__name__)
```

### 3. Command Registry (`registry.py`)

```python
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class CommandRegistry:
    """Central registry for all commands."""
    
    def __init__(self):
        self._commands: Dict[str, Command] = {}
        self._categories: Dict[str, List[Command]] = {}
        self._shortcuts: Dict[str, str] = {}  # shortcut -> command_id
        
    def register(self, command: Command) -> None:
        """Register a command."""
        if command.id in self._commands:
            logger.warning(f"Command {command.id} already registered, overwriting")
            
        self._commands[command.id] = command
        
        # Index by category
        if command.category not in self._categories:
            self._categories[command.category] = []
        self._categories[command.category].append(command)
        
        # Register shortcut
        if command.shortcut:
            if command.shortcut in self._shortcuts:
                logger.warning(f"Shortcut {command.shortcut} already mapped, overwriting")
            self._shortcuts[command.shortcut] = command.id
            
        logger.info(f"Registered command: {command.id}")
            
    def unregister(self, command_id: str) -> bool:
        """Unregister a command."""
        if command_id not in self._commands:
            return False
            
        command = self._commands[command_id]
        del self._commands[command_id]
        
        # Remove from category
        if command.category in self._categories:
            self._categories[command.category].remove(command)
            
        # Remove shortcut
        if command.shortcut and command.shortcut in self._shortcuts:
            del self._shortcuts[command.shortcut]
            
        return True
        
    def get_command(self, command_id: str) -> Optional[Command]:
        """Get command by ID."""
        return self._commands.get(command_id)
        
    def get_all_commands(self) -> List[Command]:
        """Get all registered commands."""
        return list(self._commands.values())
        
    def get_commands_by_category(self, category: str) -> List[Command]:
        """Get all commands in a category."""
        return self._categories.get(category, [])
        
    def get_command_by_shortcut(self, shortcut: str) -> Optional[Command]:
        """Get command by keyboard shortcut."""
        command_id = self._shortcuts.get(shortcut)
        return self.get_command(command_id) if command_id else None

# Global registry instance
command_registry = CommandRegistry()
```

### 4. Command Executor (`executor.py`)

```python
from typing import Optional, List, Dict, Any
import logging
from .base import Command, CommandResult
from .context import CommandContext
from .registry import command_registry

logger = logging.getLogger(__name__)

class CommandExecutor:
    """Executes commands and manages undo/redo."""
    
    def __init__(self):
        self._undo_stack: List[tuple[Command, Dict]] = []
        self._redo_stack: List[tuple[Command, Dict]] = []
        self._max_undo_stack = 100
        
    def execute(self, 
                command_id: str, 
                context: CommandContext,
                args: Optional[Dict[str, Any]] = None) -> CommandResult:
        """Execute a command by ID."""
        
        command = command_registry.get_command(command_id)
        if not command:
            error_msg = f"Command not found: {command_id}"
            logger.error(error_msg)
            return CommandResult(False, error=error_msg)
            
        return self.execute_command(command, context, args)
        
    def execute_command(self,
                       command: Command,
                       context: CommandContext,
                       args: Optional[Dict[str, Any]] = None) -> CommandResult:
        """Execute a command instance."""
        
        # Add arguments to context
        if args:
            context.args.update(args)
            
        # Check if command can execute
        if not command.can_execute(context):
            error_msg = f"Command cannot execute: {command.id}"
            logger.warning(error_msg)
            return CommandResult(False, error=error_msg)
            
        try:
            # Execute the command
            logger.info(f"Executing command: {command.id}")
            result = command.execute(context)
            
            # Add to undo stack if successful and has undo data
            if result.success and result.undo_data is not None:
                self._add_to_undo_stack(command, result.undo_data)
                self._redo_stack.clear()  # Clear redo stack on new action
                
            return result
            
        except Exception as e:
            error_msg = f"Command execution failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return CommandResult(False, error=error_msg)
            
    def undo(self, context: CommandContext) -> CommandResult:
        """Undo the last command."""
        if not self._undo_stack:
            return CommandResult(False, error="Nothing to undo")
            
        command, undo_data = self._undo_stack.pop()
        
        try:
            result = command.undo(context, undo_data)
            if result.success:
                self._redo_stack.append((command, undo_data))
            return result
        except Exception as e:
            error_msg = f"Undo failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return CommandResult(False, error=error_msg)
            
    def redo(self, context: CommandContext) -> CommandResult:
        """Redo the last undone command."""
        if not self._redo_stack:
            return CommandResult(False, error="Nothing to redo")
            
        command, undo_data = self._redo_stack.pop()
        
        try:
            result = command.redo(context, undo_data)
            if result.success:
                self._undo_stack.append((command, undo_data))
            return result
        except Exception as e:
            error_msg = f"Redo failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return CommandResult(False, error=error_msg)
            
    def _add_to_undo_stack(self, command: Command, undo_data: Dict):
        """Add command to undo stack."""
        self._undo_stack.append((command, undo_data))
        
        # Limit stack size
        if len(self._undo_stack) > self._max_undo_stack:
            self._undo_stack.pop(0)

# Global executor instance
command_executor = CommandExecutor()
```

### 5. Command Decorator (`decorators.py`)

```python
from typing import Optional, Callable
from functools import wraps
from .base import Command, CommandResult
from .context import CommandContext
from .registry import command_registry

def command(id: str, 
           title: str,
           category: str = "General",
           description: str = "",
           shortcut: Optional[str] = None):
    """Decorator to create and register a command from a function."""
    
    def decorator(func: Callable):
        
        class DecoratedCommand(Command):
            def __init__(self):
                super().__init__(
                    id=id,
                    title=title,
                    category=category,
                    description=description,
                    shortcut=shortcut
                )
                
            def execute(self, context: CommandContext) -> CommandResult:
                return func(context)
        
        # Create and register the command
        cmd = DecoratedCommand()
        command_registry.register(cmd)
        
        # Return the original function
        return func
        
    return decorator
```

## Commands to Implement

### View Commands (`builtin/view_commands.py`)

```python
from core.commands.base import Command, CommandResult
from core.commands.context import CommandContext
from ui.icon_manager import get_icon_manager

class ToggleThemeCommand(Command):
    """Toggle between light and dark theme."""
    
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

class ToggleSidebarCommand(Command):
    """Toggle sidebar visibility."""
    
    def __init__(self):
        super().__init__(
            id="view.toggleSidebar",
            title="Toggle Sidebar",
            category="View",
            description="Show or hide the sidebar",
            shortcut="ctrl+b"
        )
        
    def execute(self, context: CommandContext) -> CommandResult:
        if context.main_window:
            context.main_window.toggle_sidebar()
            return CommandResult(success=True)
        return CommandResult(success=False, error="No main window")
```

### File Commands (`builtin/file_commands.py`)

```python
from core.commands.base import Command, CommandResult
from core.commands.context import CommandContext

class NewEditorTabCommand(Command):
    """Create a new editor tab."""
    
    def __init__(self):
        super().__init__(
            id="file.newEditorTab",
            title="New Editor Tab",
            category="File",
            description="Create a new editor tab",
            shortcut="ctrl+n"
        )
        
    def execute(self, context: CommandContext) -> CommandResult:
        if context.workspace:
            name = context.args.get("name", "New Editor")
            index = context.workspace.add_editor_tab(name)
            return CommandResult(success=True, value=index)
        return CommandResult(success=False, error="No workspace")
```

## Integration Plan

### 1. Initialize Commands (`main.py`)

```python
def initialize_commands():
    """Initialize all built-in commands."""
    from core.commands.builtin import register_all_commands
    register_all_commands()
```

### 2. Update MainWindow

```python
# Add command context creation
def create_command_context(self) -> CommandContext:
    """Create command context for execution."""
    return CommandContext(
        main_window=self,
        workspace=self.workspace,
        active_widget=self.workspace.get_current_split_widget()
    )

# Execute commands instead of direct methods
def execute_command(self, command_id: str, **kwargs):
    """Execute a command by ID."""
    from core.commands import command_executor
    context = self.create_command_context()
    return command_executor.execute(command_id, context, kwargs)
```

### 3. Migration Strategy

Keep existing QActions but route through commands:

```python
# Before
theme_action.triggered.connect(self.toggle_theme)

# After (backward compatible)
theme_action.triggered.connect(
    lambda: self.execute_command("view.toggleTheme")
)
```

## Testing Plan

### Unit Tests

1. Test command registration
2. Test command execution
3. Test context passing
4. Test error handling
5. Test undo/redo mechanisms

### Integration Tests

1. Test command execution from MainWindow
2. Test keyboard shortcuts
3. Test menu actions
4. Test backward compatibility

## Success Metrics

- [ ] All infrastructure classes implemented
- [ ] At least 5 commands migrated
- [ ] Commands executable via registry
- [ ] Unit tests with >80% coverage
- [ ] Existing UI remains functional
- [ ] Documentation complete

## Next Steps

After Phase 1 completion:
1. Phase 2: Service Layer (extract business logic)
2. Phase 3: Context System (when clauses)
3. Phase 4: Keyboard Service (shortcut management)
4. Phase 5: Command Palette UI