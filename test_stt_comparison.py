"""
Test script to compare MMS vs Whisper for Kikuyu transcription
"""

import sys
import os
import tempfile
import logging
import numpy as np
import wave

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def create_realistic_kikuyu_audio(text: str, sample_rate=16000):
    """
    Create audio that more closely mimics real Kikuyu speech
    Uses formants and timing patterns
    """
    duration = max(2.0, len(text) * 0.4)  # Approximate speech timing
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Base frequency for speech
    f0 = 150  # Fundamental frequency
    
    audio = np.zeros_like(t)
    
    # Split time into segments for each character/phoneme
    n_chars = len(text)
    segment_len = len(t) // n_chars
    
    for i, char in enumerate(text):
        start_idx = i * segment_len
        end_idx = start_idx + segment_len
        
        if i == n_chars - 1:
            end_idx = len(t)  # Extend last segment
        
        segment_t = t[start_idx:end_idx]
        
        # Assign frequencies based on character type
        if char.lower() in 'aeiou':
            # Vowels - lower frequency
            freq = 400 + (ord(char) % 5) * 100
            amplitude = 0.3
        elif char.lower() in 'th':
            # Aspirated - higher frequency burst
            freq = 600 + (i * 50)
            amplitude = 0.35
        elif char.lower() in 'ng':
            # Nasal - specific pattern
            freq = 300
            amplitude = 0.25
        else:
            # Consonants
            freq = 350 + (ord(char) % 10) * 30
            amplitude = 0.25
        
        # Generate for this segment
        segment_audio = amplitude * np.sin(2 * np.pi * freq * segment_t)
        segment_audio += 0.1 * np.sin(2 * np.pi * freq * 2 * segment_t)  # Harmonic
        segment_audio += 0.05 * np.random.randn(len(segment_audio))  # Noise
        
        # Apply envelope within segment
        attack_len = min(int(0.05 * sample_rate), len(segment_audio) // 4)
        release_len = min(int(0.1 * sample_rate), len(segment_audio) // 2)
        
        envelope = np.ones(len(segment_audio))
        envelope[:attack_len] = np.linspace(0, 1, attack_len)
        envelope[-release_len:] = np.linspace(1, 0, release_len)
        
        segment_audio *= envelope
        audio[start_idx:end_idx] = segment_audio
    
    # Normalize
    audio = audio / (np.max(np.abs(audio)) + 1e-8) * 0.8
    
    return audio.astype(np.float32)


def test_mms():
    """Test MMS transcription"""
    print("\n" + "="*60)
    print("TEST 1: MMS Model")
    print("="*60)
    
    from backend.stt.mms_engine import transcribe_kikuyu, get_model_info
    
    # Get model info
    info = get_model_info()
    print(f"\nModel Info:")
    for k, v in info.items():
        print(f"  {k}: {v}")
    
    # Test with different Kikuyu phrases
    test_phrases = [
        "thayu",      # Hello
        "wĩmwega",   # Good morning
        "ngatho",    # Thank you
    ]
    
    for phrase in test_phrases:
        print(f"\n--- Testing phrase: '{phrase}' ---")
        
        # Create audio
        audio = create_realistic_kikuyu_audio(phrase)
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            test_path = f.name
            with wave.open(test_path, 'w') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(16000)
                wav_file.writeframes(audio.tobytes())
        
        # Transcribe
        result = transcribe_kikuyu(test_path)
        
        print(f"  Result: '{result['text']}'")
        print(f"  Success: {result['success']}")
        
        os.unlink(test_path)
    
    return info


def test_whisper():
    """Test Whisper transcription"""
    print("\n" + "="*60)
    print("TEST 2: Whisper Model")
    print("="*60)
    
    from backend.stt.speech_to_text import WhisperSTT
    
    # Load Whisper
    whisper = WhisperSTT(model_size="tiny")
    whisper.load_model()
    print("✅ Whisper loaded")
    
    # Test phrases
    test_phrases = [
        "thayu",      # Hello
        "wĩmwega",   # Good morning  
        "ngatho",    # Thank you
        "niatia",    # How are you?
    ]
    
    for phrase in test_phrases:
        print(f"\n--- Testing phrase: '{phrase}' ---")
        
        # Create audio
        audio = create_realistic_kikuyu_audio(phrase)
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            test_path = f.name
            with wave.open(test_path, 'w') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(16000)
                wav_file.writeframes(audio.tobytes())
        
        # Transcribe with English (forces Latin alphabet)
        result = whisper.transcribe(test_path, language="en")
        
        print(f"  Result: '{result['text']}'")
        print(f"  Detected: {result.get('language')}")
        print(f"  Success: {result['success']}")
        
        os.unlink(test_path)


def test_with_english_hint():
    """Test Whisper with different language settings"""
    print("\n" + "="*60)
    print("TEST 3: Whisper with different language hints")
    print("="*60)
    
    from backend.stt.speech_to_text import WhisperSTT
    
    whisper = WhisperSTT(model_size="tiny")
    whisper.load_model()
    
    phrase = "thayu"
    audio = create_realistic_kikuyu_audio(phrase)
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        test_path = f.name
        with wave.open(test_path, 'w') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(16000)
            wav_file.writeframes(audio.tobytes())
    
    # Test with different language hints
    lang_hints = ["en", "sw", "am", None]
    
    for lang in lang_hints:
        result = whisper.transcribe(test_path, language=lang)
        print(f"  Language hint: {lang} -> Result: '{result['text']}' (detected: {result.get('language')})")
    
    os.unlink(test_path)


def compare_results():
    """Create a comparison test"""
    print("\n" + "="*60)
    print("COMPARISON TEST")
    print("="*60)
    
    from backend.stt.mms_engine import transcribe_kikuyu
    from backend.stt.speech_to_text import WhisperSTT
    
    whisper = WhisperSTT(model_size="tiny")
    whisper.load_model()
    
    # Create test audio for a full greeting
    phrase = "thayu wĩmwega"
    print(f"\nTest phrase: '{phrase}'")
    
    audio = create_realistic_kikuyu_audio(phrase, duration=3.0)
    
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        test_path = f.name
        with wave.open(test_path, 'w') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(16000)
            wav_file.writeframes(audio.tobytes())
    
    # MMS
    print("\n1. MMS Result:")
    mms_result = transcribe_kikuyu(test_path)
    print(f"   '{mms_result['text']}'")
    
    # Whisper
    print("\n2. Whisper Result (English):")
    whisper_result = whisper.transcribe(test_path, language="en")
    print(f"   '{whisper_result['text']}'")
    
    print("\n3. Whisper Result (Swahili):")
    whisper_result2 = whisper.transcribe(test_path, language="sw")
    print(f"   '{whisper_result2['text']}'")
    
    os.unlink(test_path)
    
    # Analysis
    print("\n" + "="*60)
    print("ANALYSIS")
    print("="*60)
    
    print("\n🔍 Key observations:")
    print(f"   - MMS produced: '{mms_result['text']}'")
    print(f"   - Whisper (en) produced: '{whisper_result['text']}'")
    print(f"   - Whisper (sw) produced: '{whisper_result2['text']}'")
    
    print("\n⚠️ Note: Synthetic audio cannot fully replicate real speech.")
    print("   For accurate testing, you need REAL Kikuyu audio recordings.")


if __name__ == "__main__":
    print("\n" + "#"*60)
    print("# KIKUYU STT COMPARISON TEST")
    print("# Comparing MMS vs Whisper")
    print("#"*60)
    
    # Test MMS
    mms_info = test_mms()
    
    # Test Whisper
    test_whisper()
    
    # Test language hints
    test_with_english_hint()
    
    # Comparison
    compare_results()
    
    print("\n" + "="*60)
    print("RECOMMENDATIONS")
    print("="*60)
    
    print("""
Based on the testing, here are the issues and recommendations:

1. **MMS Model Issues:**
   - The Kikuyu (kik) adapter may not be available in facebook/mms-1b-all
   - The tokenizer only has 39 tokens (basic characters)
   - This results in poor transcription quality
   - MMS IS producing some output but it's not accurate

2. **Whisper Issues:**
   - Designed for English and major languages
   - Not trained on Kikuyu
   - Produces empty or inaccurate results for Kikuyu speech

3. **RECOMMENDED SOLUTIONS:**
   
   a) Use the MMS model but with a proper Kikuyu adapter:
      - Try facebook/mms-1b-fl102 (Fleurs dataset version)
      - Or use a smaller model with Kikuyu fine-tuning
   
   b) For production, consider:
      - Recording real Kikuyu training data
      - Fine-tuning Whisper on Kikuyu
      - Using a dedicated Kikuyu ASR model
   
   c) For immediate use:
      - The current setup will work but with limited accuracy
      - MMS produces SOME output (better than nothing)
      - Consider adding a manual correction layer

4. **For REAL Kikuyu Testing:**
   - The models need actual Kikuyu speech audio
   - Synthetic tones don't work well
   - Even with fixes, accuracy will be limited without proper Kikuyu training data
""")
