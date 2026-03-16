"""Voice service for recording and playback."""

import logging
import os
import uuid
from typing import Optional, Dict
import sounddevice as sd
import soundfile as sf
import groq
from backend.config import settings

logger = logging.getLogger(__name__)

# Default audio settings
DEFAULT_SAMPLE_RATE = 16000
DEFAULT_CHANNELS = 1
DEFAULT_DURATION = 5  # seconds


def get_groq_client() -> groq.Groq:
    """Get Groq client with API key from settings"""
    api_key = settings.GROQ_API_KEY
    if not api_key:
        raise ValueError("GROQ_API_KEY not configured in environment")
    return groq.Groq(api_key=api_key)


def record_audio(
    duration: int = DEFAULT_DURATION,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    channels: int = DEFAULT_CHANNELS,
    output_path: Optional[str] = None
) -> Dict:
    """
    Record audio from the microphone
    
    Args:
        duration: Recording duration in seconds
        sample_rate: Audio sample rate (default: 16000)
        channels: Number of audio channels (default: 1 for mono)
        output_path: Path to save the recording
        
    Returns:
        Dict with keys:
            - success: bool
            - audio_path: path to saved audio file
            - error: error message if failed
    """
    try:
        if output_path is None:
            output_path = f"recording_{uuid.uuid4().hex[:8]}.wav"
        
        logger.info(f"Recording audio for {duration} seconds...")
        print(f"🎤 Speak now... ({duration}s)")
        
        # Record audio
        audio = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=channels,
            dtype='float32'
        )
        
        # Wait for recording to complete
        sd.wait()
        
        # Save as WAV file
        sf.write(output_path, audio, sample_rate)
        
        logger.info(f"Audio saved to: {output_path}")
        
        return {
            "success": True,
            "audio_path": output_path
        }
        
    except Exception as e:
        logger.error(f"Recording error: {e}")
        return {
            "success": False,
            "audio_path": "",
            "error": str(e)
        }


def transcribe_audio(audio_path: str) -> Dict:
    """
    Transcribe audio using Groq Whisper API
    
    Args:
        audio_path: Path to audio file
        
    Returns:
        Dict with transcription results
    """
    try:
        client = get_groq_client()
        
        with open(audio_path, "rb") as audio_file:
            # Groq uses the same Whisper API format
            transcription = client.audio.transcriptions.create(
                model="whisper-large-v3",
                file=audio_file,
                response_format="verbose_json"
            )
            
            text = transcription.text.strip()
            
            logger.info(f"Transcribed: '{text}'")
            
            return {
                "success": True,
                "text": text
            }
            
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        return {
            "success": False,
            "text": "",
            "error": str(e)
        }


def chat_with_text(text: str) -> Dict:
    """
    Process text through the Groq chatbot and get response
    
    Args:
        text: User input text
        
    Returns:
        Dict with chatbot response
    """
    try:
        client = get_groq_client()
        
        response = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that responds in Kikuyu language. Respond naturally in Kikuyu."},
                {"role": "user", "content": text}
            ]
        )
        
        reply = response.choices[0].message.content
        
        logger.info(f"Chat response: '{reply}'")
        
        return {
            "success": True,
            "response_text": reply
        }
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return {
            "success": False,
            "response_text": "",
            "error": str(e)
        }


def speak_text(text: str, output_path: Optional[str] = None) -> Dict:
    """
    Convert text to speech using OpenAI TTS (Groq doesn't have TTS, so we use OpenAI)
    
    Args:
        text: Text to speak
        output_path: Path to save audio
        
    Returns:
        Dict with TTS results
    """
    # Note: Groq doesn't have TTS, so we use OpenAI if available
    # For now, we'll just return success without generating audio
    # You can implement TTS using another provider or local TTS
    logger.warning("TTS not available with Groq - returning text only")
    
    return {
        "success": True,
        "audio_path": "",
        "text": text  # Return the text to be used by a TTS service
    }


def play_audio(audio_path: str) -> Dict:
    """
    Play audio file through speakers
    
    Args:
        audio_path: Path to audio file
        
    Returns:
        Dict with result
    """
    try:
        data, fs = sf.read(audio_path)
        sd.play(data, fs)
        sd.wait()
        
        return {
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Playback error: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def full_voice_pipeline(
    duration: int = DEFAULT_DURATION,
    sample_rate: int = DEFAULT_SAMPLE_RATE
) -> Dict:
    """
    Run the complete voice pipeline using Groq:
    1. Record audio from microphone
    2. Transcribe audio to text (Groq Whisper)
    3. Process through chatbot (Groq Llama)
    4. Return response (TTS to be added later)
    
    Args:
        duration: Recording duration in seconds
        sample_rate: Audio sample rate
        
    Returns:
        Dict with pipeline results
    """
    results = {
        "success": False,
        "transcribed_text": "",
        "response_text": "",
        "audio_path": "",
        "error": ""
    }
    
    audio_path = ""
    
    try:
        # Step 1: Record audio
        recording = record_audio(duration=duration, sample_rate=sample_rate)
        if not recording["success"]:
            results["error"] = f"Recording failed: {recording['error']}"
            return results
        
        audio_path = recording["audio_path"]
        
        # Step 2: Transcribe using Groq Whisper
        transcription = transcribe_audio(audio_path)
        if not transcription["success"]:
            results["error"] = f"Transcription failed: {transcription['error']}"
            return results
        
        transcribed_text = transcription["text"]
        results["transcribed_text"] = transcribed_text
        print(f"📝 You said: {transcribed_text}")
        
        # Step 3: Chat using Groq Llama
        chat = chat_with_text(transcribed_text)
        if not chat["success"]:
            results["error"] = f"Chat failed: {chat['error']}"
            return results
        
        response_text = chat["response_text"]
        results["response_text"] = response_text
        print(f"🤖 Bot: {response_text}")
        
        # Note: TTS not available in Groq - response is returned as text
        results["success"] = True
        print("✅ Voice pipeline complete!")
        
        return results
        
    except Exception as e:
        logger.error(f"Voice pipeline error: {e}")
        results["error"] = str(e)
        return results
    finally:
        # Cleanup: remove temporary audio file
        if audio_path and os.path.exists(audio_path):
            try:
                os.remove(audio_path)
            except:
                pass
