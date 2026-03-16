"""FastAPI route handlers"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
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
from backend.nlp.coffee_semantic_search import search_coffee_question, search_coffee_question_with_context, initialize as init_coffee_search
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
        
        # Pre-check: If query contains agricultural keywords, bypass intent classifier and go directly to agriculture
        agriculture_keywords = [
            'coffee', 'kahua', 'kahūa', 'cafe', 'café',
            'potato', 'waru', 'irio', 'chips', 'irish',
            'cabbage', 'kabichi', 'mboga', 'greens',
            'planting', 'harvest', 'fertilizer', 'soil', 'rain', 'season',
            'pests', 'diseases', 'yield', 'market', 'price',
            'ngĩgũra', 'ngũgũra', 'kūhanda', 'kūrīma', 'kūrīma', 
            'mbegu', 'mbegū', 'mūrīmi', 'mūgūnda', 'tīīri', 'thambi'
        ]
        
        text_lower = request.text.lower()
        is_agriculture_query = any(kw in text_lower for kw in agriculture_keywords)
        
        # Process input with intent classifier
        result = classifier.process_input(db, request.text, request.context)
        
        # If agriculture intent detected OR query looks like agriculture, use AI pipeline instead
        if result.get("intent") == "agriculture_question" or is_agriculture_query:
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


# ============================================
# COFFEE SEMANTIC SEARCH ENDPOINT
# ============================================

class CoffeeChatRequest(BaseModel):
    """Request schema for coffee semantic search"""
    message: str = Field(..., min_length=1, description="User's question in Kikuyu")
    session_id: Optional[str] = Field(None, description="Optional session ID")


class CoffeeChatResponse(BaseModel):
    """Response schema for coffee semantic search"""
    success: bool
    question: str
    answer: str
    confidence: float
    matched_question: Optional[str] = None


@router.post(
    "/chat/coffee",
    response_model=CoffeeChatResponse,
    summary="Coffee Q&A Semantic Search",
    description="Search coffee agriculture questions using semantic similarity",
    tags=["AI Chat"]
)
async def coffee_chat(
    request: CoffeeChatRequest
):
    """
    Search for coffee agriculture questions using semantic embeddings.
    
    - **message**: User's question in Kikuyu
    - **session_id**: Optional session ID
    
    Returns the best matching answer from the coffee Q&A dataset.
    """
    try:
        logger.info(f"Coffee semantic search: {request.message[:50]}...")
        
        # Search using semantic similarity
        result = search_coffee_question_with_context(request.message)
        
        return CoffeeChatResponse(
            success=True,
            question=request.message,
            answer=result["answer"],
            confidence=result["confidence"],
            matched_question=result.get("question")
        )
        
    except Exception as e:
        logger.error(f"Coffee chat error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Coffee chat error: {str(e)}"
        )


# ============================================
# FULL KNOWLEDGE BASE SEMANTIC SEARCH
# ============================================

class SemanticChatRequest(BaseModel):
    """Request for full KB semantic search"""
    message: str = Field(..., min_length=1, max_length=1000)
    preferred_language: str = Field("auto", description="en, ki, or auto")
    include_alternatives: bool = Field(False, description="Include alternative matches")


class SemanticChatResponse(BaseModel):
    """Response for full KB semantic search"""
    success: bool
    message_type: str  # 'answer', 'greeting', 'clarification', 'no_match'
    response: str
    response_language: str
    matched_question: Optional[str] = None
    confidence: Optional[str] = None
    confidence_score: Optional[float] = None
    topic: Optional[str] = None
    alternatives: Optional[list] = None
    detected_language: Optional[str] = None


# Global instances (initialized lazily)
_kb_processor = None
_semantic_engine = None


def _get_kb_processor():
    """Get or create KB processor"""
    global _kb_processor
    if _kb_processor is None:
        from backend.nlp.kb_processor import KnowledgeBaseProcessor
        kb_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "knowledge", "comprehensive_qa.json")
        _kb_processor = KnowledgeBaseProcessor(kb_path)
    return _kb_processor


def _get_semantic_engine():
    """Get or create semantic engine"""
    global _semantic_engine
    if _semantic_engine is None:
        from backend.nlp.semantic_engine import SemanticSearchEngine
        kb = _get_kb_processor()
        _semantic_engine = SemanticSearchEngine(kb)
    return _semantic_engine


@router.post(
    "/chat/semantic",
    response_model=SemanticChatResponse,
    summary="Full Knowledge Base Semantic Search",
    description="Search the entire knowledge base using semantic embeddings",
    tags=["AI Chat"]
)
async def semantic_chat(request: SemanticChatRequest):
    """
    Full semantic search using your comprehensive knowledge base.
    - Detects language (English/Kikuyu)
    - Checks for greetings
    - Searches all topics with semantic matching
    - Returns answer in user's language
    """
    try:
        from backend.nlp.language_utils import detect_language, is_greeting
        
        user_message = request.message.strip()
        logger.info(f"Semantic chat: {user_message[:50]}...")
        
        # Detect language
        if request.preferred_language == "auto":
            lang_info = detect_language(user_message)
            detected_lang = lang_info['language']
        else:
            detected_lang = request.preferred_language
        
        # Check greeting
        kb = _get_kb_processor()
        greeting_match = kb.check_greeting(user_message)
        if greeting_match:
            greeting_intent, best_response = greeting_match
            return SemanticChatResponse(
                success=True,
                message_type="greeting",
                response=best_response.get('text', 'Thayu!'),
                response_language=detected_lang,
                greeting_type=greeting_intent.intent_name,
                detected_language=detected_lang
            )
        
        # Search KB
        engine = _get_semantic_engine()
        results = engine.search(user_message, top_k=5 if request.include_alternatives else 1)
        
        if not results:
            return SemanticChatResponse(
                success=False,
                message_type="no_match",
                response="I'm sorry, I couldn't find a good answer. Please try rephrasing.",
                response_language=detected_lang,
                detected_language=detected_lang
            )
        
        best = results[0]
        
        # Return answer in user's language
        answer = best['answer_en'] if detected_lang == 'en' else best['answer_ki']
        matched_q = best['question_en'] if detected_lang == 'en' else best['question_ki']
        
        alternatives = None
        if request.include_alternatives and len(results) > 1:
            alternatives = []
            for r in results[1:4]:
                alternatives.append({
                    'question': r['question_en'] if detected_lang == 'en' else r['question_ki'],
                    'score': r['score']
                })
        
        return SemanticChatResponse(
            success=True,
            message_type="answer",
            response=answer,
            response_language=detected_lang,
            matched_question=matched_q,
            confidence=best['confidence'],
            confidence_score=best['score'],
            topic=best['topic'],
            alternatives=alternatives,
            detected_language=detected_lang
        )
        
    except Exception as e:
        logger.error(f"Semantic chat error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Semantic chat error: {str(e)}"
        )


@router.get(
    "/topics",
    summary="Get available topics",
    description="Get list of all topics in the knowledge base",
    tags=["Knowledge Base"]
)
async def get_topics():
    """Get all available topics in the knowledge base"""
    try:
        kb = _get_kb_processor()
        topics = kb.get_all_topics()
        return {
            "topics": topics,
            "count": len(topics)
        }
    except Exception as e:
        logger.error(f"Error getting topics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )


@router.get(
    "/questions/{topic}",
    summary="Get questions by topic",
    description="Get all questions for a specific topic",
    tags=["Knowledge Base"]
)
async def get_questions_by_topic(topic: str, language: str = "en"):
    """Get all questions for a specific topic"""
    try:
        kb = _get_kb_processor()
        qa_pairs = kb.get_qa_by_topic(topic)
        
        if not qa_pairs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Topic '{topic}' not found"
            )
        
        questions = [
            {
                "id": qa.id,
                "question_en": qa.question_en,
                "question_ki": qa.question_ki
            }
            for qa in qa_pairs
        ]
        
        return {
            "topic": topic,
            "questions": questions,
            "count": len(questions)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting questions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )


@router.get(
    "/health",
    summary="Health check",
    description="Check API health status",
    tags=["Health"]
)
async def health_check():
    """Check API health"""
    try:
        kb = _get_kb_processor()
        return {
            "status": "healthy",
            "kb_loaded": True,
            "total_qa_pairs": len(kb.qa_pairs),
            "total_topics": len(kb.get_all_topics()),
            "embedding_method": _get_semantic_engine().method
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

