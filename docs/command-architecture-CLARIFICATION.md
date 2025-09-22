# Command Architecture Clarification

## Current State (Mixed Architecture)

We currently have TWO command systems running in parallel:

### 1. Function-Based Commands (135+ commands)
- Use `@command` decorator or manual registration
- Handler is a function: `def handler(context) -> CommandResult`
- Wrapped in a data structure for registration (currently called LegacyCommand)
- Examples: All existing commands in builtin/*.py files

### 2. Class-Based Commands (12 commands)
- Inherit from abstract `Command` base class
- Handler is a method: `def execute(self, context) -> CommandResult`
- Self-contained with their own state
- Examples: CreateTabCommand, SplitPaneCommand, etc.

## The Problem

The name "LegacyCommand" is confusing because it implies old/deprecated, but we actually need this wrapper for function-based commands during the transition.

## Proposed Solution

### Option 1: Keep Both During Transition
```python
# Rename for clarity
class FunctionCommand:  # Was LegacyCommand
    """Wrapper for function-based commands"""
    handler: Callable[[CommandContext], CommandResult]

class Command(ABC):  # Keep as-is
    """Base class for class-based commands"""
    @abstractmethod
    def execute(self, context) -> CommandResult
```

### Option 2: Unified Command Class
```python
class Command:
    """Unified command that can wrap functions or be subclassed"""

    def __init__(self, handler=None, **kwargs):
        if handler:
            # Function-based command
            self.handler = handler
            self.id = kwargs.get('id')
            # ... other properties
        else:
            # Class-based command (subclass)
            pass

    def execute(self, context):
        if hasattr(self, 'handler'):
            return self.handler(context)
        else:
            # Subclass should override
            raise NotImplementedError
```

### Option 3: Complete Migration Now
Remove ALL function-based commands and convert everything to Command classes.
- PRO: Clean, single architecture
- CON: Massive change, 135+ commands to rewrite

## Recommendation

**Option 1** - Keep both during transition:
1. Rename `LegacyCommand` to `FunctionCommand` for clarity
2. Keep `Command` ABC for new class-based commands
3. Registry handles both types
4. Gradually migrate function commands to classes
5. Eventually remove FunctionCommand when migration complete

This allows:
- Existing code continues working
- New code uses clean Command classes
- Gradual migration without breaking changes
- Clear naming (not "legacy")