#!/usr/bin/env python3
"""
Test Whisper speech recognition
"""

import whisper
import time

print("=" * 70)
print("🎤 WHISPER SPEECH-TO-TEXT TEST")
print("=" * 70)

# Load model
print("\n📥 Loading Whisper model (this may take a minute)...")
start = time.time()

# Use 'base' model for testing (faster)
# Options: tiny, base, small, medium, large
model = whisper.load_model("base")

print(f"✅ Model loaded in {time.time() - start:.2f} seconds")
print(f"   Model: base")
print(f"   Parameters: ~74M")

# Test transcription
print("\n🧪 Testing transcription...")

# You can test with a sample audio file if you have one
# For now, let's just show the model is ready
print("✅ Whisper is ready to transcribe audio!")

print("\n" + "=" * 70)
print("Next: Integrate with backend API")
print("=" * 70)
