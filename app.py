import sys
import pathlib
import random
import threading
import time
import logging
import logging.handlers
import signal
import atexit
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory, make_response, abort
import csv
from io import StringIO

# Ensure local package imports work when running from different cwds
APP_ROOT = pathlib.Path(__file__).resolve().parent
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))
from flask_migrate import Migrate
import pygame
import os
from datetime import datetime
import json
from models import db, Schedule, ScheduleList
from auth import login_required, init_credentials, check_credentials, set_credentials

# Configure logging
def setup_logging():
    """Configure logging for the application"""
    # Create logs directory if it doesn't exist
    logs_dir = APP_ROOT.joinpath('logs')
    logs_dir.mkdir(exist_ok=True)
    
    # Create logger
    logger = logging.getLogger('audio_scheduler')
    logger.setLevel(logging.INFO)
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # File handler for all logs (with rotation)
    file_handler = logging.handlers.RotatingFileHandler(
        logs_dir / 'audio_scheduler.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(detailed_formatter)
    
    # File handler for audio playback logs
    audio_handler = logging.handlers.RotatingFileHandler(
        logs_dir / 'audio_playback.log',
        maxBytes=5*1024*1024,   # 5MB
        backupCount=3
    )
    audio_handler.setLevel(logging.INFO)
    audio_handler.setFormatter(simple_formatter)
    audio_handler.addFilter(lambda record: 'audio' in record.name.lower() or 'playlist' in record.getMessage().lower())
    
    # Console handler for important messages
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(audio_handler)
    logger.addHandler(console_handler)
    
    # Create specific loggers
    audio_logger = logging.getLogger('audio_scheduler.audio')
    playlist_logger = logging.getLogger('audio_scheduler.playlist')
    auth_logger = logging.getLogger('audio_scheduler.auth')
    
    return logger, audio_logger, playlist_logger, auth_logger

# Setup logging
logger, audio_logger, playlist_logger, auth_logger = setup_logging()

# Simple Polling-Based Scheduler
class SimpleScheduler:
    """
    Simple polling-based scheduler that checks database every second.
    Much more reliable than APScheduler for this use case - no job lifecycle issues.
    """
    
    def __init__(self, app_instance, db_instance, schedule_model):
        self.app = app_instance
        self.db = db_instance
        self.Schedule = schedule_model
        self.running = False
        self.thread = None
        self.executed_this_minute = set()  # Track what was executed in current minute
        self.last_cleanup_minute = None
        logger.info("SimpleScheduler initialized")
    
    def start(self):
        """Start the scheduler polling thread"""
        if self.running:
            logger.warning("Scheduler already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._schedule_loop, daemon=True, name="SchedulerThread")
        self.thread.start()
        logger.info("✅ Simple scheduler started - polling every second")
    
    def stop(self):
        """Stop the scheduler thread"""
        if not self.running:
            return
        
        logger.info("Stopping scheduler...")
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
        logger.info("✅ Scheduler stopped")
    
    def _schedule_loop(self):
        """Main scheduling loop - checks time every second"""
        last_minute_check = None
        consecutive_errors = 0
        
        while self.running:
            try:
                now = datetime.now()
                current_minute_key = (now.year, now.month, now.day, now.hour, now.minute)
                
                # Clean up executed set when minute changes
                if current_minute_key != self.last_cleanup_minute:
                    self.executed_this_minute.clear()
                    self.last_cleanup_minute = current_minute_key
                    logger.debug(f"New minute: {now.strftime('%H:%M')} - cleared execution tracker")
                
                # Only check schedules once per minute
                if current_minute_key != last_minute_check:
                    last_minute_check = current_minute_key
                    self._check_and_execute_schedules(now)
                    consecutive_errors = 0  # Reset error counter on success
                
                # Sleep for 1 second before next check
                time.sleep(1)
                
            except Exception as e:
                consecutive_errors += 1
                logger.error(f"Error in schedule loop (attempt {consecutive_errors}): {e}", exc_info=True)
                if consecutive_errors > 5:
                    logger.critical("Too many consecutive errors, scheduler loop stopping")
                    break
                time.sleep(5)  # Wait longer on error
    
    def _check_and_execute_schedules(self, now):
        """Check which schedules should run at current time and execute them"""
        with self.app.app_context():
            try:
                from models import ScheduleList
                
                # Get active schedule list
                active_list = ScheduleList.query.filter_by(is_active=True).first()
                if not active_list:
                    return
                
                # Get all non-muted schedules for active list
                schedules = self.Schedule.query.filter_by(
                    schedule_list_id=active_list.id,
                    is_muted=False
                ).all()
                
                current_time = now.strftime('%H:%M')
                current_day = now.weekday()  # 0=Monday, 6=Sunday
                
                logger.debug(f"Checking {len(schedules)} schedules for {current_time}")
                
                for schedule in schedules:
                    # Check if schedule time matches
                    if schedule.time != current_time:
                        continue
                    
                    # Check if schedule day matches
                    day_active = [
                        schedule.monday,    # 0
                        schedule.tuesday,   # 1
                        schedule.wednesday, # 2
                        schedule.thursday,  # 3
                        schedule.friday,    # 4
                        schedule.saturday,  # 5
                        schedule.sunday     # 6
                    ]
                    
                    if not day_active[current_day]:
                        continue
                    
                    # Check if already executed this minute
                    if schedule.id in self.executed_this_minute:
                        logger.debug(f"Skipping schedule {schedule.id} - already executed this minute")
                        continue
                    
                    # Mark as executed for this minute IMMEDIATELY (before starting thread)
                    self.executed_this_minute.add(schedule.id)
                    logger.info(f"🔒 Marked schedule {schedule.id} as executed for minute {current_time}")
                    
                    # Execute schedule in separate thread
                    if schedule.schedule_type == 'playlist':
                        logger.info(f"▶️  Triggering playlist: {schedule.folder_path} at {current_time}")
                        threading.Thread(
                            target=self._execute_playlist,
                            args=(schedule.id,),
                            daemon=True,
                            name=f"Playlist-{schedule.id}"
                        ).start()
                    else:
                        logger.info(f"▶️  Triggering audio: {schedule.filename} at {current_time}")
                        threading.Thread(
                            target=self._execute_audio,
                            args=(schedule.filename,),
                            daemon=True,
                            name=f"Audio-{schedule.id}"
                        ).start()
                
            except Exception as e:
                logger.error(f"Error checking schedules: {e}", exc_info=True)
    
    def _execute_audio(self, filename):
        """Execute single audio file playback"""
        try:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if os.path.exists(file_path):
                play_audio(file_path)
            else:
                audio_logger.error(f"Audio file not found: {file_path}")
        except Exception as e:
            audio_logger.error(f"Error playing audio {filename}: {e}", exc_info=True)
    
    def _execute_playlist(self, schedule_id):
        """Execute playlist playback"""
        try:
            play_playlist(schedule_id)
        except Exception as e:
            playlist_logger.error(f"Error playing playlist {schedule_id}: {e}", exc_info=True)

# Load translations
TRANSLATIONS_PATH = APP_ROOT.joinpath('static', 'translations.json')
with open(TRANSLATIONS_PATH, 'r', encoding='utf-8') as f:
    TRANSLATIONS = json.load(f)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///schedules.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your-secret-key-here'  # Required for session management

# Configure Flask's logging to be less verbose
if not app.debug:
    # Only log warnings and errors from werkzeug in production
    logging.getLogger('werkzeug').setLevel(logging.WARNING)

# Initialize pygame mixer - handle gracefully if no audio device available
try:
    pygame.mixer.init()
    audio_available = True
    audio_logger.info("Audio system initialized successfully")
except Exception as e:
    audio_available = False
    audio_logger.warning(f"Audio system not available: {str(e)}")

# Initialize database
db.init_app(app)
migrate = Migrate(app, db)

# Initialize scheduler only once (not in reloader process)
# Flask debug mode spawns two processes: main (worker) and reloader
# WERKZEUG_RUN_MAIN is None in reloader process, 'true' in main worker
# We only want the scheduler in the main worker process
import os
werkzeug_run_main = os.environ.get('WERKZEUG_RUN_MAIN')

# Only initialize if NOT in the reloader process
# When None: first launch (before reloader starts) - SKIP
# When 'true': main worker process after reloader - INITIALIZE
if werkzeug_run_main == 'true':
    # Main worker process - initialize scheduler
    from models import Schedule
    scheduler = SimpleScheduler(app, db, Schedule)
    scheduler.start()
    logger.info("✅ Simple polling scheduler initialized and started")
    
    # Register cleanup handlers to ensure scheduler shuts down properly
    def cleanup_scheduler():
        """Clean up scheduler on application exit"""
        if scheduler is not None:
            logger.info("Cleaning up scheduler on exit...")
            try:
                scheduler.stop()
                logger.info("Scheduler shutdown complete")
            except Exception as e:
                logger.error(f"Error during scheduler shutdown: {e}")
    
    # Register cleanup for normal exit
    atexit.register(cleanup_scheduler)
    
    # Register cleanup for signal interrupts (Ctrl+C, kill, etc.)
    def signal_handler(signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        cleanup_scheduler()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
else:
    scheduler = None

# Initialize default credentials
auth_logger.info("Initializing credentials...")
init_credentials()
auth_logger.info("Credentials initialization completed")

def init_schedules():
    """Initialize schedules from database"""
    with app.app_context():
        # With SimpleScheduler, no job cleanup needed
        # Schedules are automatically loaded from database each minute
        if scheduler is not None:
            logger.info("✅ SimpleScheduler will automatically load schedules from database")
        
        # Get active schedule list
        active_list = ScheduleList.query.filter_by(is_active=True).first()
        
        # Create default list if none exists
        if not active_list:
            active_list = ScheduleList(name='Default', is_active=True)
            db.session.add(active_list)
            db.session.commit()
        
        # Load schedules from active list only
        schedules = Schedule.query.filter_by(schedule_list_id=active_list.id).all()
        jobs_added = 0
        for schedule in schedules:
            if add_job_to_scheduler(schedule):
                jobs_added += 1
        logger.info(f"Initialized {jobs_added} schedule jobs from database")

def reload_all_schedules():
    """
    No-op function for compatibility.
    With SimpleScheduler, schedules are automatically loaded from database each minute.
    No need to manually reload - database is the source of truth.
    """
    if scheduler is None:
        return
    logger.info("✅ Schedules will be automatically reloaded from database by SimpleScheduler")

def play_audio(file_path):
    try:
        if not audio_available:
            audio_logger.warning(f"Audio playback skipped (no audio device): {file_path}")
            return
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
        audio_logger.info(f"Playing audio: {file_path}")
    except Exception as e:
        audio_logger.error(f"Error playing audio: {str(e)}")

def play_playlist(schedule_id):
    """Play a playlist based on schedule configuration"""
    
    try:
        # Ensure we're in an application context for database access
        with app.app_context():
            # Get the schedule
            schedule = db.session.get(Schedule, schedule_id)
            if not schedule or schedule.schedule_type != 'playlist':
                playlist_logger.error(f"Invalid playlist schedule ID: {schedule_id}")
                return
                
            # Check if muted
            if schedule.is_muted:
                playlist_logger.info(f"Playlist schedule {schedule_id} is muted, skipping")
                return
            
            # Get folder path and validate
            folder_path = APP_ROOT.joinpath(schedule.folder_path)
            if not folder_path.exists() or not folder_path.is_dir():
                playlist_logger.error(f"Playlist folder not found: {folder_path}")
                return
            
            # Get audio files
            audio_files = []
            for ext in ['*.mp3', '*.wav', '*.ogg', '*.m4a', '*.flac']:
                audio_files.extend(list(folder_path.glob(ext)))
                audio_files.extend(list(folder_path.glob(ext.upper())))
            
            if not audio_files:
                playlist_logger.warning(f"No audio files found in playlist folder: {folder_path}")
                return
            
            # Sort alphabetically first to ensure consistent order
            audio_files.sort(key=lambda f: f.name.lower())
            
            # Shuffle if enabled
            if schedule.shuffle_mode:
                random.shuffle(audio_files)
            
            playlist_logger.info(f"Starting playlist: {schedule.folder_path}, Duration: {schedule.playlist_duration or 60}min, Interval: {schedule.track_interval}sec")
            
            # Start playlist in a separate thread
            playlist_thread = threading.Thread(
                target=_run_playlist,
                args=(audio_files, schedule.playlist_duration or 60, schedule.track_interval, schedule.max_tracks, schedule.shuffle_mode),
                daemon=True
            )
            playlist_thread.start()
        
    except Exception as e:
        playlist_logger.error(f"Error starting playlist {schedule_id}: {str(e)}")

def _run_playlist(audio_files, duration_minutes, track_interval_seconds, max_tracks, shuffle_mode):
    """Run the playlist in a separate thread"""
    
    if not audio_available:
        playlist_logger.warning("Audio playback skipped (no audio device)")
        return
    
    start_time = time.time()
    # Handle None duration by setting a default of 60 minutes
    if duration_minutes is None:
        duration_minutes = 60
        playlist_logger.warning("No duration specified, using default of 60 minutes")
    end_time = start_time + (duration_minutes * 60)
    tracks_played = 0
    file_list = list(audio_files)  # Make a copy
    
    while time.time() < end_time and (max_tracks is None or tracks_played < max_tracks):
        # If we've played all files and shuffle is enabled, reshuffle
        if not file_list and shuffle_mode:
            file_list = list(audio_files)
            random.shuffle(file_list)
        elif not file_list:
            # If no shuffle, reset to original list
            file_list = list(audio_files)
        
        # Get next file
        audio_file = file_list.pop(0)
        
        try:
            playlist_logger.info(f"Playing playlist track: {audio_file.name}")
            pygame.mixer.music.load(str(audio_file))
            pygame.mixer.music.play()
            
            # Wait for the track to finish playing completely
            track_start = time.time()
            
            # Wait for track to finish playing naturally
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
                # Check if we've exceeded the total playlist duration while playing
                if time.time() >= end_time:
                    pygame.mixer.music.stop()
                    playlist_logger.info("Track stopped due to playlist duration limit")
                    break
            
            track_end = time.time()
            track_duration = track_end - track_start
            playlist_logger.info(f"Track '{audio_file.name}' finished after {track_duration:.1f}s")
            
            tracks_played += 1
            
            # Check if we've exceeded the total playlist duration
            if time.time() >= end_time:
                break
                
            # Wait for the interval time before starting the next track
            if track_interval_seconds and track_interval_seconds > 0:
                # Check if we have enough time left for the full interval
                if time.time() + track_interval_seconds < end_time:
                    playlist_logger.debug(f"Waiting {track_interval_seconds}s interval before next track")
                    time.sleep(track_interval_seconds)
                else:
                    # Wait only for the remaining time if playlist duration is about to end
                    remaining_time = end_time - time.time()
                    if remaining_time > 0:
                        playlist_logger.debug(f"Waiting {remaining_time:.1f}s (shortened interval due to playlist duration limit)")
                        time.sleep(remaining_time)
                
        except Exception as e:
            playlist_logger.error(f"Error playing playlist track {audio_file}: {str(e)}")
            tracks_played += 1  # Count failed attempts to prevent infinite loops
    
    playlist_logger.info(f"Playlist finished. Played {tracks_played} tracks in {(time.time() - start_time) / 60:.1f} minutes")

@app.route('/audio/<path:filename>')
@login_required
def serve_audio(filename):
    """Serve audio files for preview"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/set-language/<lang>')
def set_language(lang):
    """Set UI language in session.
    If the requested language isn't currently loaded, attempt to reload translations from disk
    so newly added languages in translations.json are recognized without restarting the server.
    """
    global TRANSLATIONS
    if lang not in TRANSLATIONS:
        try:
            with open(TRANSLATIONS_PATH, 'r', encoding='utf-8') as f:
                TRANSLATIONS = json.load(f)
        except Exception:
            # If reload fails, still set the session; views will fallback to English
            pass
    session['lang'] = lang
    return jsonify({'success': True})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if 'logged_in' in session:
            return redirect(url_for('index'))
        current_lang = session.get('lang', 'en')
        translations = TRANSLATIONS.get(current_lang, TRANSLATIONS['en'])
        js_translations = json.dumps({
            'login': translations.get('login', {})
        })
        return render_template('login.html', 
                               translations=translations,
                               current_lang=current_lang,
                               js_translations=js_translations)

    auth_logger.info("Login attempt received")
    data = request.get_json()
    auth_logger.debug(f"Received login data from user")
    username = data.get('username')
    password = data.get('password')
    auth_logger.debug(f"Login attempt for username: {username}")

    if check_credentials(username, password):
        session['logged_in'] = True
        session['username'] = username
        auth_logger.info(f"Successful login for user: {username}")
        return jsonify({'success': True})
    auth_logger.warning(f"Failed login attempt for username: {username}")
    return jsonify({'success': False, 'error': 'Invalid username or password'})

@app.route('/manual')
@login_required
def manual():
    # Render the manual page with current language translations
    current_lang = session.get('lang', 'en')
    translations = TRANSLATIONS.get(current_lang, TRANSLATIONS['en'])
    return render_template('manual.html', 
                           translations=translations,
                           current_lang=current_lang)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/settings')
@login_required
def settings():
    current_lang = session.get('lang', 'en')
    translations = TRANSLATIONS.get(current_lang, TRANSLATIONS['en'])
    js_translations = json.dumps({
        'settings': translations.get('settings', {})
    })
    return render_template('settings.html', 
                           translations=translations,
                           current_lang=current_lang,
                           js_translations=js_translations)

@app.route('/settings/update', methods=['POST'])
@login_required
def update_settings():
    data = request.get_json()
    new_username = data.get('newUsername')
    current_password = data.get('currentPassword')
    new_password = data.get('newPassword')

    # Verify current password
    if not check_credentials(session.get('username'), current_password):
        return jsonify({'success': False, 'error': 'Invalid current password'})

    # Update credentials
    try:
        set_credentials(new_username, new_password if new_password else current_password)
        return jsonify({
            'success': True, 
            'requireRelogin': True if new_username != session.get('username') else False
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/settings/export_csv')
@login_required
def export_schedules_csv():
    try:
        # Get the active schedule list
        active_list = ScheduleList.query.filter_by(is_active=True).first()
        if not active_list:
            return jsonify({'success': False, 'error': 'No active schedule list found'})
        
        # Get all schedules for the active list
        schedules = Schedule.query.filter_by(schedule_list_id=active_list.id).all()
        
        # Create CSV content
        output = StringIO()
        writer = csv.writer(output)
        
        # Write CSV header
        writer.writerow([
            'Schedule List Name',
            'Audio File',
            'Time',
            'Days',
            'Is Muted',
            'Created Date'
        ])
        
        # Write schedule data
        for schedule in schedules:
            # Convert days list to readable format
            days_map = {
                0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday',
                4: 'Friday', 5: 'Saturday', 6: 'Sunday'
            }
            
            # Get active days from boolean columns
            days_boolean = [
                schedule.monday, schedule.tuesday, schedule.wednesday,
                schedule.thursday, schedule.friday, schedule.saturday, schedule.sunday
            ]
            
            active_days = [i for i, day in enumerate(days_boolean) if day]
            days_names = [days_map.get(day, f'Day{day}') for day in active_days]
            days_str = ', '.join(days_names) if days_names else 'No days selected'
            
            writer.writerow([
                active_list.name,
                schedule.filename,
                schedule.time,
                days_str,
                'Yes' if schedule.is_muted else 'No',
                schedule.created_at.strftime('%Y-%m-%d %H:%M:%S') if hasattr(schedule, 'created_at') and schedule.created_at else 'Unknown'
            ])
        
        # Create response
        csv_content = output.getvalue()
        output.close()
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"audio_schedules_{active_list.name}_{timestamp}.csv"
        
        # Create response with CSV content
        response = make_response(csv_content)
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Export failed: {str(e)}'})

@app.route('/settings/import_csv', methods=['POST'])
@login_required
def import_schedules_csv():
    try:
        # Check if file was uploaded
        if 'csv_file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'})
        
        file = request.files['csv_file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})
        
        if not file.filename.lower().endswith('.csv'):
            return jsonify({'success': False, 'error': 'File must be a CSV file'})
        
        # Get the active schedule list
        active_list = ScheduleList.query.filter_by(is_active=True).first()
        if not active_list:
            return jsonify({'success': False, 'error': 'No active schedule list found'})
        
        # Read and parse CSV content
        content = file.read().decode('utf-8')
        csv_reader = csv.DictReader(StringIO(content))
        
        # Validate CSV headers
        required_headers = ['Audio File', 'Time', 'Days']
        missing_headers = [h for h in required_headers if h not in csv_reader.fieldnames]
        if missing_headers:
            return jsonify({'success': False, 'error': f'Missing required columns: {", ".join(missing_headers)}'})
        
        # Parse and validate CSV data
        new_schedules = []
        days_map = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        
        for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 since row 1 is headers
            try:
                # Validate audio file
                audio_file = row['Audio File'].strip()
                if not audio_file:
                    return jsonify({'success': False, 'error': f'Row {row_num}: Audio file cannot be empty'})
                
                # Validate time format (HH:MM)
                time_str = row['Time'].strip()
                try:
                    datetime.strptime(time_str, '%H:%M')
                except ValueError:
                    return jsonify({'success': False, 'error': f'Row {row_num}: Invalid time format. Use HH:MM (e.g., 14:30)'})
                
                # Parse days
                days_str = row['Days'].strip().lower()
                schedule_days = {
                    'monday': False, 'tuesday': False, 'wednesday': False, 'thursday': False,
                    'friday': False, 'saturday': False, 'sunday': False
                }
                
                if days_str and days_str != 'no days selected':
                    day_names = [d.strip().lower() for d in days_str.split(',')]
                    for day_name in day_names:
                        if day_name in days_map:
                            schedule_days[day_name] = True
                        else:
                            return jsonify({'success': False, 'error': f'Row {row_num}: Invalid day name "{day_name}". Use Monday, Tuesday, etc.'})
                
                # Parse muted status
                is_muted = False
                if 'Is Muted' in row:
                    muted_str = row['Is Muted'].strip().lower()
                    is_muted = muted_str in ['yes', 'true', '1']
                
                new_schedules.append({
                    'filename': audio_file,
                    'time': time_str,
                    'days': schedule_days,
                    'is_muted': is_muted
                })
                
            except Exception as e:
                return jsonify({'success': False, 'error': f'Row {row_num}: {str(e)}'})
        
        if not new_schedules:
            return jsonify({'success': False, 'error': 'No valid schedules found in CSV file'})
        
        # Delete existing schedules for the active list and insert new ones
        try:
            # With SimpleScheduler, no manual job removal needed
            # Schedules automatically picked up from database
            # Just delete from database and new schedules will be used automatically
            
            # Delete existing schedules from database
            Schedule.query.filter_by(schedule_list_id=active_list.id).delete()
            
            # Add new schedules
            for schedule_data in new_schedules:
                new_schedule = Schedule(
                    filename=schedule_data['filename'],
                    time=schedule_data['time'],
                    monday=schedule_data['days']['monday'],
                    tuesday=schedule_data['days']['tuesday'],
                    wednesday=schedule_data['days']['wednesday'],
                    thursday=schedule_data['days']['thursday'],
                    friday=schedule_data['days']['friday'],
                    saturday=schedule_data['days']['saturday'],
                    sunday=schedule_data['days']['sunday'],
                    is_muted=schedule_data['is_muted'],
                    schedule_list_id=active_list.id
                )
                db.session.add(new_schedule)
            
            # Commit all changes
            db.session.commit()
            
            # Re-schedule all jobs
            reload_all_schedules()
            
            return jsonify({
                'success': True, 
                'message': f'Successfully imported {len(new_schedules)} schedules. Existing schedules were replaced.'
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': f'Database error: {str(e)}'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Import failed: {str(e)}'})

@app.route('/')
@login_required
def index():
    # Get list of uploaded files
    uploaded_files = []
    if os.path.exists(app.config['UPLOAD_FOLDER']):
        uploaded_files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) 
                        if os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'], f))
                        and f != '.gitkeep']  # Exclude .gitkeep file
    
    # Get current language from session or default to English
    current_lang = session.get('lang', 'en')
    translations = TRANSLATIONS.get(current_lang, TRANSLATIONS['en'])
    
    # Pre-serialize the translations data needed for JavaScript
    js_translations = json.dumps({
           'navigation': translations['navigation'],
        'days_list': translations['schedule']['days_list'],
           'current_schedules': translations['current_schedules'],
           'schedule_lists': translations.get('schedule_lists', {}),
           'playlist': translations.get('playlist', {}),
           'modals': translations['modals']
    })
    
    return render_template('index.html', 
                           uploaded_files=uploaded_files,
                           translations=translations,
                           current_lang=current_lang,
                           js_translations=js_translations)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'audio' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['audio']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file:
        filename = file.filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        logger.info(f"Audio file uploaded successfully: {filename}")
        return jsonify({'success': True, 'filename': filename})

def add_job_to_scheduler(schedule):
    """
    Validate schedule before adding to database.
    With SimpleScheduler, no manual job registration needed - automatically loaded from DB.
    """
    # Skip if scheduler not initialized (reloader process)
    if scheduler is None:
        return True
    
    # Skip muted schedules
    if schedule.is_muted:
        return True
    
    # Validate based on schedule type
    if schedule.schedule_type == 'playlist':
        return add_playlist_job_to_scheduler(schedule)
    else:
        return add_single_file_job_to_scheduler(schedule)

def add_single_file_job_to_scheduler(schedule):
    """
    Validate single file schedule.
    With SimpleScheduler, no job registration needed - schedules loaded from DB automatically.
    """
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], schedule.filename)
    if not os.path.exists(file_path):
        logger.warning(f"Audio file not found for schedule {schedule.id}: {file_path}")
        return False
    return True

def add_playlist_job_to_scheduler(schedule):
    """
    Validate playlist schedule.
    With SimpleScheduler, no job registration needed - schedules loaded from DB automatically.
    """
    # Validate folder exists
    folder_path = APP_ROOT.joinpath(schedule.folder_path)
    if not folder_path.exists() or not folder_path.is_dir():
        logger.warning(f"Playlist folder not found for schedule {schedule.id}: {folder_path}")
        return False
    
    # Check for audio files
    audio_files = []
    for ext in ['*.mp3', '*.wav', '*.ogg', '*.m4a', '*.flac']:
        audio_files.extend(list(folder_path.glob(ext)))
        audio_files.extend(list(folder_path.glob(ext.upper())))
    
    if not audio_files:
        logger.warning(f"No audio files found in playlist folder for schedule {schedule.id}: {folder_path}")
        return False
    
    return True

@app.route('/schedule', methods=['POST'])
def schedule_audio():
    data = request.json
    filename = data.get('filename')
    schedule_data = data.get('schedule', [])[0]  # Get the first schedule entry
    
    if not filename or not schedule_data:
        return jsonify({'error': 'Invalid schedule data'}), 400

    time = schedule_data.get('time')
    days = schedule_data.get('days', [])

    if not time or not days:
        return jsonify({'error': 'Missing time or days'}), 400

    # Get active schedule list
    active_list = ScheduleList.query.filter_by(is_active=True).first()
    
    # Create default list if none exists
    if not active_list:
        active_list = ScheduleList(name='Default', is_active=True)
        db.session.add(active_list)
        db.session.commit()

    # Create new schedule in database
    schedule = Schedule(
        schedule_list_id=active_list.id,
        filename=filename,
        time=time,
        monday=0 in days,
        tuesday=1 in days,
        wednesday=2 in days,
        thursday=3 in days,
        friday=4 in days,
        saturday=5 in days,
        sunday=6 in days
    )

    db.session.add(schedule)
    db.session.commit()

    # Add to scheduler
    if add_job_to_scheduler(schedule):
        logger.info(f"Single file schedule added successfully: {filename} at {time} on days {days}")
        return jsonify({'success': True, 'id': schedule.id})
    else:
        db.session.delete(schedule)
        db.session.commit()
        logger.error(f"Failed to add schedule - audio file not found: {filename}")
        return jsonify({'error': 'Audio file not found'}), 404

@app.route('/add_playlist_schedule', methods=['POST'])
@login_required
def add_playlist_schedule():
    """Add a new playlist schedule"""
    try:
        data = request.json
        folder_path = data.get('folder_path')
        time = data.get('time')
        days = data.get('days', [])
        playlist_duration = data.get('playlist_duration')
        max_tracks = data.get('max_tracks')
        track_interval = data.get('track_interval', 10)
        shuffle_mode = data.get('shuffle_mode', True)
        
        # Set default duration if not provided or None
        if playlist_duration is None or playlist_duration == '':
            playlist_duration = 60  # Default to 60 minutes
        else:
            try:
                playlist_duration = int(playlist_duration)
                if playlist_duration <= 0:
                    playlist_duration = 60
            except (ValueError, TypeError):
                playlist_duration = 60
        
        if not folder_path or not time or not days:
            return jsonify({'error': 'Missing required fields: folder_path, time, or days'}), 400
        
        # Validate folder exists and has audio files
        full_folder_path = APP_ROOT.joinpath(folder_path)
        if not full_folder_path.exists() or not full_folder_path.is_dir():
            return jsonify({'error': 'Playlist folder not found'}), 400
        
        # Count audio files
        audio_files = []
        for ext in ['*.mp3', '*.wav', '*.ogg', '*.m4a', '*.flac']:
            audio_files.extend(list(full_folder_path.glob(ext)))
            audio_files.extend(list(full_folder_path.glob(ext.upper())))
        
        if not audio_files:
            return jsonify({'error': 'No audio files found in the selected folder'}), 400
        
        # Get active schedule list
        active_list = ScheduleList.query.filter_by(is_active=True).first()
        if not active_list:
            active_list = ScheduleList(name='Default', is_active=True)
            db.session.add(active_list)
            db.session.commit()
        
        # Create new playlist schedule
        schedule = Schedule(
            schedule_list_id=active_list.id,
            schedule_type='playlist',
            folder_path=folder_path,
            time=time,
            monday=0 in days,
            tuesday=1 in days,
            wednesday=2 in days,
            thursday=3 in days,
            friday=4 in days,
            saturday=5 in days,
            sunday=6 in days,
            playlist_duration=playlist_duration,
            max_tracks=max_tracks,
            track_interval=track_interval,
            shuffle_mode=shuffle_mode
        )
        
        db.session.add(schedule)
        db.session.commit()
        
        # Add to scheduler (will be handled by modified scheduler logic)
        if add_job_to_scheduler(schedule):
            logger.info(f"Playlist schedule added successfully: {folder_path} at {time} on days {days}")
            return jsonify({'success': True, 'id': schedule.id})
        else:
            db.session.delete(schedule)
            db.session.commit()
            logger.error(f"Failed to add playlist schedule: {folder_path}")
            return jsonify({'error': 'Failed to schedule playlist'}), 500
            
    except Exception as e:
        logger.error(f"Exception in add_playlist_schedule: {str(e)}")
        return jsonify({'error': f'Failed to add playlist schedule: {str(e)}'}), 500

@app.route('/get_schedules', methods=['GET'])
def get_schedules():
    # Get active schedule list
    active_list = ScheduleList.query.filter_by(is_active=True).first()
    
    if not active_list:
        # Create default list if none exists
        active_list = ScheduleList(name='Default', is_active=True)
        db.session.add(active_list)
        db.session.commit()
    
    # Get schedules ordered by time ascending
    schedules = Schedule.query.filter_by(schedule_list_id=active_list.id).order_by(Schedule.time.asc()).all()
    return jsonify([schedule.to_dict() for schedule in schedules])

@app.route('/get_playlist_folders', methods=['GET'])
@login_required
def get_playlist_folders():
    """Get list of available playlist folders"""
    try:
        playlists_dir = APP_ROOT.joinpath('playlists')
        
        # Create playlists directory if it doesn't exist
        if not playlists_dir.exists():
            playlists_dir.mkdir(exist_ok=True)
            return jsonify([])
        
        folders = []
        for item in playlists_dir.iterdir():
            if item.is_dir():
                # Count audio files in the folder
                audio_files = []
                for ext in ['*.mp3', '*.wav', '*.ogg', '*.m4a', '*.flac']:
                    audio_files.extend(list(item.glob(ext)))
                    audio_files.extend(list(item.glob(ext.upper())))
                
                folders.append({
                    'name': item.name,
                    'path': str(item.relative_to(APP_ROOT)),
                    'file_count': len(audio_files),
                    'files': [f.name for f in audio_files[:5]]  # Show first 5 files as preview
                })
        
        # Sort folders by name
        folders.sort(key=lambda x: x['name'])
        return jsonify(folders)
        
    except Exception as e:
        return jsonify({'error': f'Failed to get playlist folders: {str(e)}'}), 500

@app.route('/delete_schedule/<int:schedule_id>', methods=['DELETE'])
def delete_schedule(schedule_id):
    schedule = db.session.get(Schedule, schedule_id) or abort(404)
    schedule_info = f"ID:{schedule_id}, File:{schedule.filename if schedule.schedule_type != 'playlist' else schedule.folder_path}"
    
    # With SimpleScheduler, no manual job removal needed
    # Just delete from database and it won't be executed anymore
    
    # Remove from database
    db.session.delete(schedule)
    db.session.commit()
    
    logger.info(f"Schedule deleted: {schedule_info}")
    return jsonify({'success': True})

@app.route('/update_schedule/<int:schedule_id>', methods=['POST'])
def update_schedule(schedule_id):
    """Update an existing schedule's time and days, then refresh its job."""
    schedule = db.session.get(Schedule, schedule_id) or abort(404)
    data = request.get_json() or {}

    # Extract fields
    new_time = data.get('time')
    new_days = data.get('days', [])  # expects list of indices 0..6

    # Basic validation
    if not new_time or not isinstance(new_days, list):
        return jsonify({'success': False, 'error': 'Invalid update payload'}), 400

    # Update fields
    schedule.time = new_time
    schedule.monday = 0 in new_days
    schedule.tuesday = 1 in new_days
    schedule.wednesday = 2 in new_days
    schedule.thursday = 3 in new_days
    schedule.friday = 4 in new_days
    schedule.saturday = 5 in new_days
    schedule.sunday = 6 in new_days

    db.session.commit()

    # With SimpleScheduler, changes automatically picked up from database
    # No need to manually update jobs - database is the source of truth
    if scheduler is not None:
        logger.debug(f"Schedule {schedule.id} updated - SimpleScheduler will use new values automatically")

    return jsonify({'success': True, 'schedule': schedule.to_dict()})

@app.route('/toggle_mute/<int:schedule_id>', methods=['POST'])
@login_required
def toggle_mute(schedule_id):
    schedule = db.session.get(Schedule, schedule_id) or abort(404)
    schedule_info = f"ID:{schedule_id}, File:{schedule.filename if schedule.schedule_type != 'playlist' else schedule.folder_path}"
    
    # Toggle mute status
    schedule.is_muted = not schedule.is_muted
    db.session.commit()
    
    # With SimpleScheduler, mute status automatically checked from database
    # No manual job removal needed - scheduler checks is_muted flag automatically
    if scheduler is not None:
        if schedule.is_muted:
            logger.info(f"Schedule muted: {schedule_info}")
        else:
            logger.info(f"Schedule unmuted: {schedule_info}")
    
    return jsonify({'success': True, 'is_muted': schedule.is_muted})

@app.route('/schedule_lists', methods=['GET'])
@login_required
def get_schedule_lists():
    lists = ScheduleList.query.all()
    return jsonify([list.to_dict() for list in lists])

@app.route('/schedule_lists', methods=['POST'])
@login_required
def create_schedule_list():
    data = request.json
    name = data.get('name')
    
    if not name:
        return jsonify({'error': 'Name is required'}), 400
    
    # Create new schedule list
    schedule_list = ScheduleList(name=name, is_active=False)
    db.session.add(schedule_list)
    db.session.commit()
    
    return jsonify({'success': True, 'list': schedule_list.to_dict()})

@app.route('/schedule_lists/<int:list_id>/activate', methods=['POST'])
@login_required
def activate_schedule_list(list_id):
    # Deactivate all lists
    db.session.query(ScheduleList).update({ScheduleList.is_active: False})
    
    # Activate the selected list
    schedule_list = db.session.get(ScheduleList, list_id) or abort(404)
    schedule_list.is_active = True
    db.session.commit()
    
    # Reload all schedules using the proper function
    reload_all_schedules()
    
    logger.info(f"Activated schedule list: {schedule_list.name}")
    return jsonify({'success': True})

@app.route('/schedule_lists/<int:list_id>', methods=['DELETE'])
@login_required
def delete_schedule_list(list_id):
    schedule_list = db.session.get(ScheduleList, list_id) or abort(404)
    
    # Don't allow deleting the active list if it's the only one
    if schedule_list.is_active and ScheduleList.query.count() == 1:
        return jsonify({'error': 'Cannot delete the last schedule list'}), 400
    
    # If deleting active list, activate another one
    if schedule_list.is_active:
        other_list = ScheduleList.query.filter(ScheduleList.id != list_id).first()
        if other_list:
            other_list.is_active = True
    
    db.session.delete(schedule_list)
    db.session.commit()
    
    # Reload schedules using the proper function
    reload_all_schedules()
    
    logger.info(f"Deleted schedule list: {schedule_list.name}")
    return jsonify({'success': True})

@app.route('/get_server_ip')
@login_required
def get_server_ip():
    """Get the server's local IP address"""
    import socket
    try:
        # Connect to a remote address to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return jsonify({'ip': local_ip})
    except Exception:
        try:
            # Fallback method
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            return jsonify({'ip': local_ip})
        except Exception:
            return jsonify({'ip': None, 'error': 'Unable to determine IP'}), 500

@app.route('/schedule_lists/<int:list_id>/rename', methods=['POST'])
@login_required
def rename_schedule_list(list_id):
    data = request.json
    new_name = data.get('name')
    
    if not new_name:
        return jsonify({'error': 'Name is required'}), 400
    
    schedule_list = db.session.get(ScheduleList, list_id) or abort(404)
    schedule_list.name = new_name
    db.session.commit()
    
    return jsonify({'success': True})

if __name__ == '__main__':
    logger.info("Starting Audio Scheduler application...")
    
    # Create database tables
    with app.app_context():
        db.create_all()
        logger.info("Database tables created/verified")
        
    # Initialize schedules from database
    init_schedules()
    logger.info("Schedules initialized from database")
    
    logger.info("Starting Flask server on 0.0.0.0:5000")
    
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    finally:
        # Ensure scheduler is properly shut down on exit
        if scheduler is not None:
            logger.info("Shutting down scheduler...")
            scheduler.stop()
            logger.info("Scheduler shut down complete")