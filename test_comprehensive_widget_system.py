#!/usr/bin/env python3
"""Comprehensive test suite for the widget defaults system."""

import sys
import time
sys.path.insert(0, "packages/viloapp/src")

def test_no_widgets_available():
    """Test system behavior when no widgets are registered."""
    from viloapp.core.app_widget_manager import app_widget_manager

    # Clear all widgets
    app_widget_manager.clear()

    # System should return None when no widgets available
    default = app_widget_manager.get_default_widget_id()
    assert default is None, "Should return None when no widgets available"

    terminal = app_widget_manager.get_default_terminal_id()
    assert terminal is None, "Should return None for terminal when no widgets"

    editor = app_widget_manager.get_default_editor_id()
    assert editor is None, "Should return None for editor when no widgets"

    print("✅ System handles no widgets gracefully")
    return True

def test_plugin_as_default():
    """Test that a plugin widget can be the default."""
    from viloapp.core.app_widget_manager import app_widget_manager
    from viloapp.core.app_widget_metadata import AppWidgetMetadata, WidgetCategory

    # Clear and add only plugin widgets
    app_widget_manager.clear()

    # Register a plugin terminal
    class MockPluginTerminal:
        pass

    plugin_terminal = AppWidgetMetadata(
        widget_id="plugin.awesome.terminal",
        display_name="Awesome Terminal",
        description="A better terminal",
        icon="terminal",
        category=WidgetCategory.TERMINAL,
        widget_class=MockPluginTerminal,
        can_be_default=True,
        default_priority=5,  # Higher priority than built-in
        default_for_contexts=["terminal", "shell"],
        source="plugin",
        plugin_id="awesome"
    )

    app_widget_manager.register_widget(plugin_terminal)

    # Plugin should become default
    default = app_widget_manager.get_default_widget_id()
    assert default == "plugin.awesome.terminal", f"Plugin should be default, got {default}"

    terminal = app_widget_manager.get_default_terminal_id()
    assert terminal == "plugin.awesome.terminal", "Plugin should be terminal default"

    print("✅ Plugin widgets can be defaults")
    return True

def test_priority_competition():
    """Test that priority correctly determines defaults."""
    from viloapp.core.app_widget_manager import app_widget_manager
    from viloapp.core.app_widget_metadata import AppWidgetMetadata, WidgetCategory

    app_widget_manager.clear()

    # Register multiple widgets with different priorities
    class MockWidget:
        pass

    widgets = [
        ("widget.low", 100),   # Low priority
        ("widget.medium", 50), # Medium priority
        ("widget.high", 10),   # High priority (lower number = higher priority)
    ]

    for widget_id, priority in widgets:
        metadata = AppWidgetMetadata(
            widget_id=widget_id,
            display_name=f"Widget {priority}",
            description="Test widget",
            icon="test",
            category=WidgetCategory.TERMINAL,
            widget_class=MockWidget,
            can_be_default=True,
            default_priority=priority,
            default_for_contexts=["test"]
        )
        app_widget_manager.register_widget(metadata)

    # Highest priority (lowest number) should win
    default = app_widget_manager.get_default_widget_id()
    assert default == "widget.high", f"Highest priority should win, got {default}"

    print("✅ Priority system works correctly")
    return True

def test_user_preference_override():
    """Test that user preferences override widget priorities."""
    from viloapp.core.app_widget_manager import app_widget_manager
    from viloapp.core.app_widget_metadata import AppWidgetMetadata, WidgetCategory
    from viloapp.core.settings.app_defaults import (
        set_default_widget_preference,
        set_default_widget_for_context
    )

    # Setup widgets
    app_widget_manager.clear()

    class MockWidget:
        pass

    # High priority widget
    high_priority = AppWidgetMetadata(
        widget_id="widget.high",
        display_name="High Priority",
        description="Test",
        icon="test",
        category=WidgetCategory.TERMINAL,
        widget_class=MockWidget,
        can_be_default=True,
        default_priority=10,
        default_for_contexts=["terminal"]
    )

    # Low priority widget
    low_priority = AppWidgetMetadata(
        widget_id="widget.low",
        display_name="Low Priority",
        description="Test",
        icon="test",
        category=WidgetCategory.TERMINAL,
        widget_class=MockWidget,
        can_be_default=True,
        default_priority=100,
        default_for_contexts=["terminal"]
    )

    app_widget_manager.register_widget(high_priority)
    app_widget_manager.register_widget(low_priority)

    # Without preference, high priority wins
    default = app_widget_manager.get_default_widget_id()
    assert default == "widget.high", "High priority should win without preference"

    # Set user preference for low priority widget
    set_default_widget_preference("widget.low")

    # Now low priority should win due to user preference
    default = app_widget_manager.get_default_widget_id()
    assert default == "widget.low", "User preference should override priority"

    # Test context-specific preference
    set_default_widget_for_context("terminal", "widget.low")
    terminal = app_widget_manager.get_default_terminal_id()
    assert terminal == "widget.low", "Context preference should work"

    print("✅ User preferences override priorities")
    return True

def test_invalid_preference_fallback():
    """Test that invalid preferences fall back gracefully."""
    from viloapp.core.app_widget_manager import app_widget_manager
    from viloapp.core.settings.app_defaults import set_default_widget_preference

    # Register built-in widgets
    from viloapp.core.app_widget_registry import register_builtin_widgets
    app_widget_manager.clear()
    register_builtin_widgets()

    # Set preference for non-existent widget
    set_default_widget_preference("widget.does.not.exist")

    # Should fall back to available widget
    default = app_widget_manager.get_default_widget_id()
    assert default is not None, "Should fall back when preference invalid"
    assert default != "widget.does.not.exist", "Should not use invalid preference"

    print(f"✅ Invalid preference falls back to: {default}")
    return True

