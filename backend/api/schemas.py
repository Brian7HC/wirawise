"""
Pydantic schemas for request/response validation
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
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
