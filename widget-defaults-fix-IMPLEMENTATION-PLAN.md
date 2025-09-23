# Widget Defaults Fix - Implementation Plan

## Problem Statement
The widget system still has hardcoded widget IDs throughout the codebase, violating our core principle that plugins should be first-class citizens. We need to eliminate ALL hardcoded widget IDs and implement a registry-based discovery system with user preferences.

## Success Metrics
When complete, the system will:
1. ✅ Have ZERO hardcoded widget IDs in core
2. ✅ Support unlimited widget types
3. ✅ Allow user preference configuration
4. ✅ Enable plugins as first-class defaults
5. ✅ Gracefully handle missing widgets
6. ✅ Maintain backwards compatibility
7. ✅ Follow all North Star principles

## Implementation Tasks

### Task 1: Enhance Widget Metadata System
**Goal**: Enable widgets to declare their default capabilities

#### Changes:
1. Update `AppWidgetMetadata` class to include:
   - `can_be_default: bool = False`
   - `default_priority: int = 100` (lower = higher priority)
   - `default_for_contexts: List[str] = []` (e.g., ["terminal", "editor"])

2. Update all widget registrations to declare capabilities:
   - Terminal: `can_be_default=True, default_priority=10`
   - Editor: `can_be_default=True, default_priority=20`
   - Others: `can_be_default=False` or appropriate values

#### Acceptance Criteria:
- [ ] AppWidgetMetadata has new fields with defaults
- [ ] All 8 built-in widgets have updated registrations
- [ ] No compilation errors
- [ ] Widget metadata can be queried by default capability

---

### Task 2: Implement Registry-Based Default Discovery
**Goal**: Create methods to discover defaults without hardcoding

#### Changes:
1. In `app_widget_manager.py`, add:
   ```python
   def get_default_widget_id(self, context: Optional[str] = None) -> Optional[str]
   def get_default_terminal_id(self) -> Optional[str]
   def get_default_editor_id(self) -> Optional[str]
   def get_widgets_for_context(self, context: str) -> List[str]
   ```

2. Remove from `widget_ids.py`:
   - `DEFAULT_WIDGET_ID` constant
   - Update `get_default_widget_id()` to call registry

#### Acceptance Criteria:
- [ ] NO hardcoded widget IDs in widget_ids.py
- [ ] Registry methods return valid defaults
- [ ] Falls back gracefully if no widgets available
- [ ] Returns None rather than crashing if no widgets
- [ ] Test: Removing all terminal widgets still allows app to start

---

### Task 3: Add User Preference Support
**Goal**: Allow users to configure default widgets

#### Changes:
1. Add settings structure:
   ```python
   # In app_defaults.py
   def get_default_widget_preference() -> Optional[str]
   def set_default_widget_preference(widget_id: str) -> None
   def get_default_widget_for_context(context: str) -> Optional[str]
   ```

2. Update registry methods to check preferences first

3. Add validation to ensure preference widgets exist

#### Acceptance Criteria:
- [ ] Settings can store default widget preferences
- [ ] Invalid preferences are ignored gracefully
- [ ] Preferences override registry defaults
- [ ] Can set context-specific defaults (editor vs terminal)
- [ ] Test: Set preference, restart app, preference is used

---

### Task 4: Fix All Import Errors
**Goal**: Remove all references to old constants

#### Files to fix (17 total):
1. `workspace.py` - Replace hardcoded "com.viloapp.terminal"
2. `workspace_view.py` - Replace hardcoded "com.viloapp.editor"
3. `workspace_service.py` - Fix EDITOR.value, TERMINAL.value
4. `when_context.py` - Fix widget ID comparisons
5. `widget_bridge.py` - Remove EDITOR, TERMINAL imports
6. `service_adapters.py` - Fix EDITOR references (3 places)
7. `settings_commands.py` - Fix SETTINGS references (2 places)
8. `debug_commands.py` - Fix TERMINAL reference
9. `theme_commands.py` - Fix SETTINGS reference
10. `file_commands.py` - Fix EDITOR/TERMINAL references (4 places)
11. `tab_commands.py` - Fix EDITOR reference
12. `terminal_commands.py` - Fix TERMINAL reference
13. `workspace_commands.py` - Fix widget type mapping
14. `navigation_commands.py` - Fix TERMINAL reference
15. `pane_header.py` - Fix all widget comparisons
16. Split pane files - Update type mappings
17. Model files - Use registry for defaults

