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
from backend.nlp.chatbot import chat_full_response, process_agriculture_question
from backend.api.schemas import (
    TextChatRequest,
    ChatResponse,
    SessionResponse,
    ConversationHistoryResponse,
    VocabularyResponse,
    HealthCheckResponse,
    AnalyticsResponse,
    ErrorResponse,
    TTSRequest,
    TTSResponse,
    AgricultureChatRequest,
    AgricultureChatResponse,
    TranslationRequest,
    TranslationResponse
)
from backend.config import settings
from backend.utils.audio_utils import AudioProcessor
from backend.stt.mms_engine import transcribe_kikuyu
from backend.stt.tts_service import text_to_speech, generate_speech_bytes
from backend.nlp.chatbot import chat_full_response, process_agriculture_question
from backend.nlp.translator import translate_text
import uuid
import os

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
        
        # If agriculture intent detected, use AI pipeline instead of database response
        if result.get("intent") == "agriculture_question":
            logger.info(f"Routing agriculture question to AI pipeline: {request.text[:50]}...")
            try:
                # Use AI pipeline for agriculture questions
                ai_result = process_agriculture_question(
                    request.text,
                    include_context=True,
                    use_llm=True
                )
                
                # Calculate response time
                response_time_ms = int((time.time() - start_time) * 1000)
                
                # Build metadata
                metadata = {
                    "response_time_ms": response_time_ms,
                    "route": "ai_pipeline",
                    "processing_time": ai_result.get("processing_time"),
                    "sources": ai_result.get("sources")
                }
                
                # Build response from AI result (Kikuyu only, no translation)
                return ChatResponse(
                    success=True,
                    intent="agriculture_question",
                    intent_name="Agriculture Question",
                    confidence=result.get("confidence", 0.7),
                    matched_pattern=result.get("matched_pattern"),
                    response_text=ai_result.get("response", "Ndingĩrima ũrĩa."),
                    response_translation=None,
                    response_literal=None,
                    audio_file=None,
                    formality="neutral",
                    session_id=session_id,
                    metadata=metadata
                )
            except Exception as ai_err:
                logger.error(f"AI pipeline error: {ai_err}")
                # Fall through to classifier response
        
        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)
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
        
        # Generate TTS audio for the response
        audio_file = result.get("audio_file")
        tts_audio_path = None
        generate_tts = getattr(settings, 'AUTO_TTS', True)
        
        # Try to generate TTS using OpenAI if API key is available
        if generate_tts and settings.OPENAI_API_KEY and result.get("response_text"):
            try:
                tts_result = text_to_speech(
                    result["response_text"],
                    output_path=f"data/audio/responses/response_{uuid.uuid4().hex[:8]}.mp3",
                    engine=settings.TTS_ENGINE
                )
                if tts_result.get("success"):
                    tts_audio_path = tts_result.get("audio_path")
                    audio_file = tts_audio_path
            except Exception as tts_err:
                logger.warning(f"TTS generation failed: {tts_err}")
        
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


# ============================================
# TTS ENDPOINTS
# ============================================

@router.post(
    "/tts",
    response_model=TTSResponse,
    summary="Text-to-Speech",
    description="Convert text to speech using TTS engine",
    tags=["TTS"]
)
async def synthesize_speech(
    request: TTSRequest
):
    """
    Convert text to speech
    
    - **text**: Text to convert to speech
    - **voice**: Optional voice to use (engine-specific)
    - **engine**: Optional TTS engine (openai, coqui, khaya)
    """
    try:
        # Determine engine
        engine = request.engine or settings.TTS_ENGINE
        
        # Generate unique output path
        output_path = f"data/audio/responses/tts_{uuid.uuid4().hex[:8]}.mp3"
        if engine == "coqui" or engine == "khaya":
            output_path = output_path.replace(".mp3", ".wav")
        
        logger.info(f"TTS request: engine={engine}, text='{request.text[:50]}...'")
        
        # Generate speech
        result = text_to_speech(
            text=request.text,
            output_path=output_path,
            voice=request.voice,
            engine=engine
        )
        
        if result["success"]:
            # Construct audio URL
            audio_path = result["audio_path"]
            audio_url = f"{settings.API_PREFIX}/audio/responses/{os.path.basename(audio_path)}"
            
            return TTSResponse(
                success=True,
                text=request.text,
                audio_path=audio_path,
                audio_url=audio_url,
                engine=result.get("engine", engine)
            )
        else:
            return TTSResponse(
                success=False,
                text=request.text,
                error=result.get("error", "TTS generation failed"),
                engine=engine
            )
            
    except Exception as e:
        logger.error(f"Error in TTS endpoint: {e}", exc_info=True)
        return TTSResponse(
            success=False,
            text=request.text,
            error=str(e),
            engine=request.engine or settings.TTS_ENGINE
        )


