"""
Test that files don't exceed reasonable size limits.

Large files are often a sign of:
- Single Responsibility Principle violations
- Monolithic design
- Lack of proper modularization
- Difficult to maintain code
"""

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


def count_lines_of_code(file_path):
    """Count lines of code, excluding comments and blank lines."""
    try:
        with open(file_path, encoding="utf-8") as f:
            lines = f.readlines()

        loc = 0
        total_lines = len(lines)
        in_docstring = False
        docstring_char = None

        for line in lines:
            stripped = line.strip()

            # Handle multi-line docstrings
            if not in_docstring:
                if stripped.startswith('"""') or stripped.startswith("'''"):
                    docstring_char = stripped[:3]
                    if stripped.count(docstring_char) == 1:  # Opening docstring
                        in_docstring = True
                        continue
                    # Single-line docstring, skip it
                    continue
            else:
                if docstring_char in stripped:
                    in_docstring = False
                continue

            # Skip empty lines and comments
            if not stripped or stripped.startswith("#"):
                continue

            loc += 1

        return total_lines, loc

    except (UnicodeDecodeError, PermissionError):
        return 0, 0


def test_file_size_limits():
    """Test that files don't exceed reasonable size limits."""
    python_files = get_python_files()

    # Size limits (lines of code)
    LIMITS = {
        "critical": 1000,  # Files should never exceed this
        "warning": 500,  # Files should ideally be under this
        "ideal": 250,  # Good target size
    }

    violations = {"critical": [], "warning": [], "large_but_acceptable": []}

    for file_path in python_files:
        total_lines, loc = count_lines_of_code(file_path)
        if loc == 0:  # Skip empty files or files that couldn't be read
            continue

        relative_path = str(file_path.relative_to(file_path.parent.parent.parent))

        file_info = {"file": relative_path, "loc": loc, "total_lines": total_lines}

        # Categorize files by size
        if loc > LIMITS["critical"]:
            violations["critical"].append(file_info)
        elif loc > LIMITS["warning"]:
            # Some files are naturally large (like main components)
            # but still worth tracking
            if (
                "main_window.py" in relative_path
                or "workspace.py" in relative_path
                or "split_pane_widget.py" in relative_path
                or "theme_editor_widget.py" in relative_path
            ):
                violations["large_but_acceptable"].append(file_info)
            else:
                violations["warning"].append(file_info)

    # Report critical violations that MUST be fixed
    if violations["critical"]:
        error_msg = f"Files exceed critical size limit ({LIMITS['critical']} lines):\n"
        for file_info in sorted(
            violations["critical"], key=lambda x: x["loc"], reverse=True
        ):
            error_msg += f"  {file_info['file']}: {file_info['loc']} lines\n"

        error_msg += "\nFiles this large violate Single Responsibility Principle.\n"
        error_msg += "Consider:\n"
        error_msg += "  - Breaking into multiple classes\n"
        error_msg += "  - Extracting utility functions\n"
        error_msg += "  - Creating separate modules\n"
        error_msg += "  - Moving to service layer\n"

        pytest.fail(error_msg)

    # Report warnings for files that should be refactored
    if violations["warning"]:
        warning_msg = f"Files exceed warning size limit ({LIMITS['warning']} lines):\n"
        for file_info in sorted(
            violations["warning"], key=lambda x: x["loc"], reverse=True
        )[:5]:
            warning_msg += f"  {file_info['file']}: {file_info['loc']} lines\n"

        if len(violations["warning"]) > 5:
            warning_msg += f"  ... and {len(violations['warning']) - 5} more files\n"

        warning_msg += f"\nConsider refactoring files over {LIMITS['warning']} lines.\n"

        # Only fail if there are too many large files
        if len(violations["warning"]) > 5:
            pytest.fail(warning_msg)
        else:
            # Just warn but don't fail the test
            print(f"\n⚠️  WARNING: {warning_msg}")


