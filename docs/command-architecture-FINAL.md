# Command Architecture

## Overview

ViloxTerm uses a unified command system where all state changes flow through commands, ensuring consistent validation, execution, and undo/redo support.

## Command Types

### 1. Command Classes
Abstract base class for all commands:
```python
class Command(ABC):
    @abstractmethod
    def execute(self, context: CommandContext) -> CommandResult:
        pass
```

### 2. FunctionCommand
Wrapper for function-based commands using decorators:
```python
@command("file.open")
def open_file(context: CommandContext) -> CommandResult:
    # Implementation
    return CommandResult(status=CommandStatus.SUCCESS)
```

## CommandContext

Execution context providing access to model and parameters:
```python
@dataclass
class CommandContext:
    model: Optional[WorkspaceModel] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    active_tab_id: Optional[str] = None
    active_pane_id: Optional[str] = None
    main_window: Optional[Any] = None
    workspace: Optional[Any] = None
```

## CommandResult

Standardized response from command execution:
```python
@dataclass
class CommandResult:
    status: CommandStatus  # SUCCESS, FAILURE, NOT_APPLICABLE
    data: Optional[Any] = None
    message: Optional[str] = None
    value: Optional[Any] = None  # Alias for data
```

## Command Registry

Central registry for command registration and execution:
```python
registry = CommandRegistry()

# Register command
registry.register("tab.create", CreateTabCommand)

# Execute command
result = registry.execute("tab.create", context, name="New Tab")
```

## Command Categories

### Tab Commands
- `tab.create` - Create new tab
- `tab.close` - Close tab
- `tab.switch` - Switch to tab
- `tab.rename` - Rename tab
- `tab.duplicate` - Duplicate tab

### Pane Commands
- `pane.split` - Split pane horizontally/vertically
- `pane.close` - Close pane
- `pane.focus` - Focus specific pane
- `pane.maximize` - Maximize pane
- `pane.resize` - Resize pane

### Navigation Commands
- `navigation.focusUp` - Focus pane above
- `navigation.focusDown` - Focus pane below
- `navigation.focusLeft` - Focus pane to left
- `navigation.focusRight` - Focus pane to right
- `navigation.nextTab` - Next tab
- `navigation.previousTab` - Previous tab

### File Commands
- `file.open` - Open file
- `file.save` - Save file
- `file.saveAs` - Save file as
- `file.close` - Close file

### Workspace Commands
- `workspace.save` - Save workspace state
- `workspace.restore` - Restore workspace state
- `workspace.reset` - Reset to default

## Command Implementation

### Simple Command
```python
class CloseTabCommand(Command):
    def __init__(self, tab_id: str):
        self.tab_id = tab_id

    def execute(self, context: CommandContext) -> CommandResult:
        if not context.model:
            return CommandResult(
                status=CommandStatus.FAILURE,
                message="No model available"
            )

        success = context.model.close_tab(self.tab_id)
        return CommandResult(
            status=CommandStatus.SUCCESS if success else CommandStatus.FAILURE
        )
```

### Command with Validation
```python
class SplitPaneCommand(Command):
    def __init__(self, orientation: str):
        self.orientation = orientation

    def execute(self, context: CommandContext) -> CommandResult:
        # Validation
        if self.orientation not in ["horizontal", "vertical"]:
            return CommandResult(
                status=CommandStatus.FAILURE,
                message="Invalid orientation"
            )

        # Get active pane
        tab = context.model.state.get_active_tab()
        if not tab:
            return CommandResult(
                status=CommandStatus.NOT_APPLICABLE,
                message="No active tab"
            )

        # Execute
        new_pane = context.model.split_pane(
            tab.active_pane_id,
            self.orientation
        )

        return CommandResult(
            status=CommandStatus.SUCCESS,
            data={"new_pane_id": new_pane.id}
        )
```

## When-Clause Context

Commands can have conditional execution based on context:
```python
@command("editor.cut", when="editorTextFocus && !editorReadonly")
def cut_text(context: CommandContext) -> CommandResult:
    # Only executes when editor has focus and is not readonly
    pass
```

## Keyboard Shortcuts

Commands are bound to keyboard shortcuts:
```python
@command("pane.split", shortcut="ctrl+\\")
def split_pane_right(context: CommandContext) -> CommandResult:
    # Triggered by Ctrl+\
    pass
```

## Best Practices

1. **Always return CommandResult** - Never raise exceptions
2. **Validate inputs** - Check parameters before execution
3. **Use appropriate status** - SUCCESS, FAILURE, or NOT_APPLICABLE
4. **Include helpful messages** - Explain failures to users
5. **Keep commands focused** - Single responsibility per command
6. **Use model methods** - Don't duplicate model logic
7. **Make commands idempotent** - Safe to execute multiple times

## Migration Status

✅ **Migration Complete**: All 147 commands migrated to model-based execution
- Removed 201 service dependencies
- All commands use CommandContext with model reference
- Consistent CommandResult with status enum
- Full when-clause support implemented