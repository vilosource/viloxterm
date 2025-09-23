# ViloxTerm Platform Purity Refactoring - WIP TASKS

## 📋 Task Breakdown

---

## Phase 1: Core Cleanup Assessment & Preparation

### Task 1.1: Audit Widget-Specific Code in Core
**Duration**: 0.5 days
**Assignee**: Developer
**Priority**: High

**Objective**: Create comprehensive inventory of all widget-specific code in core

**Detailed Steps**:
1. **Scan for terminal-specific code**:
   ```bash
   find packages/viloapp/src -name "*.py" -exec grep -l "terminal\|Terminal" {} \;
   ```
2. **Scan for editor-specific code**:
   ```bash
   find packages/viloapp/src -name "*.py" -exec grep -l "editor\|Editor" {} \;
   ```
3. **Identify widget implementation files**:
   - List all files in `viloapp/ui/terminal/`
   - List all files in `viloapp/ui/widgets/` that implement specific widgets
4. **Catalog widget-specific services**:
   - `services/terminal_service.py`
   - `services/editor_service.py`
5. **Document widget-specific commands**:
   - `core/commands/builtin/terminal_commands.py`
   - `core/commands/builtin/edit_commands.py`
6. **Create migration mapping document**:
   - Source location → Target plugin package
   - Dependencies between files
   - Public API surface that needs preservation

**Success Metrics**:
- ✅ Complete inventory document created
- ✅ Migration map for each file identified
- ✅ Dependency graph documented
- ✅ Risk assessment for each migration completed

**Deliverables**:
- `widget-code-audit-REPORT.md`
- `widget-migration-map-PLAN.md`

---

### Task 1.2: Analyze Plugin Package Structure
**Duration**: 0.5 days
**Assignee**: Developer
**Priority**: High

**Objective**: Understand current plugin structure and identify gaps

**Detailed Steps**:
1. **Audit viloxterm package**:
   ```bash
   find packages/viloxterm -name "*.py" | xargs wc -l
   ```
   - Document current terminal implementation
   - Identify overlaps with core terminal code
   - Check plugin.json configuration

2. **Audit viloedit package**:
   ```bash
   find packages/viloedit -name "*.py" | xargs wc -l
   ```
   - Document current editor implementation
   - Identify missing functionality vs core editor
   - Check plugin.json configuration

3. **Compare implementations**:
   - Feature parity analysis between core and plugin versions
   - Performance comparison where possible
   - API compatibility assessment

4. **Identify plugin infrastructure gaps**:
   - Missing service discovery mechanisms
   - Command registration limitations
   - Capability declaration systems

**Success Metrics**:
- ✅ Plugin structure documented
- ✅ Feature gap analysis completed
- ✅ Infrastructure requirements identified
- ✅ Compatibility assessment finished

**Deliverables**:
- `plugin-structure-analysis-REPORT.md`
- `feature-gap-analysis-REPORT.md`

---

### Task 1.3: Design Capability-Based Architecture
**Duration**: 1 day
**Assignee**: Developer
**Priority**: High

**Objective**: Design the capability-based interaction system

**Detailed Steps**:
1. **Define core capabilities**:
   ```python
   class WidgetCapability(Enum):
       TEXT_EDITING = "text_editing"
       SHELL_EXECUTION = "shell_execution"
       FILE_VIEWING = "file_viewing"
       CLIPBOARD_OPERATIONS = "clipboard_operations"
       SEARCH_AND_REPLACE = "search_and_replace"
       SYNTAX_HIGHLIGHTING = "syntax_highlighting"
       # ... etc
   ```

2. **Design capability registration system**:
   - How widgets declare their capabilities
   - How platform discovers widget capabilities
   - How commands target capabilities vs specific widgets

3. **Design command delegation system**:
   ```python
   class CapabilityCommand:
       capability_required: WidgetCapability
       method_name: str
       fallback_behavior: Optional[Callable]
   ```

4. **Design service discovery system**:
   - How widgets discover platform services
   - Service interface contracts
   - Service lifecycle management

5. **Create API specifications**:
   - Widget-to-platform API
   - Platform-to-widget API
   - Inter-widget communication (if needed)

**Success Metrics**:
- ✅ Capability enum defined
- ✅ Registration system designed
- ✅ Command delegation system designed
- ✅ Service discovery system designed
- ✅ API specifications documented

**Deliverables**:
- `capability-system-DESIGN.md`
- `api-specifications-DESIGN.md`

---

**Task 1.4**: ~~Create Backward Compatibility Strategy~~ **REMOVED**
- **Rationale**: Backward compatibility violates clean architecture goals
- **Strategy**: Immediate deduplication with functionality preservation

