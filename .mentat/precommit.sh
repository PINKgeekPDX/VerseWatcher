#!/bin/bash

# Format code
ruff format .

# Run linting with fixes
ruff check --fix .

# Run type checking
pyright

# Run tests since there's no CI
pytest
