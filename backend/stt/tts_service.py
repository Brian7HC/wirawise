"""Text-to-Speech service."""

import logging
import os
import uuid
import requests
from typing import Optional
from backend.config import settings

logger = logging.getLogger(__name__)

# Default output directory for TTS audio
TTS_OUTPUT_DIR = "data/audio/responses"
os.makedirs(TTS_OUTPUT_DIR, exist_ok=True)


def get_openai_client():
    """Get OpenAI client with API key from settings"""
    from openai import OpenAI
    api_key = settings.OPENAI_API_KEY
    if not api_key:
        raise ValueError("OPENAI_API_KEY not configured in environment")
    return OpenAI(api_key=api_key)


def text_to_speech_openai(
    text: str,
    output_path: str = None,
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
        
        if output_path is None:
            output_path = os.path.join(TTS_OUTPUT_DIR, f"response_{uuid.uuid4().hex[:8]}.mp3")
        
        logger.info(f"OpenAI TTS: Converting text to speech: '{text[:50]}...' -> {output_path}")
        
        # Generate speech
        response = client.audio.speech.create(
            model=model,
            voice=voice,
            input=text
        )
        
        # Save to file
        response.stream_to_file(output_path)
        
        logger.info(f"OpenAI TTS: Speech saved to: {output_path}")
        
        return {
            "success": True,
            "audio_path": output_path,
            "engine": "openai"
        }
        
    except ValueError as e:
        logger.error(f"OpenAI API key not configured: {e}")
        return {
            "success": False,
            "audio_path": "",
            "error": str(e),
            "engine": "openai"
        }
    except Exception as e:
        logger.error(f"OpenAI TTS error: {e}")
        return {
            "success": False,
            "audio_path": "",
            "error": f"TTS failed: {str(e)}",
            "engine": "openai"
        }


def text_to_speech_coqui(
    text: str,
    output_path: str = None,
    voice_id: str = None
) -> dict:
    """
    Convert text to speech using Coqui TTS
    Coqui TTS is particularly good for low-resource languages like Kikuyu
    
    Args:
        text: Text to convert to speech
        output_path: Path to save the audio file
        voice_id: Coqui voice ID to use
        
    Returns:
        Dict with keys:
            - success: bool
            - audio_path: path to saved audio file
            - error: error message if failed
    """
    try:
        # Try to import TTS from Coqui
        from TTS.api import TTS
        
        if output_path is None:
            output_path = os.path.join(TTS_OUTPUT_DIR, f"response_{uuid.uuid4().hex[:8]}.wav")
        
        logger.info(f"Coqui TTS: Converting text to speech: '{text[:50]}...' -> {output_path}")
        
        # Get device (cuda or cpu)
        device = "cuda" if os.environ.get("CUDA_VISIBLE_DEVICES") else "cpu"
        
        # Initialize TTS - use a multi-language model for Kikuyu
        # You can fine-tune with Kikuyu data for better results
        if voice_id:
            tts = TTS(model_path=voice_id, gpu=(device == "cuda"))
        else:
            # Use XTTS v2 which supports multiple languages
            tts = TTS(model_name="xtts_v2", gpu=(device == "cuda"))
        
        # Generate speech
        tts.tts_to_file(
            text=text,
            file_path=output_path,
            language="sw"  # Swahili is closest available; for Kikuyu use custom model
        )
        
        logger.info(f"Coqui TTS: Speech saved to: {output_path}")
        
        return {
            "success": True,
            "audio_path": output_path,
            "engine": "coqui"
        }
        
    except ImportError:
        logger.warning("Coqui TTS not installed. Install with: pip install TTS")
        return {
            "success": False,
            "audio_path": "",
            "error": "Coqui TTS not installed",
            "engine": "coqui"
        }
    except Exception as e:
        logger.error(f"Coqui TTS error: {e}")
        return {
            "success": False,
            "audio_path": "",
            "error": f"Coqui TTS failed: {str(e)}",
            "engine": "coqui"
        }


def text_to_speech_khaya(
    text: str,
    output_path: str = None,
    voice: str = "kikuyu_male"
) -> dict:
    """
    Convert text to speech using Khaya API
    Khaya API is designed for African languages including Kikuyu
    
    Args:
        text: Text to convert to speech
        output_path: Path to save the audio file
        voice: Voice to use (default: kikuyu_male)
        
    Returns:
        Dict with keys:
            - success: bool
            - audio_path: path to saved audio file
            - error: error message if failed
    """
    try:
        api_key = settings.KHAYA_API_KEY
        api_url = settings.KHAYA_API_URL
        
        if not api_key:
            logger.warning("Khaya API key not configured")
            return {
                "success": False,
                "audio_path": "",
                "error": "KHAYA_API_KEY not configured",
                "engine": "khaya"
            }
        
        if output_path is None:
            output_path = os.path.join(TTS_OUTPUT_DIR, f"response_{uuid.uuid4().hex[:8]}.wav")
        
        logger.info(f"Khaya TTS: Converting text to speech: '{text[:50]}...' -> {output_path}")
        
        # Send request to Khaya API
        response = requests.post(
            api_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "text": text,
                "voice": voice,
                "language": "kikuyu"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            # Save audio content
            with open(output_path, "wb") as f:
                f.write(response.content)
            
            logger.info(f"Khaya TTS: Speech saved to: {output_path}")
            
            return {
                "success": True,
                "audio_path": output_path,
                "engine": "khaya"
            }
        else:
            error_msg = f"Khaya API error: {response.status_code} - {response.text}"
            logger.error(error_msg)
            return {
                "success": False,
                "audio_path": "",
                "error": error_msg,
                "engine": "khaya"
            }
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Khaya API request error: {e}")
        return {
            "success": False,
            "audio_path": "",
            "error": f"Khaya API request failed: {str(e)}",
            "engine": "khaya"
        }
    except Exception as e:
        logger.error(f"Khaya TTS error: {e}")
        return {
            "success": False,
            "audio_path": "",
            "error": f"Khaya TTS failed: {str(e)}",
            "engine": "khaya"
        }


def text_to_speech(
    text: str,
    output_path: str = None,
    voice: Optional[str] = None,
    engine: Optional[str] = None
) -> dict:
    """
    Convert text to speech using the configured TTS engine
    
    Args:
        text: Text to convert to speech
        output_path: Path to save the audio file
        voice: Voice to use
        engine: TTS engine to use (default: from settings)
        
    Returns:
        Dict with keys:
            - success: bool
            - audio_path: path to saved audio file
            - error: error message if failed
            - engine: TTS engine used
    """
    # Determine which engine to use
    if engine is None:
        engine = getattr(settings, 'TTS_ENGINE', 'openai').lower()
    
    logger.info(f"TTS request: engine={engine}, text='{text[:50]}...'")
    
    # Route to appropriate TTS engine
    if engine == "coqui":
        result = text_to_speech_coqui(text, output_path, voice)
    elif engine == "khaya":
        result = text_to_speech_khaya(text, output_path, voice)
    elif engine == "openai":
        result = text_to_speech_openai(text, output_path, voice)
    else:
        # Default to OpenAI
        logger.warning(f"Unknown TTS engine '{engine}', defaulting to OpenAI")
        result = text_to_speech_openai(text, output_path, voice)
    
    return result


def generate_speech_bytes(
    text: str,
    voice: Optional[str] = None,
    engine: Optional[str] = None
) -> tuple:
    """
    Generate speech and return as bytes (for streaming/audio playback)
    
    Args:
        text: Text to convert to speech
        voice: Voice to use
        engine: TTS engine to use
        
    Returns:
        Tuple of (success: bool, audio_bytes: bytes or None, error: str or None, engine: str)
    """
    try:
        # For OpenAI, we can get bytes directly
        if engine is None:
            engine = getattr(settings, 'TTS_ENGINE', 'openai').lower()
        
        if engine == "openai" or engine is None:
            client = get_openai_client()
            
            if voice is None:
                voice = getattr(settings, 'OPENAI_TTS_VOICE', 'alloy')
            
            response = client.audio.speech.create(
                model="gpt-4o-mini-tts",
                voice=voice,
                input=text
            )
            
            audio_bytes = response.content
            
            return True, audio_bytes, None, "openai"
        else:
            # For Coqui/Khaya, generate file then read bytes
            result = text_to_speech(text, voice=voice, engine=engine)
            
            if result["success"] and result["audio_path"]:
                with open(result["audio_path"], "rb") as f:
                    audio_bytes = f.read()
                return True, audio_bytes, None, result["engine"]
            else:
                return False, None, result.get("error", "Unknown error"), engine
        
    except Exception as e:
        logger.error(f"TTS error: {e}")
        return False, None, str(e), engine or "unknown"


def get_available_engines() -> list:
    """
    Get list of available TTS engines based on configuration
    
    Returns:
        List of available engine names
    """
    engines = []
    
    # OpenAI
    if settings.OPENAI_API_KEY:
        engines.append("openai")
    
    # Coqui - check if installed
    try:
        from TTS.api import TTS
        engines.append("coqui")
    except ImportError:
        pass
    
    # Khaya - check if API key configured
    if settings.KHAYA_API_KEY:
        engines.append("khaya")
    
    return engines
