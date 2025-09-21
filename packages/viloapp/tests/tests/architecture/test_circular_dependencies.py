#!/usr/bin/env python3
"""
Test for circular dependencies elimination.

This test verifies that Phase 6 has successfully eliminated all circular
dependencies in the ViloxTerm architecture.
"""

import ast
import os
from pathlib import Path

import pytest


class CircularDependencyChecker:
    """Checks for circular dependencies in the codebase."""

    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.service_files = []
        self.ui_files = []
        self.violations = []

    def collect_files(self):
        """Collect service and UI files."""
        # Service files
        services_dir = self.base_path / "src" / "viloapp" / "services"
        if services_dir.exists():
            self.service_files = list(services_dir.glob("*.py"))

        # UI files
        ui_dir = self.base_path / "src" / "viloapp" / "ui"
        if ui_dir.exists():
            self.ui_files = list(ui_dir.rglob("*.py"))

    def check_service_ui_calls(self):
        """Check if services call UI methods directly."""
        ui_class_patterns = [
            # Direct UI class access
            "QWidget",
            "QTabWidget",
            "QSplitterHandle",
            "QSplitter",
            "SplitPaneWidget",
            "Workspace",
            "MainWindow",
            # UI method calls that shouldn't be in services
            ".split_horizontal",
            ".split_vertical",
            ".close_pane",
            ".toggle_pane_numbers",
            ".get_current_split_widget",
            ".setCurrentIndex",
            ".addTab",
            ".removeTab",
            # Widget model direct access
            "widget.model",
            ".model.show_pane_numbers",
            ".model.change_pane_type",
        ]

        for service_file in self.service_files:
            try:
                with open(service_file, encoding="utf-8") as f:
                    content = f.read()

                    for pattern in ui_class_patterns:
                        if pattern in content:
                            # Check if it's in actual code, not comments or strings
                            lines = content.split("\n")
                            for i, line in enumerate(lines, 1):
                                if pattern in line and not line.strip().startswith("#"):
                                    # Check if it's in a string literal
                                    try:
                                        ast.parse(line.strip())
                                        # If we can parse it and it contains the pattern, it's likely code
                                        if pattern in line:
                                            self.violations.append(
                                                {
                                                    "file": str(service_file),
                                                    "line": i,
                                                    "pattern": pattern,
                                                    "content": line.strip(),
                                                    "type": "service_ui_call",
                                                }
                                            )
                                    except Exception:
                                        # If we can't parse the line, still flag it if it contains the pattern
                                        # but is not a comment
                                        if not line.strip().startswith("#") and pattern in line:
                                            self.violations.append(
                                                {
                                                    "file": str(service_file),
                                                    "line": i,
                                                    "pattern": pattern,
                                                    "content": line.strip(),
                                                    "type": "potential_service_ui_call",
                                                }
                                            )

            except Exception as e:
                print(f"Error checking {service_file}: {e}")

    def check_event_bus_usage(self):
        """Verify that services use event bus instead of direct UI calls."""
        event_patterns = [
            "event_bus.publish",
            "request_pane_close",
            "request_pane_numbers_toggle",
            "EventTypes.",
        ]

        services_using_events = 0
        for service_file in self.service_files:
            try:
                with open(service_file, encoding="utf-8") as f:
                    content = f.read()
                    if any(pattern in content for pattern in event_patterns):
                        services_using_events += 1
            except Exception as e:
                print(f"Error checking event usage in {service_file}: {e}")

        return services_using_events

    def check_ui_request_handlers(self):
        """Verify that UI components handle requests from services."""
        request_patterns = ["_handle_ui_request", "ui.request", "ui.response"]

        ui_files_with_handlers = 0
        for ui_file in self.ui_files:
            try:
                with open(ui_file, encoding="utf-8") as f:
                    content = f.read()
                    if any(pattern in content for pattern in request_patterns):
                        ui_files_with_handlers += 1
            except Exception as e:
                print(f"Error checking request handlers in {ui_file}: {e}")

        return ui_files_with_handlers


def test_no_service_ui_circular_dependencies():
    """Test that services don't call UI methods directly."""
    base_path = Path(__file__).parent.parent.parent.parent
    checker = CircularDependencyChecker(str(base_path))
    checker.collect_files()
    checker.check_service_ui_calls()

    # Report violations
    if checker.violations:
        violation_report = "\n".join(
            [
                f"VIOLATION: {v['file']}:{v['line']} - {v['pattern']} in: {v['content']}"
                for v in checker.violations
            ]
        )
        pytest.fail(
            f"Found {len(checker.violations)} circular dependency violations:\n{violation_report}"
        )


def test_event_bus_implementation():
    """Test that event bus is properly implemented and used."""
    base_path = Path(__file__).parent.parent.parent.parent
    checker = CircularDependencyChecker(str(base_path))
    checker.collect_files()

    services_using_events = checker.check_event_bus_usage()
    ui_files_with_handlers = checker.check_ui_request_handlers()

    # At least the workspace_pane_manager should use events
    assert (
        services_using_events >= 1
    ), f"Expected at least 1 service to use event bus, found {services_using_events}"

    # At least the workspace.py should handle requests
    assert (
        ui_files_with_handlers >= 1
    ), f"Expected at least 1 UI file to handle requests, found {ui_files_with_handlers}"


def test_one_way_data_flow():
    """Test that data flow is strictly one-way: UI → Command → Service → Model → Event → UI."""
    base_path = Path(__file__).parent.parent.parent.parent
    checker = CircularDependencyChecker(str(base_path))
    checker.collect_files()

    # Check that services don't import UI modules
    ui_imports = [
        "from viloapp.ui",
        "import viloapp.ui",
        "from PySide6.QtWidgets",  # Services shouldn't directly use Qt widgets
    ]

    violations = []
    for service_file in checker.service_files:
        try:
            with open(service_file, encoding="utf-8") as f:
                content = f.read()
                for ui_import in ui_imports:
                    if ui_import in content:
                        lines = content.split("\n")
                        for i, line in enumerate(lines, 1):
                            if ui_import in line and not line.strip().startswith("#"):
                                violations.append(
                                    {
                                        "file": str(service_file),
                                        "line": i,
                                        "import": ui_import,
                                        "content": line.strip(),
                                    }
                                )
        except Exception as e:
            print(f"Error checking imports in {service_file}: {e}")

    if violations:
        violation_report = "\n".join(
            [
                f"UI IMPORT IN SERVICE: {v['file']}:{v['line']} - {v['import']} in: {v['content']}"
                for v in violations
            ]
        )
        pytest.fail(
            f"Found {len(violations)} UI import violations in services:\n{violation_report}"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
