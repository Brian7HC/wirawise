"""
Speech-to-Text service using OpenAI Whisper API
This module provides the interface for the voice pipeline
"""

import logging
from typing import Optional, Dict
from backend.stt.mms_engine import transcribe_kikuyu

logger = logging.getLogger(__name__)


def get_whisper_stt(model_size: str = "tiny"):
    """
    Returns an OpenAI Whisper STT engine wrapper
    
    This function provides backward compatibility with the existing API.
    The actual transcription is done via OpenAI Whisper API.
    
    Usage:
        stt = get_whisper_stt()
        result = stt.transcribe("recording.wav")
        print(result["text"])
    """
    
    class WhisperSTT:
        """Wrapper for OpenAI Whisper STT"""
        
        def __init__(self):
            self.model = "gpt-4o-transcribe"
        
        def transcribe(self, audio_path: str, language: Optional[str] = None) -> Dict:
            """
            Transcribe audio using OpenAI Whisper API
            
            Args:
                audio_path: Path to audio file
                language: Optional language hint
                
            Returns:
                {"text": "...", "success": True/False, "duration": 1.23}
            """
            return transcribe_kikuyu(audio_path)
        
        def load_model(self):
            """No-op - API handles model loading"""
            pass
    
    return WhisperSTT()


def transcribe_audio(audio_path: str, language: Optional[str] = None) -> Dict:
    """
    Convenience function to transcribe audio using OpenAI Whisper API
    
    Usage:
        result = transcribe_audio("recording.wav")
        print(result["text"])
    """
    return transcribe_kikuyu(audio_path)
