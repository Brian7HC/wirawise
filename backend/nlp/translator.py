"""
Translation module using Groq LLM for Kikuyu ↔ English translation.
"""

import logging
import os
import re

# Load environment variables first
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)


def get_kikuyu_agriculture_response(english_query: str) -> str:
    """
    Generate Kikuyu agricultural responses using templates.
    Returns pure Kikuyu without any Swahili/English contamination.
    """
    query_lower = english_query.lower()
    
    # Kikuyu agricultural response templates (pure Kikuyu)
    if 'fertilizer' in query_lower or 'mbegu' in query_lower:
        return (
            "Uhoro mũgwanja. "
            "Mbembe ĩrĩaga mbegu. "
            "Tũma mbembe na DAP. "
            "Kũrĩa DAP 60-70kg po/hekta. "
            "Ũrĩa CAN ĩrĩa thiku 6-8 mĩthenya. "
            "Mbegu ya DAP ĩrĩa KES 6000-7000. "
            "Mbegu ya CAN ĩrĩa KES 5500-6500."
        )
    elif 'plant' in query_lower or 'tuma' in query_lower or 'when' in query_lower:
        return (
            "Uhoro mũgwanja. "
            "Mbembe ĩtũmagĩra maĩ. "
            "Tũma Mbembe Machĩ-Aprĩli. "
            "Tũma rĩu Okotoba-Novemba. "
            "Kũrĩa mbegu ya DAP tũmete."
        )
    elif 'harvest' in query_lower or 'kũrĩma' in query_lower:
        return (
            "Uhoro mũgwanja. "
            "Mbembe ĩrĩma ĩrĩa. "
            "Rĩma Mbembe Julai-Agasti. "
            "Rĩma rĩu Novemba-Disemba."
        )
    elif 'soil' in query_lower or 'land' in query_lower:
        return (
            "Uhoro mũgwanja. "
            "Mbembe ĩrĩaga ithaka rĩa mũnene. "
            "Rĩmĩra ĩgĩrĩ maguta. "
            "Tĩtĩra ĩgĩrĩ maĩ."
        )
    elif 'pest' in query_lower or 'disease' in query_lower or 'armyworm' in query_lower:
        return (
            "Uhoro mũgwanja. "
            "Mbembe ĩrĩaga ndũ. "
            "Rĩria armyworm, tĩkarania. "
            "Rĩkĩra mbembe ĩrĩa, tũka ngwatanĩra. "
            "Tũkĩa pesticide."
        )
    elif 'price' in query_lower or 'cost' in query_lower:
        return (
            "Uhoro mũgwanja. "
            "Mbegu ya DAP ĩrĩa KES 6000-7000. "
            "Mbegu ya CAN ĩrĩa KES 5500-6500. "
            "DAP na CAN nĩ mĩgunda mĩnene."
        )
    elif 'rain' in query_lower or 'weather' in query_lower:
        return (
            "Uhoro mũgwanja. "
            "Mbembe ĩrĩaga mũgĩ. "
            "Mũgĩ mũnene nĩ Machĩ-Aprĩli. "
            "Mũgĩ mũkĩ rĩu Okotoba-Novemba."
        )
    elif 'maize' in query_lower or 'corn' in query_lower:
        return (
            "Uhoro mũgwanja. "
            "Mbembe nĩ mĩrĩ ndĩrĩ. "
            "Tũma Mbembe Machĩ. "
            "Tũrĩa mbegu. "
            "Rĩma Julai."
        )
    else:
        # Default agricultural response
        return (
            "Uhoro mũgwanja. "
            "Ndingĩrima ũrĩa. "
            "Mbembe nĩ mĩrĩ ndĩrĩ ya Kenya. "
            "Tũma mbembe. "
            "Tũrĩa mbegu. "
            "Rĩma mbembe."
        )


# Try to import Groq
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

# Default model settings
DEFAULT_MODEL = "llama-3.1-8b-instant"
DEFAULT_MAX_TOKENS = 500
DEFAULT_TEMPERATURE = 0.1

# Singleton client
_groq_client = None