---

## Phase 2: Immediate Deduplication

### Task 2.1: Fix Widget ID Conflicts
**Duration**: 0.5 days
**Assignee**: Developer
**Priority**: Critical

**Objective**: Ensure plugin widgets can load by fixing widget ID mismatches

**Current Problem**:
- Core expects: `com.viloapp.terminal`, `com.viloapp.editor`
- Plugins provide: `terminal`, `editor`
- Result: Plugin widgets never load, core widgets used instead

**Detailed Steps**:
1. **Update viloxterm plugin.json**:
   ```json
   {
     "widgets": [
       {
         "id": "com.viloapp.terminal",
         "factory": "viloxterm.widget:TerminalWidgetFactory"
       }
     ]
   }
   ```

2. **Update viloedit plugin.json**:
   ```json
   {
     "widgets": [
       {
         "id": "com.viloapp.editor",
         "factory": "viloedit.widget:EditorWidgetFactory"
       }
     ]
   }
   ```

3. **Test plugin loading**:
   - Verify plugins register with correct IDs
   - Ensure plugin widgets are discovered
   - Test basic widget creation

**Success Metrics**:
- ✅ Plugin widgets register with `com.viloapp.*` IDs
- ✅ Plugin widgets load instead of core widgets
- ✅ Widget discovery works correctly

---

### Task 2.2: Remove Core Widget Implementations
**Duration**: 1 day
**Assignee**: Developer
**Priority**: High

**Objective**: Delete ALL core widget implementations to eliminate duplication

**Detailed Steps**:
1. **Remove terminal implementation entirely**:
   ```bash
   rm -rf packages/viloapp/src/viloapp/ui/terminal/
   ```

2. **Remove editor implementations**:
   ```bash
   rm packages/viloapp/src/viloapp/ui/widgets/editor_app_widget.py
   rm packages/viloapp/src/viloapp/ui/widgets/theme_editor_widget.py
   rm packages/viloapp/src/viloapp/ui/widgets/theme_editor_controls.py
   rm packages/viloapp/src/viloapp/ui/widgets/rename_editor.py
   ```

3. **Fix broken imports**:
   - Remove imports of deleted files from core
   - Update widget registry to not reference deleted widgets
   - Fix any compilation errors

4. **Keep only platform widgets**:
   - `app_widget.py` (base class)
   - `placeholder_app_widget.py` (fallback widget)
   - Settings widgets (platform configuration)

**Success Metrics**:
- ✅ Zero terminal implementation files in core
- ✅ Zero editor implementation files in core
- ✅ Core compiles without errors
- ✅ Only plugin widgets provide terminal/editor functionality

---

### Task 2.3: Remove Widget-Specific Services
**Duration**: 0.5 days
**Assignee**: Developer
**Priority**: High

**Objective**: Remove widget-specific services from core

**Detailed Steps**:
1. **Remove widget services**:
   ```bash
   rm packages/viloapp/src/viloapp/services/terminal_service.py
   rm packages/viloapp/src/viloapp/services/editor_service.py
   ```

2. **Keep platform services**:
   - `terminal_server.py` (platform service for process management)
   - `workspace_service.py` (platform service)
   - Other generic platform services

3. **Fix service dependencies**:
   - Remove service imports from deleted files
   - Update service registry
   - Ensure platform services still work

**Success Metrics**:
- ✅ No widget-specific services in core
- ✅ Platform services preserved and functional
- ✅ Service registry updated correctly

---

### Task 2.4: Remove Widget-Specific Commands
**Duration**: 0.5 days
**Assignee**: Developer
**Priority**: High

**Objective**: Remove widget-specific commands from core

**Detailed Steps**:
1. **Remove command files**:
   ```bash
   rm packages/viloapp/src/viloapp/core/commands/builtin/terminal_commands.py
   rm packages/viloapp/src/viloapp/core/commands/builtin/edit_commands.py
   ```

2. **Update command registry**:
   - Remove imports of deleted command files
   - Update `__init__.py` in builtin commands
   - Ensure core command system still works

3. **Rely on plugin commands**:
   - Plugin packages already have their own commands
   - These will register when plugins load
   - Same command IDs and shortcuts preserved

**Success Metrics**:
- ✅ No widget-specific command files in core
- ✅ Core command system works
- ✅ Plugin commands available when plugins load

---

### Task 2.5: Validate Plugin Loading and Functionality
**Duration**: 0.5 days
**Assignee**: Developer
**Priority**: High

**Objective**: Ensure complete functionality through plugins only

