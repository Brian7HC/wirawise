#!/usr/bin/env python3
"""
Test script for the voice pipeline
Run this to test the complete voice flow: record -> transcribe -> chat -> speak
"""

import os
import sys
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import settings
from backend.stt.voice_service import full_voice_pipeline, record_audio, transcribe_audio, chat_with_text, speak_text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_imports():
    """Test that all required modules can be imported"""
    print("Testing imports...")
    
    try:
        import sounddevice
        import soundfile
        from openai import OpenAI
        print("✅ All imports successful!")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False


def test_api_key():
    """Test that OpenAI API key is configured"""
    print("\nTesting API key configuration...")
    
    api_key = settings.OPENAI_API_KEY
    if not api_key:
        print("❌ OPENAI_API_KEY not set in .env file")
        print("   Please add: OPENAI_API_KEY=your_api_key_here")
        return False
    
    print(f"✅ API key configured (length: {len(api_key)})")
    return True


def test_microphone():
    """Test microphone recording"""
    print("\nTesting microphone recording...")
    print("🎤 Please speak for 3 seconds...")
    
    result = record_audio(duration=3)
    
    if result["success"]:
        print(f"✅ Recording successful: {result['audio_path']}")
        
        # Try to transcribe
        print("\nTranscribing...")
        transcription = transcribe_audio(result['audio_path'])
        
        if transcription["success"]:
            print(f"✅ Transcription: {transcription['text']}")
        else:
            print(f"❌ Transcription failed: {transcription.get('error')}")
        
        # Cleanup
        os.remove(result['audio_path'])
        return transcription["success"]
    else:
        print(f"❌ Recording failed: {result.get('error')}")
        return False


def test_full_pipeline():
    """Test the complete voice pipeline"""
    print("\n" + "="*50)
    print("TESTING FULL VOICE PIPELINE")
    print("="*5)
    print("🎤 Recording and processing voice input...")
    
    result = full_voice_pipeline(duration=5)
    
    print("\n" + "="*50)
    print("RESULTS:")
    print("="*50)
    print(f"Success: {result['success']}")
    print(f"Transcribed: {result.get('transcribed_text', 'N/A')}")
    print(f"Response: {result.get('response_text', 'N/A')}")
    print(f"Audio: {result.get('audio_path', 'N/A')}")
    if result.get('error'):
        print(f"Error: {result.get('error')}")
    
    return result["success"]


def main():
    """Run all tests"""
    print("="*50)
    print("KIKUYU VOICE CHATBOT - VOICE PIPELINE TEST")
    print("="*50)
    
    # Test imports
    if not test_imports():
        print("\n❌ Please install required packages:")
        print("   pip install sounddevice soundfile openai")
        return
    
    # Test API key
    if not test_api_key():
        return
    
    # Test microphone (optional - requires hardware)
    print("\n" + "-"*50)
    test_microphone()
    
    # Test full pipeline (optional - requires microphone)
    print("\n" + "-"*50)
    response = input("Run full voice pipeline test? (y/n): ")
    if response.lower() == 'y':
        test_full_pipeline()


if __name__ == "__main__":
    main()
