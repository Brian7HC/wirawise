"""Speech-to-Text using Groq Whisper API."""

import logging
import os
from typing import Dict, Optional
import groq
from backend.config import settings
from backend.utils.text_normalizer import normalize_text, clean_transcription

logger = logging.getLogger(__name__)

# Kikuyu text normalization mappings
KIKUYU_NORMALIZATIONS = {
    "ohoro": "uhoro",
    "ohara": "uhoro",
    "horo": "uhoro",
    "uhoru": "uhoro",
    "owimwega": "wimwega",
    "wimuga": "wimwega",
    "niatia": "niatia",
    "niatia": "niatia",
    "ngai": "ngai",
    "murathani": "murathani",
    "mwarimuki": "mwarimuki",
}

# Kikuyu vocabulary for Whisper prompt bias - improves recognition accuracy
KIKUYU_VOCABULARY = """Kikuyu greeting words: uhoro, uhoro mwega, wimwega, wimwega nawe, niatia, niatia mwega, ngai, ngai nawe, murathani, murathani mwega, mwarimuki, mwarimuki mwega, thayu, tho, rora, rora mwega. Common Kikuyu words: ndí mwega (I am good), murĩ (hello), nĩ (yes), ai (no), ũguo (this), ucio (that), ndĩ (I), we (you), athu (they), tũ (we), mũno (very), na (and), nao (with), ta (like), ekĩ (this one), icio (that one)."""

# Common Kikuyu greeting patterns for fuzzy matching
KIKUYU_GREETINGS = [
    "uhoro", "uhoro mwega", "uhoro mwega nawe",
    "wimwega", "wimwega nawe",
    "niatia", "niatia mwega",
    "ngai", "ngai nawe",
    "murathani", "murathani mwega",
    "mwarimuki", "mwarimuki mwega",
    "thayu", "tho",
    "rora", "rora mwega"
]


def load_mms_model():
    """
    Stub function for MMS warmup.
    
    Note: This module uses Groq Whisper API instead of Meta MMS.
    The API client is initialized lazily on first use.
    This function exists for backward compatibility with main.py.
    """
    logger.info("MMS warmup: Using Groq Whisper API (no local model needed)")
    return True


def normalize_kikuyu_text(text: str) -> str:
    """
    Normalize Kikuyu text to handle common transcription errors.
    
    Handles variations like:
    - ohoro → uhoro
    - ohara → uhoro
    - horo → uhoro
    
    Args:
        text: Raw transcribed text
        
    Returns:
        Normalized text
    """
    if not text:
        return text
    
    text = text.lower().strip()
    
    # Apply normalization mappings
    for wrong, correct in KIKUYU_NORMALIZATIONS.items():
        text = text.replace(wrong, correct)
    
    return text


def get_groq_client() -> groq.Groq:
    """Get Groq client with API key from settings"""
    api_key = settings.GROQ_API_KEY
    if not api_key:
        raise ValueError("GROQ_API_KEY not configured in environment")
    return groq.Groq(api_key=api_key)


def transcribe_kikuyu(audio_path: str) -> Dict:
    """
    Transcribe audio using Groq Whisper API
    
    Args:
        audio_path: Path to the audio file (wav, mp3, m4a, etc.)
        
    Returns:
        Dict with keys:
            - success: bool
            - text: transcribed text
            - language: detected language code
            - duration: audio duration (if available)
            - error: error message if failed
    """
    try:
        client = get_groq_client()
        
        # Check if file exists
        if not os.path.exists(audio_path):
            return {
                "success": False,
                "text": "",
                "error": f"Audio file not found: {audio_path}"
            }
        
        # Open and transcribe the audio file
        with open(audio_path, "rb") as audio_file:
            logger.info(f"Transcribing audio file: {audio_path}")
            
            # Use Groq Whisper API for transcription
            # Add prompt with Kikuyu vocabulary to improve recognition
            transcript = client.audio.transcriptions.create(
                model="whisper-large-v3",
                file=audio_file,
                response_format="verbose_json",
                language="sw",  # Force Swahili for better Kikuyu recognition
                prompt=KIKUYU_VOCABULARY  # Bias toward Kikuyu vocabulary
            )
            
            text = transcript.text.strip()
            
            # Apply the new text normalizer for better Kikuyu recognition
            text = clean_transcription(text)
            
            logger.info(f"Transcription successful: '{text}'")
            
            return {
                "success": True,
                "text": text,
                "language": getattr(transcript, 'language', 'auto'),
                "duration": getattr(transcript, 'duration', None)
            }
            
    except ValueError as e:
        logger.error(f"Groq API key not configured: {e}")
        return {
            "success": False,
            "text": "",
            "error": str(e)
        }
    except Exception as e:
        logger.error(f"Whisper transcription error: {e}")
        return {
            "success": False,
            "text": "",
            "error": f"Transcription failed: {str(e)}"
        }


def transcribe_with_language(audio_path: str, language: Optional[str] = None) -> Dict:
    """
    Transcribe audio with optional language specification
    
    Args:
        audio_path: Path to the audio file
        language: Language code (e.g., 'en', 'sw', 'kik'). If None, auto-detected.
        
    Returns:
        Dict with transcription results
    """
    try:
        client = get_groq_client()
        
        with open(audio_path, "rb") as audio_file:
            # Prepare transcription arguments
            kwargs = {
                "model": "whisper-large-v3",
                "file": audio_file,
                "response_format": "verbose_json"
            }
            
            # Note: Groq Whisper may not support language parameter
            # It's designed for automatic language detection
            
            transcript = client.audio.transcriptions.create(**kwargs)
            
            return {
                "success": True,
                "text": transcript.text.strip(),
                "language": getattr(transcript, 'language', language or 'auto'),
                "duration": getattr(transcript, 'duration', None)
            }
            
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        return {
            "success": False,
            "text": "",
            "error": str(e)
        }