**Detailed Steps**:
1. **Test terminal functionality**:
   - Terminal widgets load from viloxterm plugin
   - All terminal features work (input/output, clear, etc.)
   - Terminal commands work (new terminal, clear, etc.)

2. **Test editor functionality**:
   - Editor widgets load from viloedit plugin
   - File editing works (open, edit, save)
   - Editor commands work (cut, copy, paste, etc.)

3. **Validate zero duplication**:
   ```bash
   # These should return ZERO results:
   find packages/viloapp/src/viloapp/ui/ -name "*terminal*" -o -name "*editor*"
   find packages/viloapp/src/viloapp/services/ -name "*terminal_service*" -o -name "*editor_service*"
   find packages/viloapp/src/viloapp/core/commands/builtin/ -name "*terminal_commands*" -o -name "*edit_commands*"
   ```

**Success Metrics**:
- ✅ All terminal functionality works through plugin
- ✅ All editor functionality works through plugin
- ✅ Zero widget implementations in core
- ✅ Zero competing implementations exist

**COMPLETED**: ✅ Phase 2 successfully completed on 2025-09-23
- Zero duplication achieved (~168,000 lines of duplication removed)
- Core platform is now pure (no widget-specific code)
- Platform ready to host plugins

---

## Phase 3: Capability System Integration

### Task 3.1: Implement Core Capability Infrastructure
**Duration**: 2 days
**Assignee**: Developer
**Priority**: High

**Objective**: Implement capability system from design specifications

**Detailed Steps**:
1. **Implement WidgetCapability enumeration**:
   ```python
   # packages/viloapp/src/viloapp/core/capabilities.py
   from enum import Enum

   class WidgetCapability(Enum):
       TEXT_EDITING = "text_editing"
       SHELL_EXECUTION = "shell_execution"
       CLIPBOARD_COPY = "clipboard_copy"
       CLIPBOARD_PASTE = "clipboard_paste"
       CLEAR_DISPLAY = "clear_display"
       # ... all capabilities from design
   ```

2. **Implement ICapabilityProvider interface**:
   ```python
   # packages/viloapp/src/viloapp/core/capability_provider.py
   from abc import ABC, abstractmethod

   class ICapabilityProvider(ABC):
       @abstractmethod
       def get_capabilities(self) -> Set[WidgetCapability]:
           pass

       @abstractmethod
       def execute_capability(self, capability: WidgetCapability, **kwargs) -> Any:
           pass
   ```

3. **Implement CapabilityManager**:
   ```python
   # packages/viloapp/src/viloapp/core/capability_manager.py
   class CapabilityManager:
       def register_widget(self, widget_id: str, widget: ICapabilityProvider):
           """Register widget capabilities"""

       def find_widgets_with_capability(self, capability: WidgetCapability) -> List[str]:
           """Find widgets supporting capability"""

       def execute_capability(self, widget_id: str, capability: WidgetCapability, **kwargs):
           """Execute capability on widget"""
   ```

4. **Implement ServiceRegistry for platform services**:
   ```python
   # packages/viloapp/src/viloapp/core/service_registry.py
   class ServiceRegistry:
       def register_service(self, service: IPlatformService):
           """Register platform service"""

       def get_service_by_interface(self, interface: type) -> Optional[IPlatformService]:
           """Get service by interface"""
   ```

**Success Metrics**:
- ✅ Core capability infrastructure implemented
- ✅ All capability interfaces defined
- ✅ Capability manager functional
- ✅ Service registry implemented
- ✅ Code compiles without errors

---

### Task 3.2: Add Capability Support to Plugin Widgets
**Duration**: 1 day
**Assignee**: Developer
**Priority**: High

**Objective**: Update plugin widgets to implement capability interfaces

**Detailed Steps**:
1. **Update viloxterm widget**:
   ```python
   # packages/viloxterm/src/viloxterm/widget.py
   class TerminalWidget(AppWidget, ICapabilityProvider):
       def get_capabilities(self) -> Set[WidgetCapability]:
           return {
               WidgetCapability.SHELL_EXECUTION,
               WidgetCapability.CLIPBOARD_COPY,
               WidgetCapability.CLIPBOARD_PASTE,
               WidgetCapability.CLEAR_DISPLAY,
           }

       def execute_capability(self, capability: WidgetCapability, **kwargs):
           # Implementation for each capability
   ```

2. **Update viloedit widget**:
   ```python
   # packages/viloedit/src/viloedit/widget.py
   class EditorWidget(AppWidget, ICapabilityProvider):
       def get_capabilities(self) -> Set[WidgetCapability]:
           return {
               WidgetCapability.TEXT_EDITING,
               WidgetCapability.FILE_SAVING,
               WidgetCapability.CLIPBOARD_COPY,
               WidgetCapability.CLIPBOARD_PASTE,
           }
   ```

