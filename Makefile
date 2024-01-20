SHELL := /bin/bash
PATH := $(HOME)/.rye/shims:$(PATH)

EXEC ?= rye run
PYTHON_FILES := $(shell find xoeuf/ -type f -name '*.py')

install:
	rye sync
.PHONY: install


LINT_TOOL ?= ruff
LINT_PATHS ?= xoeuf/ tests/

format:
	@$(EXEC) $(LINT_TOOL) check --fix --preview $(LINT_PATHS)
	@$(EXEC) $(LINT_TOOL) format $(LINT_PATHS)
.PHONY: format-python


lint:
	@$(EXEC) $(LINT_TOOL) format --check $(LINT_PATHS)
	@$(EXEC) $(LINT_TOOL) check --preview $(LINT_PATHS)
.PHONY: lint


test: $(PYTHON_FILES)
	@rm -f .coverage*
	@if [ -z "$(PYTEST_WORKERS)" ]; then \
        $(EXEC) pytest --cov-report= --cov-config=pyproject.toml --cov=xoeuf/ $(PYTEST_ARGS) $(PYTEST_PATHS); \
    else \
        $(EXEC) pytest --cov-report= --cov-config=pyproject.toml --cov=xoeuf/ -n $(PYTEST_WORKERS) $(PYTEST_ARGS) $(PYTEST_PATHS); \
    fi
.PHONY: test


COVERAGE_PATHS ?=
coverage:
	@if [ -z "$(COVERAGE_PATHS)" ]; then \
	   $(EXEC) coverage report --precision=2 --rcfile=pyproject.toml | tee report.txt; \
    else \
       $(EXEC) coverage report --precision=2 --include=$(COVERAGE_PATHS) --rcfile=pyproject.toml | tee report.txt; \
    fi
.PHONY: coverage
