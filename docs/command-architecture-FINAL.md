# Command Architecture - Final Design

## Architecture Decision

We are using a **dual command system** during the transition period:

### 1. FunctionCommand (was LegacyCommand)
- Wraps function-based handlers from `@command` decorator
- Used by 135+ existing commands
- Allows gradual migration without breaking existing code
- Clean naming that doesn't imply "legacy" or "deprecated"

### 2. Command (Abstract Base Class)
- New architecture for class-based commands
- Subclasses implement `execute()` method
- Direct model manipulation, no services
- Currently used by tab/pane commands

## Implementation Status

### ✅ Completed
- Renamed `LegacyCommand` to `FunctionCommand` for clarity
- Added alias `LegacyCommand = FunctionCommand` for backward compatibility
- Updated all imports to use `FunctionCommand`
- Fixed `CommandContext` to have optional model parameter
- Registry's `execute()` method handles both command types
- Application starts and runs successfully

### Current Code Structure

```python
# base.py
@dataclass
class FunctionCommand:
    """Wrapper for function-based commands."""
    handler: Callable[[CommandContext], CommandResult]
    # ... properties

class Command(ABC):
    """Base class for class-based commands."""
    @abstractmethod
    def execute(self, context: CommandContext) -> CommandResult

# Alias for migration
LegacyCommand = FunctionCommand
```

```python
# registry.py
def execute(self, command_id, context, **kwargs):
    # Try FunctionCommand first
    func_cmd = self.get_command(command_id)
    if func_cmd:
        return func_cmd.execute(context)

    # Try Command class second
    cmd_class = self.get_command_class(command_id)
    if cmd_class:
        cmd = cmd_class(**kwargs)
        return cmd.execute(context)
```

## Migration Path

### Phase 1: Current State (DONE)
- Both systems work in parallel
- FunctionCommand for existing commands
- Command classes for new commands

### Phase 2: Gradual Migration (IN PROGRESS)
- Convert high-value commands to Command classes
- Remove service dependencies
- Add missing model methods

### Phase 3: Full Migration (FUTURE)
- All commands are Command classes
- Remove FunctionCommand wrapper
- Pure Model-View-Command architecture

## Next Priority Tasks

1. **Add Missing Model Methods**
   - `focus_next_pane()` / `focus_previous_pane()`
   - `save_state()` / `load_state()`
   - Complete observer implementation

2. **Migrate Critical Commands**
   - Start with commands that manipulate workspace state
   - Remove service dependencies
   - Use model directly

3. **Performance Optimization**
   - Add metrics to track command execution time
   - Ensure <1ms execution for all commands

## Benefits of This Approach

1. **No Breaking Changes** - Existing code continues working
2. **Clear Naming** - "FunctionCommand" clearly describes what it is
3. **Gradual Migration** - Can migrate one command at a time
4. **Type Safety** - Both patterns are properly typed
5. **Clean Architecture** - Moving toward pure Model-View-Command

## Success Metrics

- ✅ Application runs without errors
- ✅ Both command types execute successfully
- ✅ Clear migration path established
- ⏳ 12/147 commands migrated to new architecture
- ⏳ 0/131 service dependencies removed