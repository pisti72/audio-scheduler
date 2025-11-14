#!/usr/bin/env python3
import os
import sys
os.environ.setdefault('PULSE_SERVER', 'unix:/run/user/%d/pulse/native' % os.getuid())

import pygame
pygame.mixer.init()

# Test with a simple beep or existing file
test_file = 'uploads/school_triad.mp3'
if os.path.exists(test_file):
    print(f"Testing audio playback with {test_file}...")
    pygame.mixer.music.load(test_file)
    pygame.mixer.music.play()
    import time
    while pygame.mixer.music.get_busy():
        time.sleep(0.1)
    print("Audio test completed successfully!")
else:
    print(f"Test file {test_file} not found")
    sys.exit(1)
