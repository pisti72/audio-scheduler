import sys
import pathlib
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory

# Ensure local package imports work when running from different cwds
APP_ROOT = pathlib.Path(__file__).resolve().parent
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from flask_migrate import Migrate
import pygame
import os
from datetime import datetime
import json
from models import db, Schedule, ScheduleList
from auth import login_required, init_credentials, check_credentials, set_credentials

# Load translations
TRANSLATIONS_PATH = APP_ROOT.joinpath('static', 'translations.json')
with open(TRANSLATIONS_PATH, 'r', encoding='utf-8') as f:
    TRANSLATIONS = json.load(f)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///schedules.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your-secret-key-here'  # Required for session management

# Initialize pygame mixer - handle gracefully if no audio device available
try:
    pygame.mixer.init()
    audio_available = True
    print("Audio system initialized successfully")
except Exception as e:
    audio_available = False
    print(f"Audio system not available: {str(e)}")

# Initialize database
db.init_app(app)
migrate = Migrate(app, db)

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.start()

# Initialize default credentials
print("Initializing credentials...") # Debug log
init_credentials()
print("Credentials initialization completed") # Debug log

def init_schedules():
    """Initialize schedules from database"""
    with app.app_context():
        # Get active schedule list
        active_list = ScheduleList.query.filter_by(is_active=True).first()
        
        # Create default list if none exists
        if not active_list:
            active_list = ScheduleList(name='Default', is_active=True)
            db.session.add(active_list)
            db.session.commit()
        
        # Load schedules from active list only
        schedules = Schedule.query.filter_by(schedule_list_id=active_list.id).all()
        for schedule in schedules:
            add_job_to_scheduler(schedule)

# Initialize default credentials
init_credentials()

def play_audio(file_path):
    try:
        if not audio_available:
            print(f"Audio playback skipped (no audio device): {file_path}")
            return
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
        print(f"Playing audio: {file_path}")
    except Exception as e:
        print(f"Error playing audio: {str(e)}")

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

    print("Login attempt received") # Debug log
    data = request.get_json()
    print(f"Received data: {data}") # Debug log
    username = data.get('username')
    password = data.get('password')
    print(f"Username: {username}, Password: {password}") # Debug log

    if check_credentials(username, password):
        session['logged_in'] = True
        session['username'] = username
        return jsonify({'success': True})
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
        return jsonify({'success': True, 'filename': filename})

def add_job_to_scheduler(schedule):
    """Add a schedule to the APScheduler"""
    # Skip muted schedules
    if schedule.is_muted:
        return True
    
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], schedule.filename)
    if not os.path.exists(file_path):
        return False

    days = []
    if schedule.monday: days.append('0')
    if schedule.tuesday: days.append('1')
    if schedule.wednesday: days.append('2')
    if schedule.thursday: days.append('3')
    if schedule.friday: days.append('4')
    if schedule.saturday: days.append('5')
    if schedule.sunday: days.append('6')

    hour, minute = map(int, schedule.time.split(':'))
    day_of_week = ','.join(days)
    
    job_id = f"schedule_{schedule.id}"
    scheduler.add_job(
        play_audio,
        CronTrigger(day_of_week=day_of_week, hour=hour, minute=minute),
        args=[file_path],
        id=job_id
    )
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
        return jsonify({'success': True, 'id': schedule.id})
    else:
        db.session.delete(schedule)
        db.session.commit()
        return jsonify({'error': 'Audio file not found'}), 404

@app.route('/get_schedules', methods=['GET'])
def get_schedules():
    # Get active schedule list
    active_list = ScheduleList.query.filter_by(is_active=True).first()
    
    if not active_list:
        # Create default list if none exists
        active_list = ScheduleList(name='Default', is_active=True)
        db.session.add(active_list)
        db.session.commit()
    
    schedules = Schedule.query.filter_by(schedule_list_id=active_list.id).all()
    return jsonify([schedule.to_dict() for schedule in schedules])

@app.route('/delete_schedule/<int:schedule_id>', methods=['DELETE'])
def delete_schedule(schedule_id):
    schedule = Schedule.query.get_or_404(schedule_id)
    
    # Remove from scheduler
    job_id = f"schedule_{schedule.id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
    
    # Remove from database
    db.session.delete(schedule)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/update_schedule/<int:schedule_id>', methods=['POST'])
def update_schedule(schedule_id):
    """Update an existing schedule's time and days, then refresh its job."""
    schedule = Schedule.query.get_or_404(schedule_id)
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

    # Refresh job in scheduler
    job_id = f"schedule_{schedule.id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)

    # Only re-add if not muted and file exists
    add_job_to_scheduler(schedule)

    return jsonify({'success': True, 'schedule': schedule.to_dict()})

@app.route('/toggle_mute/<int:schedule_id>', methods=['POST'])
@login_required
def toggle_mute(schedule_id):
    schedule = Schedule.query.get_or_404(schedule_id)
    
    # Toggle mute status
    schedule.is_muted = not schedule.is_muted
    db.session.commit()
    
    # Update scheduler job
    job_id = f"schedule_{schedule.id}"
    
    if schedule.is_muted:
        # Remove job from scheduler when muted
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)
    else:
        # Add job back to scheduler when unmuted
        add_job_to_scheduler(schedule)
    
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
    ScheduleList.query.update({ScheduleList.is_active: False})
    
    # Activate the selected list
    schedule_list = ScheduleList.query.get_or_404(list_id)
    schedule_list.is_active = True
    db.session.commit()
    
    # Reload all schedules
    # Remove all current jobs
    for job in scheduler.get_jobs():
        scheduler.remove_job(job.id)
    
    # Add jobs from active list
    schedules = Schedule.query.filter_by(schedule_list_id=list_id).all()
    for schedule in schedules:
        add_job_to_scheduler(schedule)
    
    return jsonify({'success': True})

@app.route('/schedule_lists/<int:list_id>', methods=['DELETE'])
@login_required
def delete_schedule_list(list_id):
    schedule_list = ScheduleList.query.get_or_404(list_id)
    
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
    
    # Reload schedules
    for job in scheduler.get_jobs():
        scheduler.remove_job(job.id)
    
    active_list = ScheduleList.query.filter_by(is_active=True).first()
    if active_list:
        schedules = Schedule.query.filter_by(schedule_list_id=active_list.id).all()
        for schedule in schedules:
            add_job_to_scheduler(schedule)
    
    return jsonify({'success': True})

@app.route('/schedule_lists/<int:list_id>/rename', methods=['POST'])
@login_required
def rename_schedule_list(list_id):
    data = request.json
    new_name = data.get('name')
    
    if not new_name:
        return jsonify({'error': 'Name is required'}), 400
    
    schedule_list = ScheduleList.query.get_or_404(list_id)
    schedule_list.name = new_name
    db.session.commit()
    
    return jsonify({'success': True})

if __name__ == '__main__':
    # Create database tables
    with app.app_context():
        db.create_all()
    # Initialize schedules from database
    init_schedules()
    app.run(debug=True, host='0.0.0.0', port=5000)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)