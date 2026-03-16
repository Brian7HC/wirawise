"""Chatbot module combining translation and LLM."""

import logging
from typing import Dict, Optional, List
import time

from backend.nlp.translator import (
    kikuyu_to_english, 
    english_to_kikuyu,
    translate_text
)
from backend.nlp.llm import get_agriculture_info

logger = logging.getLogger(__name__)

# Intent types
INTENT_GREETING = "greeting"
INTENT_AGRICULTURE = "agriculture_question"


class AgricultureChatbot:
    """
    Main chatbot class for Kikuyu agricultural assistance.
    Pipeline: Kikuyu speech -> Translate to English (Groq) -> Get agriculture info (Groq) -> Translate to Kikuyu (Groq)
    """
    
    def __init__(self, initialize_models: bool = True):
        """
        Initialize the chatbot with all required models.
        
        Args:
            initialize_models: Whether to load models immediately
        """
        self.initialized = False
        
        if initialize_models:
            self.initialize()
    
    def initialize(self):
        """Initialize all required models and services."""
        logger.info("Initializing Agriculture Chatbot...")
        
        # Groq client is initialized lazily in translator.py and llm.py
        
        self.initialized = True
        logger.info("✅ Agriculture Chatbot initialized successfully")
    
    def _ensure_initialized(self):
        """Ensure chatbot is initialized before processing."""
        if not self.initialized:
            self.initialize()
    
    def process(self, user_input: str, 
                input_language: str = "kikuyu",
                output_language: str = "kikuyu",
                include_context: bool = False,
                use_llm: bool = True) -> Dict:
        """
        Process user input through the pipeline.
        
        NOW: Uses JSON lookup only (no AI/LLM)
        
        Args:
            user_input: Input text (in Kikuyu or English)
            input_language: Language of input ("kikuyu" or "english")
            output_language: Language of output ("kikuyu" or "english")
            include_context: Whether to include retrieval context in response
            use_llm: Ignored - now uses JSON only
            
        Returns:
            Dictionary with response and metadata
        """
        self._ensure_initialized()
        
        start_time = time.time()
        
        # Get agriculture info from JSON only (no LLM)
        # Pass original Kikuyu for direct JSON lookup
        answer = get_agriculture_info(user_input, user_input)
        
        process_time = time.time() - start_time
        
        result = {
            "response": answer,
            "english_response": None,
            "translated_input": None,
            "processing_time": round(process_time, 2),
            "sources": None
        }
        
        logger.info(f"Processed query in {process_time:.2f}s")
        return result
    
    def chat(self, kikuyu_input: str, include_sources: bool = False) -> str:
        """
        Simplified chat method for Kikuyu input.
        
        Args:
            kikuyu_input: User input in Kikuyu
            include_sources: Whether to include source information
            
        Returns:
            Response in Kikuyu
        """
        result = self.process(
            kikuyu_input,
            input_language="kikuyu",
            output_language="kikuyu",
            include_context=include_sources
        )
        return result["response"]
    
    def chat_english(self, english_input: str) -> str:
        """
        Chat method for English input (for testing).
        
        Args:
            english_input: User input in English
            
        Returns:
            Response in English
        """
        result = self.process(
            english_input,
            input_language="english",
            output_language="english"
        )
        return result["response"]
    
    def voice_chat(self, audio_file_path: str) -> Dict:
        """
        Process voice input through the full pipeline.
        Note: Audio transcription should be done separately.
        
        Args:
            audio_file_path: Path to audio file
            
        Returns:
            Full response with metadata
        """
        # This would be called after speech-to-text
        # For now, return a placeholder
        return {
            "error": "Ndagikora ico kugaya. Tikuhora kuhika kugaya.",
        }


# Global chatbot instance
_chatbot = None


def get_chatbot() -> AgricultureChatbot:
    """Get or create the global chatbot instance."""
    global _chatbot
    if _chatbot is None:
        _chatbot = AgricultureChatbot()
    return _chatbot


def chat(kikuyu_input: str) -> str:
    """
    Convenience function for quick chat.
    
    Args:
        kikuyu_input: User input in Kikuyu
        
    Returns:
        Response in Kikuyu
    """
    bot = get_chatbot()
    return bot.chat(kikuyu_input)


def chat_full_response(kikuyu_input: str, include_context: bool = True, use_llm: bool = True) -> Dict:
    """
    Convenience function for full response with metadata.
    
    Args:
        kikuyu_input: User input in Kikuyu
        include_context: Whether to include source context
        use_llm: Whether to use LLM (False for fast mode)
        
    Returns:
        Full response dictionary
    """
    bot = get_chatbot()
    return bot.process(
        kikuyu_input,
        input_language="kikuyu",
        output_language="kikuyu",
        include_context=include_context,
        use_llm=use_llm
    )


def process_agriculture_question(
    kikuyu_input: str,
    include_context: bool = True,
    use_llm: bool = True
) -> Dict:
    """
    Process an agriculture question through the AI pipeline.
    This is the core function for Option 4 (Hybrid AI + Knowledge).
    
    Pipeline:
        Kikuyu question
           ↓
        Translate to English (Groq)
           ↓
        Get agriculture info (Groq LLM)
           ↓
        Translate answer to Kikuyu (Groq)
           ↓
        Return response
    
    Args:
        kikuyu_input: User question in Kikuyu
        include_context: Whether to include source context in response
        use_llm: Whether to use LLM (False for fast mode)
        
    Returns:
        Dict with response, metadata, and optionally sources
    """
    bot = get_chatbot()
    return bot.process(
        kikuyu_input,
        input_language="kikuyu",
        output_language="kikuyu",
        include_context=include_context,
        use_llm=use_llm
    )


def process_intent(user_input: str, intent_id: str) -> Dict:
    """
    Route user input based on detected intent.
    
    This implements the hybrid approach:
    - greeting intent → JSON response from database
    - agriculture_question intent → AI pipeline
    
    Args:
        user_input: User's input text
        intent_id: Detected intent ID
        
    Returns:
        Response dictionary with appropriate handling
    """
    if intent_id == INTENT_AGRICULTURE:
        # Route to AI pipeline
        return {
            "intent": intent_id,
            "route": "ai_pipeline",
            **process_agriculture_question(user_input)
        }
    else:
        # For greetings and other intents, return a flag to use database responses
        return {
            "intent": intent_id,
            "route": "database",
            "user_input": user_input
        }
