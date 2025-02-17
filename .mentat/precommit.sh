#!/bin/bash

# Format code
ruff format .

# Run linting with fixes
ruff check --fix .

# Run tests since there's no CI
pytest
