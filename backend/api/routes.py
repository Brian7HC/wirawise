"""
FastAPI route handlers for Kikuyu Chatbot API
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional
import time
import logging
from datetime import datetime

from backend.database.connection import get_db
from backend.database.crud import (
    GreetingCRUD, 
    ConversationCRUD, 
    VocabularyCRUD,
    AnalyticsCRUD
)
from backend.nlp.intent_classifier import IntentClassifier
from backend.api.schemas import (
    TextChatRequest,
    ChatResponse,
    SessionResponse,
    ConversationHistoryResponse,
    VocabularyResponse,
    HealthCheckResponse,
    AnalyticsResponse,
    ErrorResponse
)
from backend.config import settings
from backend.utils.audio_utils import AudioProcessor
from backend.stt.mms_engine import transcribe_kikuyu
from backend.stt.tts_service import text_to_speech, generate_speech_bytes
import uuid

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Intent classifier instance
classifier = IntentClassifier()


# ============================================
# CHAT ENDPOINTS
# ============================================

@router.post(
    "/chat/text",
    response_model=ChatResponse,
    summary="Text-based chat",
    description="Send text input and get Kikuyu chatbot response",
    tags=["Chat"]
)
async def chat_text(
    request: TextChatRequest,
    db: Session = Depends(get_db)
):
    """
    Process text input and return chatbot response
    
    - **text**: User's text input in Kikuyu or English
    - **session_id**: Optional session ID (will be created if not provided)
    - **context**: Optional context for response selection
    """
    start_time = time.time()
    
    try:
        # Get or create session
        session_id = request.session_id
        if not session_id:
            session_id = ConversationCRUD.create_session(db)
            logger.info(f"Created new session: {session_id}")
        else:
            # Verify session exists
            session = ConversationCRUD.get_session(db, session_id)
            if not session:
                session_id = ConversationCRUD.create_session(db)
                logger.warning(f"Session not found, created new: {session_id}")
        
        # Process input with intent classifier
        result = classifier.process_input(db, request.text, request.context)
        
        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Log conversation
        ConversationCRUD.log_conversation(
            db=db,
            session_id=session_id,
            user_input=request.text,
            bot_response=result["response_text"],
            intent_matched=result.get("intent"),
            confidence_score=result["confidence"],
            response_time_ms=response_time_ms,
            user_input_type="text"
        )
        
        # Build metadata
        metadata = {
            "response_time_ms": response_time_ms,
            "category": result.get("category"),
            "formality_level": result.get("formality_level"),
            "politeness_score": result.get("politeness_score")
        }
        
        # Build response
        return ChatResponse(
            success=result["success"],
            intent=result.get("intent"),
            intent_name=result.get("intent_name"),
            confidence=result["confidence"],
            matched_pattern=result.get("matched_pattern"),
            response_text=result["response_text"],
            response_translation=result.get("response_translation"),
            response_literal=result.get("response_literal"),
            audio_file=result.get("audio_file"),
            formality=result.get("formality"),
            session_id=session_id,
            metadata=metadata
        )
        
    except Exception as e:
        logger.error(f"Error in chat_text: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing request: {str(e)}"
        )


@router.post(
    "/chat/voice",
    response_model=ChatResponse,
    summary="Voice-based chat",
    description="Send voice input and get chatbot response",
    tags=["Chat"]
)
async def chat_voice(
    audio: UploadFile = File(...),
    session_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Process voice input and return chatbot response
    
    - **audio**: Audio file (WAV, MP3, M4A, OGG, WebM)
    - **session_id**: Optional session ID
    """
    start_time = time.time()
    
    try:
        # Get or create session
        if not session_id:
            session_id = ConversationCRUD.create_session(db, None)
            logger.info(f"Created new session for voice: {session_id}")
        
        # Read audio file
        audio_bytes = await audio.read()
        
        # Save uploaded file
        temp_path = AudioProcessor.save_uploaded_file(
            audio_bytes,
            audio.filename or "recording.wav"
        )
        
        logger.info(f"Received audio file: {audio.filename}, size: {len(audio_bytes)} bytes")
        
        # Validate audio
        is_valid, error_msg = AudioProcessor.validate_audio_file(temp_path)
        if not is_valid:
            AudioProcessor.cleanup_temp_file(temp_path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid audio file: {error_msg}"
            )
        
        # CRITICAL: Always convert audio to ensure proper format for Wav2Vec2-BERT
        # This applies normalization and silence trimming (MANDATORY)
        # Even if input is already WAV, we need to normalize it
        wav_path = AudioProcessor.convert_to_wav(temp_path)
        
        # Transcribe with OpenAI Whisper API
        transcription_result = transcribe_kikuyu(wav_path)
        
        if not transcription_result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Transcription failed: {transcription_result.get('error')}"
            )
        
        transcribed_text = transcription_result["text"]
        
        logger.info(f"Transcribed: '{transcribed_text}'")
        
        # Process transcribed text with intent classifier
        classifier = IntentClassifier()
        result = classifier.process_input(db, transcribed_text, None)
        
        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Log conversation
        ConversationCRUD.log_conversation(
            db=db,
            session_id=session_id,
            user_input=transcribed_text,
            bot_response=result["response_text"],
            intent_matched=result.get("intent"),
            confidence_score=result["confidence"],
            response_time_ms=response_time_ms,
            user_input_type="voice"
        )
        
        # Cleanup temp files
        AudioProcessor.cleanup_temp_file(temp_path)
        if wav_path != temp_path:
            AudioProcessor.cleanup_temp_file(wav_path)
        
        # Generate TTS audio for the response
        audio_file = result.get("audio_file")
        tts_audio_path = None
        
        # Try to generate TTS using OpenAI if API key is available
        if settings.OPENAI_API_KEY and result.get("response_text"):
            try:
                tts_result = text_to_speech(
                    result["response_text"],
                    output_path=f"data/audio/responses/response_{uuid.uuid4().hex[:8]}.mp3"
                )
                if tts_result.get("success"):
                    tts_audio_path = tts_result.get("audio_path")
                    audio_file = tts_audio_path
            except Exception as tts_err:
                logger.warning(f"TTS generation failed: {tts_err}")
        
        # Build metadata
        metadata = {
            "response_time_ms": response_time_ms,
            "transcribed_text": transcribed_text,
            "detected_language": transcription_result.get("language"),
            "transcription_duration": transcription_result.get("duration"),
            "category": result.get("category"),
            "formality_level": result.get("formality_level"),
            "politeness_score": result.get("politeness_score")
        }
        
        # Build response
        return ChatResponse(
            success=result["success"],
            intent=result.get("intent"),
            intent_name=result.get("intent_name"),
            confidence=result["confidence"],
            matched_pattern=result.get("matched_pattern"),
            response_text=result["response_text"],
            response_translation=result.get("response_translation"),
            response_literal=result.get("response_literal"),
            audio_file=audio_file,
            formality=result.get("formality"),
            session_id=session_id,
            metadata=metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat_voice: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing voice input: {str(e)}"
        )


