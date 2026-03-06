"""
Diagnostic test for Meta MMS transcription - identifying why it fails
"""

import sys
import os
import tempfile
import logging
import numpy as np
import wave
import torch

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_mms_kikuyu():
    """Test MMS with detailed diagnostics"""
    print("\n" + "#"*60)
    print("# MMS KIKUYU DIAGNOSTIC TEST")
    print("#"*60)
    
    # Load model
    print("\n[1] Loading MMS model...")
    from backend.stt.mms_engine import load_mms_model, _MODEL, _PROCESSOR, KIKUYU_CODE
    
    model, processor = load_mms_model()
    
    print(f"\n[2] Checking model configuration...")
    print(f"    Model type: {type(model).__name__}")
    print(f"    Target language: {KIKUYU_CODE}")
    
    # Check processor tokenizer
    print(f"\n[3] Analyzing tokenizer...")
    tokenizer = processor.tokenizer
    print(f"    Tokenizer type: {type(tokenizer).__name__}")
    print(f"    Vocab size: {len(tokenizer)}")
    
    # This is the KEY DIAGNOSTIC:
    print(f"\n[4] 🔍 CRITICAL CHECK: Is Kikuyu adapter loaded?")
    print(f"    Expected vocab size: ~1000+ (for a language)")
    print(f"    Actual vocab size: {len(tokenizer)}")
    
    if len(tokenizer) < 100:
        print(f"    ❌ PROBLEM: Vocab size is too small!")
        print(f"    This means the Kikuyu adapter was NOT properly loaded.")
        print(f"    The model is using only basic characters, not a full tokenizer.")
    
    # Check what languages are available
    print(f"\n[5] Checking available languages...")
    if hasattr(tokenizer, 'tokenizer'):
        if hasattr(tokenizer.tokenizer, 'lang_to_id'):
            print(f"    Available languages: {list(tokenizer.tokenizer.lang_to_id.keys())[:20]}...")
    
    # Test encoding
    print(f"\n[6] Testing encoding...")
    test_words = ["thayu", "wĩmwega", "ngatho", "hello", "world"]
    for word in test_words:
        ids = tokenizer.encode(word)
        decoded = tokenizer.decode(ids)
        print(f"    '{word}' -> {ids} -> '{decoded}'")
    
    # Test with actual speech-like audio
    print(f"\n[7] Testing transcription with speech-like audio...")
    
    # Create a more realistic audio file with actual speech patterns
    # This generates a signal that mimics speech formants
    sample_rate = 16000
    duration = 3.0
    
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Create speech-like signal with formants (F1, F2, F3)
    # For "thayu" greeting: F1~500Hz, F2~1500Hz, F3~2500Hz
    audio = (
        0.3 * np.sin(2 * np.pi * 300 * t) +    # Fundamental
        0.25 * np.sin(2 * np.pi * 500 * t) +    # F1
        0.2 * np.sin(2 * np.pi * 1200 * t) +   # F2
        0.15 * np.sin(2 * np.pi * 2400 * t) +  # F3
        0.05 * np.random.randn(len(t))          # Noise
    )
    
    # Apply envelope (attack-sustain-release)
    attack = int(0.1 * sample_rate)
    release = int(0.5 * sample_rate)
    envelope = np.ones(len(t))
    envelope[:attack] = np.linspace(0, 1, attack)
    envelope[-release:] = np.linspace(1, 0, release)
    audio = audio * envelope
    
    audio = audio.astype(np.float32)
    
    # Save test file
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        test_path = f.name
        with wave.open(test_path, 'w') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio.tobytes())
    
    print(f"    Testing with {duration}s speech-like audio...")
    
    # Transcribe
    from backend.stt.mms_engine import transcribe_kikuyu
    result = transcribe_kikuyu(test_path)
    
    print(f"\n[8] Transcription result:")
    print(f"    Success: {result['success']}")
    print(f"    Text: '{result['text']}'")
    print(f"    Duration: {result.get('duration', 0):.2f}s")
    if not result['success']:
        print(f"    Error: {result.get('error')}")
    
    os.unlink(test_path)
    
    # Diagnosis
    print("\n" + "="*60)
    print("DIAGNOSIS SUMMARY")
    print("="*60)
    
    if len(tokenizer) < 100:
        print("\n❌ ROOT CAUSE IDENTIFIED:")
        print("   The Kikuyu language adapter is NOT properly loaded!")
        print("   The tokenizer only has 39 tokens (basic characters)")
        print("   instead of a full Kikuyu vocabulary.")
        print("\n🔧 SOLUTIONS:")
        print("   1. Check if 'facebook/mms-1b-all' has 'kik' language support")
        print("   2. Try using 'facebook/mms-1b-fl102' (Fleurs dataset version)")
        print("   3. Try using a different model: 'facebook/mms-1b-all' might need")
        print("      explicit adapter loading with correct language code")
        print("   4. Consider using Whisper instead for Kikuyu")
    else:
        print("\n✅ Kikuyu adapter appears to be loaded")
        print(f"   Vocab size: {len(tokenizer)}")
        
    print("\n" + "="*60)
    print("TESTING WHISPER AS ALTERNATIVE")
    print("="*60)
    
    # Test with Whisper as alternative
    print("\n[9] Testing Whisper STT as fallback...")
    try:
        from backend.stt.speech_to_text import WhisperSTT
        
        whisper = WhisperSTT(model_size="tiny")
        whisper.load_model()
        
        # Create same audio for whisper
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            test_path2 = f.name
            with wave.open(test_path2, 'w') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio.tobytes())
        
        # Use language='en' which forces Latin alphabet
        result2 = whisper.transcribe(test_path2, language="en")
        
        print(f"\n[10] Whisper result:")
        print(f"     Success: {result2['success']}")
        print(f"     Text: '{result2['text']}'")
        print(f"     Detected language: {result2.get('language')}")
        
        os.unlink(test_path2)
        
    except Exception as e:
        print(f"\n❌ Whisper test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_mms_kikuyu()
