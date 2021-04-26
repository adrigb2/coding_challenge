SHELL := /bin/bash
.PHONY: *

lint:
	@echo --- Running linting ---
	pre-commit run --all-files

test:
	@echo --- Running tests ---
	pytest -v --cov=app --cov-report term
