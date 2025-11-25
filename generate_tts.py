#!/usr/bin/env python3
"""
Generate TTS time announcements using ElevenLabs API
Reads times from CSV export and generates audio files in 5 languages
"""

import os
import csv
import requests
from pathlib import Path
from datetime import datetime

# ElevenLabs API configuration
ELEVENLABS_API_KEY = "sk_ba8d7cf6a4b4b121813ca3f1a97007d65f569a5433722b21"
ELEVENLABS_API_URL = "https://api.elevenlabs.io/v1/text-to-speech"

# Voice IDs for different languages (multilingual voices from ElevenLabs)
# You can customize these - use voice library to find suitable voices
VOICES = {
    'hu': 'Xb7hH8MSUJpSbSDYk0k2',  # Alice - multilingual (Eleven Flash v2.5)
    'en': '21m00Tcm4TlvDq8ikWAM',  # Rachel - English
    'it': 'XB0fDUnXU5powFXDhCwa',  # Charlotte - multilingual
    'de': 'ErXwobaYiN019PkySvjV',  # Antoni - multilingual
    'es': 'ThT5KcBeYPX3keUQqHPh',  # Dorothy - multilingual
}

# Model IDs for each language
MODELS = {
    'hu': 'eleven_flash_v2_5',  # Flash v2.5 for Hungarian
    'en': 'eleven_multilingual_v2',
    'it': 'eleven_multilingual_v2',
    'de': 'eleven_flash_v2_5',
    'es': 'eleven_multilingual_v2',
}

# Time format templates for each language
TIME_TEMPLATES = {
    'hu': "A pontos idő {hour} óra {minute:02d} perc.",
    'en': "The time is {hour}:{minute:02d}.",
    'it': "Sono le {hour}:{minute:02d}.",
    'de': "Es ist {hour} Uhr {minute:02d} Minuten.",
    'es': "Son las {hour}:{minute:02d}.",
}

def format_time_text(time_str, lang):
    """
    Format time string into spoken text for given language
    Args:
        time_str: Time in HH:MM format (e.g., "08:35")
        lang: Language code (hu, en, it, de, es)
    Returns:
        Formatted text ready for TTS
    """
    try:
        hour, minute = map(int, time_str.split(':'))
        
        # Special handling for Spanish
        if lang == 'es':
            if hour == 1 and minute == 0:
                return "Es la una."
            elif minute == 0:
                return f"Son las {hour}:00."
            elif hour < 2:
                return f"Es la {hour}:{minute:02d}."
            else:
                return f"Son las {hour}:{minute:02d}."
        
        # For other languages, use template
        template = TIME_TEMPLATES.get(lang, TIME_TEMPLATES['en'])
        return template.format(hour=hour, minute=minute)
        
    except Exception as e:
        print(f"Error formatting time {time_str} for {lang}: {e}")
        return None

