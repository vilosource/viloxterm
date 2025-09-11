# 🚀 Pre-Flight Checklist for Development

**STOP! Before you write ANY code, complete this checklist.**

---

## 📋 Before Starting a Feature

### 1. Understand the Current State
- [ ] Can the app start right now? Run: `python main.py`
- [ ] Note the last working commit: `git log --oneline -1`
- [ ] Create a safety branch: `git checkout -b feature/XXX-backup`

### 2. Understand What You're Changing
- [ ] Read the ACTUAL implementation of classes you'll use
  ```bash
  # Example: Before using Command class
  grep -A 20 "class Command" core/commands/base.py
  ```
- [ ] Find correct import paths
  ```bash
  # Example: Find ServiceLocator
  find . -name "*.py" -exec grep -l "class ServiceLocator" {} \;
  ```
- [ ] Look for existing patterns
  ```bash
  # Example: How are commands currently created?
  grep -A 5 "Command(" core/commands/builtin/*.py
  ```

### 3. Plan Your Approach
- [ ] Write down your assumptions
- [ ] Identify what could break
- [ ] Plan incremental steps (max 10 lines per test)

---

## 🔨 During Implementation

### Every 10 Lines of Code
- [ ] Save your file
- [ ] Run: `python -m py_compile <your_file.py>`
- [ ] If it's a critical file, run: `python main.py --check`

### Every Function/Class Added
- [ ] Write a minimal test
- [ ] Run the app: `timeout 3 python main.py`
- [ ] Check for errors in first 3 seconds

### Before Using Any Import
- [ ] Verify it exists: `ls -la path/to/module.py`
- [ ] Test the import: `python -c "from x.y import Z"`

---

## ✅ Before EVERY Commit

### The 5-Minute Safety Check

1. **Start the app** (MANDATORY)
   ```bash
   timeout 5 python main.py 2>&1 | grep -i error
   # Should see NO errors
   ```

2. **Check your changes**
   ```bash
   git diff --stat  # What did I change?
   git diff         # Do the changes make sense?
   ```

3. **Verify imports**
   ```bash
   # Check all your new imports work
   python -c "from module import thing"
   ```

4. **Run basic smoke test**
   ```python
   # quick_test.py
   from ui.main_window import MainWindow
   print("✅ Imports work")
   ```

5. **Document what you tested**
   ```bash
   # In commit message:
   git commit -m "Add feature X
   
   Tested:
   - App starts successfully
   - No import errors
   - Feature X works when clicked"
   ```

---

## 🚨 Red Flags - STOP if you see:

1. **Import Errors**
   ```
   ModuleNotFoundError: No module named 'core.services'
   ```
   **STOP!** Find the correct path first.

2. **Type Errors on Init**
   ```
   TypeError: __init__() missing required positional argument
   ```
   **STOP!** Read the actual class definition.

3. **App Won't Start**
   ```
   Traceback (most recent call last):
   ```
   **STOP!** Fix immediately, don't continue.

4. **Multiple Files Changed**
   ```bash
   git status
   # Shows 10+ files modified
   ```
   **STOP!** You're changing too much at once.

---

## 🛠️ Quick Fixes for Common Issues

### Import Error?
```bash
# Find the right import
grep -r "class ClassName" --include="*.py" .
```

### TypeError on Class Init?
```bash
# Check what parameters it needs
grep -A 10 "class ClassName" path/to/file.py
# Or check __init__ method
grep -A 10 "def __init__" path/to/file.py
```

### App Won't Start?
```bash
# Revert to last working state
git stash
python main.py  # Verify it works without your changes
git stash pop   # Now debug your changes
```

---

## 📊 Success Metrics

Your development session was successful if:
- ✅ Every commit has a working application
- ✅ You tested after every significant change
- ✅ You never had to debug for more than 5 minutes
- ✅ Your code worked on first try (because you verified everything)

---

## 🎯 The Golden Rules

1. **If you're not sure, CHECK**
   - Don't assume, verify
   - Read the actual code
   - Test the import

2. **If it breaks, STOP**
   - Don't add more code to broken code
   - Fix it immediately
   - Understand why it broke

3. **If it works, COMMIT**
   - Capture working states frequently
   - Small commits are good commits
   - You can always squash later

4. **If you're changing core code, TEST EVERYTHING**
   - Core changes affect everything
   - Test all features, not just yours
   - Have a rollback plan

---

## 📝 Template for Safe Development

```bash
# 1. Create feature branch
git checkout -b feature/safe-feature

# 2. Make tiny change (< 10 lines)
vim file.py

# 3. Test immediately
python main.py  # Does it still work?

# 4. Commit working state
git add -A
git commit -m "WIP: Feature works at basic level"

# 5. Add complexity
vim file.py  # Add 10 more lines

# 6. Test again
python main.py

# 7. Commit again
git commit -am "WIP: Feature now has X"

# 8. Repeat until done
# 9. Squash commits if desired
git rebase -i main
```

---

## 🚀 Remember

**Speed is the enemy of quality.**

It's better to:
- Take 2 hours and deliver working code
- Than take 30 minutes and deliver broken code that takes 3 hours to fix

**Test early, test often, test always.**

---

*This checklist exists because we learned the hard way. Use it.*