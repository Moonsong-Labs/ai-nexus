.PHONY: all clean check deps sync run fmt lint spell_check spell_fix test test_unit test_graphs test_watch help extended_tests ci-build-check demo

# Default target executed when no arguments are given to make.
all: help

sync:
	uv sync --extra dev

clean:
	rm -rf .venv

deps: sync

run: deps
	uv run --env-file .env -- langgraph dev --allow-blocking --debug-port 2025

ci-build-check: deps
	@ AI_NEXUS_MOCKS=true \
      timeout 30s uv run --env-file .env -- langgraph dev --no-browser --no-reload; status=$$?; [ $$status -eq 0 ] || [ $$status -eq 124 ]

set-requirement-dataset:
	uv run --env-file .env -- python tests/datasets/requirement_gatherer_dataset.py

set-task-manager-dataset:
	uv run --env-file .env -- python tests/datasets/task_manager_dataset.py

set-pr-memory-updater-dataset:
	uv run --env-file .env -- python tests/datasets/pr_memory_updater_dataset.py

############
# TESTING 
############
test: test-unit

test-unit:
	uv run pytest tests/unit_tests

test-graphs:
	uv run --env-file .env pytest -rs tests/graph_tests

test-graphs-%:
	uv run --env-file .env pytest -rs tests/graph_tests/$*

test_watch:
	uv run --env-file .env -- python -m ptw --snapshot-update --now . -- -vv tests/unit_tests

###########################
# EVALUATION & SCENARIOS
###########################

evaluation:
	uv run --env-file .env python ./scripts/pick_evaluation.py

evaluations:
	uv run --env-file .env pytest ./tests/evaluations

# Run the demo orchestration script
demo-%:
	@if [ "$*" = "ai" ]; then \
		uv run --env-file .env -- python ./src/demo/orchestrate.py exec ai; \
	elif [ "$*" = "human" ]; then \
		uv run --env-file .env -- python ./src/demo/orchestrate.py exec human; \
	else \
		echo "Unknown mode: $*, (need: human|ai)"; \
	fi

scenario-%:
	@echo "Running scenario: $*"
	uv run --env-file .env -- python ./tests/scenarios/$*/run.py

######################
# LINTING AND FORMATTING
######################

# Define a variable for Python and notebook files.
PYTHON_FILES=src/
MYPY_CACHE=.mypy_cache
lint: PYTHON_FILES=src 
fmt: PYTHON_FILES=.
lint_diff: PYTHON_FILES=$(shell git diff --name-only --diff-filter=d main | grep -E '\.py$$|\.ipynb$$')
lint_package: PYTHON_FILES=src
lint_tests: PYTHON_FILES=tests
lint_tests: MYPY_CACHE=.mypy_cache_test

lint lint_diff lint_package lint_tests:
	uv tool run ruff check .
	[ "$(PYTHON_FILES)" = "" ] || uv tool run ruff format $(PYTHON_FILES) --diff
	[ "$(PYTHON_FILES)" = "" ] || uv tool run ruff check --select I $(PYTHON_FILES)

fmt:
	uv tool run ruff format $(PYTHON_FILES)
	uv tool run ruff check --select I --fix $(PYTHON_FILES)

spell-check:
	uv tool run codespell --toml pyproject.toml

spell-fix:
	uv tool run codespell --toml pyproject.toml -w

check: lint spell-check

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
	@echo 'ci-build-check               - run build check for CI'
	@echo 'demo                         - run demo orchestration script'

