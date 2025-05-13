.PHONY: all clean check deps sync run fmt lint spell_check spell_fix test test_unit test_integration test_watch help extended_tests

# Default target executed when no arguments are given to make.
all: help

sync:
	uv sync

clean:
	rm -rf .venv

deps: sync
	uv pip install -e .[dev]

run: deps
	uv run --env-file .env -- langgraph dev --allow-blocking

# Define a variable for the test file path.
UNIT_TEST_FILE ?= tests/unit_tests/
INTEGRATION_TEST_FILE ?= tests/integration_tests/

test-grumpy:
	uv run -- pytest -rs $(INTEGRATION_TEST_FILE)test_grumpy_agent.py
test-code-reviewer:
	uv run -- pytest -rs $(INTEGRATION_TEST_FILE)test_code_reviewer_agent.py

test-requirement-gatherer:
	uv run -- pytest -rs $(INTEGRATION_TEST_FILE)test_requirement_gatherer.py

test-memory-graph:
	uv run -- pytest -rs $(INTEGRATION_TEST_FILE)test_graph.py

test-tester:
	uv run -- pytest -rs $(INTEGRATION_TEST_FILE)test_tester_agent.py

test-architect:
	uv run -- pytest -rs $(INTEGRATION_TEST_FILE)test_architect_agent.py

test_watch:
	uv run --env-file .env -- python -m ptw --snapshot-update --now . -- -vv tests/unit_tests

test-task-manager:
	uv run -- pytest -rs $(INTEGRATION_TEST_FILE)test_task_manager.py

test_unit:
	uv run pytest tests/unit_tests
test_integration:
	uv run --env-file .env -- pytest -rs $(INTEGRATION_TEST_FILE)

test: test_unit test_integration

extended_tests:
	uv run --env-file .env -- python -m pytest --only-extended $(TEST_FILE)

set-requirement-dataset:
	uv run --env-file .env -- python tests/datasets/requirement_gatherer_dataset.py

set-task-manager-dataset:
	uv run --env-file .env -- python tests/datasets/task_manager_dataset.py

######################
# LINTING AND FORMATTING
######################

# Define a variable for Python and notebook files.
PYTHON_FILES=src/
MYPY_CACHE=.mypy_cache
lint: PYTHON_FILES=src 
fmt: PYTHON_FILES=.
lint_diff format_diff: PYTHON_FILES=$(shell git diff --name-only --diff-filter=d main | grep -E '\.py$$|\.ipynb$$')
lint_package: PYTHON_FILES=src
lint_tests: PYTHON_FILES=tests
lint_tests: MYPY_CACHE=.mypy_cache_test

lint lint_diff lint_package lint_tests:
	uv tool run ruff check .
	[ "$(PYTHON_FILES)" = "" ] || uv tool run ruff format $(PYTHON_FILES) --diff
	[ "$(PYTHON_FILES)" = "" ] || uv tool run ruff check --select I $(PYTHON_FILES)
#	[ "$(PYTHON_FILES)" = "" ] || uv tool run mypy --strict $(PYTHON_FILES)
#	[ "$(PYTHON_FILES)" = "" ] || mkdir -p $(MYPY_CACHE) && uv tool run mypy --strict $(PYTHON_FILES) --cache-dir $(MYPY_CACHE)

fmt format_diff:
	uv tool run ruff format $(PYTHON_FILES)
	uv tool run ruff check --select I --fix $(PYTHON_FILES)

spell_check:
	uv tool run codespell --toml pyproject.toml

spell_fix:
	uv tool run codespell --toml pyproject.toml -w

check: lint spell_check

######################
# HELP
######################

help:
	@echo '----'
	@echo 'format                       - run code formatters'
	@echo 'lint                         - run linters'
	@echo 'test                         - run unit tests'
	@echo 'tests                        - run unit tests'
	@echo 'test TEST_FILE=<test_file>   - run all tests in file'
	@echo 'test_watch                   - run unit tests in watch mode'

