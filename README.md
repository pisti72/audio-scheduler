# Audio Scheduler

🎵 **Scheduled playing of uploaded audio files with a web interface** 🎵

Audio Scheduler is a web application that lets you upload audio files and schedule them to play automatically at specific times and days of the week. It features a simple HTML/CSS frontend and a Python Flask backend, with persistent schedule storage using SQLite. Ideal for use cases like automated school bells, timed announcements, or any scheduled audio playback needs.

## ⚡ Quick Installation (Recommended)

The easiest way to get started is with our automated installation scripts that handle everything for you:

### Linux/macOS (Automated)
```bash
git clone https://github.com/pisti72/audio-scheduler.git
cd audio-scheduler
./install.sh
```

### Windows (Automated)
```cmd
git clone https://github.com/pisti72/audio-scheduler.git
cd audio-scheduler
install.bat
```

The installation script will:
- ✅ Install all system dependencies automatically
- ✅ Create a virtual environment
- ✅ Install Python dependencies in isolation
- ✅ Initialize the database
- ✅ Create run scripts for easy startup

After installation, simply run:
- **Linux/macOS**: `./run.sh`
- **Windows**: `run.bat`

Then open your browser to: **http://localhost:5000**

Default credentials: **admin** / **admin**

## Manual Installation (Advanced Users)

⚠️ **Note**: Manual installation can be complex due to system dependencies. We strongly recommend using the automated installation scripts above for a smoother experience.

### Prerequisites
- Python 3.8 or higher
- Git
- System audio libraries (SDL2, PortMidi, ALSA)

### Step-by-Step Manual Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/pisti72/audio-scheduler.git
   cd audio-scheduler
   ```

2. **Create a virtual environment** (strongly recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/macOS
   # or
   venv\Scripts\activate     # Windows
   ```

3. **Install system dependencies**:

   **Fedora/RHEL/CentOS**:
   ```bash
   sudo dnf install python3-devel SDL2-devel SDL2_mixer-devel portmidi-devel alsa-lib-devel
   ```

   **Ubuntu/Debian**:
   ```bash
   sudo apt-get install python3-dev libsdl2-dev libsdl2-mixer-dev libportmidi-dev libasound2-dev
   ```

   **Windows**:
   ```cmd
   # Install Visual C++ Build Tools from:
   # https://visualstudio.microsoft.com/visual-cpp-build-tools/
   ```

4. **Install Python dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

5. **Initialize the application**:
   ```bash
   mkdir -p uploads instance
   python app.py  # This will create the database
   ```

### Running the Application

**Development Mode** (auto-reload, debugging):
```bash
# Using the run script (recommended)
./run.sh          # Linux/macOS
run.bat           # Windows

# Or manually
python app.py
```

**Production Mode** (stable, recommended for deployment):
```bash
# Using Gunicorn WSGI server (recommended)
./run_gunicorn.sh     # Linux/macOS
run_gunicorn.bat      # Windows

# Or manually
gunicorn -w 1 -b 0.0.0.0:5000 wsgi:app
```

**As System Service** (auto-start on boot):
```bash
# See SERVICE_INSTALL.md for full instructions
sudo cp audio-scheduler.service /etc/systemd/system/
sudo systemctl enable --now audio-scheduler
```

📚 **See also**: 
- [DEPLOYMENT.md](DEPLOYMENT.md) - Complete deployment checklist for new servers
- [GUNICORN.md](GUNICORN.md) - Production deployment with Gunicorn
- [SERVICE_INSTALL.md](SERVICE_INSTALL.md) - Systemd service setup and troubleshooting

## 🚨 Troubleshooting

### Common Installation Issues

**pygame installation fails**:
```bash
# Try installing system dependencies first, then:
pip install pygame --force-reinstall
```

**SDL/Audio library errors**:
- Ensure you have SDL2 development libraries installed
- On Linux: Install ALSA development packages
- On Windows: Install Visual C++ Build Tools

**Permission errors on Linux**:
```bash
# Make sure scripts are executable
chmod +x install.sh run.sh
```

**Python version issues**:
- Minimum required: Python 3.8
- Check with: `python --version`

**Virtual environment issues**:
```bash
# Remove and recreate virtual environment
rm -rf venv
python3 -m venv venv
```

### Getting Help

If you encounter issues not covered here:
1. Check the GitHub Issues section
2. Ensure all system dependencies are installed
3. Try the automated installation script first
4. Use virtual environments to avoid conflicts

## � Getting Started

After successful installation, here's how to use the Audio Scheduler:

1. **Access the web interface**: Open http://localhost:5000 in your browser
2. **Login**: Use default credentials `admin` / `admin`
3. **Upload audio files**: Click "Choose File" to upload your audio files (MP3, WAV, etc.)
4. **Create schedules**: Set the time and days when you want the audio to play
5. **Manage multiple schedule lists**: Use tabs to organize different sets of schedules
6. **Monitor**: The interface shows when each schedule will run next

### Features

- ✅ **Multiple Schedule Lists**: Organize schedules into different tabs/lists
- ✅ **Mute/Unmute**: Temporarily disable schedules without deleting them
- ✅ **Edit Schedules**: Modify time and days for existing schedules
- ✅ **Multi-language Support**: English, Hungarian, German, Spanish
- ✅ **Real-time Clock**: See current time in the interface
- ✅ **Manual Page**: Built-in help and documentation
- ✅ **Responsive Design**: Works on desktop and mobile devices

## �🐳 Container Deployment

To build and run this application with Docker:

1. Build the Docker image:
	```bash
	docker build -t audioscheduler .
	```

2. Run the container (with persistent uploads and database):
	```bash
	docker run -d -p 5000:5000 --name audioscheduler \
	  -v $(pwd)/uploads:/app/uploads \
	  -v $(pwd)/schedules.db:/app/schedules.db \
	  audioscheduler
	```

### Podman

To build and run this application with Podman (Docker alternative):

1. Build the Podman image:
	```bash
	podman build -t audioscheduler .
	```

2. Run the container (with persistent uploads and database):
	```bash
	podman run -d -p 5000:5000 --name audioscheduler \
	  -v $(pwd)/uploads:/app/uploads \
	  -v $(pwd)/schedules.db:/app/schedules.db \
	  audioscheduler
	```

3. Alternative: Run as systemd service (rootless):
	```bash
	# Generate systemd unit file
	podman generate systemd --new --name audioscheduler > ~/.config/systemd/user/audioscheduler.service
	
	# Enable and start the service
	systemctl --user daemon-reload
	systemctl --user enable --now audioscheduler.service
	```

**Both Docker and Podman:**
- The app will be available at http://localhost:5000
- Uploaded files and the database will be stored on your host machine.