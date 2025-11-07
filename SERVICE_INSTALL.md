# Audio Scheduler - Systemd Service Installation

## Quick Installation

```bash
# 1. Update the service file paths if needed
# Edit audio-scheduler.service and update:
#   - User (currently: istvan)
#   - WorkingDirectory path
#   - ExecStart path

# 2. Copy service file to systemd
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
ls -la /home/istvan/Dokumentumok/Dev/audio-scheduler/app.py
ls -la /home/istvan/Dokumentumok/Dev/audio-scheduler/venv/bin/python
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

- **Development**: Run with `./run.sh` or `python app.py` (debug mode, auto-reload)
- **Production**: Use systemd service (stable, auto-restart, runs on boot)

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
