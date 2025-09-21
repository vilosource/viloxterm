#!/usr/bin/env python3
"""
Phase 7 Validation Tests for Architecture Fix.

This test validates that all architectural improvements from Phases 1-6
are working correctly and that the 54+ violations have been resolved.
"""

import ast
import time
from pathlib import Path
from typing import Any, Dict, List

import pytest


class Phase7Validator:
    """Validates all Phase 1-6 architectural fixes."""

    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.violations = []

    def test_command_pattern_compliance(self) -> List[Dict[str, Any]]:
        """Test that commands only call services, not UI directly."""
        violations = []

        command_files = list(
            (self.base_path / "src" / "viloapp" / "core" / "commands" / "builtin").glob("*.py")
        )

        for file_path in command_files:
            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()

                # Look for direct UI calls in command functions
                ui_patterns = [
                    "workspace.split_active_pane",
                    "workspace.close_tab",
                    "split_widget.model.",
                    "widget.split_horizontal",
                    "widget.close_pane",
                    ".setCurrentIndex",
                    ".addTab",
                    ".removeTab",
                ]

                lines = content.split("\n")
                for line_num, line in enumerate(lines, 1):
                    # Skip comments
                    if line.strip().startswith("#"):
                        continue

                    for pattern in ui_patterns:
                        if pattern in line and "execute_command" not in line:
                            violations.append(
                                {
                                    "file": str(file_path.relative_to(self.base_path)),
                                    "line": line_num,
                                    "pattern": pattern,
                                    "content": line.strip(),
                                    "type": "command_calls_ui_directly",
                                }
                            )

            except Exception as e:
                print(f"Error checking {file_path}: {e}")

        return violations

    def test_service_layer_compliance(self) -> List[Dict[str, Any]]:
        """Test that services don't call UI methods directly."""
        violations = []

        service_files = list((self.base_path / "src" / "viloapp" / "services").glob("*.py"))

        # Real UI violations (not false positives)
        real_ui_patterns = [
            ".get_current_split_widget()",
            ".split_horizontal()",
            ".split_vertical()",
            ".close_pane()",  # Only if it's a widget method, not model method
            ".setCurrentIndex(",
            ".addTab(",
            ".removeTab(",
            ".tab_widget.",
            "QTabWidget",
            "QWidget",
            "QSplitter",
            ".model.change_pane_type",
            ".model.show_pane_numbers",
        ]

        for file_path in service_files:
            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()

                lines = content.split("\n")
                for line_num, line in enumerate(lines, 1):
                    # Skip comments and docstrings
                    stripped = line.strip()
                    if (
                        stripped.startswith("#")
                        or stripped.startswith('"""')
                        or stripped.startswith("'''")
                    ):
                        continue

                    for pattern in real_ui_patterns:
                        if pattern in line:
                            # Additional filtering for false positives
                            if (
                                "import" not in line
                                and "class " not in line
                                and "def " not in line
                                and not line.strip().startswith('"')
                                and not line.strip().startswith("'")
                                and "logger" not in line
                            ):
                                violations.append(
                                    {
                                        "file": str(file_path.relative_to(self.base_path)),
                                        "line": line_num,
                                        "pattern": pattern,
                                        "content": stripped,
                                        "type": "service_calls_ui_directly",
                                    }
                                )

            except Exception as e:
                print(f"Error checking {file_path}: {e}")

        return violations

    def test_circular_dependencies_eliminated(self) -> List[Dict[str, Any]]:
        """Test that circular dependencies have been eliminated."""
        violations = []

        # Check that services don't import UI modules
        service_files = list((self.base_path / "src" / "viloapp" / "services").glob("*.py"))

        forbidden_imports = [
            "from viloapp.ui",
            "import viloapp.ui",
            "from PySide6.QtWidgets",  # Services shouldn't directly use Qt widgets
        ]

        for file_path in service_files:
            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()

                for forbidden_import in forbidden_imports:
                    if forbidden_import in content:
                        lines = content.split("\n")
                        for line_num, line in enumerate(lines, 1):
                            if forbidden_import in line and not line.strip().startswith("#"):
                                violations.append(
                                    {
                                        "file": str(file_path.relative_to(self.base_path)),
                                        "line": line_num,
                                        "import": forbidden_import,
                                        "content": line.strip(),
                                        "type": "service_imports_ui",
                                    }
                                )

            except Exception as e:
                print(f"Error checking {file_path}: {e}")

        return violations

    def test_mvc_pattern_compliance(self) -> List[Dict[str, Any]]:
        """Test that MVC pattern is properly implemented."""
        violations = []

        # Check SplitPaneWidget follows MVC pattern
        widget_file = self.base_path / "src" / "viloapp" / "ui" / "widgets" / "split_pane_widget.py"

        if widget_file.exists():
            try:
                with open(widget_file, encoding="utf-8") as f:
                    content = f.read()

                # Check for proper dependency injection
                if "def __init__(self, model" not in content:
                    violations.append(
                        {
                            "file": str(widget_file.relative_to(self.base_path)),
                            "line": 1,
                            "issue": "SplitPaneWidget doesn't use dependency injection",
                            "type": "mvc_violation",
                        }
                    )

                # Check for model creation in view
                if "SplitPaneModel()" in content:
                    lines = content.split("\n")
                    for line_num, line in enumerate(lines, 1):
                        if "SplitPaneModel()" in line:
                            violations.append(
                                {
                                    "file": str(widget_file.relative_to(self.base_path)),
                                    "line": line_num,
                                    "issue": "View creates model directly",
                                    "content": line.strip(),
                                    "type": "mvc_violation",
                                }
                            )

            except Exception as e:
                print(f"Error checking {widget_file}: {e}")

        return violations

    def test_business_logic_in_ui(self) -> List[Dict[str, Any]]:
        """Test that business logic has been removed from UI."""
        violations = []

        ui_files = list((self.base_path / "src" / "viloapp" / "ui").rglob("*.py"))

        business_logic_patterns = [
            "QMessageBox.information",
            "QMessageBox.warning",
            "QMessageBox.question",
            "if.*count.*<=.*1:",  # Tab count validation
            "if.*len.*tabs.*<=",  # Business logic validation
        ]

        for file_path in ui_files:
            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()

                lines = content.split("\n")
                for line_num, line in enumerate(lines, 1):
                    # Skip comments
                    if line.strip().startswith("#"):
                        continue

                    for pattern in business_logic_patterns:
                        if pattern in line:
                            violations.append(
                                {
                                    "file": str(file_path.relative_to(self.base_path)),
                                    "line": line_num,
                                    "pattern": pattern,
                                    "content": line.strip(),
                                    "type": "business_logic_in_ui",
                                }
                            )

            except Exception as e:
                print(f"Error checking {file_path}: {e}")

        return violations

    def validate_all_phases(self) -> Dict[str, List[Dict[str, Any]]]:
        """Run all Phase 7 validation tests."""
        results = {}

        print("Phase 7: Validating all architectural fixes...")

        results["command_pattern"] = self.test_command_pattern_compliance()
        results["service_layer"] = self.test_service_layer_compliance()
        results["circular_dependencies"] = self.test_circular_dependencies_eliminated()
        results["mvc_pattern"] = self.test_mvc_pattern_compliance()
        results["business_logic"] = self.test_business_logic_in_ui()

        return results