def test_average_file_size():
    """Test that average file size is reasonable."""
    python_files = get_python_files()

    total_loc = 0
    file_count = 0
    size_distribution = []

    for file_path in python_files:
        total_lines, loc = count_lines_of_code(file_path)
        if loc > 0:
            total_loc += loc
            file_count += 1
            size_distribution.append(loc)

    if file_count == 0:
        pytest.skip("No Python files found")

    average_size = total_loc / file_count
    size_distribution.sort()
    median_size = size_distribution[len(size_distribution) // 2]

    # Reasonable averages for a well-structured codebase
    MAX_AVERAGE = 300
    MAX_MEDIAN = 200

    if average_size > MAX_AVERAGE:
        pytest.fail(
            f"Average file size too large: {average_size:.1f} lines "
            f"(should be under {MAX_AVERAGE})\n"
            f"This suggests the codebase lacks proper modularization."
        )

    if median_size > MAX_MEDIAN:
        pytest.fail(
            f"Median file size too large: {median_size} lines "
            f"(should be under {MAX_MEDIAN})\n"
            f"This suggests many files are larger than ideal."
        )


def test_specific_file_type_limits():
    """Test specific limits for different types of files."""
    python_files = get_python_files()
    violations = []

    # Different limits for different file types
    TYPE_LIMITS = {
        "widget": 400,  # UI widgets should be focused
        "service": 600,  # Services can be larger but should be modular
        "command": 200,  # Commands should be small and focused
        "model": 300,  # Models should be simple
        "test": 500,  # Tests can be larger but should be organized
    }

    for file_path in python_files:
        total_lines, loc = count_lines_of_code(file_path)
        if loc == 0:
            continue

        relative_path = str(file_path.relative_to(file_path.parent.parent.parent))

        # Determine file type and apply appropriate limit
        file_type = None
        limit = None

        if "/widgets/" in relative_path and "_widget.py" in relative_path:
            file_type = "widget"
            limit = TYPE_LIMITS["widget"]
        elif "/services/" in relative_path and "_service.py" in relative_path:
            file_type = "service"
            limit = TYPE_LIMITS["service"]
        elif "/commands/" in relative_path or "command" in relative_path:
            file_type = "command"
            limit = TYPE_LIMITS["command"]
        elif "/models/" in relative_path or "model" in relative_path:
            file_type = "model"
            limit = TYPE_LIMITS["model"]
        elif "test_" in relative_path or "/tests/" in relative_path:
            file_type = "test"
            limit = TYPE_LIMITS["test"]

        if file_type and loc > limit:
            # Allow some exceptions for complex but necessary files
            exceptions = [
                "main_window.py",  # Main window is naturally complex
                "split_pane_widget.py",  # Complex split pane logic
                "workspace_service.py",  # Central workspace logic
                "theme_editor_widget.py",  # Complex theme editing UI
            ]

            if not any(exception in relative_path for exception in exceptions):
                violations.append(
                    {
                        "file": relative_path,
                        "type": file_type,
                        "loc": loc,
                        "limit": limit,
                    }
                )

    if violations:
        error_msg = "Files exceed type-specific limits:\n"
        for violation in sorted(violations, key=lambda x: x["loc"], reverse=True):
            error_msg += (
                f"  {violation['file']}: {violation['loc']} lines "
                f"({violation['type']} should be ≤ {violation['limit']})\n"
            )

        error_msg += (
            "\nConsider breaking these files into smaller, focused components.\n"
        )

        # Only fail if there are many violations or very large ones
        severe_violations = [v for v in violations if v["loc"] > v["limit"] * 1.5]
        if len(violations) > 3 or severe_violations:
            pytest.fail(error_msg)
        else:
            print(f"\n⚠️  WARNING: {error_msg}")


if __name__ == "__main__":
    # Allow running the test standalone for debugging
    pytest.main([__file__, "-v"])
