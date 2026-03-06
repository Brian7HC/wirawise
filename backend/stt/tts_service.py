"""
Text-to-Speech service using OpenAI API
Converts text to speech using OpenAI's TTS models
"""

import logging
import os
from typing import Optional
from openai import OpenAI
from backend.config import settings

logger = logging.getLogger(__name__)


def get_openai_client() -> OpenAI:
    """Get OpenAI client with API key from settings"""
    api_key = settings.OPENAI_API_KEY
    if not api_key:
        raise ValueError("OPENAI_API_KEY not configured in environment")
    return OpenAI(api_key=api_key)


def text_to_speech(
    text: str,
    output_path: str = "response.mp3",
    voice: Optional[str] = None,
    model: str = "gpt-4o-mini-tts"
) -> dict:
    """
    Convert text to speech using OpenAI TTS API
    
    Args:
        text: Text to convert to speech
        output_path: Path to save the audio file
        voice: Voice to use (default: from settings or 'alloy')
        model: TTS model to use (default: gpt-4o-mini-tts)
        
    Returns:
        Dict with keys:
            - success: bool
            - audio_path: path to saved audio file
            - error: error message if failed
    """
    try:
        client = get_openai_client()
        
        # Use voice from settings if not specified
        if voice is None:
            voice = getattr(settings, 'OPENAI_TTS_VOICE', 'alloy')
        
        logger.info(f"Converting text to speech: '{text[:50]}...' -> {output_path}")
        
        # Generate speech
        response = client.audio.speech.create(
            model=model,
            voice=voice,
            input=text
        )
        
        # Save to file
        response.stream_to_file(output_path)
        
        logger.info(f"Speech saved to: {output_path}")
        
        return {
            "success": True,
            "audio_path": output_path
        }
        
    except ValueError as e:
        logger.error(f"OpenAI API key not configured: {e}")
        return {
            "success": False,
            "audio_path": "",
            "error": str(e)
        }
    except Exception as e:
        logger.error(f"TTS error: {e}")
        return {
            "success": False,
            "audio_path": "",
            "error": f"TTS failed: {str(e)}"
        }


def generate_speech_bytes(
    text: str,
    voice: Optional[str] = None,
    model: str = "gpt-4o-mini-tts"
) -> tuple:
    """
    Generate speech and return as bytes
    
    Args:
        text: Text to convert to speech
        voice: Voice to use
        model: TTS model to use
        
    Returns:
        Tuple of (success: bool, audio_bytes: bytes or None, error: str or None)
    """
    try:
        client = get_openai_client()
        
        if voice is None:
            voice = getattr(settings, 'OPENAI_TTS_VOICE', 'alloy')
        
        response = client.audio.speech.create(
            model=model,
            voice=voice,
            input=text
        )
        
        # Read the response content as bytes
        audio_bytes = response.content
        
        return True, audio_bytes, None
        
    except Exception as e:
        logger.error(f"TTS error: {e}")
        return False, None, str(e)
