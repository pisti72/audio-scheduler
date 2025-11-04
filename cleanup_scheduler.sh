#!/bin/bash
# Audio Scheduler - Cleanup Script
# Use this script if you suspect duplicate jobs or zombie processes

echo "🧹 Audio Scheduler Cleanup Script"
echo "=================================="
echo ""

# Find and kill any running Python processes for app.py
echo "1️⃣ Checking for running Audio Scheduler processes..."
PROCESSES=$(ps aux | grep -i "[a]pp.py" | awk '{print $2}')

if [ -z "$PROCESSES" ]; then
    echo "   ✅ No running processes found"
else
    echo "   ⚠️  Found running processes:"
    ps aux | grep -i "[a]pp.py"
    echo ""
    read -p "   Do you want to kill these processes? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "$PROCESSES" | xargs kill -9
        echo "   ✅ Processes terminated"
    else
        echo "   ℹ️  Processes left running"
    fi
fi
echo ""

# Check for any zombie scheduler jobs
echo "2️⃣ Checking scheduler status..."
if [ -f "schedules.db" ]; then
    echo "   ✅ Database found: schedules.db"
    
    # Show schedule count
    SCHEDULE_COUNT=$(sqlite3 schedules.db "SELECT COUNT(*) FROM schedule;" 2>/dev/null)
    if [ $? -eq 0 ]; then
        echo "   📊 Total schedules in database: $SCHEDULE_COUNT"
    fi
else
    echo "   ⚠️  Database not found"
fi
echo ""

# Check for lock files or temp files
echo "3️⃣ Checking for temporary files..."
if [ -f ".apscheduler.lock" ]; then
    echo "   ⚠️  Found scheduler lock file"
    read -p "   Remove lock file? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -f .apscheduler.lock
        echo "   ✅ Lock file removed"
    fi
else
    echo "   ✅ No lock files found"
fi
echo ""

# Summary
echo "4️⃣ Cleanup Summary"
echo "   The application has been updated with:"
echo "   • Automatic job cleanup on startup"
echo "   • Proper scheduler shutdown handlers"
echo "   • Signal handlers for graceful termination"
echo ""
echo "   💡 Tips to prevent duplicate jobs:"
echo "   • Always stop the application with Ctrl+C (SIGINT)"
echo "   • Avoid killing processes with kill -9"
echo "   • Use ./run.sh to start the application"
echo ""
echo "✅ Cleanup complete!"
echo ""
echo "You can now start the application normally."