def generate_tts(text, voice_id, output_path, lang='en'):
    """
    Generate TTS audio using ElevenLabs API
    Args:
        text: Text to convert to speech
        voice_id: ElevenLabs voice ID
        output_path: Path to save the MP3 file
        lang: Language code to select appropriate model
    Returns:
        True if successful, False otherwise
    """
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY
    }
    
    # Select model based on language
    model_id = MODELS.get(lang, 'eleven_multilingual_v2')
    
    data = {
        "text": text,
        "model_id": model_id,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0.0,
            "use_speaker_boost": True
        }
    }
    
    try:
        url = f"{ELEVENLABS_API_URL}/{voice_id}"
        response = requests.post(url, json=data, headers=headers, timeout=30)
        
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            return True
        else:
            print(f"API Error {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"Exception during TTS generation: {e}")
        return False

def get_times_from_csv(csv_path):
    """
    Extract unique times from CSV export
    Args:
        csv_path: Path to CSV file
    Returns:
        Set of time strings in HH:MM format
    """
    times = set()
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                time_str = row.get('Time', '').strip()
                if time_str and ':' in time_str:
                    times.add(time_str)
        
        return sorted(times)
        
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return []

def generate_all_tts_files(csv_path, output_dir, languages=None, skip_existing=True):
    """
    Generate all TTS files for times in CSV
    Args:
        csv_path: Path to CSV file with schedule times
        output_dir: Directory to save generated MP3 files
        languages: List of language codes (default: all 5 languages)
        skip_existing: If True, skip files that already exist
    """
    if languages is None:
        languages = ['hu', 'en', 'it', 'de', 'es']
    
    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Get times from CSV
    times = get_times_from_csv(csv_path)
    if not times:
        print("No times found in CSV file!")
        return
    
    print(f"Found {len(times)} unique times in CSV")
    print(f"Generating TTS for languages: {', '.join(languages)}")
    print(f"Output directory: {output_path}")
    print("-" * 60)
    
    total_files = len(times) * len(languages)
    generated = 0
    skipped = 0
    failed = 0
    
    for time_str in times:
        for lang in languages:
            # Generate filename: HHMM_lang.mp3
            time_clean = time_str.replace(':', '')
            filename = f"{time_clean}_{lang}.mp3"
            output_file = output_path / filename
            
            # Skip if file exists and skip_existing is True
            if skip_existing and output_file.exists():
                print(f"⏭️  Skipping {filename} (already exists)")
                skipped += 1
                continue
            
            # Format text for this language
            text = format_time_text(time_str, lang)
            if not text:
                print(f"❌ Failed to format time {time_str} for {lang}")
                failed += 1
                continue
            
            # Get voice ID for this language
            voice_id = VOICES.get(lang)
            if not voice_id:
                print(f"❌ No voice configured for language: {lang}")
                failed += 1
                continue
            
            # Generate TTS
            print(f"🔊 Generating {filename}: '{text}'")
            if generate_tts(text, voice_id, output_file, lang):
                print(f"✅ Generated: {filename}")
                generated += 1
            else:
                print(f"❌ Failed: {filename}")
                failed += 1
    
    print("-" * 60)
    print(f"Summary:")
    print(f"  ✅ Generated: {generated}")
    print(f"  ⏭️  Skipped:   {skipped}")
    print(f"  ❌ Failed:    {failed}")
    print(f"  📊 Total:     {total_files}")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Generate TTS time announcements using ElevenLabs API'
    )
    parser.add_argument(
        'csv_file',
        nargs='?',
        default='csv-exports/audio_schedules_Normál_20251026_124413.csv',
        help='Path to CSV file with schedule times'
    )
    parser.add_argument(
        '--output-dir',
        default='itstime',
        help='Output directory for MP3 files (default: itstime)'
    )
    parser.add_argument(
        '--languages',
        nargs='+',
        choices=['hu', 'en', 'it', 'de', 'es'],
        help='Languages to generate (default: all 5)'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Regenerate files even if they already exist'
    )
    parser.add_argument(
        '--test',
        metavar='TIME',
        help='Test mode: generate only for specific time (e.g., 08:00)'
    )
    
    args = parser.parse_args()
    
    # Test mode - generate single time
    if args.test:
        print(f"Test mode: Generating TTS for {args.test}")
        output_path = Path(args.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        languages = args.languages or ['hu', 'en', 'it', 'de', 'es']
        
        for lang in languages:
            text = format_time_text(args.test, lang)
            voice_id = VOICES.get(lang)
            
            time_clean = args.test.replace(':', '')
            filename = f"{time_clean}_{lang}.mp3"
            output_file = output_path / filename
            
            print(f"🔊 {lang.upper()}: '{text}'")
            if generate_tts(text, voice_id, output_file, lang):
                print(f"✅ Generated: {filename}")
            else:
                print(f"❌ Failed: {filename}")
        
        return
    
    # Normal mode - process CSV
    if not Path(args.csv_file).exists():
        print(f"Error: CSV file not found: {args.csv_file}")
        print("\nAvailable CSV files:")
        csv_dir = Path('csv-exports')
        if csv_dir.exists():
            for csv_file in csv_dir.glob('*.csv'):
                print(f"  - {csv_file}")
        return
    
    generate_all_tts_files(
        args.csv_file,
        args.output_dir,
        languages=args.languages,
        skip_existing=not args.force
    )

if __name__ == '__main__':
    main()
