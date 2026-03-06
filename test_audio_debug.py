"""
Debug script to test audio conversion
"""
import os
import tempfile

# Test with a sample webm file
test_files = os.listdir('temp/uploads')
if test_files:
    test_file = os.path.join('temp/uploads', test_files[-1])
    print(f"Testing with: {test_file}")
    
    import librosa
    import numpy as np
    
    # Load and analyze
    audio, sr = librosa.load(test_file, sr=16000, mono=True)
    print(f"Original - SR: {sr}, Duration: {len(audio)/sr:.2f}s")
    print(f"Original - min: {audio.min():.4f}, max: {audio.max():.4f}, RMS: {np.sqrt(np.mean(audio**2)):.4f}")
    
    # Normalize
    rms = np.sqrt(np.mean(audio ** 2))
    target_rms = 10 ** (-20 / 20)
    scale = target_rms / rms if rms > 1e-8 else 1
    normalized = np.clip(audio * scale, -1.0, 1.0)
    
    print(f"Normalized - min: {normalized.min():.4f}, max: {normalized.max():.4f}, RMS: {np.sqrt(np.mean(normalized**2)):.4f}")
else:
    print("No test files found")