def test_performance():
    """Test that default resolution is performant."""
    from viloapp.core.app_widget_manager import app_widget_manager
    from viloapp.core.app_widget_registry import register_builtin_widgets

    app_widget_manager.clear()
    register_builtin_widgets()

    # Measure time for default resolution
    iterations = 1000
    start = time.time()

    for _ in range(iterations):
        _ = app_widget_manager.get_default_widget_id()

    elapsed = time.time() - start
    per_call = (elapsed / iterations) * 1000  # Convert to ms

    print(f"✅ Default resolution: {per_call:.3f}ms per call")
    assert per_call < 10, f"Should be <10ms per call, got {per_call:.3f}ms"

    return True

def test_context_aware_defaults():
    """Test context-aware default selection."""
    from viloapp.core.app_widget_manager import app_widget_manager
    from viloapp.core.app_widget_registry import register_builtin_widgets

    app_widget_manager.clear()
    register_builtin_widgets()

    # Test terminal context
    terminal = app_widget_manager.get_default_widget_id(context="terminal")
    assert terminal == "com.viloapp.terminal", "Terminal context should return terminal widget"

    # Test editor context
    editor = app_widget_manager.get_default_widget_id(context="editor")
    assert editor == "com.viloapp.editor", "Editor context should return editor widget"

    # Test unknown context falls back
    unknown = app_widget_manager.get_default_widget_id(context="unknown")
    assert unknown is not None, "Unknown context should fall back"

    print("✅ Context-aware defaults work")
    return True

def test_widget_type_helpers():
    """Test widget type checking helpers."""
    from viloapp.core.app_widget_manager import app_widget_manager
    from viloapp.core.app_widget_registry import register_builtin_widgets

    app_widget_manager.clear()
    register_builtin_widgets()

    # Test terminal check
    assert app_widget_manager.is_terminal_widget("com.viloapp.terminal"), "Should identify terminal"
    assert not app_widget_manager.is_terminal_widget("com.viloapp.editor"), "Should not identify editor as terminal"

    # Test editor check
    assert app_widget_manager.is_editor_widget("com.viloapp.editor"), "Should identify editor"
    assert not app_widget_manager.is_editor_widget("com.viloapp.terminal"), "Should not identify terminal as editor"

    # Test settings check
    assert app_widget_manager.is_settings_widget("com.viloapp.settings"), "Should identify settings"
    assert app_widget_manager.is_settings_widget("plugin.foo.settings"), "Should identify plugin settings"

    print("✅ Widget type helpers work")
    return True

def test_no_hardcoded_ids_in_core():
    """Verify no hardcoded widget IDs remain in core modules."""
    import os
    import re

    core_paths = [
        "packages/viloapp/src/viloapp/core",
        "packages/viloapp/src/viloapp/models",
        "packages/viloapp/src/viloapp/services"
    ]

    # Patterns that indicate hardcoded widget IDs
    bad_patterns = [
        r'"com\.viloapp\.(terminal|editor|settings|output)"',
        r"'com\.viloapp\.(terminal|editor|settings|output)'",
        r'DEFAULT_WIDGET_ID\s*=\s*["\']',
        r'\bTERMINAL\s*=\s*["\']',
        r'\bEDITOR\s*=\s*["\']',
    ]

    violations = []

    for base_path in core_paths:
        if not os.path.exists(base_path):
            continue

        for root, _, files in os.walk(base_path):
            for file in files:
                if not file.endswith('.py'):
                    continue

                filepath = os.path.join(root, file)

                # Skip migration files and tests
                if 'migration' in filepath or 'test' in filepath:
                    continue

                with open(filepath, 'r') as f:
                    content = f.read()
                    line_num = 0

                    for line in content.split('\n'):
                        line_num += 1
                        for pattern in bad_patterns:
                            if re.search(pattern, line):
                                # Allow certain exceptions
                                if 'fallback' in line.lower() or 'placeholder' in line.lower():
                                    continue
                                if 'migrate' in line.lower():
                                    continue

                                violations.append(f"{filepath}:{line_num}: {line.strip()}")

    if violations:
        print("❌ Found hardcoded widget IDs:")
        for v in violations[:10]:  # Show first 10
            print(f"  {v}")
        return False

    print("✅ No hardcoded widget IDs in core")
    return True

def main():
    """Run comprehensive test suite."""
    print("=" * 60)
    print("Comprehensive Widget System Tests")
    print("=" * 60)

    tests = [
        ("No widgets available", test_no_widgets_available),
        ("Plugin as default", test_plugin_as_default),
        ("Priority competition", test_priority_competition),
        ("User preference override", test_user_preference_override),
        ("Invalid preference fallback", test_invalid_preference_fallback),
        ("Performance", test_performance),
        ("Context-aware defaults", test_context_aware_defaults),
        ("Widget type helpers", test_widget_type_helpers),
        ("No hardcoded IDs", test_no_hardcoded_ids_in_core),
    ]

    failed = []
    for name, test in tests:
        print(f"\nTesting: {name}")
        try:
            if not test():
                failed.append(name)
        except Exception as e:
            print(f"❌ {name} failed: {e}")
            import traceback
            traceback.print_exc()
            failed.append(name)

    print("\n" + "=" * 60)
    if failed:
        print(f"❌ {len(failed)} tests failed:")
        for f in failed:
            print(f"  - {f}")
        return 1
    else:
        print("✅ All comprehensive tests passed!")
        print("The widget system is fully functional and extensible!")
        return 0

if __name__ == "__main__":
    sys.exit(main())