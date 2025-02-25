#!/bin/bash

# Create a temporary requirements file without Windows-specific packages
grep -v "pywin32" requirements.txt > requirements_temp.txt

# Install platform-independent dependencies
pip install -r requirements_temp.txt

# Install Windows-specific dependencies if on Windows
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    pip install pywin32==306
fi

# Clean up temporary file
rm requirements_temp.txt

# Install development dependencies
pip install ruff pyright
