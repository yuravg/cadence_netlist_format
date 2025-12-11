# Makefile for building and installing Python packages
# Auto-detects project name and version from pyproject.toml
# Provides development and release workflows

MAKE = make --no-print-directory

# Auto-detect project name from pyproject.toml
# Falls back to manual override if needed: make install project=myproject
project ?= $(shell grep '^name = ' pyproject.toml | head -1 | sed 's/name = "\(.*\)"/\1/')

# Auto-detect version from pyproject.toml
version ?= $(shell grep '^version = ' pyproject.toml | head -1 | sed 's/version = "\(.*\)"/\1/')

# Get the most recent package from dist/ directory
# Uses ls -t for time-based sorting (most recent first)
get_latest_pkg = $(shell ls -t dist/*.whl 2>/dev/null | head -1)

# Check if package is currently installed (via pipx)
is_installed = $(shell pipx list 2>/dev/null | grep -q "package $(project)" && echo "yes" || echo "no")

# Python executable (can be overridden: make build PYTHON=python3.11)
# Auto-detect and use .venv if it exists
PYTHON ?= $(shell [ -f .venv/bin/python ] && echo ".venv/bin/python" || echo "python")

# Test environment Python (auto-detect test_env)
PYTHON_TEST ?= $(shell [ -f test_env/bin/python ] && echo "test_env/bin/python" || echo "python")

.PHONY: help
help:
	@echo ""
	@echo "╔═══════════════════════════════════════════════════════════════════════╗"
	@echo "║  Cadence Netlist Format - Build & Install                             ║"
	@echo "╚═══════════════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "Project: $(project) v$(version) (source)"
	@echo "Python:  $(PYTHON)"
	@echo "Install: pipx (isolated environment for CLI tools)"
	@echo ""
	@echo "VIRTUAL ENVIRONMENT (Development):"
	@echo "  venv         - create .venv virtual environment"
	@echo "  venv-install - install package in editable mode: pip install -e .[dev]"
	@echo "  venv-dev     - complete dev setup (venv + venv-install)"
	@echo "  venv-clean   - remove .venv directory"
	@echo ""
	@echo "TEST ENVIRONMENT (Testing Built Packages):"
	@echo "  test-env         - create test_env virtual environment"
	@echo "  test-env-install - install built wheel package from dist/"
	@echo "  test-env-dev     - complete test setup (test-env + test-env-install)"
	@echo "  test-env-clean   - remove test_env directory"
	@echo "  test-run         - run tests in test_env environment"
	@echo ""
	@echo "BUILD & INSTALL:"
	@echo "  build        - clean then build wheel package"
	@echo "  install      - install built package from dist/"
	@echo "  dev-install  - install in editable mode with dev dependencies"
	@echo "  reinstall    - force reinstall built package"
	@echo "  all          - clean, build, and install"
	@echo "  rall         - uninstall, clean, build, and install"
	@echo "  clean        - remove build artifacts (dist, build, egg-info)"
	@echo "  uninstall    - uninstall package"
	@echo ""
	@echo "INFORMATION:"
	@echo "  info         - show project info, built package, and installation status"
	@echo ""
	@echo "TESTING:"
	@echo "  test         - run manual tests (compare outputs in examples/ dir)"
	@echo "  pytest       - run automated pytest tests"
	@echo "  coverage     - run pytest with coverage report (HTML + terminal)"
	@echo "  test-unit    - run unit tests only"
	@echo "  test-integration - run integration tests only"
	@echo "  check-deps   - verify build dependencies are installed"
	@echo ""

.PHONY: clean build install dev-install reinstall all uninstall rall
.PHONY: info test check-deps dist
.PHONY: venv venv-install venv-dev venv-clean
.PHONY: test-env test-env-install test-env-dev test-env-clean test-run
.PHONY: pytest coverage test-unit test-integration

# Check if required build tools are installed
check-deps:
	@echo "Checking build dependencies..."
	@command -v $(PYTHON) >/dev/null 2>&1 || \
		(echo "ERROR: $(PYTHON) not found. Install Python first." && exit 1)
	@$(PYTHON) -c "import build" 2>/dev/null || \
		(echo "ERROR: 'build' module not found. Install with: pip install build" && exit 1)
	@command -v pipx >/dev/null 2>&1 || \
		(echo "ERROR: 'pipx' not found. Install with: python3 -m pip install --user pipx && pipx ensurepath" && exit 1)
	@echo "✓ All required dependencies are installed"

# Remove build artifacts
clean:
	@echo "Cleaning build artifacts..."
	@rm -rf *.egg-info 2>/dev/null || true
	@rm -rf ./dist/ 2>/dev/null || true
	@rm -rf ./build/ 2>/dev/null || true
	@rm -rf ./src/*.egg-info 2>/dev/null || true
	@rm -rf .pytest_cache 2>/dev/null || true
	@rm -rf htmlcov 2>/dev/null || true
	@rm -rf .coverage 2>/dev/null || true
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "✓ Cleanup complete"

# Build the wheel package
build: check-deps
	@$(MAKE) clean
	@echo "Building $(project) v$(version) (source)..."
	@$(PYTHON) -m build --wheel
	@echo "✓ Build complete: $(get_latest_pkg)"

# Build both wheel and source distribution
dist: check-deps
	@$(MAKE) clean
	@echo "Building distributions for $(project) v$(version) (source)..."
	@$(PYTHON) -m build
	@echo "✓ Distributions built:"
	@ls -lh dist/

# Show comprehensive project information
info:
	@echo "╔═══════════════════════════════════════════════════════════════════════╗"
	@echo "║  Project Information                                                  ║"
	@echo "╚═══════════════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "Project: $(project)"
	@echo "Source Version: $(version)"
	@echo "Python: $(PYTHON)"
	@echo ""
	@echo "Built Package:"
	@if [ -z "$(get_latest_pkg)" ]; then \
		echo "  ⚠ No package found in dist/"; \
		echo "  Run 'make build' to create one"; \
	else \
		echo "  $(get_latest_pkg)"; \
		ls -lh $(get_latest_pkg) | awk '{print "  Size: " $$5 "  Modified: " $$6 " " $$7 " " $$8}'; \
	fi
	@echo ""
	@echo "Installation Status:"
	@if [ "$(is_installed)" = "yes" ]; then \
		echo "  ✓ INSTALLED (via pipx)"; \
		echo ""; \
		echo "Installed Package Details:"; \
		pipx list --short 2>/dev/null | grep "^$(project) " | sed 's/^/  /' || \
		(pipx list 2>/dev/null | grep -A 5 "package $(project)" | head -6 | sed 's/^/  /'); \
	else \
		echo "  ✗ NOT INSTALLED"; \
		echo "  Run 'make install' to install"; \
	fi

# Install the most recently built package
install: check-deps
	@if [ -z "$(get_latest_pkg)" ]; then \
		echo "ERROR: No package found in dist/. Run 'make build' first."; \
		exit 1; \
	fi
	@echo "╔═══════════════════════════════════════════════════════════════════════╗"
	@echo "║  Installing: $(get_latest_pkg)"
	@echo "╚═══════════════════════════════════════════════════════════════════════╝"
	@pipx install $(get_latest_pkg) --force
	@echo ""
	@echo "✓ Installation complete. Run 'cnl_format' to start."

# Install in editable/development mode with dev dependencies
dev-install: check-deps
	@echo "Installing $(project) in development mode..."
	@pipx install -e . --force
	@echo ""
	@echo "✓ Development installation complete"
	@echo "  Changes to source code will be reflected immediately"
	@echo "  Run 'cnl_format' to test"

# Force reinstall (useful during development)
reinstall: check-deps
	@if [ -z "$(get_latest_pkg)" ]; then \
		echo "ERROR: No package found in dist/. Run 'make build' first."; \
		exit 1; \
	fi
	@echo "Force reinstalling: $(get_latest_pkg)"
	@pipx install $(get_latest_pkg) --force
	@echo "✓ Reinstallation complete"

# Build and install
all:
	@$(MAKE) build
	@$(MAKE) install

# Uninstall the package
uninstall:
	@if [ -z "$(project)" ]; then \
		echo "ERROR: Could not detect project name. Specify manually: make uninstall project=<name>"; \
		exit 1; \
	fi
	@if [ "$(is_installed)" = "yes" ]; then \
		echo "Uninstalling: $(project)"; \
		pipx uninstall $(project) || true; \
		echo "✓ Uninstalled"; \
	else \
		echo "⚠ $(project) is not installed"; \
	fi

# Reinstall (uninstall, build, install)
rall:
	@$(MAKE) uninstall
	@$(MAKE) all

# Run manual tests
test:
	@echo "╔═══════════════════════════════════════════════════════════════════════╗"
	@echo "║  Running Manual Tests                                                 ║"
	@echo "╚═══════════════════════════════════════════════════════════════════════╝"
	@echo ""
	@if [ "$(is_installed)" != "yes" ]; then \
		echo "ERROR: $(project) is not installed. Run 'make install' first."; \
		exit 1; \
	fi
	@echo "Testing installed package..."
	@echo "Command: cnl_format --version"
	@cnl_format --version || echo "⚠ Version flag may not be implemented"
	@echo ""
	@echo "To perform full manual testing:"
	@echo "  1. cd examples/"
	@echo "  2. Run: cnl_format"
	@echo "  3. Click 'Format Netlist' in GUI (generates NetList.rpt)"
	@echo "  4. Compare: ./diff_netlist.sh"
	@echo ""
	@echo "Note: GUI always outputs to NetList.rpt (old versions: NetList.rpt,01, etc.)"
	@echo "Reference file: tests/data/expected/netlist_v3_expected.rpt"
	@echo ""

# Virtual environment targets
venv:
	@if [ -d .venv ]; then \
		echo "✓ Virtual environment .venv already exists"; \
	else \
		echo "Creating virtual environment .venv..."; \
		python -m venv .venv; \
		echo "✓ Virtual environment created at .venv"; \
		echo ""; \
		echo "To activate manually:"; \
		echo "  source .venv/bin/activate"; \
		echo ""; \
		echo "Or run: make venv-install"; \
	fi

venv-install: venv
	@echo "Installing package in editable mode with dev dependencies..."
	@.venv/bin/pip install --upgrade pip
	@.venv/bin/pip install -e ".[dev]"
	@echo ""
	@echo "✓ Development installation complete"
	@echo "  Package installed in editable mode in .venv"
	@echo "  Python: .venv/bin/python"
	@echo "  Run with: .venv/bin/cnl_format"

venv-dev:
	@$(MAKE) venv
	@$(MAKE) venv-install

venv-clean:
	@if [ -d .venv ]; then \
		echo "Removing virtual environment .venv..."; \
		rm -rf .venv; \
		echo "✓ Virtual environment removed"; \
	else \
		echo "⚠ No virtual environment found at .venv"; \
	fi

# Test environment targets
test-env:
	@if [ -d test_env ]; then \
		echo "✓ Test environment test_env already exists"; \
	else \
		echo "Creating test environment test_env..."; \
		python -m venv test_env; \
		echo "✓ Test environment created at test_env"; \
		echo ""; \
		echo "To activate manually:"; \
		echo "  source test_env/bin/activate"; \
		echo ""; \
		echo "Or run: make test-env-install"; \
	fi

test-env-install: test-env
	@if [ -z "$(get_latest_pkg)" ]; then \
		echo "ERROR: No package found in dist/. Run 'make build' first."; \
		exit 1; \
	fi
	@echo "Installing built package in test environment..."
	@test_env/bin/pip install --upgrade pip
	@test_env/bin/pip install $(get_latest_pkg) --force-reinstall
	@echo ""
	@echo "✓ Test environment installation complete"
	@echo "  Package: $(get_latest_pkg)"
	@echo "  Python: test_env/bin/python"
	@echo "  Run with: test_env/bin/cnl_format"
	@echo "  Or use: make test-run"

test-env-dev:
	@$(MAKE) build
	@$(MAKE) test-env
	@$(MAKE) test-env-install

test-env-clean:
	@if [ -d test_env ]; then \
		echo "Removing test environment test_env..."; \
		rm -rf test_env; \
		echo "✓ Test environment removed"; \
	else \
		echo "⚠ No test environment found at test_env"; \
	fi

# Run tests using test environment
test-run:
	@if [ ! -d test_env ]; then \
		echo "ERROR: Test environment not found. Run 'make test-env-dev' first."; \
		exit 1; \
	fi
	@echo "╔═══════════════════════════════════════════════════════════════════════╗"
	@echo "║  Running Tests in test_env                                            ║"
	@echo "╚═══════════════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "Python: $(PYTHON_TEST)"
	@echo "Command: test_env/bin/cnl_format --version"
	@test_env/bin/cnl_format --version || echo "⚠ Version flag may not be implemented"
	@echo ""
	@echo "To perform full manual testing in test_env:"
	@echo "  1. cd examples/"
	@echo "  2. Run: ../test_env/bin/cnl_format"
	@echo "  3. Click 'Format Netlist' in GUI (generates NetList.rpt)"
	@echo "  4. Compare: ./diff_netlist.sh"
	@echo ""
	@echo "Note: GUI always outputs to NetList.rpt (old versions: NetList.rpt,01, etc.)"
	@echo "Reference file: tests/data/expected/netlist_v3_expected.rpt"
	@echo ""

# Automated pytest targets
pytest: venv
	@echo "╔═══════════════════════════════════════════════════════════════════════╗"
	@echo "║  Running Pytest Tests                                                 ║"
	@echo "╚═══════════════════════════════════════════════════════════════════════╝"
	@echo ""
	@.venv/bin/python -m pytest
	@echo ""
	@echo "✓ All tests complete"

coverage: venv
	@echo "╔═══════════════════════════════════════════════════════════════════════╗"
	@echo "║  Running Pytest with Coverage                                         ║"
	@echo "╚═══════════════════════════════════════════════════════════════════════╝"
	@echo ""
	@.venv/bin/python -m pytest --cov=cadence_netlist_format --cov-report=html --cov-report=term
	@echo ""
	@echo "✓ Coverage report generated:"
	@echo "  - Terminal output above"
	@echo "  - HTML report: htmlcov/index.html"
	@echo ""
	@echo "To view HTML report:"
	@echo "  open htmlcov/index.html  (macOS)"
	@echo "  xdg-open htmlcov/index.html  (Linux)"
	@echo ""

test-unit: venv
	@echo "╔═══════════════════════════════════════════════════════════════════════╗"
	@echo "║  Running Unit Tests                                                   ║"
	@echo "╚═══════════════════════════════════════════════════════════════════════╝"
	@echo ""
	@.venv/bin/python -m pytest tests/unit/
	@echo ""
	@echo "✓ Unit tests complete"

test-integration: venv
	@echo "╔═══════════════════════════════════════════════════════════════════════╗"
	@echo "║  Running Integration Tests                                            ║"
	@echo "╚═══════════════════════════════════════════════════════════════════════╝"
	@echo ""
	@.venv/bin/python -m pytest tests/integration/
	@echo ""
	@echo "✓ Integration tests complete"
