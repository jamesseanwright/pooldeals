.PHONY: install
install:
	uv sync && pre-commit install
