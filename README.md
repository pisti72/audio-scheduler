# Audio scheduler

Scheduled playing of uploaded audio files. Backend is a python webserver. The frontend is simpe html css.

Audio Scheduler is a web application that lets you upload audio files and schedule them to play automatically at specific times and days of the week. It features a simple HTML/CSS frontend and a Python Flask backend, with persistent schedule storage using SQLite. Ideal for use cases like automated school bells or timed announcements.

## Initial Setup

Before running the application, ensure you have the required directories:

```bash
# Create uploads directory for audio files
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

2. Install the required Python packages:
	```bash
	pip install -r requirements.txt
	```

3. Initialize the database:
	```bash
	flask db upgrade
	```

4. Run the application:
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