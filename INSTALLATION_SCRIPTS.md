# Audio Scheduler - Installation Scripts

This directory contains automated scripts to simplify installation and management of the Audio Scheduler service.

## 📋 Available Scripts

### 1. `install-service.sh` - Automated Service Installer

**The easiest way to install Audio Scheduler as a systemd service.**

#### Features:
- ✅ Automatic audio system detection (PipeWire/PulseAudio)
- ✅ Virtual environment setup
- ✅ Dependency installation
- ✅ Database initialization
- ✅ Default credentials creation
- ✅ Systemd service creation with proper audio environment
- ✅ Old service cleanup
- ✅ Auto-enable and start service

#### Usage:

**User-level installation (Recommended):**
```bash
./install-service.sh --user
```

**System-level installation:**
```bash
sudo ./install-service.sh --system
```

**Uninstall:**
```bash
./install-service.sh --uninstall --user
# or
sudo ./install-service.sh --uninstall --system
```

**Help:**
```bash
./install-service.sh --help
```

#### What it does:

1. **Detects your system:**
   - Checks if PipeWire or PulseAudio is running
   - Identifies the correct user and permissions
   - Determines proper runtime directories

2. **Sets up the environment:**
   - Creates Python virtual environment if needed
   - Installs all dependencies from requirements.txt
   - Creates necessary directories (logs, uploads, instance, etc.)

3. **Initializes the application:**
   - Creates SQLite database
   - Runs migrations
   - Generates default credentials (admin/admin)
   - ⚠️ **Important:** Change default password after first login!

4. **Configures systemd service:**
   - Creates service file with proper audio environment variables
   - Sets up PulseAudio/PipeWire access
   - Configures auto-restart on failure
   - Enables the service to start automatically

5. **Cleanup and migration:**
   - Removes conflicting old service files
   - Handles migration from system to user service (or vice versa)

6. **Starts the service:**
   - Enables the service
   - Starts it immediately
   - Shows status and helpful information

### 2. `service-status.sh` - Quick Status Checker

**Quick overview of your service status and logs.**

#### Usage:
```bash
./service-status.sh
```

#### What it shows:
- Service installation type (user or system)
- Current service status
- Recent systemd logs (last 10 lines)
- Recent application logs (last 5 lines)
- Quick command reference
- Web interface URL

### 3. `test_audio.py` - Audio System Tester

**Verify that audio playback works from the application context.**

#### Usage:
```bash
source venv/bin/activate
python test_audio.py
```

#### What it does:
- Sets up proper audio environment
- Initializes pygame mixer
- Plays a test audio file
- Confirms successful playback

## 🎯 Quick Start Guide

### New Installation

1. **Clone or download the repository**
2. **Run the installer:**
   ```bash
   ./install-service.sh --user
   ```
3. **Access the web interface:**
   - Open http://localhost:5000
   - Login with: admin / admin
   - **Change the password immediately!**

### Checking Status

```bash
./service-status.sh
```

### Managing the Service

**User service:**
```bash
systemctl --user start audio-scheduler.service    # Start
systemctl --user stop audio-scheduler.service     # Stop
systemctl --user restart audio-scheduler.service  # Restart
systemctl --user status audio-scheduler.service   # Status
journalctl --user -u audio-scheduler.service -f   # Logs
```

**System service:**
```bash
sudo systemctl start audio-scheduler.service    # Start
sudo systemctl stop audio-scheduler.service     # Stop
sudo systemctl restart audio-scheduler.service  # Restart
sudo systemctl status audio-scheduler.service   # Status
sudo journalctl -u audio-scheduler.service -f   # Logs
```

## 🔧 Troubleshooting

### Installation fails

1. **Check prerequisites:**
   ```bash
   python3 --version  # Should be 3.8+
   pip3 --version
   ```

2. **Run with verbose output:**
   ```bash
   bash -x ./install-service.sh --user
   ```

3. **Check permissions:**
   ```bash
   ls -la install-service.sh  # Should be executable
   ```

### Audio not working after installation

1. **Check audio system:**
   ```bash
   ps aux | grep -E "(pulseaudio|pipewire)"
   ```

2. **Test audio manually:**
   ```bash
   source venv/bin/activate
   python test_audio.py
   ```

3. **Check environment variables:**
   ```bash
   systemctl --user show audio-scheduler.service | grep Environment
   ```

4. **Restart the service:**
   ```bash
   systemctl --user restart audio-scheduler.service
   ```

### Service won't start

1. **Check the logs:**
   ```bash
   journalctl --user -u audio-scheduler.service -n 50
   ```

2. **Check port availability:**
   ```bash
   lsof -i :5000
   ```

3. **Verify file permissions:**
   ```bash
   ls -la $PWD
   ```

### After system restart, service doesn't start

**Enable user lingering:**
```bash
sudo loginctl enable-linger $USER
```

Verify:
```bash
loginctl show-user $USER | grep Linger
```

## 📚 Documentation

- **[SERVICE_SETUP.md](SERVICE_SETUP.md)** - Comprehensive service setup guide
- **[SERVICE_INSTALL.md](SERVICE_INSTALL.md)** - Manual installation instructions
- **[README.md](README.md)** - Main application documentation
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Deployment guide
- **[GUNICORN.md](GUNICORN.md)** - Gunicorn configuration guide

## 🛡️ Security Notes

1. **Default Credentials:**
   - Username: `admin`
   - Password: `admin`
   - **⚠️ CHANGE THESE IMMEDIATELY after first login!**

2. **Network Binding:**
   - Default: `0.0.0.0:5000` (accessible from network)
   - For local-only: Edit service file to use `127.0.0.1:5000`
   - Consider using a firewall or reverse proxy

3. **File Permissions:**
   - Ensure only the service user has write access
   - Database and logs should not be world-readable

## 🔄 Migration Guide

### From System to User Service

```bash
# Stop and remove system service
sudo systemctl stop audio-scheduler.service
sudo systemctl disable audio-scheduler.service
sudo rm /etc/systemd/system/audio-scheduler.service
sudo systemctl daemon-reload

# Install user service
./install-service.sh --user
```

### From User to System Service

```bash
# Stop and remove user service
systemctl --user stop audio-scheduler.service
systemctl --user disable audio-scheduler.service
rm ~/.config/systemd/user/audio-scheduler.service
systemctl --user daemon-reload

# Install system service
sudo ./install-service.sh --system
```

### Automated Migration

The installer automatically detects and offers to remove conflicting services!

## 💡 Tips

1. **Use user service for desktop/laptop** - Better audio support
2. **Use system service for headless server** - Runs without user login
3. **Enable lingering for user services** - Service runs even when logged out
4. **Check logs first when troubleshooting** - Most issues show up there
5. **Keep backups** - Database is in `instance/scheduler.db`

## 🤝 Contributing

If you improve the installation scripts, please share your changes!

## 📝 License

Same as the main Audio Scheduler application.
