# Architectural Bridge Components

## Overview

Bridge components are special architectural elements that legitimately need to span multiple layers in the ViloxTerm architecture. While our clean architecture generally enforces strict layer boundaries (UI → Service → Model), certain components inherently require cross-layer communication due to their nature.

## What are Bridge Components?

Bridge components are modules that:

1. **Provide essential cross-layer functionality** - They handle concerns that inherently span multiple architectural layers
2. **Cannot be cleanly separated** - The functionality they provide requires tight integration between layers
3. **Are explicitly documented** - Each bridge component must be clearly identified and documented
4. **Use approved patterns** - They must use specific patterns (like lazy imports) to avoid circular dependencies

## Approved Bridge Components

### 1. Terminal Server (`services/terminal_server.py`)

**Type:** Service-to-UI Bridge

**Location:** `packages/viloapp/src/viloapp/services/terminal_server.py`

**Why it's a bridge:**
- Lives in the services layer but must import UI components
- Needs to serve terminal UI assets (HTML/JS/CSS files from `ui/terminal/terminal_assets.py`)
- Requires platform-specific terminal backends from `ui/terminal/backends/`
- Manages terminal sessions that inherently combine service logic with UI resources

**Pattern used:** Direct imports with lazy loading on the consumer side

**Consumer pattern:**
```python
# In terminal_app_widget.py
@property
def terminal_server(self):
    """Lazy-load terminal_server to avoid circular import."""
    if self._terminal_server_instance is None:
        from viloapp.services.terminal_server import terminal_server
        self._terminal_server_instance = terminal_server
    return self._terminal_server_instance
```

### 2. Theme Provider (`ui/themes/theme_provider.py`)

**Type:** UI-to-Service Bridge

**Location:** `packages/viloapp/src/viloapp/ui/themes/theme_provider.py`

**Why it's a bridge:**
- Bridges ThemeService (service layer) with UI components
- Provides theme data to UI components in UI-specific formats
- Created during service initialization but lives in UI layer

**Pattern used:** Dependency injection during initialization

## Patterns for Bridge Components

### 1. Lazy Import Pattern

Used when a UI component needs to access a service that imports from UI:

```python
class UIComponent:
    def __init__(self):
        self._service_instance = None

    @property
    def service(self):
        """Lazy-load service to avoid circular import."""
        if self._service_instance is None:
            from services.module import service_instance
            self._service_instance = service_instance
        return self._service_instance
```

**Benefits:**
- Breaks circular import at module initialization time
- Import happens at runtime when modules are fully loaded
- Maintains singleton pattern for services

### 2. Interface Adapter Pattern

Used when a service needs UI resources but shouldn't directly depend on them:

```python
# In services layer
class ServiceWithUINeeds:
    def __init__(self, ui_adapter=None):
        self.ui_adapter = ui_adapter

    def operation(self):
        if self.ui_adapter:
            return self.ui_adapter.get_ui_resource()
        return None

# In initialization
service = ServiceWithUINeeds()
ui_adapter = UIAdapter()  # From UI layer
service.ui_adapter = ui_adapter
```

### 3. Event Bus Pattern

Used for decoupled communication between layers:

```python
# Service emits events
class Service:
    def operation(self):
        self.event_bus.emit("operation_complete", data)

# UI subscribes to events
class UIComponent:
    def __init__(self):
        event_bus.subscribe("operation_complete", self.handle_operation)
```

## Guidelines for Creating Bridge Components

### When to Create a Bridge Component

Bridge components should only be created when:

1. **The functionality cannot be cleanly separated** - There's no way to split the concern across layers
2. **It provides essential infrastructure** - The component is critical to application functionality
3. **It's been reviewed and approved** - The architectural team has approved the bridge

### How to Document Bridge Components

Every bridge component must include:

1. **Header comment** explaining why it's a bridge:
```python
"""
ARCHITECTURAL NOTE: Bridge Component
=====================================
This component is a special architectural bridge...
"""
```

2. **Detailed explanation** of:
   - Why it needs to span layers
   - What patterns it uses to avoid circular dependencies
   - Which other components it bridges

3. **Reference to this document**:
```python
# See: docs/architecture-BRIDGES.md for more details on bridge components
```

### Testing Bridge Components

Bridge components require special testing attention:

1. **Test both layers independently** - Mock the bridge connections
2. **Test the integration** - Verify the bridge works correctly
3. **Test initialization order** - Ensure no circular import issues

## Anti-Patterns to Avoid

### 1. Hidden Bridges

Never create undocumented cross-layer dependencies. All bridges must be explicit and documented.

### 2. Unnecessary Bridges

Don't create bridges for convenience. They should only exist when absolutely necessary.

### 3. Direct Circular Imports

Never use direct circular imports. Always use lazy loading or dependency injection.

### 4. Business Logic in Bridges

Bridges should only handle communication/adaptation, not business logic.

## Migration Strategy

When encountering existing cross-layer dependencies:

1. **Evaluate if it's necessary** - Can it be refactored to respect layer boundaries?
2. **If necessary, document it** - Add it to this document as an approved bridge
3. **Apply proper patterns** - Use lazy loading or dependency injection
4. **Add comprehensive comments** - Document in code why it's a bridge

## Review Process

All new bridge components must:

1. Be documented in this file
2. Include comprehensive code comments
3. Use approved patterns
4. Be reviewed by the architecture team

## Current Bridge Components Summary

| Component | Type | Location | Pattern | Status |
|-----------|------|----------|---------|--------|
| terminal_server | Service→UI | services/terminal_server.py | Direct import + Lazy consumer | Approved |
| theme_provider | UI→Service | ui/themes/theme_provider.py | Dependency injection | Approved |

---

*Last Updated: 2025-01-21*
*Architecture Version: 2.0 (Post Phase 7 Cleanup)*