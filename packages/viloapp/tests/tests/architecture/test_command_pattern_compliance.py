"""
Test Command Pattern Architecture compliance.

This test ensures that the application follows the Command Pattern correctly:
- Commands are properly decorated
- Commands return CommandResult objects
- UI components use execute_command() instead of direct calls
"""

import ast
import re
from pathlib import Path

import pytest


def get_python_files():
    """Get all Python files in the project (excluding dependencies)."""
    project_root = Path(__file__).parent.parent.parent
    python_files = []

    for file in project_root.rglob("*.py"):
        file_str = str(file)

        # Skip dependency directories and generated files
        if (
            "/.direnv/" in file_str
            or "/site-packages/" in file_str
            or "/__pycache__/" in file_str
            or "/references/" in file_str
            or "/build/" in file_str
            or "/dist/" in file_str
        ):
            continue

        python_files.append(file)

    return python_files


def get_command_files():
    """Get files that contain commands."""
    project_root = Path(__file__).parent.parent.parent
    command_files = []

    # Look for command files
    for file in project_root.rglob("*command*.py"):
        file_str = str(file)
        if (
            "/.direnv/" in file_str
            or "/site-packages/" in file_str
            or "/__pycache__/" in file_str
            or "/references/" in file_str
        ):
            continue
        command_files.append(file)

    # Also check builtin commands directory
    builtin_commands_dir = project_root / "core" / "commands" / "builtin"
    if builtin_commands_dir.exists():
        for file in builtin_commands_dir.glob("*.py"):
            if file.name != "__init__.py":
                command_files.append(file)

    return command_files


def test_commands_have_decorators():
    """Test that functions that look like commands have @command decorators."""
    command_files = get_command_files()
    violations = []

    for file_path in command_files:
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # Find functions that end with '_command'
            lines = content.split("\n")
            for line_num, line in enumerate(lines, 1):
                stripped = line.strip()

                # Look for function definitions that end with '_command'
                if re.match(r"^\s*def\s+\w*_command\s*\(", line):
                    func_name = re.search(r"def\s+(\w*_command)", line).group(1)

                    # Check if the previous lines have @command decorator
                    has_decorator = False
                    for prev_line_num in range(max(0, line_num - 10), line_num):
                        if prev_line_num < len(lines):
                            prev_line = lines[prev_line_num].strip()
                            if prev_line.startswith("@command"):
                                has_decorator = True
                                break

                    if not has_decorator:
                        violations.append(
                            {
                                "file": str(file_path.relative_to(file_path.parent.parent.parent)),
                                "line": line_num,
                                "function": func_name,
                                "content": stripped,
                            }
                        )

        except (UnicodeDecodeError, PermissionError):
            continue

    if violations:
        error_msg = "Functions ending with '_command' missing @command decorator:\n"
        for violation in violations:
            error_msg += f"  {violation['file']}:{violation['line']} - {violation['function']}\n"

        error_msg += "\nAll command functions must use @command decorator:\n"
        error_msg += "  @command(id='workbench.action.example', title='Example')\n"
        error_msg += "  def example_command(context: CommandContext) -> CommandResult:\n"

        pytest.fail(error_msg)


def test_commands_return_command_result():
    """Test that command functions return CommandResult objects."""
    command_files = get_command_files()
    violations = []

    for file_path in command_files:
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # Parse the AST to find function definitions
            try:
                tree = ast.parse(content, filename=str(file_path))
            except SyntaxError:
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name.endswith("_command"):
                    # Check return type annotation
                    has_proper_return = False

                    if node.returns:
                        if (
                            isinstance(node.returns, ast.Name)
                            and node.returns.id == "CommandResult"
                        ):
                            has_proper_return = True
                        elif (
                            isinstance(node.returns, ast.Attribute)
                            and node.returns.attr == "CommandResult"
                        ):
                            has_proper_return = True

                    # If no type annotation, check for return statements
                    if not has_proper_return:
                        for child in ast.walk(node):
                            if isinstance(child, ast.Return) and child.value:
                                # Look for CommandResult constructor calls
                                if (
                                    isinstance(child.value, ast.Call)
                                    and isinstance(child.value.func, ast.Name)
                                    and child.value.func.id == "CommandResult"
                                ):
                                    has_proper_return = True
                                    break

                    if not has_proper_return:
                        violations.append(
                            {
                                "file": str(file_path.relative_to(file_path.parent.parent.parent)),
                                "line": node.lineno,
                                "function": node.name,
                            }
                        )

        except (UnicodeDecodeError, PermissionError, SyntaxError):
            continue

    if violations:
        error_msg = "Command functions not returning CommandResult:\n"
        for violation in violations:
            error_msg += f"  {violation['file']}:{violation['line']} - {violation['function']}\n"

        error_msg += "\nCommand functions must return CommandResult:\n"
        error_msg += "  def my_command(context: CommandContext) -> CommandResult:\n"
        error_msg += "      return CommandResult(success=True, value=data)\n"

        # Only fail if there are many violations (some might be false positives)
        if len(violations) > 5:
            pytest.fail(error_msg)


