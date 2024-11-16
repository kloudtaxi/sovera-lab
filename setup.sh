#!/bin/bash

# Exit on error
set -e

echo "Creating Python virtual environment..."
python3 -m venv venv

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing requirements..."
pip install -r requirements.txt

echo "Setup complete! Virtual environment is activated."
echo "To activate the virtual environment in the future, run: source venv/bin/activate"
