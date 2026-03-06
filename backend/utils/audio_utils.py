"""
Audio processing utilities for Kikuyu Chatbot
Handles audio file conversion, validation, and processing
"""

import os
import tempfile
import logging
import subprocess
import numpy as np
from pathlib import Path
from typing import Optional, Tuple
import soundfile as sf
import librosa

logger = logging.getLogger(__name__)

# Audio configuration for Wav2Vec2-BERT (badrex/w2v-bert-2.0-kikuyu-asr)
SAMPLE_RATE = 16000  # Model requires 16kHz
MAX_AUDIO_LENGTH_SEC = 10  # Max 10 seconds for the model
MAX_AUDIO_SIZE_MB = 10
SUPPORTED_FORMATS = ['.wav', '.mp3', '.m4a', '.ogg', '.webm']

# Normalization settings - use -16dB which is more typical for speech
NORMALIZE_TARGET_DB = -16.0  # Target loudness in dB
SILENCE_THRESHOLD_DB = -40.0  # Silence threshold in dB
SILENCE_MIN_DURATION = 0.1  # Minimum silence duration to trim (seconds)


class AudioProcessor:
    """Handle audio file processing and validation"""
    
    @staticmethod
    def validate_audio_file(file_path: str) -> Tuple[bool, str]:
        """
        Validate audio file
        
        Returns:
            (is_valid, error_message)
        """
        if not os.path.exists(file_path):
            return False, "File does not exist"
        
        # Check file size
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if file_size_mb > MAX_AUDIO_SIZE_MB:
            return False, f"File too large: {file_size_mb:.2f}MB (max: {MAX_AUDIO_SIZE_MB}MB)"
        
        # Check file extension
        ext = Path(file_path).suffix.lower()
        if ext not in SUPPORTED_FORMATS:
            return False, f"Unsupported format: {ext} (supported: {SUPPORTED_FORMATS})"
        
        return True, ""
    
    @staticmethod
    def convert_to_wav(input_path: str, output_path: Optional[str] = None) -> str:
        """
        Convert audio file to WAV format at 16kHz mono with normalization and silence trimming.
        
        Uses FFmpeg for reliable WebM/Opus decoding, then librosa for processing.
        
        Args:
            input_path: Path to input audio file
            output_path: Path for output file (optional)
            
        Returns:
            Path to converted WAV file
        """
        try:
            # Create output path if not provided
            if output_path is None:
                output_path = tempfile.NamedTemporaryFile(
                    suffix='.wav',
                    delete=False
                ).name
            
            # First convert to intermediate WAV using FFmpeg (handles WebM/Opus properly)
            temp_wav = tempfile.NamedTemporaryFile(suffix='.wav', delete=False).name
            
            # Use FFmpeg to convert - it properly handles WebM/Opus
            cmd = [
                'ffmpeg', '-y',
                '-i', input_path,
                '-ar', '16000',  # 16kHz
                '-ac', '1',       # Mono
                '-acodec', 'pcm_s16le',  # 16-bit PCM
                temp_wav
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.warning(f"FFmpeg conversion failed, falling back to librosa: {result.stderr}")
                # Fallback to librosa
                audio, sr = librosa.load(input_path, sr=SAMPLE_RATE, mono=True)
            else:
                # Load the FFmpeg-converted audio
                audio, sr = librosa.load(temp_wav, sr=SAMPLE_RATE, mono=True)
                os.unlink(temp_wav)  # Clean up temp file
            
            logger.info(f"DEBUG: Loaded audio - sample rate: {sr}, length: {len(audio)}, duration: {len(audio)/sr:.2f}s")
            logger.info(f"DEBUG: Audio min: {audio.min():.4f}, max: {audio.max():.4f}, RMS: {np.sqrt(np.mean(audio**2)):.4f}")
            
            # Apply audio normalization (MANDATORY for Wav2Vec2-BERT)
            audio = AudioProcessor.normalize_audio(audio)
            
            # Trim silence from beginning and end (REQUIRED)
            audio = AudioProcessor.trim_silence(audio)
            
            logger.info(f"DEBUG: After normalization - min: {audio.min():.4f}, max: {audio.max():.4f}, RMS: {np.sqrt(np.mean(audio**2)):.4f}")
            logger.info(f"DEBUG: After trimming - length: {len(audio)}, duration: {len(audio)/sr:.2f}s")
            
            # Check audio length - must be < 10 seconds
            if len(audio) / SAMPLE_RATE > MAX_AUDIO_LENGTH_SEC:
                # Truncate to max length
                max_samples = int(MAX_AUDIO_LENGTH_SEC * SAMPLE_RATE)
                audio = audio[:max_samples]
                logger.warning(f"Audio truncated to {MAX_AUDIO_LENGTH_SEC} seconds")
            
            # Save as 16-bit PCM WAV
            audio_int16 = (audio * 32767).astype(np.int16)
            sf.write(output_path, audio_int16, SAMPLE_RATE)
            
            logger.info(f"Converted audio: {input_path} -> {output_path} (normalized, trimmed)")
            return output_path
            
        except Exception as e:
            logger.error(f"Error converting audio: {e}")
            raise
    
    @staticmethod
    def normalize_audio(audio: np.ndarray) -> np.ndarray:
        """
        Normalize audio to target loudness (MANDATORY for Wav2Vec2-BERT).
        
        Without normalization, the model produces [UNK] tokens because
        the audio features are outside the expected range.
        
        Args:
            audio: Audio waveform as numpy array
            
        Returns:
            Normalized audio waveform
        """
        try:
            # Calculate current RMS
            rms = np.sqrt(np.mean(audio ** 2))
            
            if rms < 1e-8:  # Handle silent audio
                return audio
            
            # Calculate target RMS for desired dB level
            target_rms = 10 ** (NORMALIZE_TARGET_DB / 20)
            
            # Scale audio to match target
            scale = target_rms / rms
            normalized = audio * scale
            
            # Clip to prevent clipping distortion
            normalized = np.clip(normalized, -1.0, 1.0)
            
            return normalized
            
        except Exception as e:
            logger.warning(f"Normalization failed: {e}, returning original")
            return audio
    
    @staticmethod
    def trim_silence(audio: np.ndarray) -> np.ndarray:
        """
        Trim leading and trailing silence from audio.
        
        Silence at the beginning/end causes transcription issues
        and leads to [UNK] output from the model.
        
        Args:
            audio: Audio waveform as numpy array
            
        Returns:
            Trimmed audio waveform
        """
        try:
            # Calculate frame-wise energy in dB
            frame_length = int(SAMPLE_RATE * 0.025)  # 25ms frames
            hop_length = int(SAMPLE_RATE * 0.010)    # 10ms hop
            
            # Use librosa's trim function
            trimmed, _ = librosa.effects.trim(
                audio,
                top_db=-SILENCE_THRESHOLD_DB,
                frame_length=frame_length,
                hop_length=hop_length
            )
            
            return trimmed
            
        except Exception as e:
            logger.warning(f"Silence trimming failed: {e}, returning original")
            return audio
    
    @staticmethod
    def get_audio_duration(file_path: str) -> float:
        """Get duration of audio file in seconds"""
        try:
            audio, sr = librosa.load(file_path, sr=None)
            duration = len(audio) / sr
            return duration
        except Exception as e:
            logger.error(f"Error getting audio duration: {e}")
            return 0.0
    
    @staticmethod
    def save_uploaded_file(file_data: bytes, filename: str) -> str:
        """
        Save uploaded audio file to temporary location
        
        Returns:
            Path to saved file
        """
        # Create temp directory for uploads
        upload_dir = Path("temp/uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        import uuid
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        file_path = upload_dir / unique_filename
        
        # Save file
        with open(file_path, 'wb') as f:
            f.write(file_data)
        
        logger.info(f"Saved uploaded file: {file_path}")
        return str(file_path)
    
    @staticmethod
    def cleanup_temp_file(file_path: str):
        """Remove temporary audio file"""
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
                logger.info(f"Cleaned up temp file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup temp file {file_path}: {e}")
