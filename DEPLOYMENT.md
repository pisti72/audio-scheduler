# Deployment Checklist for Audio Scheduler

## Quick Deployment Steps for New Server

### 1. System Requirements
- **OS**: Linux (tested on Fedora, works on Ubuntu/Debian/RHEL/CentOS)
- **Python**: 3.9 or higher (tested with 3.14)
- **Audio**: ALSA/PulseAudio for sound playback
- **Network**: Port 5000 available (or configure different port)

### 2. Clone/Copy Application

```bash
# Copy application to server
scp -r audio-scheduler user@server:/path/to/destination/

# Or clone from git
git clone https://github.com/yourusername/audio-scheduler.git
cd audio-scheduler
```

### 3. Setup Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Verify Gunicorn is installed
which gunicorn
```

### 4. Create Required Directories

```bash
# These directories MUST exist before starting service
mkdir -p logs
mkdir -p uploads
mkdir -p playlists
mkdir -p instance
```

### 5. Configure Service File

Edit `audio-scheduler.service` and update these values:

```ini
# Change username
User=your_username

# Change working directory
WorkingDirectory=/path/to/your/audio-scheduler
```

**Note**: All other paths are relative to `WorkingDirectory`, so you don't need to change them!

### 6. Configure Audio Access (CRITICAL for sound playback)

```bash
# Add user to audio group
sudo usermod -a -G audio your_username

# Enable user lingering (required for PulseAudio/Pipewire)
sudo loginctl enable-linger your_username

# Update service file with audio environment variables
# Edit audio-scheduler.service and add these lines after PYTHONUNBUFFERED:
#   Environment="XDG_RUNTIME_DIR=/run/user/YOUR_USER_ID"
#   Environment="PULSE_RUNTIME_PATH=/run/user/YOUR_USER_ID/pulse"

# Get your user ID:
id -u your_username  # e.g., 1000

# Example service file section:
# Environment="FLASK_ENV=production"
# Environment="PYTHONUNBUFFERED=1"
# Environment="XDG_RUNTIME_DIR=/run/user/1000"
# Environment="PULSE_RUNTIME_PATH=/run/user/1000/pulse"

# IMPORTANT: Log out and log back in (or reboot) after adding to audio group!
```

### 7. Handle SELinux (Fedora/RHEL/CentOS only)

```bash
# Check if SELinux is enforcing
getenforce

# If output is "Enforcing":
# ✅ The service file already handles this with bash wrapper
# ✅ No additional configuration needed!

# If you see permission errors anyway:
sudo ausearch -m avc -ts recent  # Check SELinux denials
```

### 7. Handle SELinux (Fedora/RHEL/CentOS only)

```bash
# Check if SELinux is enforcing
getenforce

# If output is "Enforcing":
# ✅ The service file already handles this with bash wrapper
# ✅ No additional configuration needed!

# If you see permission errors anyway:
sudo ausearch -m avc -ts recent  # Check SELinux denials
```

### 8. Install and Start Service

**Choose one of two options:**

#### Option A: User Service (RECOMMENDED for desktop systems with GUI)

✅ **Best for**: Systems where user logs in (desktop, laptop)
✅ **Audio works**: Even when screen is locked
✅ **No sudo needed**: For service management

```bash
# Ensure lingering is enabled (service runs even when logged out)
sudo loginctl enable-linger your_username

# Create user systemd directory
mkdir -p ~/.config/systemd/user

# Copy user service file
cp audio-scheduler-user.service ~/.config/systemd/user/audio-scheduler.service

# Update paths in service file if needed
nano ~/.config/systemd/user/audio-scheduler.service

# Reload, enable, and start
systemctl --user daemon-reload
systemctl --user enable audio-scheduler
systemctl --user start audio-scheduler

# Check status
systemctl --user status audio-scheduler

# View logs
journalctl --user -u audio-scheduler -f
```

#### Option B: System Service (for headless servers)

⚠️ **Note**: Audio may not work when screen is locked on desktop systems

```bash
# Copy service file
sudo cp audio-scheduler.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable auto-start on boot
sudo systemctl enable audio-scheduler

# Start service
sudo systemctl start audio-scheduler

# Check status
sudo systemctl status audio-scheduler

# View logs
journalctl -u audio-scheduler -f
```

### 9. Verify Installation

```bash
# Check if service is running
systemctl is-active audio-scheduler

# Check if scheduler initialized
grep "Simple scheduler started" logs/audio_scheduler.log

# Check if audio system initialized
grep "Audio system initialized successfully" logs/audio_scheduler.log

# Check how many schedulers are running (should be 1)
grep "SimpleScheduler initialized" logs/audio_scheduler.log | tail -1

# Check if schedules loaded
grep "Initialized.*schedule jobs" logs/audio_scheduler.log | tail -1

# Test web interface
curl http://localhost:5000
# Or open in browser: http://server-ip:5000
```

### 10. Configure Firewall (if needed)

```bash
# For Fedora/RHEL/CentOS (firewalld)
sudo firewall-cmd --permanent --add-port=5000/tcp
sudo firewall-cmd --reload

# For Ubuntu/Debian (ufw)
sudo ufw allow 5000/tcp
sudo ufw reload

# For iptables
sudo iptables -A INPUT -p tcp --dport 5000 -j ACCEPT
sudo service iptables save  # RHEL/CentOS
sudo iptables-save > /etc/iptables/rules.v4  # Debian/Ubuntu
```

### 11. Test Audio Playback

```bash
# Test pygame audio as service user with proper environment
sudo -u your_username XDG_RUNTIME_DIR=/run/user/$(id -u your_username) python3 -c "import pygame; pygame.mixer.init(); print('Audio OK')"

