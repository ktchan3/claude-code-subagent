#!/bin/bash
# Activation script for the people management system

echo "Activating People Management System environment..."

# Activate the UV virtual environment
source .venv/bin/activate

echo "Environment activated!"
echo "Available commands:"
echo "  make run-server    - Start the FastAPI server"
echo "  make run-client    - Start the PySide6 client"
echo "  make test          - Run tests"
echo "  make lint          - Run linting"
echo "  make format        - Format code"
echo "  make help          - Show all available commands"
echo ""
echo "To deactivate, run: deactivate"