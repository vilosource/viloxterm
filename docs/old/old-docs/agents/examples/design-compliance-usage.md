# Design Compliance Analyzer - Usage Examples

## How to Use This Agent

### Basic Invocation

```bash
# Full design compliance check
claude "Use the design-compliance-analyzer agent to analyze our keyboard command implementation against docs/features/KEYBOARD_COMMAND_DESIGN.md"

# Specific feature verification
claude "Use the design-compliance-analyzer to verify if all shortcuts from the design document are implemented"

# Code quality review
claude "Use the design-compliance-analyzer to review the command system for code smells and duplicate definitions"
```

## Example Scenarios

### Scenario 1: Full Design Compliance Check

**Input:**
```
Use the design-compliance-analyzer agent to verify our command palette implementation against the design specification in docs/features/KEYBOARD_COMMAND_DESIGN.md
```

**Expected Output:**
```markdown
# Design Compliance Analysis Report

## Executive Summary
- Total features in design: 12
- Implemented: 7 (58%)
- Not Found: 3 (25%)
- Partial: 2 (17%)
- Duplicates found: 5 instances

## Detailed Findings

### Feature: Fuzzy Search
**Status:** PARTIAL
**Evidence:** 
  - Location: core/commands/registry.py:194-241 (basic substring matching only)
  - Missing: Character distance scoring, fuzzy algorithm
**Search Log:**
  - Direct: Searched "fuzzy" - Found in comments only
  - Alternative: Searched "search_commands" - Found at registry.py:194
  - Pattern: Searched "score|rank|match" - Found basic scoring at :209-236
**Confidence:** VERIFIED
**Issues Found:**
  - ⚠️ Implementation is substring matching, not true fuzzy search
  - ⚠️ No character distance algorithm as specified

### Feature: Recent Commands
**Status:** NOT_FOUND (stub only)
**Evidence:**
  - Location: ui/command_palette/palette_controller.py:244-253 (returns empty list)
**Search Log:**
  - Direct: Searched "recent_commands" - Found stub method
  - Alternative: Searched "history|mru|frequently" - No implementation found
  - Pattern: Searched "deque|cache.*command" - Not found
  - Files examined: 47 files in ui/, core/, services/
**Confidence:** VERIFIED
**Issues Found:**
  - ⚠️ Method exists but has no implementation
  - ⚠️ No persistence mechanism found
```

### Scenario 2: Duplicate Detection

**Input:**
```
Use the design-compliance-analyzer to find all duplicate keyboard shortcut definitions
```

**Expected Output:**
```markdown
# Duplicate Detection Report

## Duplicate Shortcuts Found

### File: core/keyboard/keymaps.py

#### Shortcut: "ctrl+n" (New File)
**Locations:**
- Line 65: {"id": "file.new", "sequence": "ctrl+n", "command_id": "file.newEditorTab"}
- Line 116: {"id": "file.new", "sequence": "ctrl+n", "command_id": "file.newEditorTab"}  
- Line 173: {"id": "file.new", "sequence": "ctrl+n", "command_id": "file.newEditorTab"}

#### Shortcut: "ctrl+shift+p" (Command Palette)
**Locations:**
- Line 136: {"id": "view.command_palette", "sequence": "ctrl+shift+p", ...}
(Note: Only one definition found despite initial analysis - correcting previous error)

## Summary
- Total duplicate definitions: 15 shortcuts defined 3 times each
- Files affected: 1 (keymaps.py)
- Recommended action: Consolidate into single definition list
```

### Scenario 3: Missing Feature Verification

**Input:**
```
Use the design-compliance-analyzer to verify if Focus Management from the design is implemented
```

**Expected Output:**
```markdown
# Feature Verification: Focus Management

## Search Methodology
Exhaustive search performed using three-pass protocol:

### PASS 1: Direct Search
- Searched: "FocusManager" in all .py files
- Result: NOT FOUND
- Searched: "FocusGroup" in all .py files  
- Result: NOT FOUND

### PASS 2: Alternative Search
- Searched: "focus_manager", "focusmanager", "focus-manager"
- Result: NOT FOUND
- Searched: "focus.*group", "focus.*navigation"
- Result: NOT FOUND
- Searched: "F6", "Shift+F6", "Focus.*Next.*Part"
- Result: Found "F6" in ui/vscode_theme.py:34 (just a color constant)

### PASS 3: Pattern Search
- Pattern: "class.*Focus.*Manager"
- Result: NOT FOUND
- Pattern: "def.*focus.*next|def.*focus.*previous"
- Result: Found focus methods but not for navigation between UI parts
- Checked test files: No focus manager tests found
- Checked imports: No focus manager imports found

## Feature: Focus Management System
**Status:** NOT_FOUND
**Evidence:** 
  - No FocusManager class exists
  - No FocusGroup implementation
  - No F6/Shift+F6 shortcuts registered
  - No focus navigation between UI parts
**Search Log:**
  - Direct searches: 8 different terms
  - Alternative searches: 12 variations
  - Pattern searches: 6 regex patterns
  - Files examined: 127 .py files across entire project
**Confidence:** VERIFIED (exhaustive search completed)
**Notes:** 
  - Basic focus handling exists in Qt widgets
  - No systematic focus management as specified in design
```

## Best Practices

### DO:
✅ Specify exact design document path
✅ Ask for specific features if you want targeted analysis
✅ Request search logs if you want to verify thoroughness
✅ Ask for confidence levels on findings

### DON'T:
❌ Accept "not found" without search evidence
❌ Trust analysis without file:line references
❌ Assume first occurrence is the only one
❌ Skip verification of the analysis

## Interpreting Results

### Status Meanings:
- **IMPLEMENTED**: Feature found and working as designed
- **NOT_FOUND**: Exhaustive search found no implementation
- **PARTIAL**: Some but not all aspects implemented
- **DUPLICATE**: Multiple definitions of same feature

### Confidence Levels:
- **VERIFIED**: Direct evidence found in code
- **PROBABLE**: Strong indicators but not definitive
- **UNCERTAIN**: Ambiguous or conflicting evidence

## Validation Checklist

After receiving analysis, verify:
- [ ] Every "NOT_FOUND" has search log
- [ ] Every "IMPLEMENTED" has file:line reference
- [ ] Duplicate definitions are checked
- [ ] Alternative naming was considered
- [ ] Test files were searched
- [ ] Config files were checked

## Common Issues This Agent Prevents

1. **Missing duplicates** (like the Ctrl+Shift+P in keymaps.py)
2. **False negatives** due to incomplete search
3. **Assumptions** about implementation
4. **Overlooking** alternative architectures
5. **Missing** configuration-based features

## Troubleshooting

If the agent seems to miss something:
1. Ask it to show its search log
2. Verify it checked all three passes
3. Suggest specific search terms
4. Point to specific files to examine
5. Ask for confidence level justification