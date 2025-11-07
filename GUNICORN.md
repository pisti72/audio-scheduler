# Running Audio Scheduler with Gunicorn

## Quick Start

### Linux/macOS
```bash
./run_gunicorn.sh
```

### Windows
```bash
run_gunicorn.bat
```

### Manual Command
```bash
gunicorn -w 1 -b 0.0.0.0:5000 wsgi:app
```

## Why Gunicorn?

✅ **Production-ready** - Designed for production workloads  
✅ **Better performance** - More efficient than Flask dev server  
✅ **Process management** - Automatic restarts on crashes  
✅ **Proper logging** - Structured access and error logs  
✅ **Security** - Better handling of concurrent requests  
✅ **Stability** - Battle-tested WSGI server  

## Important: Single Worker Configuration

⚠️ **CRITICAL**: Always use `-w 1` (single worker) because:

1. **Scheduler must run only once** - Multiple workers would create duplicate schedulers
2. **Audio playback** - pygame can only be used in one process
3. **Database consistency** - Single worker ensures no race conditions

## Command Line Options

```bash
gunicorn [OPTIONS] wsgi:app

Common options:
  -w 1                  # Workers (MUST be 1 for this app)
  -b 0.0.0.0:5000      # Bind address:port
  --timeout 120        # Request timeout (seconds)
  --log-level info     # Logging level
  --access-logfile FILE # Access log file
  --error-logfile FILE  # Error log file
  --daemon             # Run in background
  --pid FILE           # PID file location
```

## Log Files

When running with Gunicorn, logs are written to:

- **Application logs**: `logs/audio_scheduler.log`
- **Audio playback logs**: `logs/audio_playback.log`
- **Gunicorn access logs**: `logs/gunicorn_access.log`
- **Gunicorn error logs**: `logs/gunicorn_error.log`

View logs:
```bash
# Application logs
tail -f logs/audio_scheduler.log

# Gunicorn access logs
tail -f logs/gunicorn_access.log

# All logs
tail -f logs/*.log
```

## Running as Background Process

```bash
# Start in background
gunicorn -w 1 -b 0.0.0.0:5000 --daemon --pid gunicorn.pid wsgi:app

# Stop
kill $(cat gunicorn.pid)

# Or use systemd service (recommended)
sudo systemctl start audio-scheduler
```

## Testing

```bash
# Start Gunicorn
./run_gunicorn.sh

# In another terminal, test
curl http://localhost:5000

# Check if scheduler is running
grep "scheduler" logs/audio_scheduler.log
```

## Troubleshooting

### Port Already in Use
```bash
# Find process using port 5000
sudo lsof -i :5000

# Kill process
sudo kill -9 <PID>
```

### Scheduler Not Running
Check logs for initialization:
```bash
grep "SimpleScheduler" logs/audio_scheduler.log
```

Should see:
- `SimpleScheduler initialized`
- `✅ Simple scheduler started - polling every second`

### Audio Not Playing
Ensure pygame can access audio:
```bash
python -c "import pygame; pygame.mixer.init(); print('Audio OK')"
```

## Comparison: Flask Dev Server vs Gunicorn

| Feature | Flask Dev Server | Gunicorn |
|---------|-----------------|----------|
| **Purpose** | Development | Production |
| **Performance** | Low | High |
| **Stability** | Basic | Excellent |
| **Auto-reload** | Yes | No |
| **Process management** | None | Built-in |
| **Logging** | Basic | Advanced |
| **Security** | Minimal | Production-grade |
| **Use for** | Development | Production |

## For Systemd Service

See [SERVICE_INSTALL.md](SERVICE_INSTALL.md) for deploying as a systemd service.