@router.get(
    "/tts/engines",
    summary="Get available TTS engines",
    tags=["TTS"]
)
async def get_tts_engines():
    """Get list of available TTS engines"""
    from backend.stt.tts_service import get_available_engines
    engines = get_available_engines()
    return {
        "engines": engines,
        "default": settings.TTS_ENGINE,
        "configured_engine": settings.TTS_ENGINE
    }


# ============================================
# AI AGRICULTURE CHATBOT ENDPOINTS
# ============================================

@router.post(
    "/chat/agriculture",
    response_model=AgricultureChatResponse,
    summary="AI Agriculture Chatbot",
    description="Get AI-powered agriculture advice using RAG and LLM",
    tags=["AI Chat"]
)
async def chat_agriculture(
    request: AgricultureChatRequest
):
    """
    Process user question through AI agriculture pipeline:
    
    1. Translate Kikuyu to English (if needed)
    2. Search agriculture knowledge base (RAG)
    3. Generate answer using LLM
    4. Translate answer to Kikuyu (if needed)
    5. Generate TTS audio (optional)
    
    - **text**: User's question in Kikuyu or English
    - **input_language**: Language of input ('kikuyu' or 'english')
    - **output_language**: Language of response ('kikuyu' or 'english')
    - **include_sources**: Include source documents in response
    - **generate_audio**: Generate TTS audio response
    """
    start_time = time.time()
    
    try:
        logger.info(f"Agriculture chat request: '{request.text[:50]}...'")
        
        # Use LLM for agricultural questions to get accurate answers from knowledge base
        result = chat_full_response(request.text, use_llm=True)
        
        # Override languages based on request
        if request.output_language.lower() == "english":
            final_response = result.get("english_response", result["response"])
        else:
            final_response = result["response"]
        
        # Build sources list if requested
        sources = None
        if request.include_sources and result.get("sources"):
            sources = result["sources"]
        
        # Generate TTS audio if requested
        audio_url = None
        if request.generate_audio and final_response:
            try:
                output_path = f"data/audio/responses/agriculture_{uuid.uuid4().hex[:8]}.mp3"
                tts_result = text_to_speech(
                    final_response,
                    output_path=output_path,
                    engine=settings.TTS_ENGINE
                )
                if tts_result.get("success"):
                    audio_url = f"{settings.API_PREFIX}/audio/responses/{os.path.basename(output_path)}"
            except Exception as tts_err:
                logger.warning(f"TTS generation failed: {tts_err}")
        
        processing_time = time.time() - start_time
        
        return AgricultureChatResponse(
            success=True,
            response=final_response,
            english_response=result.get("english_response"),
            translated_input=result.get("translated_input"),
            processing_time=round(processing_time, 2),
            sources=sources,
            audio_url=audio_url
        )
        
    except Exception as e:
        logger.error(f"Error in agriculture chat: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing agriculture chat: {str(e)}"
        )


