# Audio Scheduler - Service Setup Guide

This guide explains how to install and manage the Audio Scheduler as a systemd service.

## Quick Start

### User-Level Installation (Recommended)

```bash
./install-service.sh --user
```

**Benefits:**
- Runs without root privileges
- Automatically starts when you log in
- Easier to manage and troubleshoot
- Proper audio access out of the box

### System-Level Installation

```bash
sudo ./install-service.sh --system
```

**Use when:**
- You need the service to run for all users
- You want it to start before any user logs in
- You're running on a headless server

## What the Installer Does

The `install-service.sh` script automatically handles:

1. ✅ **Environment Detection**
   - Detects PipeWire or PulseAudio
   - Identifies the correct user and permissions
   - Sets up proper audio environment variables

2. ✅ **Virtual Environment**
   - Creates Python virtual environment if needed
   - Installs all dependencies from requirements.txt

3. ✅ **Directory Structure**
   - Creates logs/, uploads/, instance/, csv-exports/, playlists/

4. ✅ **Database Setup**
   - Initializes SQLite database
   - Runs migrations if needed

5. ✅ **Credentials**
   - Creates default admin credentials (admin/admin)
   - ⚠️ **Remember to change the password after first login!**

6. ✅ **Systemd Service**
   - Creates properly configured service file
   - Sets up environment variables for audio access
   - Configures auto-restart on failure
   - Enables the service to start automatically

7. ✅ **Cleanup**
   - Removes conflicting old service files
   - Handles migration from system to user service (or vice versa)

## Service Management

### User-Level Service

```bash
# Start the service
systemctl --user start audio-scheduler.service

# Stop the service
systemctl --user stop audio-scheduler.service

# Restart the service
systemctl --user restart audio-scheduler.service

# Check status
systemctl --user status audio-scheduler.service

# View logs (live)
journalctl --user -u audio-scheduler.service -f

# View logs (last 100 lines)
journalctl --user -u audio-scheduler.service -n 100
```

### System-Level Service

```bash
# Start the service
sudo systemctl start audio-scheduler.service

# Stop the service
sudo systemctl stop audio-scheduler.service

# Restart the service
sudo systemctl restart audio-scheduler.service

# Check status
sudo systemctl status audio-scheduler.service

# View logs (live)
sudo journalctl -u audio-scheduler.service -f

# View logs (last 100 lines)
sudo journalctl -u audio-scheduler.service -n 100
```

## Uninstallation

### Remove User Service

```bash
./install-service.sh --uninstall --user
```

### Remove System Service

```bash
sudo ./install-service.sh --uninstall --system
```

**Note:** Uninstalling removes only the systemd service. Your application files, database, schedules, and logs are preserved.

## Troubleshooting

### Audio Not Playing

1. **Check audio system is running:**
   ```bash
   ps aux | grep -E "(pulseaudio|pipewire)"
   ```

2. **Verify environment variables:**
   ```bash
   # For user service
   systemctl --user show audio-scheduler.service | grep Environment
   
   # For system service
   sudo systemctl show audio-scheduler.service | grep Environment
   ```

3. **Check the logs:**
   ```bash
   tail -50 logs/gunicorn_error.log | grep -i audio
   ```

4. **Test audio manually:**
   ```bash
   source venv/bin/activate
   python test_audio.py
   ```

### Service Won't Start

1. **Check the status:**
   ```bash
   systemctl --user status audio-scheduler.service
   ```

2. **View detailed logs:**
   ```bash
   journalctl --user -u audio-scheduler.service -n 50
   ```

3. **Check port availability:**
   ```bash
   lsof -i :5000
   ```

4. **Verify file permissions:**
   ```bash
   ls -la /home/tesztelek/Dokumentumok/audio-scheduler/
   ```

### After System Restart, Service Doesn't Start

**For user services:**

Enable user lingering to allow services to run without login:
```bash
sudo loginctl enable-linger $USER
```

The installer does this automatically, but verify with:
```bash
loginctl show-user $USER | grep Linger
```

### Migration from Old Installation

If you previously had a system-level service and want to switch to user-level:

1. **Run the user installation:**
   ```bash
   ./install-service.sh --user
   ```

2. **The script will automatically detect and offer to remove the old system service**

3. **If you need to manually remove the old service:**
   ```bash
   sudo systemctl stop audio-scheduler.service
   sudo systemctl disable audio-scheduler.service
   sudo rm /etc/systemd/system/audio-scheduler.service
   sudo systemctl daemon-reload
   ```

## Advanced Configuration

### Custom Port

Edit the service file and change the `-b 0.0.0.0:5000` parameter:

**User service:**
```bash
nano ~/.config/systemd/user/audio-scheduler.service
systemctl --user daemon-reload
systemctl --user restart audio-scheduler.service
```

**System service:**
```bash
sudo nano /etc/systemd/system/audio-scheduler.service
sudo systemctl daemon-reload
sudo systemctl restart audio-scheduler.service
```

### Increase Workers

⚠️ **WARNING:** The scheduler uses `-w 1` (single worker) to prevent duplicate scheduled events. Only increase workers if you know what you're doing!

### Environment Variables

Add custom environment variables to the service file under the `[Service]` section:

```ini
Environment="YOUR_VAR=value"
```

## File Locations

### User-Level Installation
- **Service file:** `~/.config/systemd/user/audio-scheduler.service`
- **Application:** `/home/tesztelek/Dokumentumok/audio-scheduler/`
- **Logs:** `/home/tesztelek/Dokumentumok/audio-scheduler/logs/`
- **Database:** `/home/tesztelek/Dokumentumok/audio-scheduler/instance/scheduler.db`

### System-Level Installation
- **Service file:** `/etc/systemd/system/audio-scheduler.service`
- **Application:** `/home/tesztelek/Dokumentumok/audio-scheduler/`
- **Logs:** `/home/tesztelek/Dokumentumok/audio-scheduler/logs/`
- **Database:** `/home/tesztelek/Dokumentumok/audio-scheduler/instance/scheduler.db`

## Security Notes

1. **Default Credentials:** The installer creates default credentials (admin/admin). **Change these immediately** after first login!

2. **Network Binding:** The service binds to `0.0.0.0:5000`, making it accessible from the network. Consider:
   - Using a firewall to restrict access
   - Changing to `127.0.0.1:5000` for local-only access
   - Setting up a reverse proxy with HTTPS

3. **File Permissions:** Ensure only the service user has write access to the application directory.

## Getting Help

- Check application logs: `logs/gunicorn_error.log`
- Check systemd logs: `journalctl --user -u audio-scheduler.service`
- Check service status: `systemctl --user status audio-scheduler.service`

## Additional Resources

- Main README: [README.md](README.md)
- Deployment Guide: [DEPLOYMENT.md](DEPLOYMENT.md)
- Gunicorn Setup: [GUNICORN.md](GUNICORN.md)