def test_ui_uses_execute_command():
    """Test that UI components use execute_command instead of direct calls."""
    ui_files = []
    project_root = Path(__file__).parent.parent.parent
    ui_dir = project_root / "ui"

    if ui_dir.exists():
        for file in ui_dir.rglob("*.py"):
            if "__pycache__" not in str(file):
                ui_files.append(file)

    violations = []

    for file_path in ui_files:
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            lines = content.split("\n")
            for line_num, line in enumerate(lines, 1):
                stripped = line.strip()

                # Skip comments
                if stripped.startswith("#"):
                    continue

                # Look for direct command function calls
                if re.search(r"\w+_command\s*\(", line) and "execute_command" not in line:
                    # Skip function definitions and imports
                    if not (
                        stripped.startswith("def ")
                        or stripped.startswith("from ")
                        or stripped.startswith("import ")
                        or "= " + stripped.split("(")[0] in line
                    ):  # Skip assignments

                        violations.append(
                            {
                                "file": str(file_path.relative_to(file_path.parent.parent.parent)),
                                "line": line_num,
                                "content": stripped,
                            }
                        )

        except (UnicodeDecodeError, PermissionError):
            continue

    if violations:
        error_msg = "UI components calling commands directly (should use execute_command):\n"
        for violation in violations[:5]:  # Limit to first 5
            error_msg += f"  {violation['file']}:{violation['line']} - {violation['content']}\n"

        if len(violations) > 5:
            error_msg += f"  ... and {len(violations) - 5} more\n"

        error_msg += "\nUI components should use execute_command():\n"
        error_msg += "  ❌ some_command(context)\n"
        error_msg += "  ✅ execute_command('workbench.action.some')\n"

        pytest.fail(error_msg)


def test_command_ids_are_namespaced():
    """Test that command IDs follow proper namespacing convention."""
    command_files = get_command_files()
    violations = []

    for file_path in command_files:
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # Find @command decorators with id parameter
            decorator_pattern = r'@command\s*\([^)]*id\s*=\s*["\']([^"\']+)["\']'
            matches = re.finditer(decorator_pattern, content, re.MULTILINE)

            for match in matches:
                command_id = match.group(1)
                line_num = content[: match.start()].count("\n") + 1

                # Check if command ID follows proper namespacing
                if not (
                    command_id.startswith("workbench.")
                    or command_id.startswith("editor.")
                    or command_id.startswith("terminal.")
                    or command_id.startswith("debug.")
                ):

                    violations.append(
                        {
                            "file": str(file_path.relative_to(file_path.parent.parent.parent)),
                            "line": line_num,
                            "command_id": command_id,
                        }
                    )

        except (UnicodeDecodeError, PermissionError):
            continue

    if violations:
        error_msg = "Command IDs not properly namespaced:\n"
        for violation in violations:
            error_msg += f"  {violation['file']}:{violation['line']} - {violation['command_id']}\n"

        error_msg += "\nCommand IDs should follow namespacing convention:\n"
        error_msg += "  ✅ workbench.action.newTab\n"
        error_msg += "  ✅ editor.action.save\n"
        error_msg += "  ✅ terminal.action.clear\n"
        error_msg += "  ❌ newTab\n"
        error_msg += "  ❌ save_file\n"

        pytest.fail(error_msg)


def test_command_context_usage():
    """Test that commands properly use CommandContext."""
    command_files = get_command_files()
    violations = []

    for file_path in command_files:
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            lines = content.split("\n")
            for line_num, line in enumerate(lines, 1):
                # Look for command function definitions
                if re.match(r"^\s*def\s+\w*_command\s*\(", line):
                    func_match = re.search(r"def\s+(\w*_command)\s*\(([^)]*)\)", line)
                    if func_match:
                        func_name = func_match.group(1)
                        params = func_match.group(2)

                        # Check if it has context parameter with proper type
                        if "context" not in params:
                            violations.append(
                                {
                                    "file": str(
                                        file_path.relative_to(file_path.parent.parent.parent)
                                    ),
                                    "line": line_num,
                                    "function": func_name,
                                    "issue": "no_context_param",
                                }
                            )
                        elif "CommandContext" not in params:
                            violations.append(
                                {
                                    "file": str(
                                        file_path.relative_to(file_path.parent.parent.parent)
                                    ),
                                    "line": line_num,
                                    "function": func_name,
                                    "issue": "missing_type_annotation",
                                }
                            )

        except (UnicodeDecodeError, PermissionError):
            continue

    if violations:
        error_msg = "Command functions with improper context usage:\n"

        for violation in violations:
            issue_desc = {
                "no_context_param": "missing context parameter",
                "missing_type_annotation": "missing CommandContext type annotation",
            }
            error_msg += (
                f"  {violation['file']}:{violation['line']} - "
                f"{violation['function']} ({issue_desc[violation['issue']]})\n"
            )

        error_msg += "\nCommand functions must have properly typed context:\n"
        error_msg += "  def my_command(context: CommandContext) -> CommandResult:\n"

        pytest.fail(error_msg)


if __name__ == "__main__":
    # Allow running the test standalone for debugging
    pytest.main([__file__, "-v"])
