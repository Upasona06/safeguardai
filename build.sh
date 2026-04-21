#!/bin/bash
# Force Python 3.12 for builds to avoid Python 3.14 wheel availability issues

# Create .python-version file
echo "3.12.0" > .python-version

# Force pyenv to use 3.12 if available
export PYTHON_VERSION=3.12.0
