#!/bin/bash
# Setup virtual environment for VTK Python documentation enhancement

set -e  # Exit on any error

echo "🚀 Setting up virtual environment for VTK Python Documentation Enhancement"
echo "=================================================================="

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not found!"
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv .venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📋 Installing requirements..."
pip install -r requirements.txt

# Verify VTK installation
echo "🔍 Verifying VTK installation..."
python -c "import vtk; print(f'✅ VTK {vtk.vtkVersion.GetVTKVersion()} installed successfully')"

# Run setup
echo "🛠️  Running project setup..."
python setup.py

echo ""
echo "✅ Virtual environment setup completed!"
echo ""
echo "🎯 To activate the environment in the future:"
echo "   source .venv/bin/activate"
echo ""
echo "🚀 To run a complete build from scratch:"
echo "   python build.py"
echo ""
echo "🧹 To clean and rebuild:"
echo "   python clean.py && python build.py"
