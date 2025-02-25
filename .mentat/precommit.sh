#!/bin/bash

# Format code
ruff format .

# Run linting with auto-fix
ruff check --fix .
