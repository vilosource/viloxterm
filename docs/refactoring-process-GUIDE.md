# Systematic Refactoring Process Guide

## Executive Summary

This guide ensures refactoring is complete, verified, and doesn't introduce bugs like the `widget_type` undefined variable error that slipped through our WidgetType enum removal.

**Core Principle**: Trust tools, not manual inspection.

---

## 🎯 When This Guide Applies

Use this process for:
- Removing or renaming symbols (classes, functions, constants)
- Changing data types (enum → string, int → float)
- Updating import paths or module structures
- Replacing patterns across multiple files
- Any change affecting >5 files

---

## 📋 Pre-Refactoring Analysis

### 1. Symbol Usage Discovery

**Never trust grep alone. Use multiple tools:**

```bash
# Find all imports
grep -r "from.*import.*WidgetType" packages/viloapp/src
grep -r "import.*WidgetType" packages/viloapp/src

# Find all usages
rg "WidgetType" --type py -C 2  # ripgrep with context
ag "WidgetType" --python         # silver searcher

# Find variable patterns (critical for our widget_type bug)
rg "widget_type|widget_id|widgetType" --type py | sort | uniq
```

**AST-based discovery (most accurate):**

```python
#!/usr/bin/env python3
"""Find all usages of a symbol using AST."""
import ast
import os
from pathlib import Path

def find_symbol_usage(directory, symbol_name):
    """Find all usages of a symbol using AST parsing."""
    usages = []

    for py_file in Path(directory).rglob("*.py"):
        try:
            with open(py_file) as f:
                tree = ast.parse(f.read(), filename=str(py_file))

            for node in ast.walk(tree):
                # Check for Name nodes (variable usage)
                if isinstance(node, ast.Name) and node.id == symbol_name:
                    usages.append((py_file, node.lineno, "variable"))

                # Check for attribute access (WidgetType.TERMINAL)
                if isinstance(node, ast.Attribute) and node.attr == symbol_name:
                    usages.append((py_file, node.lineno, "attribute"))

                # Check for imports
                if isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        if alias.name == symbol_name:
                            usages.append((py_file, node.lineno, "import"))

        except Exception as e:
            print(f"Error parsing {py_file}: {e}")

    return usages

# Use it
usages = find_symbol_usage("packages/viloapp/src", "WidgetType")
print(f"Found {len(usages)} usages:")
for file, line, usage_type in usages:
    print(f"  {file}:{line} ({usage_type})")
```

### 2. Impact Assessment

Create a refactoring manifest:

```python
# refactoring_manifest.py
REFACTORING = {
    "description": "Replace WidgetType enum with string widget_id",
    "removing": [
        "viloapp.core.widget_ids.WidgetType",
        "viloapp.core.widget_ids.TERMINAL",
        "viloapp.core.widget_ids.EDITOR",
    ],
    "replacing_with": {
        "WidgetType": "str",
        "WidgetType.TERMINAL": '"com.viloapp.terminal"',
        "widget_type": "widget_id",  # Variable rename!
    },
    "affected_files_estimate": 57,
    "risk_level": "HIGH",  # Touches core functionality
    "rollback_strategy": "git revert to checkpoint",
}

# Critical: Document variable name changes!
VARIABLE_MAPPINGS = {
    "widget_type": "widget_id",
    "widgetType": "widget_id",
    "default_widget_type": "default_widget_id",
}
```

### 3. Test Coverage Check

```bash
# Ensure affected code has tests
pytest packages/viloapp/tests --cov=viloapp --cov-report=html
# Check coverage for files you're changing
# If <80%, add tests FIRST
```

---

## 🔄 Systematic Refactoring Steps

### Phase 1: Setup Continuous Validation

**Create monitoring script:**

```bash
#!/bin/bash
# monitor_refactoring.sh - Run this continuously during refactoring

while true; do
    clear
    echo "==================================="
    echo "     REFACTORING MONITOR"
    echo "==================================="

    # Check for undefined variables (catches our widget_type bug!)
    echo -e "\n🔍 Undefined Variables Check:"
    python -c "
import subprocess
import sys
result = subprocess.run(['python', '-m', 'py_compile'] +
    glob.glob('packages/viloapp/src/**/*.py', recursive=True),
    capture_output=True, text=True)
if 'NameError' in result.stderr:
    print('❌ UNDEFINED VARIABLES FOUND!')
    print(result.stderr)
else:
    print('✅ No undefined variables')
"

    # Check variable consistency
    echo -e "\n📊 Variable Name Consistency:"
    echo -n "  widget_type: "
    grep -r "widget_type" packages/viloapp/src --include="*.py" 2>/dev/null | wc -l
    echo -n "  widget_id:   "
    grep -r "widget_id" packages/viloapp/src --include="*.py" 2>/dev/null | wc -l

    # Quick test
    echo -e "\n🧪 Quick Test:"
    python test_workspace_command_fix.py 2>&1 | tail -5

    # Git status
    echo -e "\n📝 Changed Files:"
    git status -s | head -10

    sleep 3
done
```

