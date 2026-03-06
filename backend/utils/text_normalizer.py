"""
Text normalizer for Kikuyu transcription cleanup.
Handles common Whisper transcription errors and provides fuzzy matching.
"""

import json
import os
import logging
from typing import Optional, List, Tuple, Dict
from rapidfuzz import fuzz, process

logger = logging.getLogger(__name__)

# Load corrections from JSON file
def _load_corrections() -> Dict[str, str]:
    """Load normalization corrections from JSON file."""
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "data", "text", "normalization.json"
    )
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("corrections", {})
    except FileNotFoundError:
        logger.warning(f"Normalization config not found at {config_path}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing normalization config: {e}")
        return {}


def _load_common_greetings() -> List[str]:
    """Load common greetings for fuzzy matching."""
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "data", "text", "normalization.json"
    )
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("common_greetings", [])
    except FileNotFoundError:
        logger.warning(f"Normalization config not found at {config_path}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing normalization config: {e}")
        return []


# Global correction dictionary
_CORRECTIONS = _load_corrections()
_COMMON_GREETINGS = _load_common_greetings()

# Fuzzy match threshold (70% = accept)
FUZZY_THRESHOLD = 70


def normalize_text(text: str) -> str:
    """
    Normalize Kikuyu text to handle common transcription errors.
    
    This applies:
    1. Lowercase conversion
    2. Dictionary-based corrections (ohoro → uhoro, etc.)
    3. Character removal (accents, special chars)
    
    Args:
        text: Raw transcribed text
        
    Returns:
        Normalized text
    """
    if not text:
        return text
    
    # Convert to lowercase and strip whitespace
    text = text.lower().strip()
    
    # Remove common noise patterns
    noise_patterns = ['ʔ', '˖', '累', '!', '?', '.', ',', "'", '"']
    for noise in noise_patterns:
        text = text.replace(noise, '')
    
    # Apply dictionary corrections (longest keys first for proper replacement)
    sorted_corrections = sorted(_CORRECTIONS.keys(), key=len, reverse=True)
    for wrong in sorted_corrections:
        if wrong in text:
            text = text.replace(wrong, _CORRECTIONS[wrong])
    
    # Clean up extra spaces
    text = ' '.join(text.split())
    
    return text


def fuzzy_match_greeting(text: str, threshold: int = FUZZY_THRESHOLD) -> Optional[Tuple[str, int]]:
    """
    Use fuzzy matching to find the closest greeting match.
    
    Args:
        text: Input text to match
        threshold: Minimum similarity score (0-100)
        
    Returns:
        Tuple of (matched_greeting, score) or None if no match
    """
    if not text or not _COMMON_GREETINGS:
        return None
    
    # First try exact match after normalization
    normalized = normalize_text(text)
    if normalized in _COMMON_GREETINGS:
        return (normalized, 100)
    
    # Use rapidfuzz to find best match
    result = process.extractOne(
        normalized,
        _COMMON_GREETINGS,
        scorer=fuzz.ratio
    )
    
    if result and result[1] >= threshold:
        return (result[0], int(result[1]))
    
    return None


def match_intent_fuzzy(text: str, intent_keywords: Dict[str, List[str]], threshold: int = 65) -> Optional[str]:
    """
    Match text to intent using fuzzy matching.
    
    Args:
        text: Input text
        intent_keywords: Dict mapping intent names to lists of keywords
        threshold: Minimum similarity score
        
    Returns:
        Matched intent name or None
    """
    if not text:
        return None
    
    normalized = normalize_text(text)
    best_match = None
    best_score = 0
    
    for intent, keywords in intent_keywords.items():
        for keyword in keywords:
            # Calculate similarity
            score = fuzz.ratio(normalized, keyword.lower())
            
            # Also check partial match (contains)
            partial_score = fuzz.partial_ratio(normalized, keyword.lower())
            
            # Use the higher score
            max_score = max(score, partial_score * 0.9)
            
            if max_score > best_score and max_score >= threshold:
                best_score = max_score
                best_match = intent
    
    return best_match


def clean_transcription(text: str) -> str:
    """
    Clean transcription by normalizing and attempting fuzzy match.
    
    Args:
        text: Raw transcription from Whisper
        
    Returns:
        Cleaned and normalized text
    """
    if not text:
        return ""
    
    # First pass: normalize
    cleaned = normalize_text(text)
    
    # Try to match against known greetings
    match_result = fuzzy_match_greeting(cleaned)
    if match_result:
        logger.info(f"Fuzzy matched '{text}' -> '{match_result[0]}' (score: {match_result[1]})")
        return match_result[0]
    
    return cleaned


# Convenience function for quick normalization
def quick_normalize(text: str) -> str:
    """Quick normalization without loading files."""
    if not text:
        return text
    
    text = text.lower().strip()
    
    # Basic corrections
    basic_corrections = {
        'uuhoro': 'uhoro',
        'ohoro': 'uhoro',
        'ohro': 'uhoro',
        'ndimuega': 'ndimwega',
        'wimuga': 'wimwega',
    }
    
    for wrong, correct in basic_corrections.items():
        if wrong in text:
            text = text.replace(wrong, correct)
    
    return text