#### Acceptance Criteria:
- [ ] NO import errors when running the app
- [ ] NO NameError for TERMINAL, EDITOR, etc.
- [ ] All files use registry methods for defaults
- [ ] grep for "TERMINAL|EDITOR|SETTINGS" returns only comments/strings
- [ ] Application starts without errors

---

### Task 5: Implement Context-Aware Defaults
**Goal**: Different defaults for different situations

#### Changes:
1. Commands specify context when requesting defaults:
   ```python
   # In file_commands.py
   widget_id = app_widget_manager.get_default_editor_id()

   # In terminal_commands.py
   widget_id = app_widget_manager.get_default_terminal_id()
   ```

2. Widget creation uses appropriate context

#### Acceptance Criteria:
- [ ] Editor commands get editor-type defaults
- [ ] Terminal commands get terminal-type defaults
- [ ] General commands get general defaults
- [ ] Fallback chain works correctly
- [ ] Test: Each context returns appropriate widget type

---

### Task 6: Update Widget Type Comparisons
**Goal**: Fix all hardcoded widget type checks

#### Changes:
1. Replace direct comparisons:
   ```python
   # OLD: if widget_id == TERMINAL
   # NEW: if self._is_terminal_widget(widget_id)
   ```

2. Add helper methods for type checking:
   ```python
   def _is_terminal_widget(widget_id: str) -> bool
   def _is_editor_widget(widget_id: str) -> bool
   def _is_settings_widget(widget_id: str) -> bool
   ```

#### Acceptance Criteria:
- [ ] No direct string comparisons to widget IDs
- [ ] Type checks use capability/category from registry
- [ ] Plugin widgets are correctly categorized
- [ ] Test: Plugin terminal recognized as terminal type

---

### Task 7: Settings UI Integration
**Goal**: Allow users to configure defaults through UI

#### Changes:
1. Add to Settings widget:
   - Default widget dropdown
   - Context-specific default dropdowns
   - File type associations

2. Populate dropdowns from registry

3. Save preferences on change

#### Acceptance Criteria:
- [ ] Settings UI shows available widgets
- [ ] Can select and save default widget
- [ ] Changes apply to new tabs/panes
- [ ] Plugin widgets appear in dropdowns
- [ ] Test: Change default in UI, create new tab, uses new default

---

### Task 8: Migration and Backwards Compatibility
**Goal**: Ensure existing configs still work

#### Changes:
1. Keep `migrate_widget_type()` for old saves
2. Update restoration to use new system
3. Add migration for old DEFAULT constants

#### Acceptance Criteria:
- [ ] Old saved states load correctly
- [ ] Old widget types map to new IDs
- [ ] No data loss during migration
- [ ] Test: Load pre-refactor save file successfully

---

### Task 9: Comprehensive Testing
**Goal**: Verify system works end-to-end

#### Test Scenarios:
1. Start app with no widgets registered
2. Start app with only plugin widgets
3. Remove all terminal widgets, app still works
4. Set preference for non-existent widget
5. Plugin declares itself as default
6. Multiple widgets compete for default

#### Acceptance Criteria:
- [ ] All test scenarios pass
- [ ] No crashes regardless of widget availability
- [ ] Graceful degradation at every level
- [ ] Performance unchanged (<10ms operations)
- [ ] Test suite updated with new test cases

---

### Task 10: Documentation
**Goal**: Document the new system

#### Deliverables:
1. Update architecture docs
2. Create widget registration guide
3. Document preference system
4. Add plugin developer guide

#### Acceptance Criteria:
- [ ] Clear documentation of resolution chain
- [ ] Examples for plugin developers
- [ ] User guide for setting preferences
- [ ] Migration guide for existing code

---

## Definition of Done
- [ ] All 10 tasks completed
- [ ] All acceptance criteria met
- [ ] Application runs without errors
- [ ] Tests pass (including new tests)
- [ ] Code review completed
- [ ] Documentation updated
- [ ] No hardcoded widget IDs remain

## Implementation Order
Tasks will be implemented in sequence as they build upon each other:
1. Task 1: Enhance metadata (foundation)
2. Task 2: Registry discovery (core mechanism)
3. Task 3: User preferences (preference layer)
4. Task 4: Fix imports (cleanup)
5. Task 5: Context-aware defaults (refinement)
6. Task 6: Type comparisons (consistency)
7. Task 7: Settings UI (user interface)
8. Task 8: Migration (compatibility)
9. Task 9: Testing (validation)
10. Task 10: Documentation (completion)