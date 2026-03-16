"""
Language Detection Utilities
"""

import re
import unicodedata

# Kikuyu markers for detection
KIKUYU_MARKERS = [
    'nĩ', 'ũ', 'kũ', 'gũ', 'ĩ', 'mũ', 'rĩ', 'thĩ', 'ndĩ', 
    'ūrīkū', 'atīa', 'kahūa', 'gīkū', 'wīra', 'tīīri',
    'nīkīī', 'harī', 'kūrī', 'gatagatī', 'mūgūnda',
    # ASCII versions
    'ni', 'ku', 'gu', 'mu', 'ri', 'thi', 'ndi',
    'uriku', 'atia', 'kahua', 'giku', 'wira', 'tiiri',
    'nikii', 'hari', 'kuri', 'gatagati', 'mugunda'
]

KIKUYU_WORDS = {
    'nĩ', 'na', 'wa', 'ya', 'ta', 'nī', 'ūū', 'ũndũ',
    'kahūa', 'waru', 'mboco', 'mūtī', 'tīīri', 'mbura',
    'magetha', 'kūhanda', 'kūrīma', 'mūrīmi', 'mūgūnda',
    # ASCII versions
    'ni', 'na', 'wa', 'ya', 'ta', 'ni', 'uu', 'undu',
    'kahua', 'waru', 'mboco', 'muti', 'tiiri', 'mbura',
    'magetha', 'kuhanda', 'kurima', 'murimi', 'mugunda'
}

# Mapping from diacritical Kikuyu to ASCII
KIKUYU_DIACRITIC_MAP = {
    'ā': 'a', 'á': 'a', 'à': 'a', 'ã': 'a',
    'ē': 'e', 'é': 'e', 'è': 'e', 'ẽ': 'e',
    'ī': 'i', 'í': 'i', 'ì': 'i', 'ĩ': 'i',
    'ō': 'o', 'ó': 'o', 'ò': 'o', 'õ': 'o',
    'ū': 'u', 'ú': 'u', 'ù': 'u', 'ũ': 'u',
    'ġ': 'g', 'ğ': 'g',
    'ţ': 'th',  # For th sounds
}

# Reverse mapping: ASCII to diacritical (for KB matching)
ASCII_TO_DIACRITIC = {
    'aa': 'ā', 'ee': 'ē', 'ii': 'ī', 'oo': 'ō', 'uu': 'ū',
    'ng': 'ng',  # Keep ng as is
}


def normalize_kikuyu(text: str) -> str:
    """
    Normalize Kikuyu text to handle both diacritical and ASCII inputs.
    Converts all diacritical characters to their base forms.
    """
    if not text:
        return text
    
    result = text
    for diacritic, base in KIKUYU_DIACRITIC_MAP.items():
        result = result.replace(diacritic, base)
    
    return result


def normalize_text_for_matching(text: str) -> str:
    """
    Comprehensive text normalization for matching.
    Handles Kikuyu diacritics, punctuation, case, etc.
    """
    if not text:
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Normalize Kikuyu diacritics
    text = normalize_kikuyu(text)
    
    # Remove punctuation but keep spaces
    text = re.sub(r'[?!.,;:\'"()\[\]{}]', '', text)
    
    # Normalize whitespace
    text = ' '.join(text.split())
    
    return text.strip()


def detect_language(text: str) -> dict:
    """
    Detect if text is English or Kikuyu
    """
    text_lower = text.lower().strip()
    
    # Check Kikuyu markers
    kikuyu_marker_count = sum(1 for m in KIKUYU_MARKERS if m in text_lower)
    kikuyu_word_count = sum(1 for w in text_lower.split() if w in KIKUYU_WORDS)
    
    if kikuyu_marker_count >= 2 or kikuyu_word_count >= 2:
        return {
            'language': 'ki',
            'confidence': min(0.95, 0.6 + (kikuyu_marker_count * 0.1) + (kikuyu_word_count * 0.05)),
            'method': 'kikuyu_markers'
        }
    
    # Check special characters
    special_chars = ['ĩ', 'ũ', 'ī', 'ū']
    if any(c in text for c in special_chars):
        return {'language': 'ki', 'confidence': 0.85, 'method': 'kikuyu_chars'}
    
    # Fallback to langdetect
    try:
        from langdetect import detect
        detected = detect(text)
        if detected == 'en':
            return {'language': 'en', 'confidence': 0.90, 'method': 'langdetect'}
        elif detected in ['sw', 'lg', 'rw']:
            return {'language': 'ki', 'confidence': 0.70, 'method': 'langdetect_fallback'}
        return {'language': 'en', 'confidence': 0.60, 'method': 'default'}
    except:
        return {'language': 'en', 'confidence': 0.50, 'method': 'error_fallback'}


def is_greeting(text: str) -> bool:
    """Quick check if text is a greeting"""
    import re
    greeting_patterns = [
        r'^hi\b', r'^hello\b', r'^hey\b', r'^good\s+(morning|afternoon|evening)',
        r'^thayu', r'^thaayu', r'^wĩ\s+mwega', r'^ūhoro'
    ]
    text_lower = text.lower().strip()
    return any(re.match(p, text_lower) for p in greeting_patterns)
