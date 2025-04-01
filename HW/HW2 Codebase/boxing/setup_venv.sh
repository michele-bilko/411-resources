#!/bin/bash

# Set the name of the virtual environment directory
VENV_DIR="venv"
REQUIREMENTS_FILE="requirements.txt"

# Check if the virtual environment already exists
if [ ! -d "$VENV_DIR" ]; then
  echo "Creating virtual environment..."
  python -m venv "$VENV_DIR"
  source "$VENV_DIR/bin/activate"


  # Install dependencies from requirements.lock if it exists
  if [ -f "$REQUIREMENTS_FILE" ]; then
    echo "Installing dependencies from $REQUIREMENTS_FILE..."
    pip install -r "$REQUIREMENTS_FILE"
    pip install pytest pytest-mock
  else
    echo "Error: $REQUIREMENTS_FILE not found."
    exit 1
  fi
else
  source "$VENV_DIR/bin/activate"
  echo "Virtual environment already exists. Activated."
fi