# Check audio logs
tail -f logs/audio_scheduler.log | grep -i audio

# Wait for next scheduled time or test via web interface
# You should see logs like:
#   "Audio system initialized successfully"
#   "Playing audio: uploads/file.mp3"
```

## Common Issues and Solutions

### Issue: "Audio stops working when screen is locked"

**Cause**: Using system service on desktop system. PulseAudio/Pipewire becomes unavailable to system services when user session is locked.

**Solution**: Switch to user service!
```bash
# Stop system service
sudo systemctl stop audio-scheduler
sudo systemctl disable audio-scheduler

# Install as user service instead
mkdir -p ~/.config/systemd/user
cp audio-scheduler-user.service ~/.config/systemd/user/audio-scheduler.service
systemctl --user daemon-reload
systemctl --user enable --now audio-scheduler

# Verify
systemctl --user status audio-scheduler
```

### Issue: "Audio playback skipped (no audio device)"

**Cause**: Service can't access audio system (most common issue)

**Solution**:
```bash
# 1. Add user to audio group
sudo usermod -a -G audio your_username

# 2. Enable user lingering
sudo loginctl enable-linger your_username

# 3. Add to service file (after PYTHONUNBUFFERED line):
#    Environment="XDG_RUNTIME_DIR=/run/user/YOUR_USER_ID"
#    Environment="PULSE_RUNTIME_PATH=/run/user/YOUR_USER_ID/pulse"

# 4. Get your user ID:
id -u your_username  # e.g., 1000

# 5. Update service, copy it, and restart:
sudo cp audio-scheduler.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl restart audio-scheduler

# 6. IMPORTANT: Log out and log back in (or reboot) after audio group change
```

Verify fix:
```bash
# Should show "Audio system initialized successfully"
grep "Audio system" logs/audio_scheduler.log | tail -1
```

### Issue: "Permission denied" (exit code 203/EXEC)

**Cause**: SELinux blocking execution (Fedora/RHEL/CentOS)

**Solution**: Already handled! The service file uses:
```bash
ExecStart=/bin/bash -c 'source venv/bin/activate && exec gunicorn ...'
```

This avoids direct execution of venv binaries.

### Issue: Duplicate audio playback

**Cause**: Multiple schedulers initialized (multiple workers or processes)

**Solution**: Always use `-w 1` (single worker) in Gunicorn command. Already configured in service file.

### Issue: Logs not created

**Cause**: `logs/` directory doesn't exist or not writable

**Solution**:
```bash
mkdir -p logs
chmod 755 logs
chown your_username:your_username logs
```

### Issue: Database not found

**Cause**: `instance/` directory doesn't exist

**Solution**:
```bash
mkdir -p instance
# Database will be created automatically on first run
```

### Issue: Audio files not found

**Cause**: `uploads/` or `playlists/` directories don't exist

**Solution**:
```bash
mkdir -p uploads playlists
# Copy your audio files
cp /path/to/audio/*.mp3 uploads/
```

## Port Configuration

To use a different port (e.g., 8080 instead of 5000):

1. Edit `audio-scheduler.service`:
   ```ini
   ExecStart=/bin/bash -c 'source venv/bin/activate && exec gunicorn \
       -w 1 \
       -b 0.0.0.0:8080 \  # <-- Change port here
       ...
   ```

2. Update firewall rules for new port

3. Reload and restart:
   ```bash
   sudo cp audio-scheduler.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl restart audio-scheduler
   ```

## Security Considerations

1. **Change default credentials** immediately after first login
2. **Firewall**: Only allow access from trusted networks
3. **SELinux**: Keep it enforcing (don't disable)
4. **Updates**: Regularly update dependencies with `pip install -U -r requirements.txt`
5. **Backups**: Backup `instance/schedules.db` and `credentials.json` regularly

## Migration from Another Server

```bash
# On old server - backup data
cd /path/to/old/audio-scheduler
tar -czf backup.tar.gz instance/ uploads/ playlists/ credentials.json

# Copy to new server
scp backup.tar.gz user@newserver:/path/to/audio-scheduler/

# On new server - restore data
cd /path/to/audio-scheduler
tar -xzf backup.tar.gz

# Start service
sudo systemctl start audio-scheduler
```

## Checklist Summary

- [ ] Python 3.9+ installed
- [ ] Virtual environment created and activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Directories created (`logs`, `uploads`, `playlists`, `instance`)
- [ ] **User added to audio group** (`sudo usermod -a -G audio username`)
- [ ] **User lingering enabled** (`sudo loginctl enable-linger username`)
- [ ] **Audio environment variables added to service file**
- [ ] Service file edited (User, WorkingDirectory, XDG_RUNTIME_DIR)
- [ ] Service file copied to `/etc/systemd/system/`
- [ ] SELinux handled (automatic with bash wrapper)
- [ ] Service enabled and started
- [ ] **Logged out and back in (or rebooted) after audio group change**
- [ ] Firewall configured (port 5000 or custom)
- [ ] **Audio system initialized successfully (check logs)**
- [ ] Web interface accessible
- [ ] Scheduler initialized (check logs)
- [ ] No duplicate executions (check logs)
- [ ] Default credentials changed

## Getting Help

1. Check logs: `journalctl -u audio-scheduler -f`
2. Check application logs: `tail -f logs/audio_scheduler.log`
3. Check Gunicorn logs: `tail -f logs/gunicorn_error.log`
4. Verify service status: `systemctl status audio-scheduler`
5. See troubleshooting in `SERVICE_INSTALL.md`
