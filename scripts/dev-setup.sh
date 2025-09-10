#!/bin/bash
"""
Development environment setup script for Operato Runner
"""

set -e

echo "🚀 Setting up Operato Runner development environment..."

# Create runtime directories
echo "📁 Creating runtime directories..."
mkdir -p runtime/module_envs runtime/uploads runtime/logs runtime/temp

# Install development dependencies
echo "📦 Installing development dependencies..."
if command -v uv &> /dev/null; then
    echo "Using uv (recommended)..."
    uv pip install -e ".[dev,test,security]"
else
    echo "Using pip..."
    pip install -e ".[dev,test,security]"
fi

# Setup pre-commit hooks
echo "🔧 Setting up pre-commit hooks..."
pre-commit install || echo "⚠️ Pre-commit not available, skipping..."

# Run import fixer
echo "🔧 Fixing import paths..."
python scripts/fix-imports.py

# Test basic functionality
echo "🧪 Testing basic functionality..."
python main.py --help > /dev/null && echo "✅ Main script runs successfully"

# Run tests
echo "🧪 Running tests..."
make test || echo "⚠️ Some tests failed, but setup completed"

echo "✅ Development environment setup complete!"
echo ""
echo "Next steps:"
echo "  make run          # Start development server"
echo "  make test         # Run tests"
echo "  make lint         # Check code quality"
echo "  make format       # Format code"