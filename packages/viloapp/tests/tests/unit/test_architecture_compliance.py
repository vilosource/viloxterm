#!/usr/bin/env python3
"""
Architecture Compliance Tests

These tests ensure our MVC patterns remain intact and prevent future violations.
They automatically detect architecture violations, ensuring commands always use
services and never access UI directly.

Key Principles Enforced:
1. Commands MUST use services (never direct UI access)
2. Commands MUST return CommandResult objects
3. Commands MUST handle service unavailability gracefully
4. UI status messages MUST go through UIService
5. Commands MUST use proper error handling patterns
"""

import ast
import re
from pathlib import Path
from typing import Dict, List
from unittest.mock import Mock

import pytest

from viloapp.core.commands.base import CommandContext, CommandResult
from viloapp.services.state_service import StateService
from viloapp.services.ui_service import UIService
from viloapp.services.workspace_service import WorkspaceService


class TestArchitectureCompliance:
    """Test suite for architecture compliance verification."""

    @pytest.fixture
    def command_files(self) -> List[Path]:
        """Get all command files in the builtin directory."""
        command_dir = Path("core/commands/builtin")
        return list(command_dir.glob("*.py"))

    @pytest.fixture
    def forbidden_ui_patterns(self) -> List[str]:
        """Patterns that indicate direct UI access in commands."""
        return [
            # Direct widget access
            r"workspace\.tab_widget",
            r"workspace\.tab_bar",
            r"main_window\.status_bar",
            r"main_window\.workspace",
            r"context\.workspace\.tab_widget",
            r"context\.main_window\.status_bar",
            # Direct QMessageBox usage
            r"QMessageBox\.(?:information|warning|critical|question)",
            # Direct UI component imports in command files
            r"from ui\.",
            r"import.*ui\.",
            # Direct Qt widget operations (should use services)
            r"\.setTabText\(",
            r"\.tabText\(",
            r"\.currentIndex\(",
            r"\.setCurrentIndex\(",
            # Direct focus/visibility operations
            r"\.setFocus\(",
            r"\.setVisible\(",
            r"\.show\(",
            r"\.hide\(",
        ]

    @pytest.fixture
    def required_service_patterns(self) -> List[str]:
        """Patterns that commands should use for proper service delegation."""
        return [
            r"context\.get_service\(",
            r"WorkspaceService",
            r"UIService",
            r"StateService",
            r"TerminalService",
        ]

    def test_no_direct_ui_access_in_commands(self, command_files, forbidden_ui_patterns):
        """
        Scan command files for direct UI access patterns.

        This is the primary test that prevents MVC violations by ensuring
        commands never access UI components directly.
        """
        violations = []

        for file_path in command_files:
            if file_path.name == "__init__.py":
                continue

            try:
                content = file_path.read_text(encoding="utf-8")

                for pattern in forbidden_ui_patterns:
                    matches = re.finditer(pattern, content, re.MULTILINE)
                    for match in matches:
                        # Get line number for better error reporting
                        line_num = content[: match.start()].count("\n") + 1
                        line_content = content.split("\n")[line_num - 1].strip()

                        violations.append(
                            {
                                "file": str(file_path),
                                "line": line_num,
                                "pattern": pattern,
                                "content": line_content,
                                "violation_type": "direct_ui_access",
                            }
                        )

            except Exception as e:
                violations.append(
                    {
                        "file": str(file_path),
                        "error": f"Failed to read file: {e}",
                        "violation_type": "file_error",
                    }
                )

        if violations:
            violation_report = self._format_violation_report(violations)
            pytest.fail(f"Architecture violations found:\n{violation_report}")

    def test_commands_use_service_layer(self, command_files):
        """
        Verify that commands use the service layer properly.

        Commands should get services via context.get_service() and handle
        service unavailability gracefully.
        """
        violations = []

        for file_path in command_files:
            if file_path.name == "__init__.py":
                continue

            try:
                content = file_path.read_text(encoding="utf-8")

                # Check for command functions
                if "@command(" in content or "def.*_command(" in content:
                    # Must have service usage
                    if "context.get_service(" not in content:
                        violations.append(
                            {
                                "file": str(file_path),
                                "violation_type": "missing_service_usage",
                                "description": "Command file contains commands but no service usage",
                            }
                        )

                    # Must handle service unavailability
                    if (
                        "Service not available" not in content
                        and "service.*not.*available" not in content
                    ):
                        violations.append(
                            {
                                "file": str(file_path),
                                "violation_type": "missing_service_error_handling",
                                "description": "Command file does not handle service unavailability",
                            }
                        )

            except Exception as e:
                violations.append(
                    {
                        "file": str(file_path),
                        "error": f"Failed to analyze file: {e}",
                        "violation_type": "analysis_error",
                    }
                )

        if violations:
            violation_report = self._format_violation_report(violations)
            pytest.fail(f"Service layer violations found:\n{violation_report}")

    def test_commands_return_commandresult(self, command_files):
        """
        Verify that all command functions return CommandResult objects.

        This ensures consistent error handling and result propagation.
        """
        violations = []

        for file_path in command_files:
            if file_path.name == "__init__.py":
                continue

            try:
                content = file_path.read_text(encoding="utf-8")
                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Check if this is a command function
                        if node.name.endswith("_command") or any(
                            (
                                decorator.id == "command"
                                if isinstance(decorator, ast.Name)
                                else getattr(decorator.func, "id", None) == "command"
                            )
                            for decorator in node.decorator_list
                            if hasattr(decorator, "id") or hasattr(decorator, "func")
                        ):

                            # Check return type annotation
                            if node.returns:
                                if not (
                                    isinstance(node.returns, ast.Name)
                                    and node.returns.id == "CommandResult"
                                ):
                                    violations.append(
                                        {
                                            "file": str(file_path),
                                            "function": node.name,
                                            "line": node.lineno,
                                            "violation_type": "incorrect_return_type",
                                            "description": "Command function should return CommandResult",
                                        }
                                    )

                            # Check for CommandResult usage in function body
                            has_command_result = False
                            for body_node in ast.walk(node):
                                if (
                                    isinstance(body_node, ast.Name)
                                    and body_node.id == "CommandResult"
                                ):
                                    has_command_result = True
                                    break

                            if not has_command_result:
                                violations.append(
                                    {
                                        "file": str(file_path),
                                        "function": node.name,
                                        "line": node.lineno,
                                        "violation_type": "missing_commandresult",
                                        "description": "Command function does not use CommandResult",
                                    }
                                )

            except Exception as e:
                violations.append(
                    {
                        "file": str(file_path),
                        "error": f"Failed to parse file: {e}",
                        "violation_type": "parse_error",
                    }
                )

        if violations:
            violation_report = self._format_violation_report(violations)
            pytest.fail(f"CommandResult violations found:\n{violation_report}")

    def test_forbidden_imports_in_commands(self, command_files):
        """
        Verify command files don't import UI components directly.

        Commands should only import services and command-related modules.
        """
        forbidden_imports = [
            "from viloapp.ui.",
            "from viloapp.ui.widgets",
            "from viloapp.ui.main_window",
            "from viloapp.ui.workspace",
            "import viloapp.ui.",
            "from PySide6.QtWidgets import QMessageBox",
        ]

        allowed_ui_imports = [
            "from viloapp.ui.widgets.widget_registry import WidgetType",  # Allowed for type references
        ]

        violations = []

        for file_path in command_files:
            if file_path.name == "__init__.py":
                continue

            try:
                content = file_path.read_text(encoding="utf-8")
                lines = content.split("\n")

                for line_num, line in enumerate(lines, 1):
                    line = line.strip()

                    # Skip allowed imports
                    if any(allowed in line for allowed in allowed_ui_imports):
                        continue

                    # Check for forbidden imports
                    for forbidden in forbidden_imports:
                        if forbidden in line:
                            violations.append(
                                {
                                    "file": str(file_path),
                                    "line": line_num,
                                    "content": line,
                                    "violation_type": "forbidden_import",
                                    "description": f"Forbidden import: {forbidden}",
                                }
                            )

            except Exception as e:
                violations.append(
                    {
                        "file": str(file_path),
                        "error": f"Failed to check imports: {e}",
                        "violation_type": "import_check_error",
                    }
                )

        if violations:
            violation_report = self._format_violation_report(violations)
            pytest.fail(f"Import violations found:\n{violation_report}")

    def test_workspace_service_has_required_methods(self):
        """
        Ensure WorkspaceService has all necessary methods that commands expect.

        This prevents runtime errors when commands try to call service methods.
        """
        required_methods = [
            "duplicate_tab",
            "close_tabs_to_right",
            "close_other_tabs",
            "rename_tab",
            "get_current_widget",
            "get_current_split_widget",
            "get_workspace",
            "add_terminal_tab",
            "add_editor_tab",
            "close_tab",
            "get_current_tab_index",
        ]

        service = WorkspaceService()
        missing_methods = []

        for method_name in required_methods:
            if not hasattr(service, method_name):
                missing_methods.append(method_name)
            elif not callable(getattr(service, method_name)):
                missing_methods.append(f"{method_name} (not callable)")

        assert not missing_methods, f"WorkspaceService missing required methods: {missing_methods}"

    def test_service_error_handling_patterns(self):
        """
        Test that commands handle service unavailability correctly.

        All commands should gracefully handle cases where services are unavailable.
        """
        # Test with mock context that returns None for all services
        mock_context = Mock(spec=CommandContext)
        mock_context.get_service.return_value = None
        mock_context.args = {}

        # Import and test a few representative commands
        try:
            from viloapp.core.commands.builtin.tab_commands import duplicate_tab_command

            result = duplicate_tab_command(mock_context)
            assert isinstance(result, CommandResult)
            assert not result.success
            assert "not available" in result.error.lower()
        except ImportError:
            pytest.skip("tab_commands not available")

        try:
            from viloapp.core.commands.builtin.file_commands import save_state_command

            result = save_state_command(mock_context)
            assert isinstance(result, CommandResult)
            assert not result.success
            assert "not available" in result.error.lower()
        except ImportError:
            pytest.skip("file_commands not available")

    def test_ui_service_status_message_usage(self, command_files):
        """
        Verify that status messages go through UIService, not direct status bar access.

        Commands should use ui_service.set_status_message() instead of
        context.main_window.status_bar.set_message().
        """
        violations = []

        for file_path in command_files:
            if file_path.name == "__init__.py":
                continue

            try:
                content = file_path.read_text(encoding="utf-8")

                # Check for direct status bar usage
                if "status_bar.set_message" in content:
                    lines = content.split("\n")
                    for line_num, line in enumerate(lines, 1):
                        if "status_bar.set_message" in line:
                            violations.append(
                                {
                                    "file": str(file_path),
                                    "line": line_num,
                                    "content": line.strip(),
                                    "violation_type": "direct_status_bar_access",
                                    "description": "Should use UIService.set_status_message() instead",
                                }
                            )

            except Exception as e:
                violations.append(
                    {
                        "file": str(file_path),
                        "error": f"Failed to check status bar usage: {e}",
                        "violation_type": "status_check_error",
                    }
                )

        if violations:
            violation_report = self._format_violation_report(violations)
            pytest.fail(f"Status bar access violations found:\n{violation_report}")

    def test_command_decorator_compliance(self, command_files):
        """
        Verify that all commands have proper @command decorators with required metadata.

        Commands should have ID, title, category, and description.
        """
        violations = []

        for file_path in command_files:
            if file_path.name == "__init__.py":
                continue

            try:
                content = file_path.read_text(encoding="utf-8")

                # Find @command decorators
                command_decorators = re.finditer(r"@command\((.*?)\)", content, re.DOTALL)

                for match in command_decorators:
                    decorator_content = match.group(1)
                    line_num = content[: match.start()].count("\n") + 1

                    # Check for required fields
                    required_fields = ["id=", "title=", "category=", "description="]
                    missing_fields = []

                    for field in required_fields:
                        if field not in decorator_content:
                            missing_fields.append(field.rstrip("="))

                    if missing_fields:
                        violations.append(
                            {
                                "file": str(file_path),
                                "line": line_num,
                                "violation_type": "incomplete_command_decorator",
                                "description": f"Missing required fields: {missing_fields}",
                            }
                        )

            except Exception as e:
                violations.append(
                    {
                        "file": str(file_path),
                        "error": f"Failed to check command decorators: {e}",
                        "violation_type": "decorator_check_error",
                    }
                )

        if violations:
            violation_report = self._format_violation_report(violations)
            pytest.fail(f"Command decorator violations found:\n{violation_report}")

    def _format_violation_report(self, violations: List[Dict]) -> str:
        """Format violations into a readable report."""
        if not violations:
            return "No violations found."

        report = []
        report.append(f"\n{'='*80}")
        report.append(f"ARCHITECTURE COMPLIANCE VIOLATIONS ({len(violations)} total)")
        report.append(f"{'='*80}")

        # Group violations by type
        by_type = {}
        for violation in violations:
            vtype = violation.get("violation_type", "unknown")
            if vtype not in by_type:
                by_type[vtype] = []
            by_type[vtype].append(violation)

        for vtype, viols in by_type.items():
            report.append(f"\n{vtype.upper()} ({len(viols)} violations):")
            report.append("-" * 60)

            for v in viols:
                report.append(f"  File: {v.get('file', 'unknown')}")
                if "line" in v:
                    report.append(f"  Line: {v['line']}")
                if "content" in v:
                    report.append(f"  Code: {v['content']}")
                if "description" in v:
                    report.append(f"  Issue: {v['description']}")
                if "pattern" in v:
                    report.append(f"  Pattern: {v['pattern']}")
                if "error" in v:
                    report.append(f"  Error: {v['error']}")
                report.append("")

        return "\n".join(report)


