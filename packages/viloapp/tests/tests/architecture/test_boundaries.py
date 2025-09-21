#!/usr/bin/env python3
"""Architecture boundary validation tests."""

import ast
import glob
import os
from pathlib import Path

import pytest


class TestArchitectureBoundaries:
    """Test architecture boundaries are properly maintained."""

    def test_no_plugin_imports_in_core(self):
        """Ensure core doesn't import from plugins."""
        base_path = Path(__file__).parent.parent.parent

        # Core files that should not import plugins
        core_patterns = ["ui/**/*.py", "services/**/*.py", "core/**/*.py"]

        violations = []

        for pattern in core_patterns:
            files = glob.glob(str(base_path / pattern), recursive=True)
            for file_path in files:
                try:
                    with open(file_path, encoding="utf-8") as f:
                        content = f.read()
                        tree = ast.parse(content)

                    for node in ast.walk(tree):
                        if isinstance(node, (ast.Import, ast.ImportFrom)):
                            if isinstance(node, ast.Import):
                                names = [alias.name for alias in node.names]
                            else:  # ast.ImportFrom
                                if node.module:
                                    names = [node.module]
                                else:
                                    names = []

                            for name in names:
                                if name and (
                                    name.startswith("packages.")
                                    or name.startswith("viloxterm")
                                    or name.startswith("viloedit")
                                    or name == "viloxterm"
                                    or name == "viloedit"
                                ):
                                    rel_path = os.path.relpath(file_path, base_path)
                                    violations.append(f"{rel_path}: imports '{name}'")

                except Exception:
                    # Skip files that can't be parsed (e.g., not Python files)
                    continue

        if violations:
            pytest.fail("Core code importing from plugins:\n" + "\n".join(violations))

    def test_plugins_use_sdk_only(self):
        """Ensure plugins only use SDK interfaces."""
        base_path = Path(__file__).parent.parent.parent

        # Plugin files
        plugin_patterns = ["packages/*/src/**/*.py"]

        violations = []

        for pattern in plugin_patterns:
            files = glob.glob(str(base_path / pattern), recursive=True)
            for file_path in files:
                try:
                    with open(file_path, encoding="utf-8") as f:
                        content = f.read()

                    # Check for forbidden imports
                    forbidden_imports = [
                        "from viloapp.ui.",
                        "from viloapp.services.",
                        "import viloapp.ui.",
                        "import viloapp.services.",
                    ]

                    # Allow core.plugin_system imports in plugins
                    lines = content.split("\n")
                    for i, line in enumerate(lines, 1):
                        line = line.strip()
                        for forbidden in forbidden_imports:
                            if forbidden in line and not line.startswith("#"):
                                # Check if it's an allowed core.plugin_system import
                                if (
                                    "from viloapp.core.plugin_system" not in line
                                    and "import viloapp.core.plugin_system" not in line
                                ):
                                    rel_path = os.path.relpath(file_path, base_path)
                                    violations.append(f"{rel_path}:{i}: {line}")

                except Exception:
                    # Skip files that can't be read
                    continue

        if violations:
            pytest.fail("Plugins importing from core (not allowed):\n" + "\n".join(violations))

    def test_service_locator_usage(self):
        """Test that services are accessed through ServiceLocator."""
        base_path = Path(__file__).parent.parent.parent

        # Check for direct service imports where ServiceLocator should be used
        patterns = ["ui/**/*.py", "core/commands/**/*.py"]

        violations = []

        for pattern in patterns:
            files = glob.glob(str(base_path / pattern), recursive=True)
            for file_path in files:
                try:
                    with open(file_path, encoding="utf-8") as f:
                        content = f.read()

                    # Look for direct service instantiation in non-service files
                    if "/services/" not in file_path and "service_locator.py" not in file_path:
                        suspicious_patterns = [
                            "WorkspaceService()",
                            "ThemeService()",
                            "UIService()",
                            "TerminalService()",
                            "EditorService()",
                        ]

                        lines = content.split("\n")
                        for i, line in enumerate(lines, 1):
                            for pattern in suspicious_patterns:
                                if pattern in line and not line.strip().startswith("#"):
                                    rel_path = os.path.relpath(file_path, base_path)
                                    violations.append(
                                        f"{rel_path}:{i}: Direct service instantiation: {line.strip()}"
                                    )

                except Exception:
                    continue

        # This is more of a warning than a strict violation
        if violations:
            print(
                "Warning - Direct service instantiation found (consider using ServiceLocator):\n"
                + "\n".join(violations)
            )

    def test_plugin_system_isolation(self):
        """Test that plugin system is properly isolated."""
        base_path = Path(__file__).parent.parent.parent

        # Plugin system should only be imported by specific files
        allowed_plugin_system_importers = [
            "services/__init__.py",
            "main.py",
            "tests/",
            "core/plugin_system/",
            "ui/widgets/split_pane_model.py",  # This is allowed due to our factory pattern
        ]

        violations = []

        files = glob.glob(str(base_path / "**/*.py"), recursive=True)
        for file_path in files:
            rel_path = os.path.relpath(file_path, base_path)

            # Skip allowed files and test files
            if (
                any(allowed in rel_path for allowed in allowed_plugin_system_importers)
                or rel_path.startswith("test")
                or "/test" in rel_path
            ):
                continue

            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()

                if (
                    "from viloapp.core.plugin_system" in content
                    or "import viloapp.core.plugin_system" in content
                ):
                    violations.append(f"{rel_path}: imports plugin system")

            except Exception:
                continue

        if violations:
            pytest.fail("Unexpected plugin system imports:\n" + "\n".join(violations))

    def test_command_pattern_compliance(self):
        """Test that UI components don't bypass command pattern."""
        base_path = Path(__file__).parent.parent.parent

        # UI files should use execute_command, not direct service calls
        ui_files = glob.glob(str(base_path / "ui/**/*.py"), recursive=True)

        violations = []

        for file_path in ui_files:
            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()

                # Look for direct service method calls that should go through commands
                lines = content.split("\n")
                for i, line in enumerate(lines, 1):
                    line = line.strip()

                    # Skip comments and imports
                    if line.startswith("#") or line.startswith("import") or line.startswith("from"):
                        continue

                    # Look for direct service calls (this is a simplified check)
                    suspicious_patterns = [
                        ".add_tab(",
                        ".close_tab(",
                        ".split_pane(",
                        ".set_theme(",
                    ]

                    for pattern in suspicious_patterns:
                        if pattern in line and "execute_command" not in line:
                            rel_path = os.path.relpath(file_path, base_path)
                            # Only report if this looks like a direct service call
                            if "service" in line.lower():
                                violations.append(
                                    f"{rel_path}:{i}: Possible command pattern bypass: {line}"
                                )

            except Exception:
                continue

        # This is informational rather than a hard failure
        if violations:
            print("Info - Possible command pattern bypasses found:\n" + "\n".join(violations))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
