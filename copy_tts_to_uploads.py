#!/usr/bin/env python3
"""
Copy TTS files to uploads folder and optionally create schedules
"""

import os
import shutil
import sys
from pathlib import Path

def copy_tts_to_uploads(language='hu', prefix='time_', dry_run=False):
    """
    Copy TTS files from itstime/ to uploads/ folder
    
    Args:
        language: Language code (hu, en, it, de, es)
        prefix: Prefix to add to uploaded filenames
        dry_run: If True, just show what would be copied
    """
    script_dir = Path(__file__).parent
    itstime_dir = script_dir / 'itstime'
    uploads_dir = script_dir / 'uploads'
    
    if not itstime_dir.exists():
        print(f"Error: {itstime_dir} not found!")
        return False
    
    if not uploads_dir.exists():
        print(f"Creating uploads directory: {uploads_dir}")
        if not dry_run:
            uploads_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all TTS files for the specified language
    pattern = f"*_{language}.mp3"
    tts_files = sorted(itstime_dir.glob(pattern))
    
    if not tts_files:
        print(f"No TTS files found for language: {language}")
        return False
    
    print(f"Found {len(tts_files)} TTS files for language: {language.upper()}")
    print("-" * 60)
    
    copied = 0
    skipped = 0
    
    for src_file in tts_files:
        # Extract time from filename (e.g., "0745_hu.mp3" -> "0745")
        time_part = src_file.stem.split('_')[0]
        
        # Create destination filename
        dest_filename = f"{prefix}{time_part}_{language}.mp3"
        dest_file = uploads_dir / dest_filename
        
        # Check if file already exists
        if dest_file.exists():
            src_size = src_file.stat().st_size
            dest_size = dest_file.stat().st_size
            
            if src_size == dest_size:
                print(f"⏭️  Skip: {dest_filename} (already exists, same size)")
                skipped += 1
                continue
            else:
                print(f"⚠️  Replace: {dest_filename} (different size)")
        
        # Copy file
        if dry_run:
            print(f"📋 Would copy: {src_file.name} -> {dest_filename}")
        else:
            shutil.copy2(src_file, dest_file)
            print(f"✅ Copied: {src_file.name} -> {dest_filename}")
        
        copied += 1
    
    print("-" * 60)
    print(f"Summary:")
    print(f"  ✅ Copied: {copied}")
    print(f"  ⏭️  Skipped: {skipped}")
    print(f"  📊 Total: {len(tts_files)}")
    
    if dry_run:
        print("\nThis was a dry run. Use --execute to actually copy files.")
    
    return True

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Copy TTS files from itstime/ to uploads/ folder'
    )
    parser.add_argument(
        '--language',
        choices=['hu', 'en', 'it', 'de', 'es', 'all'],
        default='hu',
        help='Language to copy (default: hu)'
    )
    parser.add_argument(
        '--prefix',
        default='time_',
        help='Prefix for uploaded filenames (default: time_)'
    )
    parser.add_argument(
        '--execute',
        action='store_true',
        help='Actually copy files (default is dry-run)'
    )
    
    args = parser.parse_args()
    
    if args.language == 'all':
        languages = ['hu', 'en', 'it', 'de', 'es']
        print("Copying TTS files for ALL languages")
        print("=" * 60)
        
        for lang in languages:
            print(f"\n### Processing {lang.upper()} ###")
            copy_tts_to_uploads(lang, args.prefix, dry_run=not args.execute)
    else:
        copy_tts_to_uploads(args.language, args.prefix, dry_run=not args.execute)

if __name__ == '__main__':
    main()