class TestSpecificArchitecturePatterns:
    """Test specific architecture patterns we recently fixed."""

    def test_tab_commands_use_workspace_service(self):
        """Test that tab commands properly use WorkspaceService."""
        mock_context = Mock(spec=CommandContext)
        mock_workspace_service = Mock(spec=WorkspaceService)
        mock_context.get_service.return_value = mock_workspace_service
        mock_context.args = {"tab_index": 1}

        # Configure service mock
        mock_workspace_service.duplicate_tab.return_value = 2
        mock_workspace_service.close_tabs_to_right.return_value = 3
        mock_workspace_service.close_other_tabs.return_value = 5
        mock_workspace_service.rename_tab.return_value = True
        mock_workspace_service.get_workspace.return_value = Mock()
        mock_workspace_service.get_current_tab_index.return_value = 0

        try:
            from viloapp.core.commands.builtin.tab_commands import (
                close_other_tabs_command,
                close_tabs_to_right_command,
                duplicate_tab_command,
                rename_tab_command,
            )

            # Test duplicate tab
            result = duplicate_tab_command(mock_context)
            assert result.success
            mock_workspace_service.duplicate_tab.assert_called_once_with(1)

            # Test close tabs to right
            result = close_tabs_to_right_command(mock_context)
            assert result.success
            mock_workspace_service.close_tabs_to_right.assert_called_once_with(1)

            # Test close other tabs
            result = close_other_tabs_command(mock_context)
            assert result.success
            mock_workspace_service.close_other_tabs.assert_called_once_with(1)

            # Test rename tab with new name
            mock_context.args = {"tab_index": 1, "new_name": "New Name"}
            result = rename_tab_command(mock_context)
            assert result.success
            mock_workspace_service.rename_tab.assert_called_once_with(1, "New Name")

        except ImportError:
            pytest.skip("Tab commands not available")

    def test_terminal_commands_use_workspace_service(self):
        """Test that terminal commands use WorkspaceService for current widget access."""
        mock_context = Mock(spec=CommandContext)
        mock_workspace_service = Mock(spec=WorkspaceService)
        mock_context.get_service.return_value = mock_workspace_service
        mock_context.args = {}

        # Mock terminal widget
        mock_terminal = Mock()
        mock_terminal.clear_terminal = Mock()
        mock_terminal.copy_selection = Mock()
        mock_terminal.restart_terminal = Mock()
        mock_workspace_service.get_current_widget.return_value = mock_terminal

        try:
            from viloapp.core.commands.builtin.terminal_commands import (
                clear_terminal_handler,
                copy_terminal_handler,
                restart_terminal_handler,
            )

            # Test clear terminal
            result = clear_terminal_handler(mock_context)
            assert result.success
            mock_workspace_service.get_current_widget.assert_called()
            mock_terminal.clear_terminal.assert_called_once()

            # Test copy from terminal
            result = copy_terminal_handler(mock_context)
            assert result.success
            mock_terminal.copy_selection.assert_called_once()

            # Test restart terminal
            result = restart_terminal_handler(mock_context)
            assert result.success
            mock_terminal.restart_terminal.assert_called_once()

        except ImportError:
            pytest.skip("Terminal commands not available")

    def test_file_commands_use_multiple_services(self):
        """Test that file commands properly coordinate multiple services."""
        mock_context = Mock(spec=CommandContext)

        # Mock services
        mock_state_service = Mock(spec=StateService)
        mock_ui_service = Mock(spec=UIService)
        mock_workspace_service = Mock(spec=WorkspaceService)

        def get_service(service_type):
            if service_type == StateService:
                return mock_state_service
            elif service_type == UIService:
                return mock_ui_service
            elif service_type == WorkspaceService:
                return mock_workspace_service
            return None

        mock_context.get_service.side_effect = get_service
        mock_context.args = {}

        try:
            from viloapp.core.commands.builtin.file_commands import save_state_command

            # Test save state command
            result = save_state_command(mock_context)
            assert result.success

            # Verify proper service delegation
            mock_state_service.save_all_state.assert_called_once()
            mock_ui_service.set_status_message.assert_called_once_with("State saved", 2000)

        except ImportError:
            pytest.skip("File commands not available")

    def test_service_unavailable_error_handling(self):
        """Test that commands handle service unavailability gracefully."""
        mock_context = Mock(spec=CommandContext)
        mock_context.get_service.return_value = None
        mock_context.args = {}

        try:
            from viloapp.core.commands.builtin.file_commands import save_state_command
            from viloapp.core.commands.builtin.tab_commands import duplicate_tab_command
            from viloapp.core.commands.builtin.terminal_commands import clear_terminal_handler

            # Test various commands with no services available
            commands_to_test = [
                duplicate_tab_command,
                clear_terminal_handler,
                save_state_command,
            ]

            for command_func in commands_to_test:
                result = command_func(mock_context)
                assert isinstance(result, CommandResult)
                assert not result.success
                assert "not available" in result.error.lower()

        except ImportError:
            pytest.skip("Some commands not available")


