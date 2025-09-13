# Makefile for ViloxTerm
# VSCode-style PySide6 Application

# Python paths (using direnv virtual environment)
PYTHON := .direnv/python-3.12.3/bin/python
PIP := .direnv/python-3.12.3/bin/pip
PYTEST := .direnv/python-3.12.3/bin/pytest
BLACK := .direnv/python-3.12.3/bin/black
RUFF := .direnv/python-3.12.3/bin/ruff
MYPY := .direnv/python-3.12.3/bin/mypy
PYSIDE6_RCC := .direnv/python-3.12.3/bin/pyside6-rcc
PYSIDE6_DEPLOY := .direnv/python-3.12.3/bin/pyside6-deploy

# Default target
.DEFAULT_GOAL := help

.PHONY: help
help: ## Show this help message
	@echo "ViloxTerm Development Commands"
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
	$(PYTEST) tests/unit/ -v

.PHONY: test-unit-clean
test-unit-clean: ## Run unit tests with minimal output
	$(PYTEST) tests/unit/ -q --tb=line --disable-warnings

.PHONY: test-integration
test-integration: ## Run integration tests only
	$(PYTEST) -m integration

.PHONY: test-e2e
test-e2e: ## Run end-to-end tests only
	$(PYTEST) -m e2e

.PHONY: test-coverage
test-coverage: ## Run tests with coverage report
	$(PYTEST) --cov=ui --cov=models --cov-report=html --cov-report=term

.PHONY: test-gui
test-gui: ## Run GUI tests only
	$(PYTEST) tests/gui/ -v

.PHONY: test-gui-clean
test-gui-clean: ## Run GUI tests with minimal output
	$(PYTEST) tests/gui/ -q --tb=line --disable-warnings

.PHONY: test-gui-headless
test-gui-headless: ## Run GUI tests in headless mode (Linux)
	xvfb-run -a $(PYTEST) tests/gui/ -v

.PHONY: test-gui-fast
test-gui-fast: ## Run GUI tests excluding slow tests
	$(PYTEST) tests/gui/ -v -m "gui and not slow"

.PHONY: test-gui-slow
test-gui-slow: ## Run only slow GUI tests
	$(PYTEST) tests/gui/ -v -m "slow"

.PHONY: test-gui-animation
test-gui-animation: ## Run GUI animation tests
	$(PYTEST) tests/gui/ -v -m "animation"

.PHONY: test-gui-keyboard
test-gui-keyboard: ## Run GUI keyboard interaction tests
	$(PYTEST) tests/gui/ -v -m "keyboard"

.PHONY: test-gui-mouse
test-gui-mouse: ## Run GUI mouse interaction tests
	$(PYTEST) tests/gui/ -v -m "mouse"

.PHONY: test-gui-theme
test-gui-theme: ## Run GUI theme tests
	$(PYTEST) tests/gui/ -v -m "theme"

.PHONY: test-gui-integration
test-gui-integration: ## Run GUI integration tests
	$(PYTEST) tests/gui/ -v -m "integration"

.PHONY: test-gui-performance
test-gui-performance: ## Run GUI performance tests
	$(PYTEST) tests/gui/ -v -m "performance"

.PHONY: test-gui-accessibility
test-gui-accessibility: ## Run GUI accessibility tests
	$(PYTEST) tests/gui/ -v -m "accessibility"

.PHONY: test-gui-coverage
test-gui-coverage: ## Run GUI tests with coverage report
	$(PYTEST) tests/gui/ --cov=ui --cov-report=html --cov-report=term -v

.PHONY: test-headless
test-headless: ## Run all tests in headless mode (Linux)
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

# Build executable targets
.PHONY: build-icons
build-icons: ## Generate application icons
	$(PYTHON) deploy/scripts/generate_simple_icon.py

.PHONY: build-init
build-init: ## Initialize build configuration
	$(PYSIDE6_DEPLOY) --init main.py

.PHONY: build-dry-run
build-dry-run: ## Show build commands without executing
	$(PYSIDE6_DEPLOY) --dry-run

.PHONY: build
build: resources ## Build standalone executable
	@echo "Building ViloxTerm executable..."
	$(PYSIDE6_DEPLOY) -v

.PHONY: build-onefile
build-onefile: resources ## Build single-file executable
	@echo "Building single-file ViloxTerm executable..."
	@cp pysidedeploy.spec pysidedeploy.spec.bak
	@sed -i 's/mode = standalone/mode = onefile/' pysidedeploy.spec
	$(PYSIDE6_DEPLOY) -v
	@mv pysidedeploy.spec.bak pysidedeploy.spec

.PHONY: build-clean
build-clean: ## Clean build artifacts
	rm -rf deployment/ build/ dist/
	rm -f *.bin *.exe *.app
	rm -f main.dist/ main.build/
	find . -name "*.dist" -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.build" -type d -exec rm -rf {} + 2>/dev/null || true

.PHONY: test-executable
test-executable: ## Test the built executable
	@if [ -f "main.bin" ]; then \
		echo "Testing Linux executable..."; \
		./main.bin --version; \
	elif [ -f "main.exe" ]; then \
		echo "Testing Windows executable..."; \
		./main.exe --version; \
	elif [ -d "main.app" ]; then \
		echo "Testing macOS app..."; \
		./main.app/Contents/MacOS/main --version; \
	else \
		echo "No executable found. Run 'make build' first."; \
	fi