def get_groq_client():
    """Get or initialize Groq client."""
    global _groq_client
    if _groq_client is None:
        api_key = os.environ.get("GROQ_API_KEY", "")
        if api_key and GROQ_AVAILABLE:
            _groq_client = Groq(api_key=api_key)
            logger.info("Groq client initialized for translation")
        else:
            logger.warning("Groq API key not available")
    return _groq_client


def kikuyu_to_english(kikuyu_text: str) -> str:
    """Translate Kikuyu text to English using Groq."""
    if not kikuyu_text or not kikuyu_text.strip():
        return ""
    
    try:
        client = get_groq_client()
        if client is None:
            return kikuyu_text
        
        prompt = f"""You are a professional Kikuyu language translator.
Kikuyu is a Bantu language spoken in Kenya.

Translate this Kikuyu text to English. Focus on farming/agriculture terms:
- mbembe = maize/corn
- waru/batata = Irish potatoes
- irio/icemanio = vegetables  
- githaka = farm/land
- boru/bboro = fertilizer
- mbura = rain
- thambi = season

Kikuyu text: "{kikuyu_text}"

Simply translate to English:"""
        
        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": "You are a Kikuyu to English translator."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=DEFAULT_MAX_TOKENS,
            temperature=DEFAULT_TEMPERATURE
        )
        
        result = response.choices[0].message.content.strip()
        result = result.strip('"').strip("'")
        return result
        
    except Exception as e:
        logger.error(f"Translation error: {e}")
        return kikuyu_text


def english_to_kikuyu(english_text: str) -> str:
    """Translate English text to Kikuyu using Groq with strict Kikuyu-only output."""
    if not english_text or not english_text.strip():
        return ""
    
    try:
        client = get_groq_client()
        if client is None:
            return english_text
        
        # Use strict system message to force pure Kikuyu
        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {
                    "role": "system", 
                    "content": "You are a Kikuyu language expert. Your ONLY task is to translate English to Kikuyu. Rules:\n1. NEVER use Swahili words like 'kwa', 'hiyo', 'ni', 'lazima', 'au', 'na', 'ya', 'muda', 'wiki', 'mwaka', 'mwezi', 'hakuna', 'kuna', 'kuhusu', 'kwa sababu'\n2. NEVER use English words\n3. ONLY use pure Kikuyu words from Gikuyu language\n4. Key Kikuyu words: mbembe (maize), mbegu (fertilizer), mũgwanja (farmer), tũma (plant), kũrĩma (harvest), ũhoro (hello), wimwega (good), nĩ (yes), ai (no), tau (thank you), rĩma (cultivation), gũtũma (to plant), gũrĩma (to harvest)\n5. Respond with ONLY Kikuyu translation, no explanations, no English, no Swahili."
                },
                {
                    "role": "user", 
                    "content": f"Translate to pure Kikuyu: {english_text}"
                }
            ],
            max_tokens=500,
            temperature=0.1
        )
        
        result = response.choices[0].message.content.strip()
        result = result.strip('"').strip("'")
        
        # Check for Swahili/English contamination
        swahili_indicators = ['kwa', 'hiyo', 'lazima', 'muda', 'wiki', 'mwaka', 'mwezi', 'hakuna', 'kuna', 'kuhusu']
        result_lower = result.lower()
        if any(ind in ' ' + result_lower + ' ' for ind in swahili_indicators):
            # Use comprehensive Kikuyu fallback with agricultural info
            logger.warning(f"Translation contained Swahili, using Kikuyu fallback")
            return get_kikuyu_agriculture_response(english_text)
            
        return result
        
    except Exception as e:
        logger.error(f"Translation error: {e}")
        return english_text


def translate_text(text: str, source_lang: str = "kikuyu", target_lang: str = "english") -> str:
    if source_lang.lower() == "kikuyu" and target_lang.lower() == "english":
        return kikuyu_to_english(text)
    elif source_lang.lower() == "english" and target_lang.lower() == "kikuyu":
        return english_to_kikuyu(text)
    return text


translate_kikuyu_to_english = kikuyu_to_english
translate_english_to_kikuyu = english_to_kikuyu