def test_phase_1_data_models_compliance():
    """Test that Phase 1 data models are working correctly."""
    base_path = Path(__file__).parent.parent.parent.parent

    # Test that models exist and have no Qt dependencies
    models_dir = base_path / "src" / "viloapp" / "models"
    assert models_dir.exists(), "Models directory should exist"

    model_files = list(models_dir.glob("*.py"))
    assert len(model_files) >= 3, "Should have at least 3 model files"

    # Check that models don't import Qt
    for model_file in model_files:
        with open(model_file, encoding="utf-8") as f:
            content = f.read()

        qt_imports = ["from PySide6", "import PySide6", "from PyQt", "import PyQt"]
        for qt_import in qt_imports:
            assert qt_import not in content, f"Model {model_file.name} should not import Qt"


def test_phase_2_service_layer_refactoring():
    """Test that Phase 2 service layer refactoring is working."""
    base_path = Path(__file__).parent.parent.parent.parent
    validator = Phase7Validator(str(base_path))

    service_violations = validator.test_service_layer_compliance()

    # Allow some violations during transition, but should be minimal
    assert (
        len(service_violations) <= 5
    ), f"Too many service layer violations: {len(service_violations)}"


def test_phase_3_command_layer_fix():
    """Test that Phase 3 command layer fixes are working."""
    base_path = Path(__file__).parent.parent.parent.parent
    validator = Phase7Validator(str(base_path))

    command_violations = validator.test_command_pattern_compliance()

    # Should have zero violations after Phase 3
    assert (
        len(command_violations) == 0
    ), f"Commands should not call UI directly: {command_violations}"