### Phase 2: Update Tests FIRST

**Critical: Tests must work with NEW API before changing implementation**

```python
# test_widget_refactoring.py
def test_new_api():
    """Test the NEW way before removing old way."""
    # Instead of WidgetType.TERMINAL
    widget_id = "com.viloapp.terminal"
    assert isinstance(widget_id, str)

    # Instead of widget_type parameter
    result = create_tab(widget_id="com.viloapp.editor")
    assert result.widget_id == "com.viloapp.editor"
```

### Phase 3: Incremental Changes

**One file at a time, with verification:**

```bash
# refactor_incremental.sh
#!/bin/bash

FILES=(
    "packages/viloapp/src/viloapp/core/widget_ids.py"
    "packages/viloapp/src/viloapp/core/commands/builtin/workspace_commands.py"
    # ... list all files
)

for FILE in "${FILES[@]}"; do
    echo "Refactoring: $FILE"

    # Make change
    python refactor_file.py "$FILE"

    # Immediately verify
    python -m py_compile "$FILE"
    if [ $? -ne 0 ]; then
        echo "❌ Syntax error in $FILE"
        exit 1
    fi

    # Test
    pytest -xvs tests/test_for_this_file.py
    if [ $? -ne 0 ]; then
        echo "❌ Tests failed after changing $FILE"
        exit 1
    fi

    # Check for undefined vars
    python -m pyflakes "$FILE"

    # Commit
    git add "$FILE"
    git commit -m "refactor: Update $FILE for widget_id migration [n/57]"
done
```

### Phase 4: Variable Consistency Check

**The bug that got us: mixed variable names**

```python
#!/usr/bin/env python3
"""Check for variable naming consistency issues."""

import re
from pathlib import Path

def check_variable_consistency(directory):
    """Find mixed variable usage that causes NameError."""
    issues = []

    for py_file in Path(directory).rglob("*.py"):
        with open(py_file) as f:
            content = f.read()
            lines = content.split('\n')

        # Check for assignments to one name and usage of another
        if 'widget_id =' in content and 'widget_type' in content:
            # Found mixed usage!
            for i, line in enumerate(lines, 1):
                if 'widget_id =' in line:
                    # Check if widget_type used later
                    for j, check_line in enumerate(lines[i:], i+1):
                        if 'widget_type' in check_line and 'widget_type =' not in check_line:
                            issues.append(f"{py_file}:{j}: Uses 'widget_type' but 'widget_id' was assigned")

    return issues

# This would have caught our bug!
issues = check_variable_consistency("packages/viloapp/src")
for issue in issues:
    print(f"⚠️ {issue}")
```

---

## 🧪 Verification Tools

### 1. Static Analysis Suite

```python
#!/usr/bin/env python3
"""Complete static analysis for refactoring verification."""

import subprocess
import sys
from pathlib import Path

def run_checks():
    """Run all static checks."""

    checks = {
        "Syntax Check": ["python", "-m", "py_compile"],
        "Undefined Variables": ["python", "-m", "pyflakes"],
        "Type Check": ["python", "-m", "mypy", "--ignore-missing-imports"],
    }

    failed = []

    for name, cmd in checks.items():
        print(f"\n🔍 Running {name}...")

        for py_file in Path("packages/viloapp/src").rglob("*.py"):
            result = subprocess.run(
                cmd + [str(py_file)],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                if "undefined name" in result.stdout or "NameError" in result.stderr:
                    print(f"❌ {py_file}: {result.stdout}")
                    failed.append((name, py_file))

    if failed:
        print(f"\n❌ {len(failed)} checks failed")
        return False

    print("\n✅ All static checks passed")
    return True

if __name__ == "__main__":
    if not run_checks():
        sys.exit(1)
```

### 2. Command Execution Test

```python
#!/usr/bin/env python3
"""Test all commands can execute without NameError."""

import sys
sys.path.insert(0, "packages/viloapp/src")

from viloapp.core.commands.registry import command_registry
from viloapp.core.commands.base import CommandContext
from viloapp.models.workspace_model import WorkspaceModel

def test_all_commands():
    """Execute every command to catch NameErrors."""

    failed = []

    # Create minimal context
    context = CommandContext()
    context.model = WorkspaceModel()

    for cmd_id in command_registry.get_all_commands():
        try:
            # Just try to execute - we don't care about success
            # We're looking for NameError/ImportError
            cmd = command_registry.get_command(cmd_id)
            if cmd and hasattr(cmd, 'execute'):
                cmd.execute(context)
            print(f"✅ {cmd_id}")

        except (NameError, ImportError) as e:
            print(f"❌ {cmd_id}: {e}")
            failed.append((cmd_id, str(e)))

        except Exception:
            # Other errors are OK for this test
            print(f"⚠️ {cmd_id} (failed but no NameError)")

    if failed:
        print(f"\n❌ {len(failed)} commands have undefined variables:")
        for cmd, error in failed:
            print(f"  {cmd}: {error}")
        return False

    return True

if __name__ == "__main__":
    if not test_all_commands():
        sys.exit(1)
```

