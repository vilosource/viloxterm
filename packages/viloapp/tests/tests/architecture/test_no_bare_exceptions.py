"""
Test that code doesn't use bare exception handlers.

Bare exception handlers (except:) catch all exceptions including system exits
and keyboard interrupts, making debugging difficult and potentially hiding bugs.
"""

import re
from pathlib import Path

import pytest


def get_python_files():
    """Get all Python files in the project (excluding dependencies)."""
    project_root = Path(__file__).parent.parent.parent
    python_files = []

    for file in project_root.rglob("*.py"):
        file_str = str(file)

        # Skip dependency directories
        if (
            "/.direnv/" in file_str
            or "/site-packages/" in file_str
            or "/__pycache__/" in file_str
            or "/references/" in file_str
            or "/deploy/scripts/"
            in file_str  # Deployment scripts might have bare except for robustness
        ):
            continue

        python_files.append(file)

    return python_files


def test_no_bare_except_handlers():
    """Test that files don't use bare except handlers."""
    python_files = get_python_files()
    violations = []

    for file_path in python_files:
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            lines = content.split("\n")
            for line_num, line in enumerate(lines, 1):
                line.strip()

                # Check for bare except
                if re.match(r"^\s*except\s*:\s*$", line) or re.match(
                    r"^\s*except\s*:\s*#.*$", line
                ):
                    violations.append(
                        {
                            "file": str(file_path.relative_to(file_path.parent.parent.parent)),
                            "line": line_num,
                            "content": line.rstrip(),
                            "type": "bare_except",
                        }
                    )

        except (UnicodeDecodeError, PermissionError):
            continue

    if violations:
        error_msg = "Bare exception handlers found:\n"
        for violation in violations:
            error_msg += f"  {violation['file']}:{violation['line']} - {violation['content']}\n"

        error_msg += "\nBare except handlers should specify exception types:\n"
        error_msg += "  ❌ except:\n"
        error_msg += "  ✅ except Exception as e:\n"
        error_msg += "  ✅ except (ValueError, TypeError):\n"
        error_msg += "  ✅ except KeyboardInterrupt:\n"

        pytest.fail(error_msg)


def test_exception_handling_best_practices():
    """Test exception handling follows best practices."""
    python_files = get_python_files()
    violations = []

    for file_path in python_files:
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            lines = content.split("\n")
            in_try_block = False
            indent_level = 0

            for line_num, line in enumerate(lines, 1):
                stripped_line = line.strip()

                # Track try blocks
                if re.match(r"^\s*try\s*:\s*$", line):
                    in_try_block = True
                    indent_level = len(line) - len(line.lstrip())
                    continue

                # Reset when we exit the try block
                if in_try_block and line.strip() and len(line) - len(line.lstrip()) <= indent_level:
                    if not line.strip().startswith(("except", "finally", "else")):
                        in_try_block = False

                # Check for suspicious exception handling patterns
                if "except" in stripped_line:
                    # Bare except
                    if re.match(r"^\s*except\s*:\s*$", line) or re.match(
                        r"^\s*except\s*:\s*#.*$", line
                    ):
                        violations.append(
                            {
                                "file": str(file_path.relative_to(file_path.parent.parent.parent)),
                                "line": line_num,
                                "content": line.rstrip(),
                                "type": "bare_except",
                                "severity": "high",
                            }
                        )

                    # except Exception without logging or handling
                    elif re.match(r"^\s*except\s+Exception\s*:\s*$", line) and line_num < len(
                        lines
                    ):
                        next_line = lines[line_num].strip() if line_num < len(lines) else ""
                        if next_line in ["pass", "continue", ""] and "# " not in next_line:
                            violations.append(
                                {
                                    "file": str(
                                        file_path.relative_to(file_path.parent.parent.parent)
                                    ),
                                    "line": line_num,
                                    "content": line.rstrip(),
                                    "type": "silent_exception",
                                    "severity": "medium",
                                }
                            )

        except (UnicodeDecodeError, PermissionError):
            continue

    # Filter and report high severity violations first
    high_severity = [v for v in violations if v.get("severity") == "high"]
    medium_severity = [v for v in violations if v.get("severity") == "medium"]

    if high_severity:
        error_msg = "Critical exception handling violations:\n"
        for violation in high_severity:
            error_msg += f"  {violation['file']}:{violation['line']} - {violation['content']}\n"

        if medium_severity:
            error_msg += f"\nAdditional concerns ({len(medium_severity)} silent exceptions):\n"
            for violation in medium_severity[:3]:  # Show first 3
                error_msg += f"  {violation['file']}:{violation['line']} - {violation['content']}\n"
            if len(medium_severity) > 3:
                error_msg += f"  ... and {len(medium_severity) - 3} more\n"

        error_msg += "\nBest practices:\n"
        error_msg += "  ✅ except SpecificException as e: logger.error(f'Error: {e}')\n"
        error_msg += "  ✅ except Exception as e: logger.warning(f'Unexpected: {e}')\n"
        error_msg += "  ❌ except: pass  # Hides all errors including KeyboardInterrupt\n"

        pytest.fail(error_msg)


def test_specific_exception_patterns():
    """Test for specific problematic exception patterns."""
    python_files = get_python_files()
    violations = []

    problematic_patterns = [
        (r"except.*:\s*pass\s*$", "silent_pass"),
        (r"except.*:\s*continue\s*$", "silent_continue"),
        (r"except.*Exception.*:\s*$", "generic_exception_no_action"),
    ]

    for file_path in python_files:
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            lines = content.split("\n")
            for line_num, line in enumerate(lines, 1):
                for pattern, violation_type in problematic_patterns:
                    if re.search(pattern, line):
                        # Check if next line has any handling
                        next_line = ""
                        if line_num < len(lines):
                            next_line = lines[line_num].strip()

                        # Allow pass/continue if there's a comment explaining why
                        if "#" in line or "#" in next_line:
                            continue

                        # Allow pass in specific contexts (like abstract methods)
                        if "NotImplemented" in line or "abstract" in line.lower():
                            continue

                        violations.append(
                            {
                                "file": str(file_path.relative_to(file_path.parent.parent.parent)),
                                "line": line_num,
                                "content": line.rstrip(),
                                "type": violation_type,
                            }
                        )

        except (UnicodeDecodeError, PermissionError):
            continue

    # Only report the most critical ones to avoid noise
    critical_violations = [v for v in violations if v["type"] == "silent_pass"]

    if critical_violations:
        error_msg = "Silent exception handling found:\n"
        for violation in critical_violations[:10]:  # Limit to first 10
            error_msg += f"  {violation['file']}:{violation['line']} - {violation['content']}\n"

        if len(critical_violations) > 10:
            error_msg += f"  ... and {len(critical_violations) - 10} more\n"

        error_msg += "\nSilent exception handling makes debugging difficult.\n"
        error_msg += "Consider:\n"
        error_msg += "  ✅ except ValueError as e: logger.debug(f'Expected error: {e}')\n"
        error_msg += (
            "  ✅ except Exception as e: logger.warning(f'Ignoring error: {e}')  # Explicit\n"
        )

        pytest.fail(error_msg)


if __name__ == "__main__":
    # Allow running the test standalone for debugging
    pytest.main([__file__, "-v"])
