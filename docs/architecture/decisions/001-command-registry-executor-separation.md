# ADR-001: Separation of CommandRegistry and CommandExecutor

**Status:** Accepted  
**Date:** 2025-09-11  
**Decision Makers:** ViloApp Development Team  

## Context

The original design specification in `docs/features/KEYBOARD_COMMAND_DESIGN.md` proposed that the `CommandRegistry` class should have an `execute_command()` method, making it responsible for both:
1. Command storage and lookup
2. Command execution

During implementation, we chose to separate these concerns into two distinct classes:
- `CommandRegistry`: Handles command registration, storage, lookup, and indexing
- `CommandExecutor`: Handles command execution, undo/redo stack, and execution history

## Decision

We will maintain the separation of CommandRegistry and CommandExecutor as two distinct classes with clear, focused responsibilities.

## Rationale

### 1. Single Responsibility Principle (SRP)

**CommandRegistry Responsibilities:**
- Register/unregister commands
- Index commands by category, shortcut, and keywords
- Search and retrieve commands
- Notify observers of registry changes

**CommandExecutor Responsibilities:**
- Execute commands with proper context
- Manage undo/redo stack
- Track execution history
- Handle command result processing
- Manage execution state (can_undo, can_redo)

### 2. Separation of Concerns

The registry is a data structure concern - it's about organizing and finding commands. Execution is a behavioral concern - it's about running commands and managing their effects. These are fundamentally different responsibilities that change for different reasons.

### 3. Testability

```python
# Easy to test registry without execution side effects
def test_command_registration():
    registry = CommandRegistry()
    cmd = Command(id="test.cmd", title="Test")
    registry.register(cmd)
    assert registry.get_command("test.cmd") == cmd

# Easy to test execution without registry complexity
def test_command_execution():
    executor = CommandExecutor()
    cmd = Command(id="test.cmd", handler=lambda ctx: CommandResult(success=True))
    result = executor.execute(cmd, {})
    assert result.success
    assert executor.can_undo()
```

### 4. Flexibility and Extension

Separation allows for:
- Multiple executors with different strategies (async, queued, prioritized)
- Different undo/redo implementations (linear, branching)
- Registry backends (in-memory, database, remote)
- Independent evolution of each component

### 5. Clear Dependencies

```python
# Clear dependency direction: Executor depends on Registry
class CommandExecutor:
    def __init__(self, registry: CommandRegistry):
        self._registry = registry
    
    def execute_by_id(self, command_id: str, context: Dict):
        command = self._registry.get_command(command_id)
        if command:
            return self.execute(command, context)
```

## Consequences

### Positive

1. **Cleaner Code**: Each class has a focused purpose with cohesive methods
2. **Better Testing**: Can test registration logic without execution side effects
3. **Easier Debugging**: Clear separation makes it obvious where issues lie
4. **Future Flexibility**: Can swap executors without touching registry
5. **Parallel Development**: Teams can work on registry features and execution features independently

### Negative

1. **More Classes**: Two classes instead of one (minimal complexity increase)
2. **Documentation Mismatch**: Implementation differs from original design spec
3. **Learning Curve**: New developers need to understand both classes

### Neutral

1. **Service Locator Pattern**: Both are accessed via ServiceLocator, so consumer code is similar
2. **Performance**: Negligible difference - one extra lookup per execution

## Implementation Example

```python
# Current implementation (separated)
registry = ServiceLocator.get_service("command_registry")
command = registry.get_command("file.save")

executor = ServiceLocator.get_service("command_executor")  
result = executor.execute(command, context)

# Original design (combined)
registry = ServiceLocator.get_service("command_registry")
result = registry.execute_command("file.save", context)
```

## Alternatives Considered

### Alternative 1: Combined Registry/Executor (Original Design)

**Pros:**
- Single point of interaction
- Matches original specification
- One less class

**Cons:**
- Violates SRP
- Harder to test
- Mixes data and behavior concerns
- Less flexible for future changes

### Alternative 2: Command Pattern with Self-Execution

```python
class Command:
    def execute(self, context: Dict) -> CommandResult:
        # Command executes itself
        return self.handler(context)
```

**Pros:**
- Classic GoF Command pattern
- Commands are self-contained

**Cons:**
- Commands can't be simple data objects
- Undo/redo logic scattered across commands
- No central execution control

### Alternative 3: Event-Driven Execution

```python
# Commands as events
event_bus.publish(CommandEvent("file.save", context))
```

**Pros:**
- Fully decoupled
- Async by default

**Cons:**
- Harder to debug
- No direct return values
- More complex for simple cases

## Decision Outcome

We maintain the current separation as it provides the best balance of:
- Clean architecture
- Testability  
- Flexibility
- Maintainability

The original design document should be updated to reflect this architectural improvement, noting it as an enhancement discovered during implementation.

## Related Decisions

- ADR-002: Singleton Pattern for Core Services (if created)
- ADR-003: ServiceLocator vs Dependency Injection (if created)

## References

- Original Design: `/docs/features/KEYBOARD_COMMAND_DESIGN.md`
- Implementation: `/core/commands/registry.py`, `/core/commands/executor.py`
- Analysis: `/docs/analysis/KEYBOARD_COMMAND_IMPLEMENTATION_ANALYSIS.md`