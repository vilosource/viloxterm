#!/usr/bin/env python3
"""
Verification script for command system centralization.

This script checks that all UI actions have been properly centralized
through the command system and reports any remaining direct connections.
"""

import re
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def find_direct_connections(file_path: Path) -> list[dict[str, str]]:
    """Find remaining direct signal connections in a file."""
    violations = []

    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
            lines = content.split("\n")

        # Patterns that indicate direct connections (not through commands)
        violation_patterns = [
            # Direct slot connections
            (
                r"\.connect\s*\(\s*lambda.*?self\.\w+\([^)]*\)",
                "Direct lambda connection",
            ),
            (r"\.connect\s*\(\s*self\.\w+\)", "Direct method connection"),
            # Signal emissions (should go through commands in most cases)
            (r"\.emit\(\)", "Signal emission without command"),
            # Direct widget method calls in UI event handlers
            (
                r"lambda.*?:\s*self\.(close_tab|duplicate_tab|rename_tab)",
                "Direct tab method call",
            ),
            (
                r"lambda.*?:\s*self\.(split_horizontal|split_vertical|close_pane)",
                "Direct pane method call",
            ),
        ]

        for line_num, line in enumerate(lines, 1):
            for pattern, description in violation_patterns:
                if re.search(pattern, line):
                    # Skip if the line contains execute_command (already converted)
                    if "execute_command" not in line:
                        violations.append(
                            {
                                "file": str(file_path),
                                "line": line_num,
                                "content": line.strip(),
                                "type": description,
                            }
                        )

    except Exception as e:
        print(f"Error reading {file_path}: {e}")

    return violations


def find_command_usage(file_path: Path) -> list[dict[str, str]]:
    """Find command usage in a file."""
    commands = []

    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
            lines = content.split("\n")

        # Find execute_command calls
        for line_num, line in enumerate(lines, 1):
            if "execute_command(" in line:
                # Extract command ID
                match = re.search(r'execute_command\(["\']([^"\']+)["\']', line)
                if match:
                    commands.append(
                        {
                            "file": str(file_path),
                            "line": line_num,
                            "command_id": match.group(1),
                            "content": line.strip(),
                        }
                    )

    except Exception as e:
        print(f"Error reading {file_path}: {e}")

    return commands


def verify_command_centralization():
    """Main verification function."""
    ui_dir = project_root / "ui"

    # Files to check for violations
    ui_files = [
        ui_dir / "activity_bar.py",
        ui_dir / "workspace_simple.py",
        ui_dir / "widgets" / "pane_header.py",
        ui_dir / "widgets" / "split_pane_widget.py",
    ]

    print("🔍 Verifying Command System Centralization")
    print("=" * 50)

    all_violations = []
    all_commands = []

    # Check each file
    for file_path in ui_files:
        if file_path.exists():
            violations = find_direct_connections(file_path)
            commands = find_command_usage(file_path)

            all_violations.extend(violations)
            all_commands.extend(commands)

            print(f"\n📁 {file_path.relative_to(project_root)}")
            print(f"   ✅ Commands found: {len(commands)}")
            print(f"   ⚠️  Violations found: {len(violations)}")

            if violations:
                for v in violations:
                    print(f"      Line {v['line']}: {v['type']}")
                    print(f"        {v['content']}")

    # Summary
    print("\n📊 Summary")
    print(f"   Total commands implemented: {len(all_commands)}")
    print(f"   Total violations remaining: {len(all_violations)}")

    # Command breakdown
    if all_commands:
        print("\n✅ Commands Successfully Implemented:")
        command_counts = {}
        for cmd in all_commands:
            cmd_id = cmd["command_id"]
            command_counts[cmd_id] = command_counts.get(cmd_id, 0) + 1

        for cmd_id, count in sorted(command_counts.items()):
            print(f"   • {cmd_id} ({count} uses)")

    # Violation breakdown
    if all_violations:
        print("\n⚠️ Remaining Violations:")
        violation_types = {}
        for v in all_violations:
            v_type = v["type"]
            violation_types[v_type] = violation_types.get(v_type, 0) + 1

        for v_type, count in sorted(violation_types.items()):
            print(f"   • {v_type}: {count} instances")

    # Check if commands are registered
    print("\n🔧 Checking Command Registration...")
    try:
        from core.commands.registry import command_registry

        registered_commands = command_registry.get_all_commands()
        print(f"   Commands in registry: {len(registered_commands)}")

        for cmd in registered_commands:
            print(f"   • {cmd.id}: {cmd.title}")

    except Exception as e:
        print(f"   ❌ Error checking command registry: {e}")

    # Final assessment
    print("\n🎯 Final Assessment:")
    if len(all_violations) == 0:
        print("   🎉 SUCCESS: All UI actions are centralized through commands!")
    elif len(all_violations) < 5:
        print(f"   ✅ GOOD: Only {len(all_violations)} minor violations remaining")
    else:
        print(f"   ⚠️ NEEDS WORK: {len(all_violations)} violations need attention")

    return len(all_violations) == 0


if __name__ == "__main__":
    success = verify_command_centralization()
    sys.exit(0 if success else 1)
