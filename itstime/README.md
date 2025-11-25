# Time To Speech (TTS)

This folder contains AI-generated time announcements in 5 languages using ElevenLabs API.

## Languages Supported

- **HU (Hungarian)**: "A pontos idő 8:00 óra."
- **EN (English)**: "It is 8:00."
- **IT (Italian)**: "Sono le 8:00."
- **DE (German)**: "Es ist 8:00 Uhr."
- **ES (Spanish)**: "Son las 8:00." (or "Es la 1:00." for 1 AM/PM)

## File Naming Convention

Files are named using the format: `HHMM_lang.mp3`

Examples:
- `0745_hu.mp3` - 7:45 in Hungarian
- `1215_en.mp3` - 12:15 in English
- `1600_de.mp3` - 16:00 in German

## Generating TTS Files

### Prerequisites
```bash
source venv/bin/activate
pip install requests
```

### Usage

Generate all times from a CSV file (default: skips existing files):
```bash
python generate_tts.py csv-exports/audio_schedules_Normál_20251026_124413.csv
```

Generate for specific languages only:
```bash
python generate_tts.py --languages hu en de
```

Force regeneration (overwrite existing files):
```bash
python generate_tts.py --force
```

Test with a single time:
```bash
python generate_tts.py --test 14:30 --languages hu en
```

Custom output directory:
```bash
python generate_tts.py --output-dir custom_folder
```

### Help
```bash
python generate_tts.py --help
```

## ElevenLabs API Configuration

API Key: `sk_ba8d7cf6a4b4b121813ca3f1a97007d65f569a5433722b21`
API Docs: https://elevenlabs.io/app/developers/api-keys

### Voice Settings
- Model: `eleven_multilingual_v2` (EN, IT, DE, ES) / `eleven_flash_v2_5` (HU)
- Stability: 0.5
- Similarity Boost: 0.75
- Speaker Boost: Enabled

### Configured Voices
The script uses optimized voices for each language:
- HU: Alice (Eleven Flash v2.5 - high quality multilingual)
- EN: Rachel (English native)
- IT: Charlotte (multilingual)
- DE: Antoni (multilingual)
- ES: Dorothy (multilingual)

You can change voice IDs in `generate_tts.py` by browsing the ElevenLabs voice library.

## Current Status

Total files generated: 102 MP3 files
- 20 unique times
- 5 languages each
- Plus 2 test files (0800_hu.mp3, 0800_en.mp3)
