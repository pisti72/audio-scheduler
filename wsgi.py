"""
WSGI entry point for production deployment with Gunicorn.
This file is used when running the application with a WSGI server like Gunicorn.
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
APP_ROOT = Path(__file__).resolve().parent
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from app import app, logger, db, init_schedules

# Initialize database and schedules when Gunicorn loads the application
with app.app_context():
    db.create_all()
    logger.info("Database tables created/verified (Gunicorn startup)")

# Initialize schedules
init_schedules()
logger.info("Schedules initialized from database (Gunicorn startup)")

# For Gunicorn, we need to ensure the scheduler is initialized
# The app module already handles this based on WERKZEUG_RUN_MAIN
# In production (Gunicorn), WERKZEUG_RUN_MAIN will be None, so scheduler initializes
logger.info("WSGI application ready for Gunicorn")

if __name__ == "__main__":
    # This won't be used by Gunicorn, but useful for testing
    app.run()
