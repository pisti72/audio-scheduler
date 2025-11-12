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

### 6. Handle SELinux (Fedora/RHEL/CentOS only)

```bash
# Check if SELinux is enforcing
getenforce

# If output is "Enforcing":
# ✅ The service file already handles this with bash wrapper
# ✅ No additional configuration needed!

# If you see permission errors anyway:
sudo ausearch -m avc -ts recent  # Check SELinux denials
```

### 7. Install and Start Service

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

### 8. Verify Installation

```bash
# Check if service is running
systemctl is-active audio-scheduler

# Check if scheduler initialized
grep "Simple scheduler started" logs/audio_scheduler.log

# Check how many schedulers are running (should be 1)
grep "SimpleScheduler initialized" logs/audio_scheduler.log | tail -1

# Check if schedules loaded
grep "Initialized.*schedule jobs" logs/audio_scheduler.log | tail -1

# Test web interface
curl http://localhost:5000
# Or open in browser: http://server-ip:5000
```

### 9. Configure Firewall (if needed)

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

### 10. Test Audio Playback

```bash
# Test pygame audio as service user
sudo -u your_username python3 -c "import pygame; pygame.mixer.init(); print('Audio OK')"

# If audio fails, add user to audio group
sudo usermod -a -G audio your_username

# Restart service
sudo systemctl restart audio-scheduler
```

## Common Issues and Solutions

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
- [ ] Service file edited (User, WorkingDirectory)
- [ ] Service file copied to `/etc/systemd/system/`
- [ ] SELinux handled (automatic with bash wrapper)
- [ ] Service enabled and started
- [ ] Firewall configured (port 5000 or custom)
- [ ] Audio playback tested
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
