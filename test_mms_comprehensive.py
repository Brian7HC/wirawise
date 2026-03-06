"""
Comprehensive test script for Meta MMS transcription
Tests with synthetic Kikuyu audio patterns
"""

import sys
import os
import tempfile
import logging
import numpy as np
import wave

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

from backend.stt.mms_engine import (
    transcribe_kikuyu, 
    load_mms_model, 
    KIKUYU_CODE,
    _MODEL,
    _PROCESSOR
)

def create_test_audio_with_tone(frequency=200, duration=2.0, sample_rate=16000):
    """Create a test audio file with a specific tone"""
    t = np.linspace(0, duration, int(sample_rate * duration))
    # Generate a simple tone with some variation to simulate speech-like patterns
    audio = 0.3 * np.sin(2 * np.pi * frequency * t)
    audio += 0.1 * np.sin(2 * np.pi * (frequency * 2) * t)  # Add harmonics
    audio += 0.05 * np.sin(2 * np.pi * (frequency * 0.5) * t)  # Add sub-harmonics
    return audio.astype(np.float32)

def create_kikuyu_greeting_audio(sample_rate=16000, duration=2.0):
    """
    Create audio simulating Kikuyu greeting "thayu" (hello)
    This uses frequency patterns that approximate speech
    """
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # "thayu" - starting with 'th' sound (higher frequency), then 'a', 'yu'
    # Create a more complex waveform
    audio = np.zeros_like(t)
    
    # First second: 'th' sound (sharp attack, higher pitch ~300Hz)
    mid = int(sample_rate * 0.5)
    audio[:mid] = 0.4 * np.sin(2 * np.pi * 300 * t[:mid])
    audio[:mid] += 0.2 * np.sin(2 * np.pi * 600 * t[:mid])
    
    # Second part: 'ayu' sound (lower frequency ~200Hz)
    audio[mid:] = 0.3 * np.sin(2 * np.pi * 200 * t[mid:])
    audio[mid:] += 0.15 * np.sin(2 * np.pi * 400 * t[mid:])
    
    # Add some noise to make it more realistic
    audio += 0.02 * np.random.randn(len(audio))
    
    return audio.astype(np.float32)

def test_model_loading():
    """Test 1: Verify model loads correctly"""
    print("\n" + "="*60)
    print("TEST 1: Model Loading")
    print("="*60)
    
    model, processor = load_mms_model()
    
    print(f"\n✅ Model loaded successfully!")
    print(f"   Model type: {type(model).__name__}")
    print(f"   Processor type: {type(processor).__name__}")
    
    # Check tokenizer settings
    print(f"\n   Target language code: {KIKUYU_CODE}")
    print(f"  Tokenizer vocab size: {len(processor.tokenizer)}")
    
    # Test tokenizer
    test_ids = processor.tokenizer.encode("thayu")
    print(f"   Test encoding 'thayu': {test_ids}")
    
    return model, processor

def test_adapter_loading(model, processor):
    """Test 2: Verify adapter loading for Kikuyu"""
    print("\n" + "="*60)
    print("TEST 2: Adapter Loading for Kikuyu")
    print("="*60)
    
    try:
        # Check if adapter is loaded
        if hasattr(model, 'config'):
            print(f"   Model config adapter: {model.config.adapter}")
            
        # Test encoding with Kikuyu
        test_text = "thayu"
        inputs = processor(test_text, return_tensors="pt")
        print(f"   ✅ Tokenizer configured for Kikuyu")
        print(f"   Test encoding '{test_text}': {inputs['input_ids'].tolist()}")
        
    except Exception as e:
        print(f"   ❌ Adapter test failed: {e}")
        import traceback
        traceback.print_exc()

def test_silent_audio():
    """Test 3: Test with silent audio"""
    print("\n" + "="*60)
    print("TEST 3: Silent Audio Test")
    print("="*60)
    
    # Create silence
    sample_rate = 16000
    duration = 1.0
    silence = np.zeros(sample_rate * duration, dtype=np.float32)
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        test_path = f.name
        with wave.open(test_path, 'w') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(silence.tobytes())
    
    print(f"   Testing with {duration}s of silence...")
    result = transcribe_kikuyu(test_path)
    
    print(f"   Result: '{result['text']}' (success: {result['success']})")
    
    os.unlink(test_path)
    return result

def test_tone_audio():
    """Test 4: Test with tone audio"""
    print("\n" + "="*60)
    print("TEST 4: Tone Audio Test")
    print("="*60)
    
    # Create test audio
    sample_rate = 16000
    duration = 2.0
    audio = create_test_audio_with_tone(frequency=250, duration=duration, sample_rate=sample_rate)
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        test_path = f.name
        with wave.open(test_path, 'w') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio.tobytes())
    
    print(f"   Testing with {duration}s tone at 250Hz...")
    result = transcribe_kikuyu(test_path)
    
    print(f"   Result: '{result['text']}' (success: {result['success']})")
    if not result['success']:
        print(f"   Error: {result.get('error')}")
    
    os.unlink(test_path)
    return result

