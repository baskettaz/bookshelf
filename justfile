# Justfile for bookshelf

# Show available commands
list:
    @just --list

alias b := build
alias c := clean
alias d := docs-serve
alias t := test
alias ty := type-check

# Type check the project with ty
type-check:
    uv run --python=3.14 ty check .

# Type check with concise output (one diagnostic per line)
type-check-concise:
    uv run --python=3.14 ty check --output-format=concise .

# Type check in watch mode (rechecks on file changes)
type-check-watch:
    uv run --python=3.14 ty check --watch .

# Run all the formatting, linting, and testing commands
qa:
    uv run --python=3.14 ruff format .
    uv run --python=3.14 ruff check . --fix
    uv run --python=3.14 ruff check --select I --fix .
    uv run --python=3.14 ty check --output-format=concise .
    uv run --python=3.14 pytest

# Run all the tests for all the supported Python versions
testall:
    uv run --python=3.14 pytest

# Run all the tests, but allow for arguments to be passed
test *ARGS:
    @echo "Running with arg: {{ARGS}}"
    uv run --python=3.14 pytest {{ARGS}}

# Run all the tests, but on failure, drop into the debugger
pdb *ARGS:
    @echo "Running with arg: {{ARGS}}"
    uv run --python=3.14 pytest --pdb --maxfail=10 {{ARGS}}

# Run tests with coverage across all supported Python versions
coverage:
    uv run --python=3.14 coverage run -m pytest
    uv run --python=3.14 coverage report
    uv run --python=3.14 coverage html

# Serve docs locally with live reload
docs-serve:
    -lsof -ti :8000 | xargs kill
    uv run --group docs zensical serve

# Build docs (strict mode, fails on warnings)
docs-build:
    uv run --group docs zensical build --clean

# Build the project, useful for checking that packaging is correct
build:
    rm -rf build
    rm -rf dist
    uv build

# Tag, push, and create a GitHub release
release:
    uv run scripts/release.py

# Remove all build, test, coverage and Python artifacts
clean: clean-build clean-pyc clean-test

# Remove build artifacts
clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

# Remove Python file artifacts
clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

# Remove test and coverage artifacts
clean-test:
	rm -f .coverage
	rm -f .coverage.*
	rm -fr htmlcov/
	rm -fr .pytest_cache

# recreates the .qrc file for the new icons
update-resources:
    uv run python "$(pwd)/scripts/update_rc.py"
    @echo "===] Resource file (QRC) updated"

# compiles all the resources to the binary format
# Note: Still using pyrcc5, because there is no such distributed utility with PyQt6
pyrcc5:
    pyrcc5 ./bookshelf/gui/resources.qrc -o ./bookshelf/gui/resources_rc.py
    @echo "===] Resource file compiled"

# Update all qt-resources
update-qt:
    just update-resources
    just pyrcc5

# Update uv dependencies
uv-update:
    uv lock --upgrade
    uv sync

# Publish to PyPI (manual alternative to GitHub Actions)
publish:
    uv build
    uv publish
