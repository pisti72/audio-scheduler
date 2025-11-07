#!/usr/bin/env python3
"""
Production entry point for Audio Scheduler
Runs without debug mode for systemd service deployment
"""
import sys
import pathlib

# Ensure the app root is in the path
APP_ROOT = pathlib.Path(__file__).resolve().parent
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from app import app, logger, scheduler, init_schedules, db

if __name__ == '__main__':
    logger.info("Starting Audio Scheduler in PRODUCTION mode...")
    
    # Create database tables
    with app.app_context():
        db.create_all()
        logger.info("Database tables created/verified")
        
    # Initialize schedules from database
    init_schedules()
    logger.info("Schedules initialized from database")
    
    logger.info("Starting Flask server on 0.0.0.0:5000 (production mode)")
    
    try:
        # Run in production mode (debug=False)
        app.run(debug=False, host='0.0.0.0', port=5000, threaded=True)
    finally:
        # Ensure scheduler is properly shut down on exit
        if scheduler is not None:
            logger.info("Shutting down scheduler...")
            scheduler.stop()
            logger.info("Scheduler shut down complete")
