#!/bin/bash

# Format code
ruff format .

# Run linting with fixes
ruff check --fix .
