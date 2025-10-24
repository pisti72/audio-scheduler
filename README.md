# Audio scheduler

Scheduled playing of uploaded audio files. Backend is a python webserver. The frontend is simpe html css.

Audio Scheduler is a web application that lets you upload audio files and schedule them to play automatically at specific times and days of the week. It features a simple HTML/CSS frontend and a Python Flask backend, with persistent schedule storage using SQLite. Ideal for use cases like automated school bells or timed announcements.

## Initial Setup

Before running the application, ensure you have the required directories:

```bash
# Create uploads directory for audio files if not exists
mkdir -p uploads

# Create instance directory for the SQLite database
mkdir -p instance
```

These directories are essential for persistent storage:
- `uploads/`: Stores all uploaded audio files
- `instance/`: Contains the SQLite database (schedules.db)

## Installation and Running

### Manual Installation (without Docker)

1. Install Python 3.7 or higher on your system

2. Install system dependencies (Fedora/RHEL/CentOS):
	```bash
	sudo dnf install SDL2-devel SDL2_mixer-devel SDL2_image-devel SDL2_ttf-devel
	sudo dnf install portmidi-devel
	sudo dnf install python3-devel
	sudo dnf install python3-pygame
	```

	For Ubuntu/Debian systems, use equivalent packages:
	```bash
	sudo apt-get install libsdl2-dev libsdl2-mixer-dev libsdl2-image-dev libsdl2-ttf-dev
	sudo apt-get install libportmidi-dev
	sudo apt-get install python3-dev
	sudo apt-get install python3-pygame
	```

	For Windows systems:
	```cmd
	# Install Visual C++ Build Tools if not already installed
	# Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
	
	# Update pip and install wheel first
	python -m pip install --upgrade pip wheel
	
	# Install pygame separately (often resolves SDL dependency issues)
	pip install pygame
	
	# If pygame installation fails, try pre-compiled wheel:
	pip install --upgrade pygame --force-reinstall
	```

3. Install the required Python packages:
	```bash
	pip install -r requirements.txt
	```

	If you encounter compatibility issues, try installing specific versions:
	```bash
	pip install Flask==2.0.1 APScheduler==3.9.1 python-dotenv==0.19.0
	pip install 'Werkzeug<2.1.0'
	```

4. Initialize the database:
	```bash
	flask db upgrade
	```

5. Run the application:
	```bash
	python app.py
	```

The application will be available at http://localhost:5000

### Docker

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

- The app will be available at http://localhost:5000
- Uploaded files and the database will be stored on your host machine.