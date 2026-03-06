"""
Intent classification and NLP utilities
"""

from typing import Optional, Dict, List
from sqlalchemy.orm import Session
import logging

from backend.database.crud import GreetingCRUD
from backend.config import settings

logger = logging.getLogger(__name__)


class IntentClassifier:
    """
    Classifies user input to matching intents
    Uses PostgreSQL similarity matching with fallback logic
    """
    
    def __init__(self, confidence_threshold: float = None):
        self.confidence_threshold = confidence_threshold or settings.CONFIDENCE_THRESHOLD
    
    def classify(self, db: Session, user_input: str) -> Optional[Dict]:
        """
        Classify user input to intent
        
        Args:
            db: Database session
            user_input: User's text input
            
        Returns:
            Intent dict with confidence score or None
        """
        if not user_input or not user_input.strip():
            return None
        
        # Use database similarity matching
        intent = GreetingCRUD.find_intent(
            db, 
            user_input, 
            self.confidence_threshold
        )
        
        if intent:
            logger.info(
                f"Matched intent '{intent['intent_id']}' "
                f"with confidence {intent['confidence']:.2f}"
            )
        else:
            logger.warning(f"No intent match found for: '{user_input}'")
        
        return intent
    
    def get_response_for_intent(
        self, 
        db: Session, 
        intent_id: str,
        context: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Get appropriate response for an intent
        
        Args:
            db: Database session
            intent_id: Intent identifier
            context: Optional context (formality, etc.)
            
        Returns:
            Response dict or None
        """
        formality = None
        if context:
            formality = context.get("formality_preference")
        
        response = GreetingCRUD.get_response(db, intent_id, formality)
        
        if response:
            logger.info(f"Selected response for intent '{intent_id}'")
        
        return response
    
    def process_input(
        self, 
        db: Session, 
        user_input: str,
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Complete processing: classify intent and get response
        
        Args:
            db: Database session
            user_input: User's input
            context: Optional context
            
        Returns:
            Complete response dict with intent and response
        """
        # Classify intent
        intent = self.classify(db, user_input)
        
        if not intent:
            return {
                "success": False,
                "intent": None,
                "confidence": 0.0,
                "response_text": "Ndingĩũĩka ũguo. Cokeria rĩngĩ?",
                "response_translation": "I don't understand. Try again?",
                "matched_pattern": None
            }
        
        # Get response
        response = self.get_response_for_intent(db, intent["intent_id"], context)
        
        if not response:
            return {
                "success": False,
                "intent": intent["intent_id"],
                "intent_name": intent["intent_name"],
                "confidence": intent["confidence"],
                "response_text": "Nĩ wega!",
                "response_translation": "Okay!",
                "matched_pattern": intent["matched_pattern"]
            }
        
        return {
            "success": True,
            "intent": intent["intent_id"],
            "intent_name": intent["intent_name"],
            "confidence": intent["confidence"],
            "matched_pattern": intent["matched_pattern"],
            "response_text": response["response_text"],
            "response_translation": response["translation"],
            "response_literal": response.get("literal_meaning"),
            "audio_file": response.get("audio_file"),
            "formality": response.get("formality"),
            "response_notes": response.get("notes"),
            "category": intent["category"],
            "formality_level": intent["formality_level"],
            "politeness_score": intent["politeness_score"]
        }


# Global classifier instance
classifier = IntentClassifier()
