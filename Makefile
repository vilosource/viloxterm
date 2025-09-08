# Makefile for ViloApp
# VSCode-style PySide6 Application

# Python paths (using direnv virtual environment)
PYTHON := .direnv/python-3.12.3/bin/python
PIP := .direnv/python-3.12.3/bin/pip
PYTEST := .direnv/python-3.12.3/bin/pytest
BLACK := .direnv/python-3.12.3/bin/black
RUFF := .direnv/python-3.12.3/bin/ruff
MYPY := .direnv/python-3.12.3/bin/mypy
PYSIDE6_RCC := .direnv/python-3.12.3/bin/pyside6-rcc

# Default target
.DEFAULT_GOAL := help

.PHONY: help
help: ## Show this help message
	@echo "ViloApp Development Commands"
	@echo "============================"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.PHONY: resources
resources: ## Compile Qt resource files
	$(PYSIDE6_RCC) resources/resources.qrc -o resources/resources_rc.py
	@echo "Resources compiled successfully!"

.PHONY: run
run: resources ## Run the application
	$(PYTHON) main.py

.PHONY: install
install: ## Install dependencies
	$(PIP) install -r requirements.txt

.PHONY: install-dev
install-dev: ## Install development dependencies
	$(PIP) install -r requirements-dev.txt

.PHONY: test
test: ## Run all tests
	$(PYTEST)

.PHONY: test-unit
test-unit: ## Run unit tests only
	$(PYTEST) -m unit

.PHONY: test-integration
test-integration: ## Run integration tests only
	$(PYTEST) -m integration

.PHONY: test-e2e
test-e2e: ## Run end-to-end tests only
	$(PYTEST) -m e2e

.PHONY: test-coverage
test-coverage: ## Run tests with coverage report
	$(PYTEST) --cov=ui --cov=models --cov-report=html --cov-report=term

.PHONY: test-headless
test-headless: ## Run tests in headless mode (Linux)
	xvfb-run -a $(PYTEST)

.PHONY: format
format: ## Format code with black
	$(BLACK) .

.PHONY: lint
lint: ## Lint code with ruff
	$(RUFF) check .

.PHONY: lint-fix
lint-fix: ## Lint and auto-fix code with ruff
	$(RUFF) check --fix .

.PHONY: typecheck
typecheck: ## Run type checking with mypy
	$(MYPY) .

.PHONY: check
check: format lint typecheck ## Run all code quality checks

.PHONY: clean
clean: ## Clean up generated files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "build" -exec rm -rf {} + 2>/dev/null || true
	rm -f resources/resources_rc.py

.PHONY: clean-all
clean-all: clean ## Clean everything including virtual environment
	rm -rf .direnv/

.PHONY: setup
setup: ## Initial project setup
	direnv allow
	$(PIP) install --upgrade pip
	$(MAKE) install
	$(MAKE) install-dev
	@echo "Setup complete! Run 'make run' to start the application."

.PHONY: dev
dev: ## Run application in development mode with auto-reload (if implemented)
	$(PYTHON) main.py --debug

.PHONY: build
build: clean ## Build distribution packages
	$(PYTHON) -m build

.PHONY: docs
docs: ## Build documentation
	cd docs && make html

.PHONY: serve-docs
serve-docs: ## Serve documentation locally
	cd docs/_build/html && $(PYTHON) -m http.server

.PHONY: watch-tests
watch-tests: ## Run tests in watch mode
	$(PYTEST) --looponfail

.PHONY: profile
profile: ## Profile the application
	$(PYTHON) -m cProfile -s cumulative main.py

.PHONY: freeze
freeze: ## Freeze current dependencies
	$(PIP) freeze > requirements-frozen.txt

.PHONY: update
update: ## Update all dependencies to latest versions
	$(PIP) install --upgrade -r requirements.txt

.PHONY: tree
tree: ## Show project structure
	@find . -type d -name ".git" -prune -o -type d -name "__pycache__" -prune -o -type d -name ".direnv" -prune -o -type d -name "*.egg-info" -prune -o -type f -print | sed -e "s/[^-][^\/]*\// |/g" -e "s/|\([^ ]\)/|-\1/"

.PHONY: count
count: ## Count lines of Python code
	@find . -name "*.py" -not -path "./.direnv/*" -not -path "./tests/*" | xargs wc -l | tail -1

.PHONY: todo
todo: ## Find all TODO comments in code
	@grep -r "TODO" --include="*.py" . 2>/dev/null || echo "No TODOs found"

.PHONY: debug
debug: ## Run with Python debugger
	$(PYTHON) -m pdb main.py

.PHONY: shell
shell: ## Open Python shell with app context
	$(PYTHON) -i -c "from main import *; from ui.main_window import *; from PySide6.QtWidgets import QApplication; import sys"

.PHONY: validate
validate: check test ## Run all checks and tests

.PHONY: ci
ci: ## Run CI pipeline locally
	$(MAKE) clean
	$(MAKE) install
	$(MAKE) install-dev
	$(MAKE) check
	$(MAKE) test-coverage

# Quick aliases
.PHONY: r
r: run ## Alias for 'run'

.PHONY: t
t: test ## Alias for 'test'

.PHONY: c
c: clean ## Alias for 'clean'

.PHONY: f
f: format ## Alias for 'format'

.PHONY: l
l: lint ## Alias for 'lint'