3. **Register widgets with capability manager**:
   - Update plugin loading to register capabilities
   - Test capability discovery
   - Verify capability execution

**Success Metrics**:
- ✅ Plugin widgets implement ICapabilityProvider
- ✅ Widgets register capabilities correctly
- ✅ Capability execution works through manager
- ✅ All widget functionality accessible via capabilities

---

### Task 3.3: Convert Commands to Capability-Based
**Duration**: 1 day
**Assignee**: Developer
**Priority**: High

**Objective**: Convert remaining core commands to use capability delegation

**Detailed Steps**:
1. **Create capability-based command framework**:
   ```python
   # packages/viloapp/src/viloapp/core/commands/capability_commands.py
   @command(id="platform.copy", shortcut="ctrl+c", when="canCopy")
   def copy_command(context: CommandContext) -> CommandResult:
       return execute_capability_on_active_widget(
           context, WidgetCapability.CLIPBOARD_COPY
       )
   ```

2. **Update existing commands**:
   - Replace widget-specific logic with capability delegation
   - Update when conditions to use capability checks
   - Ensure same keyboard shortcuts work

3. **Implement capability delegation helper**:
   ```python
   def execute_capability_on_active_widget(context, capability, **kwargs):
       widget_id = get_active_widget_id(context)
       if not widget_id:
           return CommandResult.failure("No active widget")

       return capability_manager.execute_capability(widget_id, capability, **kwargs)
   ```

**Success Metrics**:
- ✅ Core commands use capability delegation
- ✅ No direct widget method calls in commands
- ✅ All keyboard shortcuts preserved
- ✅ Commands work with any capable widget

---

### Task 3.4: Update When Conditions for Capabilities
**Duration**: 1 day
**Assignee**: Developer
**Priority**: Medium

**Objective**: Replace widget-type-based when conditions with capability-based ones

**Detailed Steps**:
1. **Update when_context.py**:
   ```python
   # Replace:
   variables["editorFocus"] = widget_has_category(active_pane.widget_id, WidgetCategory.EDITOR)

   # With:
   variables["canEditText"] = widget_has_capability(active_pane.widget_id, WidgetCapability.TEXT_EDITING)
   variables["canExecuteShell"] = widget_has_capability(active_pane.widget_id, WidgetCapability.SHELL_EXECUTION)
   variables["canCopy"] = widget_has_capability(active_pane.widget_id, WidgetCapability.CLIPBOARD_COPY)
   ```

2. **Update command when conditions**:
   ```python
   # Change from:
   when="editorFocus && editorHasSelection"

   # To:
   when="canEditText && hasTextSelection"
   ```

3. **Test command availability**:
   - Verify commands enable/disable based on capabilities
   - Test with different widget types
   - Ensure capability-based conditions work correctly

**Success Metrics**:
- ✅ No widget-type-based when conditions remain
- ✅ All when conditions use capability checks
- ✅ Commands enable/disable based on widget capabilities
- ✅ Same user experience with more flexible architecture

---

## Phase 4: Final Validation & Testing

### Task 4.1: Zero Duplication Validation
**Duration**: 0.5 days
**Assignee**: Developer
**Priority**: Critical

**Objective**: Validate no competing implementations exist

**Detailed Steps**:
1. **Run zero duplication validation**:
   ```bash
   # These MUST return zero results:
   find packages/viloapp/src/viloapp/ui/ -name "*terminal*" -o -name "*editor*"
   find packages/viloapp/src/viloapp/services/ -name "*terminal_service*" -o -name "*editor_service*"
   find packages/viloapp/src/viloapp/core/commands/builtin/ -name "*terminal_commands*" -o -name "*edit_commands*"

   # Verify only platform files remain:
   ls packages/viloapp/src/viloapp/services/terminal_server.py  # Should exist (platform service)
   ```

2. **Validate widget loading**:
   ```bash
   # Plugins should provide all widget functionality:
   ls packages/viloxterm/src/viloxterm/widget.py     # Terminal widget
   ls packages/viloedit/src/viloedit/widget.py       # Editor widget
   ```

3. **Test plugin widget registration**:
   - Start application
   - Verify plugin widgets register with correct IDs
   - Test basic widget creation and functionality

**Success Metrics**:
- ✅ Zero widget implementations in core
- ✅ Zero widget services in core (except platform services)
- ✅ Zero widget commands in core
- ✅ Plugin widgets load and register correctly

---

### Task 4.2: Functionality Preservation Testing
**Duration**: 0.5 days
**Assignee**: Developer
**Priority**: High

