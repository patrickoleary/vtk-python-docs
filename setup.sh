#!/bin/bash
# Setup virtual environment for VTK Python documentation

set -e

echo "🚀 Setting up virtual environment with uv..."

uv sync --extra dev

echo ""
echo "✅ Setup complete!"
echo ""
echo "To activate: source .venv/bin/activate"
echo "To build:    uv run vtk-docs build"
echo ""
echo "Available commands:"
echo "   uv run vtk-docs --help     Show all commands"
echo "   uv run vtk-docs build      Run full build pipeline"
echo "   uv run vtk-docs extract    Extract VTK documentation"
echo "   uv run vtk-docs search     Search the documentation"