### 3. Real Test Runner (No Mocks)

```python
#!/usr/bin/env python3
"""Run tests that actually execute code, not just mocks."""

import pytest
import sys

# Run only integration tests that execute real code
exit_code = pytest.main([
    "packages/viloapp/tests",
    "-m", "not unit",  # Skip unit tests with mocks
    "--tb=short",
    "-v"
])

sys.exit(exit_code)
```

---

## ⚠️ Common Pitfalls

### 1. The Silent NameError
**What happened to us:**
```python
widget_id = get_default_widget_type()  # Returns widget_id
name = f"New {widget_type.title()}"   # NameError: widget_type not defined!
```

**Prevention:**
- Use consistent variable names
- Run pyflakes after EVERY change
- No copy-paste without verification

### 2. The Mock That Lies
```python
@patch("WorkspaceService")
def test_command(mock_service):
    mock_service.add_tab()  # Test passes
    # But real code has NameError!
```

**Prevention:**
- Test real code paths
- Use integration tests
- Execute actual commands

### 3. The Incomplete Import Update
```python
from viloapp.core.widget_ids import TERMINAL  # ImportError!
# TERMINAL was removed but import wasn't updated
```

**Prevention:**
- Find ALL imports first
- Update imports before usage
- Test imports separately

### 4. The Mixed Variable Names
```python
def process(widget_id):  # Parameter named widget_id
    if widget_type == "terminal":  # But uses widget_type!
        pass
```

**Prevention:**
- Use refactoring tools in IDE
- Consistent naming conventions
- Automated consistency checks

---

## 📊 Metrics for Success

Your refactoring is complete when:

✅ **Zero undefined variables**
```bash
python -m pyflakes packages/viloapp/src  # No output
```

✅ **All tests pass**
```bash
pytest packages/viloapp/tests  # 100% pass
```

✅ **All commands execute**
```bash
python test_all_commands.py  # No NameErrors
```

✅ **Consistent variable names**
```bash
# Only ONE of these should have results
grep -r "widget_type" packages/viloapp/src
grep -r "widget_id" packages/viloapp/src
```

✅ **Application starts and runs**
```bash
python packages/viloapp/src/viloapp/main.py  # No crashes
```

---

## 🚀 Recovery Procedures

### If You Find Undefined Variables After Refactoring

1. **Immediate Stop**
```bash
git stash  # Save current work
git checkout -b fix-undefined-vars
```

2. **Systematic Discovery**
```bash
python -m pyflakes packages/viloapp/src > undefined.txt
grep "undefined name" undefined.txt | cut -d: -f1 | sort | uniq
```

3. **Fix Pattern**
```python
# For each file with undefined vars
for file in files_with_errors:
    # 1. Identify what variable is undefined
    # 2. Find where it should be defined
    # 3. Check for naming inconsistency
    # 4. Fix and verify immediately
```

### Rollback Strategy

```bash
# Create checkpoints during refactoring
git tag refactor-checkpoint-1
git tag refactor-checkpoint-2

# If something goes wrong
git reset --hard refactor-checkpoint-1
```

---

## 📝 Documentation Requirements

After refactoring, create:

### 1. Migration Guide
```markdown
# Migration: WidgetType to widget_id

## What Changed
- Removed: WidgetType enum
- Added: String-based widget_id

## Update Your Code
```python
# Before
widget_type = WidgetType.TERMINAL

# After
widget_id = "com.viloapp.terminal"
```
```

### 2. Deprecation Notices
```python
def get_widget_type():
    """
    DEPRECATED: Use get_widget_id() instead.
    Will be removed in v2.0.
    """
    warnings.warn("get_widget_type is deprecated", DeprecationWarning)
    return get_widget_id()
```

### 3. Refactoring Report
```markdown
# Refactoring Report: WidgetType Removal

- Files Changed: 57
- Tests Updated: 23
- Undefined Variables Fixed: 3
- Time Taken: 4 hours
- Issues Found: widget_type vs widget_id inconsistency
```

---

## 🎯 Quick Reference Card

```bash
# Before ANY refactoring
find . -name "*.py" -exec grep -l "SymbolName" {} \;
pytest --cov  # Baseline coverage

# During refactoring (keep running)
while true; do
  python -m pyflakes packages/viloapp/src | grep undefined
  sleep 2
done

# After each file change
python -m py_compile changed_file.py
pytest tests/for_that_file.py
git commit -m "refactor: [n/total]"

# Before declaring complete
python test_all_commands.py
python -m pyflakes packages/viloapp/src
pytest packages/viloapp/tests
python packages/viloapp/src/viloapp/main.py
```

---

## Conclusion

The `widget_type` undefined error taught us: **Never trust manual refactoring**.

Use tools. Verify continuously. Test actual code paths.

This process would have caught our bug in seconds, not after deployment.

**Remember**: Refactoring without verification is just breaking code with confidence.