def test_kikuyu_greeting():
    """Test 5: Test with simulated Kikuyu greeting"""
    print("\n" + "="*60)
    print("TEST 5: Kikuyu Greeting Audio Test")
    print("="*60)
    
    # Create Kikuyu greeting audio
    sample_rate = 16000
    duration = 2.0
    audio = create_kikuyu_greeting_audio(sample_rate=sample_rate, duration=duration)
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        test_path = f.name
        with wave.open(test_path, 'w') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio.tobytes())
    
    print(f"   Testing with simulated Kikuyu greeting 'thayu'...")
    result = transcribe_kikuyu(test_path)
    
    print(f"   Result: '{result['text']}' (success: {result['success']})")
    print(f"   Duration: {result.get('duration', 0):.2f}s")
    if not result['success']:
        print(f"   Error: {result.get('error')}")
    
    os.unlink(test_path)
    return result

def diagnose_issues():
    """Run diagnostics to identify issues"""
    print("\n" + "="*60)
    print("DIAGNOSIS: Identifying Issues")
    print("="*60)
    
    # Check global state
    print(f"\nGlobal model state:")
    print(f"   _MODEL is None: {_MODEL is None}")
    print(f"   _PROCESSOR is None: {_PROCESSOR is None}")
    
    # Try to get model info
    if _MODEL is not None:
        print(f"\nModel details:")
        print(f"   Model class: {type(_MODEL).__name__}")
        
        # Check for adapters
        if hasattr(_MODEL, 'config'):
            print(f"   Has config: Yes")
            if hasattr(_MODEL.config, 'adapter'):
                print(f"   Adapter config: {_MODEL.config.adapter}")
        
        # Check for LoRA adapters (common in MMS)
        if hasattr(_MODEL, 'get_active_adapters'):
            try:
                adapters = _MODEL.get_active_adapters()
                print(f"   Active adapters: {adapters}")
            except:
                print(f"   Active adapters: None or error getting")
    
    if _PROCESSOR is not None:
        print(f"\nProcessor details:")
        print(f"   Processor class: {type(_PROCESSOR).__name__}")
        
        # Check tokenizer
        tokenizer = _PROCESSOR.tokenizer
        print(f"   Tokenizer class: {type(tokenizer).__name__}")
        print(f"   Vocab size: {len(tokenizer)}")
        
        # Check current language
        if hasattr(tokenizer, 'target_lang'):
            print(f"   Target lang: {tokenizer.target_lang}")

def main():
    """Run all tests"""
    print("\n" + "#"*60)
    print("# COMPREHENSIVE MMS TRANSCRIPTION TEST")
    print("# Testing Meta MMS for Kikuyu")
    print("#"*60)
    
    # Test 1: Model loading
    model, processor = test_model_loading()
    
    # Test 2: Adapter loading
    test_adapter_loading(model, processor)
    
    # Test 3: Silent audio
    result3 = test_silent_audio()
    
    # Test 4: Tone audio  
    result4 = test_tone_audio()
    
    # Test 5: Kikuyu greeting
    result5 = test_kikuyu_greeting()
    
    # Diagnosis
    diagnose_issues()
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    issues_found = []
    
    if not result3['success']:
        issues_found.append("Silent audio test failed")
    if not result4['success']:
        issues_found.append("Tone audio test failed")
    if not result5['success']:
        issues_found.append("Kikuyu greeting test failed")
    
    # Check if transcription is empty for non-silent audio
    if result5['success'] and result5['text'] == '':
        issues_found.append("Kikuyu greeting audio produced empty transcription")
    
    if issues_found:
        print("\n❌ ISSUES FOUND:")
        for issue in issues_found:
            print(f"   - {issue}")
        print("\n🔧 RECOMMENDED FIXES:")
        print("   1. Check if MMS adapter for 'kik' is properly loaded")
        print("   2. Verify the model has the Kikuyu language adapter")
        print("   3. Consider using a different approach (e.g., Whisper with Kikuyu fine-tuning)")
    else:
        print("\n✅ All tests passed!")
    
    print("\n" + "="*60)
    print("NOTE: The MMS model requires REAL Kikuyu speech audio")
    print("to accurately transcribe. Synthetic tones won't produce")
    print("meaningful text as they don't contain actual speech patterns.")
    print("="*60)

if __name__ == "__main__":
    main()