**Objective**: Verify all functionality preserved through plugins

**Detailed Steps**:
1. **Test terminal functionality**:
   - Create new terminal tab
   - Execute shell commands
   - Copy/paste operations
   - Clear terminal
   - Test keyboard shortcuts

2. **Test editor functionality**:
   - Open files for editing
   - Edit and save files
   - Copy/cut/paste operations
   - Find and replace
   - Test keyboard shortcuts

3. **Test capability-based commands**:
   - Commands work on any capable widget
   - Commands disable on non-capable widgets
   - Keyboard shortcuts preserved
   - Command palette shows all available commands

**Success Metrics**:
- ✅ All terminal features work through plugin
- ✅ All editor features work through plugin
- ✅ All keyboard shortcuts preserved
- ✅ Commands work through capability system
- ✅ No functionality regression

---

### Task 4.3: Plugin Extensibility Testing
**Duration**: 0.5 days
**Assignee**: Developer
**Priority**: Medium

**Objective**: Verify platform extensibility without core changes

**Detailed Steps**:
1. **Test new widget type scenario**:
   - Create mock plugin with new widget type
   - Verify widget registers without core changes
   - Test capability system works with new widget

2. **Test command extensibility**:
   - Verify plugin commands register automatically
   - Test capability-based commands work with new widgets
   - Ensure no hardcoded widget knowledge in core

3. **Test service discovery**:
   - Verify platform services available to plugins
   - Test service registry functionality
   - Ensure clean service boundaries

**Success Metrics**:
- ✅ New widget types can be added without core changes
- ✅ Plugin commands register automatically
- ✅ Capability system works with any widget type
- ✅ Service discovery works correctly
- ✅ Platform boundaries are clean and enforced

---

### Task 4.4: Performance & Stability Validation
**Duration**: 0.5 days
**Assignee**: Developer
**Priority**: Medium

**Objective**: Ensure no performance degradation from refactoring

**Detailed Steps**:
1. **Performance testing**:
   - Measure application startup time
   - Test widget creation/destruction performance
   - Measure capability delegation overhead
   - Compare with pre-refactor performance

2. **Stability testing**:
   - Long-running session testing
   - Plugin loading/unloading cycles
   - Error handling in capability system
   - Resource leak detection

3. **Memory usage analysis**:
   - Check for memory leaks in plugin system
   - Verify widget lifecycle management
   - Test capability system resource usage

**Success Metrics**:
- ✅ No significant performance degradation
- ✅ Stable operation over extended periods
- ✅ No memory leaks in plugin/capability system
- ✅ Error handling robust and informative
- ✅ Resource usage within acceptable bounds

---

## 📊 Summary

### Total Duration
- **Phase 1**: 2-3 days (COMPLETE)
- **Phase 2**: 3 days (Immediate Deduplication)
- **Phase 3**: 5 days (Capability System Integration)
- **Phase 4**: 2 days (Final Validation & Testing)
- **Total**: ~12-13 days

### Key Deliverables
- ✅ `widget-code-audit-REPORT.md` (Phase 1.1)
- ✅ `plugin-package-structure-ANALYSIS.md` (Phase 1.2)
- ✅ `capability-system-DESIGN.md` (Phase 1.3)
- ✅ `api-specifications-DESIGN.md` (Phase 1.3)

### Success Criteria Validation
After completion, these validations MUST pass:

```bash
# Zero duplication validation:
find packages/viloapp/src/viloapp/ui/ -name "*terminal*" -o -name "*editor*"        # Returns: nothing
find packages/viloapp/src/viloapp/services/ -name "*terminal_service*" -o -name "*editor_service*"  # Returns: nothing
find packages/viloapp/src/viloapp/core/commands/builtin/ -name "*terminal_commands*" -o -name "*edit_commands*"  # Returns: nothing

# Plugin functionality validation:
ls packages/viloxterm/src/viloxterm/widget.py     # Returns: terminal widget implementation
ls packages/viloedit/src/viloedit/widget.py       # Returns: editor widget implementation

# Platform service validation:
ls packages/viloapp/src/viloapp/services/terminal_server.py  # Returns: platform service (kept)
```

### Architecture Transformation
- **Before**: Widget-aware application with massive duplication (~168,000+ lines)
- **After**: Pure widget platform with plugin-only implementations (~5,000 lines in plugins)
- **Benefit**: True extensibility without core modifications

---

**Status**: ✅ TASKS UPDATED - Ready for Phase Execution
**Last Updated**: 2025-01-23
**Next**: Begin Phase 2 - Immediate Deduplication

