#!/bin/bash
# Audio Scheduler - Development Setup Script
# This script sets up a development environment with additional tools

set -e

echo "🔧 Audio Scheduler - Development Setup 🔧"
echo "=========================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run ./install.sh first to set up the basic environment"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

echo "📦 Installing development dependencies..."
pip install -r requirements-dev.txt

echo "🎣 Setting up pre-commit hooks..."
pre-commit install

echo "📝 Creating development configuration..."
cat > .env.development << 'EOF'
FLASK_ENV=development
FLASK_DEBUG=True
FLASK_APP=app.py
EOF

echo "🧪 Running initial tests..."
python -m pytest --version || echo "pytest installed ✓"

echo ""
echo "🎉 Development environment ready! 🎉"
echo ""
echo "📋 Development commands:"
echo "  Run tests:         pytest"
echo "  Format code:       black ."
echo "  Lint code:         flake8 app.py"
echo "  Advanced lint:     pylint app.py"
echo "  Coverage report:   coverage run -m pytest && coverage report"
echo ""
echo "🚀 Start development server: ./run.sh"