@router.post(
    "/chat/agriculture/voice",
    response_model=AgricultureChatResponse,
    summary="Voice Agriculture Chatbot",
    description="Process voice input through AI agriculture pipeline",
    tags=["AI Chat"]
)
async def chat_agriculture_voice(
    audio: UploadFile = File(...),
    output_language: str = "kikuyu",
    generate_audio: bool = True
):
    """
    Process voice input through full AI agriculture pipeline:
    
    1. Transcribe voice to text (Whisper)
    2. Translate Kikuyu to English (if needed)
    3. Search agriculture knowledge base (RAG)
    4. Generate answer using LLM
    5. Translate answer to Kikuyu (if needed)
    6. Generate TTS audio
    
    - **audio**: Audio file with user's question
    - **output_language**: Language of response ('kikuyu' or 'english')
    - **generate_audio**: Generate TTS audio response
    """
    start_time = time.time()
    
    try:
        # Read audio file
        audio_bytes = await audio.read()
        
        # Save uploaded file
        temp_path = AudioProcessor.save_uploaded_file(
            audio_bytes,
            audio.filename or "recording.wav"
        )
        
        logger.info(f"Received voice audio: {audio.filename}, size: {len(audio_bytes)} bytes")
        
        # Validate audio
        is_valid, error_msg = AudioProcessor.validate_audio_file(temp_path)
        if not is_valid:
            AudioProcessor.cleanup_temp_file(temp_path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid audio file: {error_msg}"
            )
        
        # Convert to WAV for processing
        wav_path = AudioProcessor.convert_to_wav(temp_path)
        
        # Transcribe audio
        transcription_result = transcribe_kikuyu(wav_path)
        
        if not transcription_result["success"]:
            AudioProcessor.cleanup_temp_file(temp_path)
            if wav_path != temp_path:
                AudioProcessor.cleanup_temp_file(wav_path)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Transcription failed: {transcription_result.get('error')}"
            )
        
        transcribed_text = transcription_result["text"]
        logger.info(f"Transcribed: '{transcribed_text}'")
        
        # Process through chatbot pipeline
        result = chat_full_response(transcribed_text)
        
        # Override output language based on request
        if output_language.lower() == "english":
            final_response = result.get("english_response", result["response"])
        else:
            final_response = result["response"]
        
        # Generate TTS audio if requested
        audio_url = None
        if generate_audio and final_response:
            try:
                output_path = f"data/audio/responses/agriculture_voice_{uuid.uuid4().hex[:8]}.mp3"
                tts_result = text_to_speech(
                    final_response,
                    output_path=output_path,
                    engine=settings.TTS_ENGINE
                )
                if tts_result.get("success"):
                    audio_url = f"{settings.API_PREFIX}/audio/responses/{os.path.basename(output_path)}"
            except Exception as tts_err:
                logger.warning(f"TTS generation failed: {tts_err}")
        
        # Cleanup temp files
        AudioProcessor.cleanup_temp_file(temp_path)
        if wav_path != temp_path:
            AudioProcessor.cleanup_temp_file(wav_path)
        
        processing_time = time.time() - start_time
        
        return AgricultureChatResponse(
            success=True,
            response=final_response,
            english_response=result.get("english_response"),
            translated_input=result.get("translated_input"),
            processing_time=round(processing_time, 2),
            sources=result.get("sources"),
            audio_url=audio_url
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in agriculture voice chat: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing voice input: {str(e)}"
        )


@router.post(
    "/translate",
    response_model=TranslationResponse,
    summary="Translate text",
    description="Translate text between Kikuyu and English using NLLB",
    tags=["Translation"]
)
async def translate_text_endpoint(
    request: TranslationRequest
):
    """
    Translate text between Kikuyu and English:
    
    - **text**: Text to translate
    - **source_language**: Source language ('kikuyu' or 'english')
    - **target_language**: Target language ('kikuyu' or 'english')
    """
    try:
        logger.info(f"Translation request: {request.source_language} -> {request.target_language}")
        
        translated = translate_text(
            request.text,
            source_lang=request.source_language,
            target_lang=request.target_language
        )
        
        return TranslationResponse(
            success=True,
            original_text=request.text,
            translated_text=translated,
            source_language=request.source_language,
            target_language=request.target_language
        )
        
    except Exception as e:
        logger.error(f"Translation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Translation error: {str(e)}"
        )