# ============================================
# SESSION ENDPOINTS
# ============================================

@router.post(
    "/session/create",
    response_model=SessionResponse,
    summary="Create new session",
    tags=["Session"]
)
async def create_session(
    user_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Create a new conversation session"""
    try:
        session_id = ConversationCRUD.create_session(db, user_id)
        session = ConversationCRUD.get_session(db, session_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create session"
            )
        
        return SessionResponse(**session)
        
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/session/{session_id}",
    response_model=SessionResponse,
    summary="Get session info",
    tags=["Session"]
)
async def get_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Get information about a session"""
    session = ConversationCRUD.get_session(db, session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    
    return SessionResponse(**session)


@router.get(
    "/session/{session_id}/history",
    response_model=ConversationHistoryResponse,
    summary="Get conversation history",
    tags=["Session"]
)
async def get_conversation_history(
    session_id: str,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get conversation history for a session"""
    # Verify session exists
    session = ConversationCRUD.get_session(db, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    
    history = ConversationCRUD.get_conversation_history(db, session_id, limit)
    
    return ConversationHistoryResponse(
        session_id=session_id,
        history=history,
        total_count=len(history)
    )


# ============================================
# VOCABULARY ENDPOINTS
# ============================================

@router.get(
    "/vocabulary/{word}",
    response_model=VocabularyResponse,
    summary="Look up Kikuyu word",
    tags=["Vocabulary"]
)
async def lookup_word(
    word: str,
    db: Session = Depends(get_db)
):
    """
    Look up meaning and pronunciation of a Kikuyu word
    
    Example: /vocabulary/thayu
    """
    meaning = VocabularyCRUD.get_word_meaning(db, word)
    pronunciation = VocabularyCRUD.get_pronunciation(db, word)
    
    return VocabularyResponse(
        word=word,
        meaning=meaning,
        pronunciation=pronunciation,
        found=meaning is not None or pronunciation is not None
    )


# ============================================
# ANALYTICS ENDPOINTS
# ============================================

@router.get(
    "/analytics",
    response_model=AnalyticsResponse,
    summary="Get analytics",
    tags=["Analytics"]
)
async def get_analytics(
    days: int = 7,
    db: Session = Depends(get_db)
):
    """Get analytics for the last N days"""
    try:
        # Update today's analytics first
        AnalyticsCRUD.update_daily_analytics(db)
        
        # Get analytics
        data = AnalyticsCRUD.get_analytics(db, days)
        
        return AnalyticsResponse(
            period=f"Last {days} days",
            data=data
        )
    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ============================================
# HEALTH CHECK ENDPOINTS
# ============================================

@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Health check",
    tags=["System"]
)
async def health_check(db: Session = Depends(get_db)):
    """Check API and database health"""
    from backend.database.connection import get_db_info
    
    db_info = get_db_info()
    
    return HealthCheckResponse(
        status="healthy" if db_info.get("connected") else "unhealthy",
        version=settings.APP_VERSION,
        database=db_info,
        timestamp=datetime.now()
    )


@router.get(
    "/",
    summary="API Root",
    tags=["System"]
)
async def root():
    """API root endpoint with basic information"""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "chat_text": "/api/v1/chat/text",
            "health": "/api/v1/health",
            "vocabulary": "/api/v1/vocabulary/{word}"
        }
    }
