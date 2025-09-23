# Design Principles Checklist

This checklist MUST be reviewed before ANY architectural change or significant feature addition.

## Before You Code

### Extensibility Check
- [ ] Can plugins extend this without modifying core files?
- [ ] Are we using runtime discovery instead of compile-time constants?
- [ ] Is there a registry for this type of extension?
- [ ] Would adding a new variant require changing core code?

### Separation of Concerns Check
- [ ] Does each component own its own data?
- [ ] Are we importing from the correct layer only?
- [ ] Is business logic in services, not UI?
- [ ] Are widget IDs owned by widgets, not core?

### Plugin Architecture Check
- [ ] Do widget IDs follow the convention pattern?
  - Built-in: `com.viloapp.<name>`
  - Plugin: `plugin.<plugin_id>.<widget_name>`
- [ ] Can plugins register widgets dynamically?
- [ ] Is core completely agnostic to specific implementations?
- [ ] Are we using patterns instead of instances in core modules?

### Data Flow Check
- [ ] Does data flow in one direction only?
- [ ] Are we using commands for ALL user operations?
- [ ] Is the model the single source of truth?
- [ ] Do UI components only observe, never directly manipulate?

### Dependency Check
- [ ] UI → Services → Models (never reversed)?
- [ ] No circular dependencies?
- [ ] No direct UI-to-UI communication?
- [ ] Services don't know about UI?

## Code Review Questions

### For New Features
1. **Can this be added without touching core files?**
   - If NO, redesign using registry pattern

2. **Are we hardcoding any IDs or types?**
   - If YES, move to runtime discovery

3. **Does core need to know about this specific implementation?**
   - If YES, abstract to interface/pattern

### For Widget Changes
1. **Is the widget ID hardcoded anywhere in core?**
   - Should be in widget class only

2. **Can plugins add similar widgets?**
   - Must work without core changes

3. **Is widget creation going through the registry?**
   - Never direct instantiation

### For Command Changes
1. **Does the command go through the command registry?**
   - No direct function calls

2. **Is the command modifying the model directly?**
   - Should go through services

3. **Can plugins add similar commands?**
   - Must be extensible

## Red Flags 🚩

**STOP and reconsider if you see:**
- Hardcoded lists of widget types in core
- Enums for extensible concepts
- Core imports from plugins
- Switch/case statements for types
- Core files that need updates for new features
- Direct widget manipulation outside commands
- Business logic in UI components
- UI calling services that call back to UI

## Testing Your Design

### The Plugin Test
> "Could a third-party developer add this feature as a plugin without modifying any core files?"

If the answer is NO, the design is wrong.

### The Registry Test
> "Is this capability discoverable at runtime through a registry?"

If the answer is NO, consider using a registry pattern.

### The Separation Test
> "If I delete the UI layer, would the business logic still work?"

If the answer is NO, you have UI logic in the wrong layer.

### The Model Test
> "Can I serialize the entire application state from the model?"

If the answer is NO, you have state outside the model.

## Remember

**Every violation of these principles is technical debt that will require future refactoring.**

It's always cheaper to design correctly upfront than to fix architectural violations later.

When in doubt, ask:
- Is this extensible?
- Is this decoupled?
- Is this discoverable at runtime?
- Does this follow the one-way data flow?