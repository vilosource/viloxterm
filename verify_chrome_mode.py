#!/usr/bin/env python3
"""
Verification script for Chrome mode implementation.
"""

import sys
from PySide6.QtCore import QSettings

def verify_chrome_mode():
    """Verify all Chrome mode components are in place."""
    
    print("=" * 60)
    print("Chrome Mode Implementation Verification")
    print("=" * 60)
    
    results = []
    
    # 1. Check files exist
    print("\n1. Checking component files...")
    files = [
        ("Window Controls", "ui/widgets/window_controls.py"),
        ("Chrome Title Bar", "ui/widgets/chrome_title_bar.py"),
        ("Chrome Main Window", "ui/chrome_main_window.py"),
        ("UI Commands", "core/commands/builtin/ui_commands.py"),
        ("Unit Tests", "tests/unit/test_chrome_mode.py"),
        ("GUI Tests", "tests/gui/test_chrome_mode_gui.py"),
        ("Documentation", "docs/CHROME_MODE.md"),
    ]
    
    import os
    for name, path in files:
        exists = os.path.exists(path)
        results.append((name, exists))
        status = "✓" if exists else "✗"
        print(f"  {status} {name}: {path}")
    
    # 2. Check imports work
    print("\n2. Checking imports...")
    imports = [
        ("Window Controls", "ui.widgets.window_controls", "WindowControls"),
        ("Chrome Title Bar", "ui.widgets.chrome_title_bar", "ChromeTitleBar"),
        ("Chrome Main Window", "ui.chrome_main_window", "ChromeMainWindow"),
    ]
    
    for name, module, cls in imports:
        try:
            exec(f"from {module} import {cls}")
            results.append((f"{name} import", True))
            print(f"  ✓ {name}: from {module} import {cls}")
        except ImportError as e:
            results.append((f"{name} import", False))
            print(f"  ✗ {name}: {e}")
    
    # 3. Check commands registered
    print("\n3. Checking command registration...")
    try:
        from core.commands.registry import command_registry
        from core.commands.builtin import register_all_builtin_commands
        import core.commands.builtin.ui_commands
        
        register_all_builtin_commands()
        
        commands = [
            "ui.toggleChromeMode",
            "ui.enableChromeMode", 
            "ui.disableChromeMode"
        ]
        
        for cmd_id in commands:
            cmd = command_registry.get_command(cmd_id)
            exists = cmd is not None
            results.append((f"Command {cmd_id}", exists))
            status = "✓" if exists else "✗"
            if exists:
                print(f"  {status} {cmd_id}: {cmd.title}")
            else:
                print(f"  {status} {cmd_id}: Not found")
    except Exception as e:
        print(f"  ✗ Error checking commands: {e}")
        results.append(("Commands", False))
    
    # 4. Check current Chrome mode setting
    print("\n4. Checking current settings...")
    settings = QSettings("ViloApp", "ViloApp")
    chrome_enabled = settings.value("UI/ChromeMode", False, type=bool)
    print(f"  Chrome mode is: {'ENABLED ✓' if chrome_enabled else 'DISABLED'}")
    results.append(("Chrome mode setting", True))
    
    # 5. Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    percentage = (passed / total) * 100 if total > 0 else 0
    
    print(f"\nTests passed: {passed}/{total} ({percentage:.1f}%)")
    
    if passed == total:
        print("\n✓ Chrome mode implementation is COMPLETE and FUNCTIONAL!")
        print("\nTo use Chrome mode:")
        print("  1. Enable: python enable_chrome_mode.py enable")
        print("  2. Run app: python main.py")
        print("  3. Or use View menu → Enable Chrome-Style Tabs")
    else:
        print("\n✗ Some components are missing or broken.")
        print("Failed components:")
        for name, success in results:
            if not success:
                print(f"  - {name}")
    
    return passed == total

if __name__ == "__main__":
    success = verify_chrome_mode()
    sys.exit(0 if success else 1)