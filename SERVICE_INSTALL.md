# Audio Scheduler - Systemd Service Installation

## 🚀 Quick Start (Recommended)

**Use the automated installer for hassle-free setup:**

```bash
# Install as user service (recommended - better audio support)
./install-service.sh --user

# Or install as system service (requires sudo)
sudo ./install-service.sh --system
```

The automated installer handles everything:
- ✅ Detects your audio system (PipeWire/PulseAudio)
- ✅ Creates virtual environment and installs dependencies
- ✅ Sets up proper directory structure
- ✅ Initializes database and credentials
- ✅ Creates systemd service with correct audio environment
- ✅ Cleans up old/conflicting services
- ✅ Enables and starts the service

**For detailed information**, see [SERVICE_SETUP.md](SERVICE_SETUP.md)

**Quick status check:**
```bash
./service-status.sh
```

---

## Manual Installation (Advanced Users)

If you prefer manual setup or need to customize the installation, follow the detailed steps below.

## Prerequisites

```bash
# 1. Install Gunicorn
pip install gunicorn>=21.0.0

# Or install all requirements
pip install -r requirements.txt

# 2. Create logs directory (required for Gunicorn)
mkdir -p logs

# 3. Ensure virtual environment is activated
source venv/bin/activate

# 4. Add user to audio group (REQUIRED for sound playback)
sudo usermod -a -G audio $USER

# 5. Enable user lingering (REQUIRED for PulseAudio/Pipewire access)
sudo loginctl enable-linger $USER

# 6. For Fedora/RHEL/CentOS: Verify SELinux won't block execution
getenforce  # If "Enforcing", the service file already handles this

# NOTE: After step 4, you need to log out and log back in for audio group to take effect
# Or just reboot the system before starting the service
```

## Manual Installation Options

There are two ways to install the service manually:

### Option 1: User Service (RECOMMENDED for audio playback)

**Pros**: 
- ✅ Audio works even when screen is locked
- ✅ Proper access to PulseAudio/Pipewire
- ✅ Automatic audio environment setup
- ✅ No sudo needed for service management

**Cons**:
- Service runs only when user is logged in (unless lingering is enabled)

```bash
# 1. Ensure lingering is enabled (allows service to run when logged out)
sudo loginctl enable-linger $USER

# 2. Create user systemd directory
mkdir -p ~/.config/systemd/user

# 3. Copy the user service file
cp audio-scheduler-user.service ~/.config/systemd/user/audio-scheduler.service

# 4. Update paths in the service file if needed
nano ~/.config/systemd/user/audio-scheduler.service
# Change WorkingDirectory if your installation is in a different location

# 5. Reload user systemd
systemctl --user daemon-reload

# 6. Enable service to start automatically
systemctl --user enable audio-scheduler

# 7. Start the service
systemctl --user start audio-scheduler

# 8. Check status
systemctl --user status audio-scheduler
```

### Option 2: System Service (for servers without GUI)

### Option 2: System Service (for servers without GUI)

**Pros**:
- Runs regardless of user login status
- Good for headless servers

**Cons**:
- ❌ Audio may not work when screen is locked
- Requires environment variables for audio access
- Needs sudo for service management

```bash
# 1. Update the service file paths if needed
# Edit audio-scheduler.service and update:
#   - User (currently: istvan)
#   - WorkingDirectory path (all paths are relative to this)
#   - XDG_RUNTIME_DIR and PULSE_RUNTIME_PATH (use your user ID from: id -u)

# 2. Ensure logs directory exists
mkdir -p logs

# 3. Copy service file to systemd
sudo cp audio-scheduler.service /etc/systemd/system/

# 3. Reload systemd
sudo systemctl daemon-reload

# 4. Enable service to start on boot
sudo systemctl enable audio-scheduler

# 5. Start the service
sudo systemctl start audio-scheduler

# 6. Check status
sudo systemctl status audio-scheduler
```

## Service Management Commands

### For User Service (recommended)

```bash
# Start service
systemctl --user start audio-scheduler

# Stop service
systemctl --user stop audio-scheduler

# Restart service
systemctl --user restart audio-scheduler

# Check status
systemctl --user status audio-scheduler

# View logs
journalctl --user -u audio-scheduler -f

# View application logs
tail -f ~/Dokumentumok/Dev/audio-scheduler/logs/audio_scheduler.log

# Disable service (prevent auto-start)
systemctl --user disable audio-scheduler
```

### For System Service

```bash
# Start service
sudo systemctl start audio-scheduler

# Stop service
sudo systemctl stop audio-scheduler

# Restart service
sudo systemctl restart audio-scheduler

# Check status
sudo systemctl status audio-scheduler

# View logs
sudo journalctl -u audio-scheduler -f

# View application logs
tail -f ~/Dokumentumok/Dev/audio-scheduler/logs/audio_scheduler.log

# Disable service (prevent auto-start on boot)
sudo systemctl disable audio-scheduler
```

## Troubleshooting

### SELinux Permission Denied (Fedora/RHEL/CentOS)

**Symptoms**: Service fails with "Permission denied" (exit code 203/EXEC) in `journalctl`:
```
audio-scheduler.service: Unable to locate executable '.../venv/bin/gunicorn': Permission denied
```

**Cause**: SELinux blocks systemd from executing files in user home directories.

**Solution**: The service file already uses `/bin/bash -c 'source venv/bin/activate && ...'` to avoid this issue. This works because:
- `/bin/bash` has proper SELinux context
- Bash then activates venv and runs gunicorn
- No direct execution of home directory binaries

