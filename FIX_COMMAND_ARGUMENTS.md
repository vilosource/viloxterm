# Command Arguments Fix

## Issue
The error log showed:
```
TypeError: update_registry_after_close_command() missing 1 required positional argument: 'closed_index'
```

Commands were defined with additional parameters beyond `context`, but the command decorator only passes the context parameter when executing.

## Root Cause
The command decorator pattern wraps functions to only receive `CommandContext`. Additional arguments must be passed through `context.args` dictionary, not as function parameters.

## Solution

### Before (Incorrect)
```python
@command(id="workspace.updateRegistryAfterClose", ...)
def update_registry_after_close_command(
    context: CommandContext,
    closed_index: int,  # ❌ Can't receive these directly
    widget_id: Optional[str] = None
) -> CommandResult:
    ...
```

### After (Correct)
```python
@command(id="workspace.updateRegistryAfterClose", ...)
def update_registry_after_close_command(context: CommandContext) -> CommandResult:
    # ✅ Get arguments from context.args
    closed_index = context.args.get('closed_index')
    widget_id = context.args.get('widget_id')

    if closed_index is None:
        return CommandResult(success=False, error="closed_index is required")
    ...
```

## Files Fixed

### 1. `/core/commands/builtin/registry_commands.py`
Fixed all command functions:
- `register_widget_command` - Now gets `widget_id` and `tab_index` from context.args
- `unregister_widget_command` - Now gets `widget_id` from context.args
- `update_registry_after_close_command` - Now gets `closed_index` and `widget_id` from context.args
- `get_widget_tab_index_command` - Now gets `widget_id` from context.args
- `is_widget_registered_command` - Now gets `widget_id` from context.args

### 2. `/tests/unit/test_registry_commands.py`
Updated all test calls to set `context.args` instead of passing parameters:
```python
# Before
result = command._original_func(context, widget_id="test", tab_index=0)

# After
context.args = {"widget_id": "test", "tab_index": 0}
result = command._original_func(context)
```

## How Commands Work

1. **Definition**: Commands only receive `CommandContext` parameter
2. **Execution**: `execute_command("command.id", arg1=value1, arg2=value2)`
3. **Executor**: Adds kwargs to `context.args` dictionary
4. **Command**: Retrieves arguments from `context.args.get('arg_name')`

## Testing
All 11 registry command tests now pass ✅

## Lesson Learned
All commands in the command pattern must:
1. Only accept `CommandContext` as parameter
2. Get additional arguments from `context.args`
3. Validate required arguments are present
4. Return appropriate error if required args missing

This ensures consistent command execution through the decorator pattern.