.PHONY: build-all
build-all: build-icons build ## Build executable with all assets

.PHONY: executable
executable: build ## Build the ViloxTerm executable (alias for build)

.PHONY: exe
exe: build ## Short alias for building executable
	find . -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "build" -exec rm -rf {} + 2>/dev/null || true
	rm -f resources/resources_rc.py

.PHONY: appimage
appimage: resources ## Build AppImage (portable Linux executable)
	@echo "Building AppImage..."
	cd builder && ./build.sh appimage
	@echo "AppImage created: docker-build-output/ViloxTerm-x86_64.AppImage"
	@ls -lh docker-build-output/ViloxTerm-x86_64.AppImage 2>/dev/null || echo "Build may have failed - check output above"

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

.PHONY: dist
dist: clean ## Build distribution packages (wheel/sdist)
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
validate: check test test-gui-fast ## Run all checks and tests

.PHONY: ci
ci: ## Run CI pipeline locally
	$(MAKE) clean
	$(MAKE) install
	$(MAKE) install-dev
	$(MAKE) check
	$(MAKE) test-coverage
	$(MAKE) test-gui-headless

.PHONY: ci-full
ci-full: ## Run full CI pipeline including slow GUI tests
	$(MAKE) clean
	$(MAKE) install
	$(MAKE) install-dev
	$(MAKE) check
	$(MAKE) test-coverage
	$(MAKE) test-gui-coverage

# Settings development targets
.PHONY: run-dev
run-dev: resources ## Run with development settings directory
	VILOXTERM_SETTINGS_DIR=~/.viloxterm-dev $(PYTHON) main.py

.PHONY: run-test
run-test: resources ## Run with temporary settings (no persistence)
	$(PYTHON) main.py --temp-settings

.PHONY: run-clean
run-clean: resources ## Run with reset defaults and temp settings
	$(PYTHON) main.py --reset-settings --temp-settings

.PHONY: run-portable
run-portable: resources ## Run in portable mode (settings in app directory)
	$(PYTHON) main.py --portable

.PHONY: run-custom
run-custom: resources ## Run with custom settings file (specify with SETTINGS_FILE=path)
	$(PYTHON) main.py --settings-file $(or $(SETTINGS_FILE),/tmp/viloxterm-custom.ini)

.PHONY: settings-info
settings-info: ## Show current settings location
	@echo "Settings configuration for ViloxTerm:"
	@echo "===================================="
	@echo "Default: System locations (Registry/~/.config/macOS ~/Library)"
	@echo ""
	@echo "Command line options:"
	@echo "  --settings-dir <path>    Custom directory for settings files"
	@echo "  --settings-file <path>   Specific settings file (INI format)" 
	@echo "  --portable               Store in ./settings/ (app directory)"
	@echo "  --temp-settings          Temporary (deleted on exit)"
	@echo "  --reset-settings         Reset to defaults"
	@echo ""
	@echo "Environment variables:"
	@echo "  VILOXTERM_SETTINGS_DIR     Custom settings directory"
	@echo "  VILOXTERM_SETTINGS_FILE    Specific settings file"
	@echo "  VILOXTERM_PORTABLE=1       Enable portable mode"
	@echo "  VILOXTERM_TEMP_SETTINGS=1  Enable temporary settings"
	@echo ""
	@echo "Development targets:"
	@echo "  make run-dev            Run with dev settings (~/.viloxterm-dev)"
	@echo "  make run-test           Run with temporary settings"
	@echo "  make run-clean          Run with defaults + temp settings"
	@echo "  make run-portable       Run in portable mode"
	@echo "  make run-custom         Run with custom file (set SETTINGS_FILE)"

.PHONY: clean-dev-settings
clean-dev-settings: ## Remove development settings directory
	rm -rf ~/.viloxterm-dev
	@echo "Development settings directory removed"

.PHONY: backup-settings
backup-settings: ## Backup current settings to ~/viloxterm-settings-backup
	@echo "Creating settings backup..."
	@mkdir -p ~/viloxterm-settings-backup
	@if [ -d ~/.config/ViloxTerm ]; then cp -r ~/.config/ViloxTerm ~/viloxterm-settings-backup/system-config-$(shell date +%Y%m%d-%H%M%S); fi
	@if [ -d ~/.viloxterm-dev ]; then cp -r ~/.viloxterm-dev ~/viloxterm-settings-backup/dev-settings-$(shell date +%Y%m%d-%H%M%S); fi
	@if [ -d ./settings ]; then cp -r ./settings ~/viloxterm-settings-backup/portable-settings-$(shell date +%Y%m%d-%H%M%S); fi
	@echo "Settings backed up to ~/viloxterm-settings-backup/"

# Quick aliases
.PHONY: r
r: run ## Alias for 'run'

.PHONY: t
t: test ## Alias for 'test'

.PHONY: tg
tg: test-gui ## Alias for 'test-gui'

.PHONY: tgh
tgh: test-gui-headless ## Alias for 'test-gui-headless'

.PHONY: c
c: clean ## Alias for 'clean'

.PHONY: f
f: format ## Alias for 'format'

.PHONY: l
l: lint ## Alias for 'lint'

.PHONY: rd
rd: run-dev ## Alias for 'run-dev'

.PHONY: rt
rt: run-test ## Alias for 'run-test'

.PHONY: rc
rc: run-clean ## Alias for 'run-clean'