**Alternative Solution** (if you modify ExecStart to use direct paths):
```bash
# Check SELinux status
getenforce  # Should show: Enforcing

# Option 1: Use bash wrapper (already implemented in service file)
# Option 2: Set SELinux contexts (more complex)
sudo semanage fcontext -a -t bin_t "/path/to/venv/bin/.*"
sudo restorecon -Rv /path/to/venv/bin/

# Option 3: Disable SELinux (NOT recommended for production)
# sudo setenforce 0
```

### Audio Not Playing

**Symptoms**: Scheduler triggers but you hear no sound. Logs show:
```
Audio playback skipped (no audio device): uploads/file.mp3
Audio system not available: ALSA: Couldn't open audio device
```

**Causes and Solutions**:

1. **Screen is locked and using system service** (most common on desktop systems):

**Solution**: Switch to user service instead!
```bash
# Stop system service
sudo systemctl stop audio-scheduler
sudo systemctl disable audio-scheduler

# Install user service (see "Option 1: User Service" above)
mkdir -p ~/.config/systemd/user
cp audio-scheduler-user.service ~/.config/systemd/user/audio-scheduler.service
systemctl --user daemon-reload
systemctl --user enable --now audio-scheduler
```

2. **User not in audio group**:
```bash
# Add user to audio group
sudo usermod -a -G audio istvan

# Verify
groups istvan  # Should show 'audio' in the list

# IMPORTANT: Log out and log back in, or reboot for changes to take effect
```

2. **User lingering not enabled** (required for PulseAudio/Pipewire):
```bash
# Enable lingering
sudo loginctl enable-linger istvan

# Verify
loginctl show-user istvan | grep Linger
# Should show: Linger=yes
```

3. **Missing audio environment variables** in service file:
```ini
[Service]
Environment="XDG_RUNTIME_DIR=/run/user/1000"  # Replace 1000 with your user ID
Environment="PULSE_RUNTIME_PATH=/run/user/1000/pulse"
```

Get your user ID: `id -u username`

4. **Restart service after changes**:
```bash
sudo systemctl restart audio-scheduler
```

5. **Test audio manually**:
```bash
# Test as the service user
sudo -u istvan XDG_RUNTIME_DIR=/run/user/$(id -u istvan) python3 -c "import pygame; pygame.mixer.init(); print('Audio OK')"
```

### Scheduler Not Working

Check the logs to see if scheduler initialized:

```bash
grep "scheduler" ~/Dokumentumok/Dev/audio-scheduler/logs/audio_scheduler.log
```

You should see:
- `✅ Simple polling scheduler initialized and started`
- Schedule execution logs like `🔒 Marked schedule X as executed`

### Audio Not Playing

1. Make sure your user has access to audio devices:
```bash
groups istvan  # Check if user is in 'audio' group
sudo usermod -a -G audio istvan  # Add to audio group if needed
```

2. Check if pygame can access audio in service context:
```bash
sudo -u istvan XDG_RUNTIME_DIR=/run/user/$(id -u istvan) python3 -c "import pygame; pygame.mixer.init(); print('Audio OK')"
```

### Service Won't Start

```bash
# Check for errors
sudo journalctl -u audio-scheduler -n 50 --no-pager

# Check service file syntax
sudo systemctl cat audio-scheduler

# Verify paths exist
ls -la /path/to/audio-scheduler/wsgi.py
ls -la /path/to/audio-scheduler/venv/bin/gunicorn
ls -la /path/to/audio-scheduler/logs/

# Check if logs directory is writable
touch /path/to/audio-scheduler/logs/test.log
rm /path/to/audio-scheduler/logs/test.log

# Verify Gunicorn works manually
cd /path/to/audio-scheduler
source venv/bin/activate
gunicorn -w 1 -b 0.0.0.0:5000 wsgi:app
```

## Environment Variables

If you need to set environment variables for the service, edit the service file:

```ini
[Service]
Environment="AUDIO_SCHEDULER_ENV=production"
Environment="FLASK_ENV=production"
```

## Running Multiple Instances

If you need to run multiple schedulers on different ports:

1. Copy the service file: `sudo cp /etc/systemd/system/audio-scheduler.service /etc/systemd/system/audio-scheduler-2.service`
2. Edit the new file and change the port in ExecStart
3. Reload and start: `sudo systemctl daemon-reload && sudo systemctl start audio-scheduler-2`

## Production vs Development

- **Development**: 
  - Run with `./run.sh` or `python app.py` (Flask dev server, debug mode, auto-reload)
  - Good for: Testing, debugging, development
  
- **Production with Gunicorn**: 
  - Run with `./run_gunicorn.sh` (Gunicorn WSGI server)
  - Good for: Production testing, manual deployment
  - Use systemd service for: Auto-start on boot, automatic restarts, service management

## Running Manually with Gunicorn

```bash
# Start with Gunicorn (recommended for production)
./run_gunicorn.sh

# Or manually:
gunicorn -w 1 -b 0.0.0.0:5000 wsgi:app

# With logging:
gunicorn -w 1 -b 0.0.0.0:5000 \
  --access-logfile logs/gunicorn_access.log \
  --error-logfile logs/gunicorn_error.log \
  wsgi:app
```

**IMPORTANT**: Always use `-w 1` (single worker) to prevent duplicate schedulers!

## Uninstall

```bash
# Stop and disable service
sudo systemctl stop audio-scheduler
sudo systemctl disable audio-scheduler

# Remove service file
sudo rm /etc/systemd/system/audio-scheduler.service

# Reload systemd
sudo systemctl daemon-reload
```
