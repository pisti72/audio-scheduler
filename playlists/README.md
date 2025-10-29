# Playlists Folders

## Overview
This directory contains playlist folders that can be used for scheduled audio playback in the Audio Scheduler application.

## How to Add Playlists

To make your audio folders available in the playlist selection list:

1. **Create a folder** in this `playlists/` directory with a descriptive name
   - Example: `morning_music`, `lunch_break`, `school_announcements`

2. **Add your audio files** to the folder
   - Supported formats: MP3, WAV, OGG, M4A, FLAC
   - Files can be in any organization within the folder

3. **Folder structure example:**
   ```
   playlists/
   ├── morning_music/
   │   ├── song1.mp3
   │   ├── song2.mp3
   │   └── song3.wav
   ├── lunch_break/
   │   ├── announcement.mp3
   │   └── background_music.mp3
   └── school_radio/
       ├── intro.mp3
       ├── news.wav
       └── outro.mp3
   ```

4. **Access in the application:**
   - Go to the "Playlists" tab in the web interface
   - Your folders will appear in the "Playlist Folder" dropdown
   - Select a folder to see a preview of its audio files

## Features

When creating a playlist schedule, you can configure:
- **Start time** and **days** for playback
- **Duration** (how long the playlist should run)
- **Max tracks** (limit the number of songs played)
- **Track interval** (time between songs)
- **Shuffle mode** (random or sequential playback)

## Notes

- Folder names should not contain special characters
- Only folders with audio files will appear in the selection list
- Changes to folders are detected automatically when you reload the playlist tab
- Audio files are played in random order by default (configurable)