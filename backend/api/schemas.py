"""
Pydantic schemas for request/response validation
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


# ============================================
# REQUEST SCHEMAS
# ============================================

class TextChatRequest(BaseModel):
    """Request schema for text-based chat"""
    text: str = Field(..., min_length=1, max_length=500, description="User's text input")
    session_id: Optional[str] = Field(None, description="Session ID for conversation tracking")
    context: Optional[Dict[str, Any]] = Field(None, description="Optional context (formality, etc.)")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "text": "Thayu",
                    "session_id": "550e8400-e29b-41d4-a716-446655440000",
                    "context": {"formality_preference": "formal"}
                }
            ]
        }
    }


class VoiceChatRequest(BaseModel):
    """Request schema for voice-based chat (future use)"""
    session_id: Optional[str] = None
    language: str = "kik"


class TTSRequest(BaseModel):
    """Request schema for Text-to-Speech conversion"""
    text: str = Field(..., min_length=1, max_length=2000, description="Text to convert to speech")
    voice: Optional[str] = Field(None, description="Voice to use (engine-specific)")
    engine: Optional[str] = Field(None, description="TTS engine to use (openai, coqui, khaya)")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "text": "Thayu! Thayu thayu!",
                    "voice": "alloy",
                    "engine": "openai"
                }
            ]
        }
    }


class TTSResponse(BaseModel):
    """Response schema for TTS endpoint"""
    success: bool = Field(..., description="Whether the request was successful")
    text: str = Field(..., description="Original text that was converted")
    audio_path: Optional[str] = Field(None, description="Path to generated audio file")
    audio_url: Optional[str] = Field(None, description="URL to access the audio")
    engine: str = Field(..., description="TTS engine used")
    error: Optional[str] = Field(None, description="Error message if failed")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "text": "Thayu! Thayu thayu!",
                    "audio_path": "data/audio/responses/response_abc123.wav",
                    "audio_url": "http://localhost:8000/api/v1/audio/responses/response_abc123.wav",
                    "engine": "openai"
                }
            ]
        }
    }


# ============================================
# RESPONSE SCHEMAS
# ============================================

class ChatResponse(BaseModel):
    """Response schema for chat endpoints"""
    success: bool = Field(..., description="Whether the request was successful")
    intent: Optional[str] = Field(None, description="Matched intent ID")
    intent_name: Optional[str] = Field(None, description="Human-readable intent name")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0.0 to 1.0)")
    matched_pattern: Optional[str] = Field(None, description="The pattern that matched user input")
    
    response_text: str = Field(..., description="Bot's response in Kikuyu")
    response_translation: Optional[str] = Field(None, description="English translation")
    response_literal: Optional[str] = Field(None, description="Literal word-by-word translation")
    
    audio_file: Optional[str] = Field(None, description="Path to audio response file")
    formality: Optional[str] = Field(None, description="Formality level of response")
    
    session_id: str = Field(..., description="Session ID for this conversation")
    
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "intent": "greeting_thayu",
                    "intent_name": "Most Polite Traditional Greeting (Thayu)",
                    "confidence": 0.95,
                    "matched_pattern": "Thayu",
                    "response_text": "Thayu! Thayu thayu!",
                    "response_translation": "Peace be upon you! Peace, peace!",
                    "response_literal": "Peace! Peace peace!",
                    "audio_file": "audio/responses/greetings/thayu_thayu_response.wav",
                    "formality": "very_formal",
                    "session_id": "550e8400-e29b-41d4-a716-446655440000",
                    "metadata": {
                        "category": "greetings",
                        "formality_level": 10,
                        "politeness_score": 10
                    }
                }
            ]
        }
    }


class SessionResponse(BaseModel):
    """Response schema for session information"""
    session_id: str
    user_id: Optional[str] = None
    started_at: datetime
    last_active: datetime
    conversation_count: int
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "session_id": "550e8400-e29b-41d4-a716-446655440000",
                    "user_id": None,
                    "started_at": "2024-01-15T10:30:00",
                    "last_active": "2024-01-15T10:35:00",
                    "conversation_count": 5
                }
            ]
        }
    }


class ConversationHistoryResponse(BaseModel):
    """Response schema for conversation history"""
    session_id: str
    history: list[Dict[str, Any]]
    total_count: int


class VocabularyResponse(BaseModel):
    """Response schema for vocabulary lookup"""
    word: str
    meaning: Optional[str] = None
    pronunciation: Optional[str] = None
    found: bool


class HealthCheckResponse(BaseModel):
    """Response schema for health check endpoint"""
    status: str
    version: str
    database: Dict[str, Any]
    timestamp: datetime


class AnalyticsResponse(BaseModel):
    """Response schema for analytics"""
    period: str
    data: list[Dict[str, Any]]


class ErrorResponse(BaseModel):
    """Response schema for errors"""
    success: bool = False
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


# ============================================
# AGRICULTURE CHATBOT SCHEMAS
# ============================================

class AgricultureChatRequest(BaseModel):
    """Request schema for AI agriculture chatbot"""
    text: str = Field(..., min_length=1, max_length=1000, description="User's question in Kikuyu or English")
    input_language: Optional[str] = Field("kikuyu", description="Input language: 'kikuyu' or 'english'")
    output_language: Optional[str] = Field("kikuyu", description="Output language: 'kikuyu' or 'english'")
    include_sources: Optional[bool] = Field(False, description="Whether to include source documents in response")
    generate_audio: Optional[bool] = Field(True, description="Whether to generate TTS audio response")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "text": "Ndiwigura iti?",
                    "input_language": "kikuyu",
                    "output_language": "kikuyu",
                    "include_sources": True
                }
            ]
        }
    }


class AgricultureSource(BaseModel):
    """Source document from RAG search"""
    text: str
    category: str
    crop: str


class AgricultureChatResponse(BaseModel):
    """Response schema for AI agriculture chatbot"""
    success: bool
    response: str = Field(..., description="Chatbot response in requested language")
    english_response: Optional[str] = Field(None, description="English response (if output is Kikuyu)")
    translated_input: Optional[str] = Field(None, description="Translated input (if input was Kikuyu)")
    processing_time: float = Field(..., description="Processing time in seconds")
    sources: Optional[List[AgricultureSource]] = Field(None, description="Retrieved source documents")
    audio_url: Optional[str] = Field(None, description="URL to audio response if generated")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "response": "Mbura ya maize inowera ikagwa mabanga 75cm Hagati na 25cm Hagati ya mime. Iyo ni ya maana sana.",
                    "english_response": "Maize should be planted at a spacing of 75cm between rows and 25cm between plants. This is very important.",
                    "translated_input": "How do I plant maize?",
                    "processing_time": 2.5,
                    "sources": [
                        {
                            "text": "The recommended spacing for maize planting is 75cm between rows and 25cm between plants.",
                            "category": "planting",
                            "crop": "maize"
                        }
                    ]
                }
            ]
        }
    }


class TranslationRequest(BaseModel):
    """Request schema for translation"""
    text: str = Field(..., min_length=1, max_length=2000, description="Text to translate")
    source_language: str = Field(..., description="Source language: 'kikuyu' or 'english'")
    target_language: str = Field(..., description="Target language: 'kikuyu' or 'english'")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "text": "Ndiwigura iti?",
                    "source_language": "kikuyu",
                    "target_language": "english"
                }
            ]
        }
    }


class TranslationResponse(BaseModel):
    """Response schema for translation"""
    success: bool
    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    error: Optional[str] = None


# ============================================
# PRODUCTION ENGINE SCHEMAS
# ============================================

class ProductionChatRequest(BaseModel):
    """Request schema for production coffee chatbot"""
    message: str = Field(..., min_length=1, max_length=500, description="User's question")
    language: str = Field("auto", description="Language: 'en', 'ki', or 'auto'")
    include_seasonal: bool = Field(True, description="Include seasonal tips")
    location: Optional[str] = Field(None, description="User location (optional)")


class ProductionChatResponse(BaseModel):
    """Response schema for production coffee chatbot"""
    success: bool
    message_type: str
    response: str
    language: str
    confidence: float
    confidence_level: Optional[str] = None
    match_type: Optional[str] = None
    topic: Optional[str] = None
    matched_question: Optional[str] = None
    seasonal_tip: Optional[dict] = None
    related_questions: Optional[list] = None
    suggested_queries: Optional[list] = None
    processing_time_ms: float
    emergency: Optional[bool] = False
