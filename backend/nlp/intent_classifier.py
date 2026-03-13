"""
Intent classification and NLP utilities
"""

from typing import Optional, Dict, List
from sqlalchemy.orm import Session
import logging
import re

from backend.database.crud import GreetingCRUD
from backend.config import settings

logger = logging.getLogger(__name__)

# Agriculture keywords for fallback detection
AGRICULTURE_KEYWORDS = [
    # Maize/Crops
    'mbembe', 'mabembe', 'ĩrĩa', 'mirio', 'mĩrĩo',
    # Farm/Land
    'gĩthaka', 'githaka', 'thambi', 'ngwacoka',
    # Farming activities
    'ngĩgũra', 'ngituma', 'ngũgũra', 'ngethereka',
    # Inputs
    'boro', 'mboro', 'mbura',
    # Other
    'mbĩrĩ', 'mĩtĩ', 'ĩcemanio', 'irio', 'mbemebe',
    # Coffee
    'kahua', 'kahūa'
]

# Agriculture patterns (regex)
AGRICULTURE_PATTERNS = [
    r'mbembe\s+\w+',  # mbembe + anything
    r'ĩrĩa\s+\w+',     # planting/crops + anything
    r'mabembe\s+\w+',  # crops + anything
    r'gĩthaka\s+\w+', # farm/land + anything
    r'ngĩgũra',         # I am cultivating
    r'ngĩtũma',         # I need/want
    r'ngethereka',      # I am harvesting
    r'ngwacoka',        # harvesting
    r'\bmbura\b',      # rain
    r'\bboro\b',       # fertilizer
    r'thambi',          # season
]


class IntentClassifier:
    """
    Classifies user input to matching intents
    Uses PostgreSQL similarity matching with fallback logic
    """
    
    def __init__(self, confidence_threshold: float = None):
        self.confidence_threshold = confidence_threshold or settings.CONFIDENCE_THRESHOLD
    
    def _detect_agriculture_intent(self, user_input: str) -> Optional[Dict]:
        """
        Detect agriculture intent using keyword and pattern matching.
        This is a fallback when database matching doesn't find a greeting intent.
        
        Args:
            user_input: User's text input
            
        Returns:
            Intent dict if agriculture keywords found, None otherwise
        """
        normalized_input = user_input.lower().strip()
        
        # Check for agriculture keywords
        keyword_count = sum(1 for kw in AGRICULTURE_KEYWORDS if kw in normalized_input)
        
        # Check for agriculture patterns
        pattern_matches = sum(1 for pattern in AGRICULTURE_PATTERNS 
                              if re.search(pattern, normalized_input, re.IGNORECASE))
        
        # If we have keyword or pattern matches, classify as agriculture
        if keyword_count >= 1 or pattern_matches >= 1:
            confidence = min(0.7, 0.3 + (keyword_count * 0.1) + (pattern_matches * 0.1))
            
            logger.info(
                f"Agriculture intent detected: {keyword_count} keywords, "
                f"{pattern_matches} patterns matched, confidence: {confidence:.2f}"
            )
            
            return {
                "intent_id": "agriculture_question",
                "intent_name": "Agriculture Question",
                "category": "agriculture",
                "subcategory": None,
                "formality_level": 5,
                "politeness_score": 5,
                "matched_pattern": f"keyword:{keyword_count},pattern:{pattern_matches}",
                "confidence": confidence
            }
        
        return None
    
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
        
        # Use database similarity matching for greetings
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
            # Fallback: Check for agriculture keywords when no greeting intent found
            logger.warning(f"No greeting intent match found for: '{user_input}'")
            
            # Try agriculture keyword detection as fallback
            agriculture_intent = self._detect_agriculture_intent(user_input)
            if agriculture_intent:
                logger.info(f"Falling back to agriculture intent for: '{user_input}'")
                return agriculture_intent
        
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
