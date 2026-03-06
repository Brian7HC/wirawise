f#!/usr/bin/env python3
"""
Test script for badrex/w2v-bert-2.0-kikuyu-asr
Run this to test the model with a local WAV file
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from stt.mms_engine import transcribe_kikuyu
import logging

# Enable logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

def test_transcription(audio_path):
    """
    Test transcription with a local audio file
    """
    print(f"\n{'='*60}")
    print(f"Testing Kikuyu ASR with: {audio_path}")
    print(f"{'='*60}")
    
    if not os.path.exists(audio_path):
        print(f"\n❌ File not found: {audio_path}")
        print("\nPlease provide a valid WAV file path.")
        print("You can record one using:")
        print("  - Voice recorder app on your phone")
        print("  - Audacity or similar on desktop")
        print("  - Browser recording (after refreshing the page)")
        return
    
    # Run transcription
    result = transcribe_kikuyu(audio_path)
    
    print(f"\n{'='*60}")
    print("RESULTS:")
    print(f"{'='*60}")
    print(f"Success: {result['success']}")
    print(f"Text: {result.get('text', 'N/A')}")
    print(f"Duration: {result.get('duration', 0):.2f}s")
    if 'error' in result:
        print(f"Error: {result['error']}")
    print(f"{'='*60}")

if __name__ == "__main__":
    # Check for audio file argument
    if len(sys.argv) > 1:
        audio_file = sys.argv[1]
    else:
        # Check for any existing test audio
        test_files = [
            "test_audio.wav",
            "data/audio/test.wav",
            "recording.wav"
        ]
        
        for f in test_files:
            if os.path.exists(f):
                audio_file = f
                break
        else:
            print("\n" + "="*60)
            print("KIKUYU ASR TEST SCRIPT")
            print("="*60)
            print("\nUsage: python test_kikuyu_asr.py <audio_file.wav>")
            print("\nExample:")
            print("  python test_kikuyu_asr.py my_recording.wav")
            print("\nThe model is already loaded and ready!")
            print("Just provide a WAV file path to test transcription.")
            sys.exit(1)
    
    test_transcription(audio_file)
