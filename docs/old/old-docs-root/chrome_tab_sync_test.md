# Chrome Mode Tab Synchronization Test Guide

## Setup
1. Start the application: `make run` or `.direnv/python-3.12.3/bin/python main.py`
2. Chrome mode should be enabled (tabs in title bar)

## Test Steps

### Test 1: Keyboard Navigation
1. Ensure you have multiple tabs open (use Ctrl+T to add tabs if needed)
2. Press **Ctrl+PgDown** to navigate to the next tab
   - ✅ Expected: Both workspace content AND Chrome title bar tab selection should move forward
3. Press **Ctrl+PgUp** to navigate to the previous tab
   - ✅ Expected: Both workspace content AND Chrome title bar tab selection should move backward

### Test 2: Chrome Tab Click
1. Click directly on a Chrome tab in the title bar
   - ✅ Expected: The workspace content should switch to that tab

### Test 3: Tab Closing
1. Click the X on a Chrome tab
   - ✅ Expected: Both the Chrome tab AND workspace tab should close

### Test 4: New Tab
1. Click the + button in the Chrome title bar
   - ✅ Expected: A new tab should appear in both Chrome title bar and workspace

## What Was Fixed

The issue was that the workspace's `tab_widget.currentChanged` signal wasn't connected to the Chrome title bar's `set_current_tab` method. When keyboard shortcuts (Ctrl+PgUp/PgDown) changed the workspace tabs, the Chrome title bar wasn't being notified.

### The Fix (in `ui/chrome_main_window.py:134-137`)
```python
# Connect workspace tab changes to Chrome title bar (for keyboard shortcuts)
self.workspace.tab_widget.currentChanged.connect(
    lambda index: self.chrome_title_bar.set_current_tab(index)
)
```

This ensures bidirectional synchronization:
- Chrome tab clicks → workspace tabs (already working)
- Workspace tab changes → Chrome tabs (now fixed)

## Verification
If the tabs stay synchronized during all the above tests, the fix is working correctly!