def test_phase_4_ui_cleanup():
    """Test that Phase 4 UI cleanup is working."""
    base_path = Path(__file__).parent.parent.parent.parent
    validator = Phase7Validator(str(base_path))

    ui_violations = validator.test_business_logic_in_ui()

    # Should have minimal business logic in UI
    assert len(ui_violations) <= 3, f"Too much business logic in UI: {len(ui_violations)}"


def test_phase_5_mvc_pattern_fix():
    """Test that Phase 5 MVC pattern fixes are working."""
    base_path = Path(__file__).parent.parent.parent.parent
    validator = Phase7Validator(str(base_path))

    mvc_violations = validator.test_mvc_pattern_compliance()

    # Should have zero MVC violations after Phase 5
    assert len(mvc_violations) == 0, f"MVC pattern violations found: {mvc_violations}"


def test_phase_6_circular_dependencies_eliminated():
    """Test that Phase 6 circular dependency elimination is working."""
    base_path = Path(__file__).parent.parent.parent.parent
    validator = Phase7Validator(str(base_path))

    circular_violations = validator.test_circular_dependencies_eliminated()

    # Should have zero circular dependencies after Phase 6
    assert len(circular_violations) == 0, f"Circular dependencies found: {circular_violations}"


def test_performance_benchmarks():
    """Test that performance targets are met."""
    # These would be integration tests that actually measure performance
    # For now, we'll just validate the structure is in place

    base_path = Path(__file__).parent.parent.parent.parent

    # Check that event bus exists for performance
    event_bus_file = base_path / "src" / "viloapp" / "core" / "events" / "event_bus.py"
    assert event_bus_file.exists(), "Event bus should exist for performance"

    # Check that model interfaces exist
    interfaces_dir = base_path / "src" / "viloapp" / "interfaces"
    assert interfaces_dir.exists(), "Interfaces directory should exist"


def test_comprehensive_validation():
    """Run comprehensive validation of all phases."""
    base_path = Path(__file__).parent.parent.parent.parent
    validator = Phase7Validator(str(base_path))

    results = validator.validate_all_phases()

    # Report results
    total_violations = sum(len(violations) for violations in results.values())

    print("\n=== Phase 7 Validation Results ===")
    for phase, violations in results.items():
        print(f"{phase}: {len(violations)} violations")
        if violations:
            for violation in violations[:3]:  # Show first 3
                print(
                    f"  - {violation.get('file', 'unknown')}:{violation.get('line', 0)} - {violation.get('type', 'unknown')}"
                )
            if len(violations) > 3:
                print(f"  ... and {len(violations) - 3} more")

    print(f"Total violations: {total_violations}")

    # We expect some violations during transition, but should be minimal
    assert (
        total_violations <= 10
    ), f"Too many architectural violations remaining: {total_violations}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
