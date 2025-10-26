#!/bin/bash
# Audio Scheduler - Run Script

cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run ./install.sh first"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if all dependencies are installed
if ! python -c "import flask, pygame, sqlalchemy" 2>/dev/null; then
    echo "❌ Dependencies not properly installed!"
    echo "Please run ./install.sh again"
    exit 1
fi

echo "🎵 Starting Audio Scheduler..."
echo "📡 Server will be available at: http://localhost:5000"
echo "🛑 Press Ctrl+C to stop the server"
echo ""

# Run the application
python app.py