#!/bin/bash
# Audio Scheduler - Production Run Script with Gunicorn

cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run ./install.sh first"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if gunicorn is installed
if ! python -c "import gunicorn" 2>/dev/null; then
    echo "❌ Gunicorn not installed!"
    echo "Installing gunicorn..."
    pip install gunicorn>=21.0.0
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Set environment variables
export FLASK_ENV=production
export PYTHONUNBUFFERED=1

echo "🚀 Starting Audio Scheduler with Gunicorn..."
echo "📡 Server will be available at: http://localhost:5000"
echo "🛑 Press Ctrl+C to stop the server"
echo ""

# Run with Gunicorn
# -w 1: Use only 1 worker (CRITICAL: prevents duplicate schedulers!)
# -b 0.0.0.0:5000: Bind to all interfaces on port 5000
# --timeout 120: Allow 2 minutes for long-running requests
# --log-level info: Log level
# --access-logfile logs/gunicorn_access.log: Access log
# --error-logfile logs/gunicorn_error.log: Error log
# --capture-output: Capture stdout/stderr to error log
exec gunicorn \
    -w 1 \
    -b 0.0.0.0:5000 \
    --timeout 120 \
    --log-level info \
    --access-logfile logs/gunicorn_access.log \
    --error-logfile logs/gunicorn_error.log \
    --capture-output \
    wsgi:app