class TestRegressionPrevention:
    """Tests that prevent regression to patterns we've already fixed."""

    def test_no_workspace_tab_widget_access(self):
        """Prevent regression: commands should not access workspace.tab_widget directly."""
        command_dir = Path("core/commands/builtin")
        violations = []

        for file_path in command_dir.glob("*.py"):
            if file_path.name == "__init__.py":
                continue

            content = file_path.read_text(encoding="utf-8")

            # Check for specific violations we fixed
            patterns = [
                r"workspace\.tab_widget\.tabText",
                r"workspace\.tab_widget\.setTabText",
                r"workspace\.tab_widget\.currentIndex",
                r"workspace\.tab_widget\.count\(\)",
            ]

            for pattern in patterns:
                if re.search(pattern, content):
                    violations.append(f"{file_path}: {pattern}")

        assert not violations, "Regression detected - direct tab_widget access:\n" + "\n".join(
            violations
        )

    def test_no_main_window_status_bar_access(self):
        """Prevent regression: commands should not access main_window.status_bar directly."""
        command_dir = Path("core/commands/builtin")
        violations = []

        for file_path in command_dir.glob("*.py"):
            if file_path.name == "__init__.py":
                continue

            content = file_path.read_text(encoding="utf-8")

            # Check for direct status bar access
            if "main_window.status_bar.set_message" in content:
                lines = content.split("\n")
                for line_num, line in enumerate(lines, 1):
                    if "main_window.status_bar.set_message" in line:
                        violations.append(f"{file_path}:{line_num} - {line.strip()}")

        assert not violations, "Regression detected - direct status bar access:\n" + "\n".join(
            violations
        )

    def test_commands_import_only_services(self):
        """Prevent regression: command files should only import services, not UI components."""
        command_dir = Path("core/commands/builtin")
        violations = []

        forbidden_imports = [
            "from viloapp.ui.workspace import",
            "from viloapp.ui.main_window import",
            "from viloapp.ui.widgets import",
        ]

        for file_path in command_dir.glob("*.py"):
            if file_path.name == "__init__.py":
                continue

            content = file_path.read_text(encoding="utf-8")

            for forbidden in forbidden_imports:
                if forbidden in content:
                    violations.append(f"{file_path}: {forbidden}")

        assert not violations, "Regression detected - forbidden UI imports:\n" + "\n".join(
            violations
        )
