#!/bin/bash

# Setup script for ViloxTerm development environment hooks

set -e

echo "🔧 Setting up ViloxTerm development hooks..."

# Ensure we're in the project directory
if [ ! -f "main.py" ]; then
    echo "❌ Error: Not in ViloxTerm project directory"
    exit 1
fi

# Check if direnv is being used
if [ -f ".direnv/python-3.12.3/bin/python" ]; then
    PYTHON=".direnv/python-3.12.3/bin/python"
    PIP=".direnv/python-3.12.3/bin/pip"
    echo "✅ Using direnv Python environment"
else
    PYTHON="python3"
    PIP="pip3"
    echo "⚠️  Using system Python (direnv not detected)"
fi

# Install pre-commit if not available
if ! command -v pre-commit >/dev/null 2>&1; then
    echo "📦 Installing pre-commit..."
    $PIP install pre-commit
else
    echo "✅ pre-commit already installed"
fi

# Install pre-commit hooks
echo "🪝 Installing pre-commit hooks..."
if command -v pre-commit >/dev/null 2>&1; then
    pre-commit install
    echo "✅ Pre-commit hooks installed from .pre-commit-config.yaml"
else
    echo "⚠️  pre-commit not available, using git hooks only"
fi

# Ensure git hooks are executable
echo "🔑 Setting up git hook permissions..."
chmod +x .git/hooks/pre-commit
chmod +x .git/hooks/commit-msg

# Test the setup
echo ""
echo "🧪 Testing hook setup..."

# Create a temporary file with syntax error to test
temp_file="/tmp/test_syntax_error_$$.py"
echo "def broken_syntax():" > "$temp_file"
echo "    if True" >> "$temp_file"
echo "        print('missing colon')" >> "$temp_file"

# Test Python compilation check
echo "  Testing Python syntax checking..."
if $PYTHON -m py_compile "$temp_file" 2>/dev/null; then
    echo "❌ Error: Syntax check didn't catch error"
    rm -f "$temp_file"
    exit 1
else
    echo "✅ Syntax checking works correctly"
fi

# Clean up
rm -f "$temp_file"

echo ""
echo "🎉 Development hooks setup complete!"
echo ""
echo "Summary of protections installed:"
echo "  ✅ Pre-commit hook: Checks syntax, formatting, and linting"
echo "  ✅ Commit-msg hook: Prevents AI attribution in commits"
echo "  ✅ Pre-commit framework: Additional checks via .pre-commit-config.yaml"
echo ""
echo "To run checks manually:"
echo "  make syntax-check     # Check Python syntax"
echo "  make check            # Run all quality checks"
echo "  make pre-commit-run   # Run pre-commit on all files"
echo ""
echo "The next commit will automatically run these checks!"