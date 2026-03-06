"""
Test script for Meta MMS transcription
"""

import sys
import os
import tempfile

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.stt.mms_engine import transcribe_kikuyu, load_mms_model

print("Testing Meta MMS for Kikuyu...")

# First, load the model
print("\n1. Loading MMS model...")
model, processor = load_mms_model()
print("✅ Model loaded successfully!")

# Test with a simple sine wave audio (will produce empty transcription but tests the pipeline)
print("\n2. Creating test audio file...")
import numpy as np
import wave

# Create a simple test audio file (1 second of silence at 16kHz)
sample_rate = 16000
duration = 1  # seconds
samples = np.zeros(sample_rate * duration, dtype=np.float32)

# Save to temporary file
with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
    test_audio_path = f.name
    with wave.open(test_audio_path, 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(samples.tobytes())

print(f"✅ Test audio created: {test_audio_path}")

# Test transcription
print("\n3. Testing transcription...")
result = transcribe_kikuyu(test_audio_path)

print(f"\nResult:")
print(f"  Success: {result['success']}")
print(f"  Text: '{result['text']}'")
print(f"  Duration: {result.get('duration', 0):.2f}s")

if result['success']:
    print("\n✅ MMS transcription pipeline is working!")
else:
    print(f"\n❌ Transcription failed: {result.get('error')}")

# Cleanup
os.unlink(test_audio_path)
print("\nTest complete!")
