.PHONY: install test lint run check

install:
	python -m pip install -e '.[dev]'

test:
	pytest

lint:
	ruff check src tests

run:
	agent-control-plane

check: lint test
