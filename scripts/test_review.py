#!/usr/bin/env python3
"""
Test Review Script - Analyzes test coverage and quality for changed files.
Used by the Test Guardian agent to verify testing methodology compliance.
"""

import subprocess
import sys
import os
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import ast
import json

class TestReviewer:
    """Analyzes test coverage and quality for changed files."""

    def __init__(self, base_ref: str = "HEAD~1"):
        self.base_ref = base_ref
        self.project_root = Path.cwd()
        self.issues = {
            "critical": [],
            "warning": [],
            "info": [],
            "suggestion": []
        }

    def get_changed_files(self) -> List[Path]:
        """Get list of changed Python files using git diff."""
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", self.base_ref],
                capture_output=True,
                text=True,
                check=True
            )

            changed_files = []
            for file in result.stdout.strip().split('\n'):
                if file and file.endswith('.py') and not file.startswith('tests/'):
                    changed_files.append(Path(file))

            return changed_files
        except subprocess.CalledProcessError:
            print("Error: Failed to get git diff")
            return []

    def find_test_file(self, source_file: Path) -> Optional[Path]:
        """Find the corresponding test file for a source file."""
        # Remove .py extension
        base_name = source_file.stem

        # Possible test file patterns
        test_patterns = [
            f"tests/unit/test_{base_name}.py",
            f"tests/gui/test_{base_name}.py",
            f"tests/integration/test_{base_name}.py",
            f"tests/test_{base_name}.py",
            f"tests/{source_file.parent}/test_{base_name}.py"
        ]

        for pattern in test_patterns:
            test_file = self.project_root / pattern
            if test_file.exists():
                return test_file

        return None

    def check_test_updated(self, test_file: Path) -> bool:
        """Check if test file was updated with the source file."""
        try:
            result = subprocess.run(
                ["git", "diff", self.base_ref, "--", str(test_file)],
                capture_output=True,
                text=True,
                check=True
            )
            return bool(result.stdout.strip())
        except subprocess.CalledProcessError:
            return False

    def analyze_test_file(self, test_file: Path) -> Dict:
        """Analyze a test file for quality metrics."""
        metrics = {
            "total_tests": 0,
            "qt_patterns": {
                "qtbot_usage": 0,
                "signal_tests": 0,
                "wait_usage": 0,
                "process_events": 0  # Anti-pattern
            },
            "assertions": {
                "total": 0,
                "weak": 0,  # is not None, is None, etc.
                "strong": 0
            },
            "anti_patterns": [],
            "edge_cases": 0,
            "mocking": 0,
            "parametrized": 0
        }

        try:
            with open(test_file, 'r') as f:
                content = f.read()
                tree = ast.parse(content)

            for node in ast.walk(tree):
                # Count test functions
                if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                    metrics["total_tests"] += 1

                    # Check for Qt patterns
                    func_source = ast.unparse(node) if hasattr(ast, 'unparse') else ""

                    if 'qtbot' in func_source:
                        metrics["qt_patterns"]["qtbot_usage"] += 1
                    if 'wait_signal' in func_source or 'wait_until' in func_source:
                        metrics["qt_patterns"]["wait_usage"] += 1
                    if 'processEvents' in func_source:
                        metrics["qt_patterns"]["process_events"] += 1
                        metrics["anti_patterns"].append(f"{node.name}: Uses processEvents()")

                    # Check for weak assertions
                    for stmt in ast.walk(node):
                        if isinstance(stmt, ast.Assert):
                            metrics["assertions"]["total"] += 1
                            assertion_str = ast.unparse(stmt.test) if hasattr(ast, 'unparse') else ""

                            if 'is not None' in assertion_str or 'is None' in assertion_str:
                                metrics["assertions"]["weak"] += 1
                            else:
                                metrics["assertions"]["strong"] += 1

                    # Check for parametrized tests
                    for decorator in node.decorator_list:
                        if hasattr(decorator, 'func'):
                            if hasattr(decorator.func, 'attr') and decorator.func.attr == 'parametrize':
                                metrics["parametrized"] += 1
                                metrics["edge_cases"] += 1

            # Check for signal testing
            if 'wait_signal' in content or 'QSignalSpy' in content:
                metrics["qt_patterns"]["signal_tests"] += content.count('wait_signal') + content.count('QSignalSpy')

            # Check for mocking
            metrics["mocking"] = content.count('mock') + content.count('Mock') + content.count('patch')

        except Exception as e:
            print(f"Error analyzing {test_file}: {e}")

        return metrics

    def check_qt_compliance(self, test_file: Path) -> List[str]:
        """Check for Qt/PySide6 specific testing patterns."""
        issues = []

        try:
            with open(test_file, 'r') as f:
                content = f.read()

            # Check for missing qtbot.addWidget()
            if 'qtbot' in content:
                widget_creations = re.findall(r'(\w+)\s*=\s*\w+Widget\(', content)
                for widget_var in widget_creations:
                    if f'qtbot.addWidget({widget_var})' not in content:
                        issues.append(f"Widget '{widget_var}' created without qtbot.addWidget()")

            # Check for hardcoded delays
            if 'time.sleep' in content or 'QTest.qWait' in content:
                issues.append("Uses hardcoded delays instead of wait conditions")

            # Check for direct exec() on dialogs
            if '.exec()' in content and 'mock' not in content.lower():
                issues.append("Modal dialog exec() not mocked")

        except Exception as e:
            print(f"Error checking Qt compliance: {e}")

        return issues

    def generate_report(self) -> str:
        """Generate a comprehensive test review report."""
        report = []
        report.append("=" * 60)
        report.append("TEST REVIEW REPORT")
        report.append("=" * 60)
        report.append("")

        # Get changed files
        changed_files = self.get_changed_files()
        report.append(f"Changed Files: {len(changed_files)}")
        report.append("")

        total_coverage = 0
        files_with_tests = 0

        for source_file in changed_files:
            report.append(f"\n📁 {source_file}")
            test_file = self.find_test_file(source_file)

            if not test_file:
                self.issues["critical"].append(f"No test file found for {source_file}")
                report.append("  ❌ No test file found")
                continue

            report.append(f"  📝 Test file: {test_file}")
            files_with_tests += 1

            # Check if test was updated
            if not self.check_test_updated(test_file):
                self.issues["warning"].append(f"Test file {test_file.name} not updated with source changes")
                report.append("  ⚠️  Test file not updated with source changes")

            # Analyze test quality
            metrics = self.analyze_test_file(test_file)

            report.append(f"  📊 Test Metrics:")
            report.append(f"     - Total tests: {metrics['total_tests']}")
            report.append(f"     - Assertions: {metrics['assertions']['total']} "
                         f"(strong: {metrics['assertions']['strong']}, "
                         f"weak: {metrics['assertions']['weak']})")

            if metrics['assertions']['weak'] > metrics['assertions']['strong']:
                self.issues["warning"].append(f"{test_file.name} has mostly weak assertions")

            # Qt patterns
            if test_file.parent.name == 'gui' or 'widget' in str(test_file).lower():
                report.append(f"  🎯 Qt/PySide6 Patterns:")
                report.append(f"     - qtbot usage: {metrics['qt_patterns']['qtbot_usage']}")
                report.append(f"     - Signal tests: {metrics['qt_patterns']['signal_tests']}")
                report.append(f"     - Wait patterns: {metrics['qt_patterns']['wait_usage']}")

                if metrics['qt_patterns']['process_events'] > 0:
                    report.append(f"     - ❌ processEvents() calls: {metrics['qt_patterns']['process_events']}")

                # Check Qt compliance
                qt_issues = self.check_qt_compliance(test_file)
                if qt_issues:
                    report.append(f"  ⚠️  Qt Compliance Issues:")
                    for issue in qt_issues:
                        report.append(f"     - {issue}")
                        self.issues["warning"].append(f"{test_file.name}: {issue}")

            # Other metrics
            if metrics['parametrized'] > 0:
                report.append(f"  ✅ Parametrized tests: {metrics['parametrized']}")
            if metrics['mocking'] > 0:
                report.append(f"  🎭 Mocking usage: {metrics['mocking']}")

            # Anti-patterns
            if metrics['anti_patterns']:
                report.append(f"  ❌ Anti-patterns detected:")
                for pattern in metrics['anti_patterns']:
                    report.append(f"     - {pattern}")
                    self.issues["critical"].append(pattern)

        # Summary
        report.append("\n" + "=" * 60)
        report.append("SUMMARY")
        report.append("=" * 60)

        if changed_files:
            coverage_pct = (files_with_tests / len(changed_files)) * 100
            report.append(f"Test Coverage: {coverage_pct:.1f}% of changed files have tests")

        # Issues summary
        if self.issues["critical"]:
            report.append("\n❌ CRITICAL ISSUES:")
            for issue in self.issues["critical"]:
                report.append(f"  - {issue}")

        if self.issues["warning"]:
            report.append("\n⚠️  WARNINGS:")
            for issue in self.issues["warning"]:
                report.append(f"  - {issue}")

        # Grade
        grade = self.calculate_grade(changed_files, files_with_tests)
        report.append(f"\n📊 GRADE: {grade}")

        # Recommendations
        report.append("\n💡 RECOMMENDATIONS:")
        if not files_with_tests:
            report.append("  - Create test files for all changed source files")
        if self.issues["warning"]:
            report.append("  - Update test files when source files change")
            report.append("  - Replace weak assertions with specific checks")
        report.append("  - Consider adding parametrized tests for edge cases")
        report.append("  - Use qtbot.wait_until() instead of hardcoded delays")

        return "\n".join(report)

    def calculate_grade(self, changed_files: List[Path], files_with_tests: int) -> str:
        """Calculate an overall grade for test quality."""
        if not changed_files:
            return "N/A"

        coverage_score = (files_with_tests / len(changed_files)) * 100

        # Deduct points for issues
        critical_penalty = len(self.issues["critical"]) * 10
        warning_penalty = len(self.issues["warning"]) * 5

        final_score = max(0, coverage_score - critical_penalty - warning_penalty)

        if final_score >= 90:
            return "A"
        elif final_score >= 80:
            return "B+"
        elif final_score >= 70:
            return "B"
        elif final_score >= 60:
            return "C+"
        elif final_score >= 50:
            return "C"
        else:
            return "D"

    def run(self) -> int:
        """Run the test review and return exit code."""
        report = self.generate_report()
        print(report)

        # Return non-zero if critical issues found
        return 1 if self.issues["critical"] else 0


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Review test coverage and quality for changed files")
    parser.add_argument("--since", default="HEAD~1", help="Git ref to compare against (default: HEAD~1)")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")

    args = parser.parse_args()

    reviewer = TestReviewer(base_ref=args.since)

    if args.json:
        # JSON output for CI/CD integration
        result = {
            "changed_files": [str(f) for f in reviewer.get_changed_files()],
            "issues": reviewer.issues,
            "grade": reviewer.calculate_grade(reviewer.get_changed_files(), 0)
        }
        print(json.dumps(result, indent=2))
        return 0
    else:
        return reviewer.run()


if __name__ == "__main__":
    sys.exit(main())