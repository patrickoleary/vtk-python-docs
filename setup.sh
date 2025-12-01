#!/bin/bash
# Setup virtual environment for VTK Python documentation

set -e

echo "🚀 Setting up virtual environment..."

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip

echo "📦 Installing vtk-python-docs package..."
pip install -e .

echo ""
echo "✅ Setup complete!"
echo ""
echo "To activate: source .venv/bin/activate"
echo "To build:    vtk-docs build"
echo ""
echo "Available commands:"
echo "   vtk-docs --help     Show all commands"
echo "   vtk-docs build      Run full build pipeline"
echo "   vtk-docs extract    Extract VTK documentation"
echo "   vtk-docs search     Search the documentation"
