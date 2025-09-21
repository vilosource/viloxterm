.PHONY: help setup dev test test-sdk test-terminal test-editor test-app build format lint typecheck clean install-dev run

help:
	@echo "ViloxTerm Monorepo Commands"
	@echo "============================"
	@echo "  setup        - Setup development environment"
	@echo "  dev          - Run in development mode"
	@echo "  test         - Run all tests"
	@echo "  test-sdk     - Test SDK package"
	@echo "  test-terminal- Test terminal plugin"
	@echo "  test-editor  - Test editor plugin"
	@echo "  test-app     - Test main application"
	@echo "  build        - Build all packages"
	@echo "  format       - Format code with black"
	@echo "  lint         - Lint code with ruff"
	@echo "  typecheck    - Type check with mypy"
	@echo "  clean        - Clean build artifacts"
	@echo "  install-dev  - Install all packages in development mode"
	@echo "  run          - Run the application (same as dev)"

setup:
	python scripts/dev-setup.py

dev:
	python main.py --dev

test:
	pytest packages/*/tests -v

test-sdk:
	pytest packages/viloapp-sdk/tests -v

test-terminal:
	pytest packages/viloxterm/tests -v

test-editor:
	pytest packages/viloedit/tests -v

test-app:
	pytest packages/viloapp/tests -v

build:
	python scripts/build.py

format:
	black packages/*/src packages/*/tests

lint:
	ruff check packages/*/src packages/*/tests

typecheck:
	mypy packages/*/src

install-dev:
	pip install -e packages/viloapp-sdk/
	pip install -e packages/viloapp/
	pip install -e packages/viloxterm/
	pip install -e packages/viloedit/
	pip install -e packages/viloapp-cli/

run:
	python main.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "build" -path "*/packages/*" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "dist" -path "*/packages/*" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .coverage htmlcov