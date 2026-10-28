.PHONY: help install test lint format format-check build docker-build

help:
	@echo "install       Sync locked dependencies"
	@echo "test          Run the test suite"
	@echo "lint          Run Ruff linting"
	@echo "format        Format the code"
	@echo "format-check  Check code formatting"
	@echo "build         Build Python distributions"
	@echo "docker-build  Build the Docker image"

install:
	uv sync --locked

test:
	uv run pytest

lint:
	uv run ruff check .

format:
	uv run ruff format .

format-check:
	uv run ruff format --check .

build:
	uv build

docker-build:
	docker build -t reaper .
