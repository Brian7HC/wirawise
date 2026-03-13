"""
LLM module using Groq for agriculture advice.
Now integrates with Knowledge Base for accurate, real data.
"""

import logging
import os

# Load environment variables first
from dotenv import load_dotenv
load_dotenv()

from backend.nlp.knowledge_base import get_knowledge_base, search_knowledge, search_coffee_qa
from backend.nlp.translator import translate_english_to_kikuyu

logger = logging.getLogger(__name__)

# Groq imports
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    logger.warning("Groq not available")

# Model settings
DEFAULT_MODEL = "llama-3.1-8b-instant"
DEFAULT_MAX_TOKENS = 800
DEFAULT_TEMPERATURE = 0.2

# Singleton client
_groq_client = None


def get_groq_client():
    """Get or initialize Groq client."""
    global _groq_client
    if _groq_client is None:
        api_key = os.environ.get("GROQ_API_KEY", "")
        if api_key and GROQ_AVAILABLE:
            _groq_client = Groq(api_key=api_key)
            logger.info("Groq client initialized")
        else:
            logger.warning("Groq API key not available")
    return _groq_client


def get_agriculture_advice(english_query: str, original_kikuyu: str = "") -> dict:
    """
    Get agriculture advice using knowledge base + LLM.
    
    Priority:
    1. Search Q&A using original Kikuyu (most accurate)
    2. If no Kikuyu match, search using English
    3. Use LLM with knowledge base context to avoid hallucinations
    """
    kb = get_knowledge_base()
    client = get_groq_client()
    
    # Step 1: Check Q&A - try Kikuyu first (since translation is unreliable)
    qa_result = None
    
    # If we have original Kikuyu, search with it FIRST
    if original_kikuyu:
        logger.info(f"Searching with original Kikuyu: '{original_kikuyu[:50]}...'")
        qa_result = search_coffee_qa(original_kikuyu, "ki")
    
    # If no Kikuyu result or no original Kikuyu, try English
    if not qa_result:
        logger.info(f"Searching with English: '{english_query[:50]}...'")
        qa_result = search_coffee_qa(english_query, "en")
    
    if qa_result:
        # Use the Q&A answer directly
        topic = qa_result.get("topic", "Agriculture")
        logger.info(f"Found Q&A match in topic: {topic}")
        return {
            "answer_en": qa_result.get("answer_en", ""),
            "answer_ki": qa_result.get("answer_ki", ""),
            "sources": [f"{topic} Research Kenya"],
            "type": "qa"
        }
    
    # Step 2: Search knowledge base for general agriculture (legacy format)
    kb_results = search_knowledge(english_query)
    
    # Step 2: Build context from knowledge base
    context_parts = []
    sources = []
    
    # Add crop information
    for crop_result in kb_results.get('crops', []):
        for crop_name, crop_data in crop_result.items():
            context_parts.append(f"CROP - {crop_name}:")
            if crop_data.get('kikuyu_name'):
                context_parts.append(f"  Kikuyu: {crop_data['kikuyu_name']}")
            if crop_data.get('seasons'):
                context_parts.append(f"  Seasons: {crop_data['seasons']}")
            if crop_data.get('fertilizer'):
                context_parts.append(f"  Fertilizer: {crop_data['fertilizer']}")
            if crop_data.get('spacing'):
                context_parts.append(f"  Spacing: {crop_data['spacing']}")
            if crop_data.get('maturity'):
                context_parts.append(f"  Maturity: {crop_data['maturity']}")
            if crop_data.get('soil_requirements'):
                context_parts.append(f"  Soil: {crop_data['soil_requirements']}")
            sources.append("KALRO Kenya")
    
    # Add fertilizer information
    for fert_result in kb_results.get('fertilizers', []):
        for fert_name, fert_data in fert_result.items():
            context_parts.append(f"FERTILIZER - {fert_name}:")
            if fert_data.get('full_name'):
                context_parts.append(f"  Name: {fert_data['full_name']}")
            if fert_data.get('composition'):
                context_parts.append(f"  Composition: {fert_data['composition']}")
            if fert_data.get('price_range_kes'):
                context_parts.append(f"  Price: KES {fert_data['price_range_kes']} per 50kg")
            if fert_data.get('application'):
                context_parts.append(f"  Use: {fert_data['application']}")
            sources.append("KALRO Kenya")
    
    # Add general practices
    for practice_result in kb_results.get('general', []):
        for practice, details in practice_result.items():
            context_parts.append(f"PRACTICE - {practice}: {details}")
            sources.append("FAO Kenya")
    
    knowledge_context = "\n".join(context_parts) if context_parts else ""
    
    # Step 3: Build prompt with knowledge base context
    if knowledge_context:
        prompt = f"""You are an agricultural advisor for Kenyan farmers in the Central Highlands (Kiambu, Nyeri, Murang'a).
Use ONLY the information from the knowledge base below. Do NOT make up information.

KNOWLEDGE BASE DATA:
{knowledge_context}

IMPORTANT FACTS FOR KENYA FARMERS:
- Current season: Long rains (March-May) - main planting season
- DAP fertilizer: KES 6,000-7,000 per 50kg bag
- CAN fertilizer: KES 5,500-6,500 per 50kg bag
- Recommended maize planting: 75cm x 30cm spacing
- Use DAP at planting (60-70 kg/ha), CAN as top dressing 6-8 weeks later
- Plant maize in March-April for long rains, October for short rains
- Crop rotation with beans improves soil fertility

Based ONLY on the knowledge base above, answer this farmer's question:

Farmer's Question (in English): {english_query}

Provide practical advice suitable for Kenyan smallholder farmers.
If you don't have specific information from the knowledge base, provide general best practices based on the facts above.
Be specific with quantities, prices, and timing."""
    else:
        # Fallback if no knowledge base data found
        prompt = f"""You are an agricultural advisor for Kenyan farmers in the Central Highlands (Kiambu, Nyeri, Murang'a).

IMPORTANT FACTS FOR KENYA FARMERS:
- Current season: Long rains (March-May) - main planting season
- DAP (Diammonium Phosphate): KES 6,000-7,000 per 50kg bag - use 60-70 kg/ha at planting
- CAN (Calcium Ammonium Nitrate): KES 5,500-6,500 per 50kg bag - use 60-70 kg/ha as top dressing
- Recommended maize planting: 75cm x 30cm spacing = 44,444 plants/ha
- Plant maize seeds 2-5 cm deep
- Best planting time: March-April (long rains), October (short rains)
- Apply DAP at planting, CAN 6-8 weeks after planting
- Use farmyard manure 5-10 tons/ha for organic matter
- Soil pH should be 5.5-7.0 for maize

Answer this farmer's question with practical advice:

Farmer's Question (in English): {english_query}

Provide specific quantities, prices in KES, and timing for Kenya."""
    
    try:
        if client is None:
            return {
                "success": False,
                "answer": "AI service not available. Please try again later.",
                "sources": []
            }
        
        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful agricultural advisor for Kenyan farmers. Provide accurate, practical advice based on Kenyan agriculture."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=DEFAULT_MAX_TOKENS,
            temperature=DEFAULT_TEMPERATURE
        )
        
        english_answer = response.choices[0].message.content.strip()
        
        # Step 4: Translate to Kikuyu
        kikuyu_answer = translate_english_to_kikuyu(english_answer)
        
        # If translation fails or returns English, use English with note
        if kikuyu_answer == english_answer or len(kikuyu_answer) < 10:
            # Try a simpler translation approach
            kikuyu_answer = translate_english_to_kikuyu(english_answer)
            if kikuyu_answer == english_answer:
                kikuyu_answer = english_answer  # Return English if translation fails
        
        return {
            "success": True,
            "answer_english": english_answer,
            "answer_kikuyu": kikuyu_answer,
            "sources": list(set(sources)) if sources else ["KALRO Kenya", "FAO Kenya", "Kenya Meteorology"]
        }
        
    except Exception as e:
        logger.error(f"Error getting agriculture advice: {e}")
        return {
            "success": False,
            "answer": f"Error: {str(e)}",
            "sources": []
        }


def ask_agriculture_model(query: str, context: str = "") -> str:
    """Legacy function - now uses get_agriculture_advice."""
    result = get_agriculture_advice(query)
    return result.get("answer_english", result.get("answer", ""))


def get_agriculture_info(query: str, original_kikuyu: str = "") -> str:
    """
    Get agriculture information from JSON only (no LLM).
    
    This function ONLY searches the comprehensive_qa.json for answers.
    No AI/LLM is used - just direct JSON lookup.
    
    Args:
        query: The agriculture question in English
        original_kikuyu: Original Kikuyu question (for direct JSON lookup)
        
    Returns:
        The answer as a string (Kikuyu if found in JSON)
    """
    # Search with original Kikuyu first (most accurate)
    if original_kikuyu:
        logger.info(f"JSON-only search with Kikuyu: '{original_kikuyu[:50]}...'")
        qa_result = search_coffee_qa(original_kikuyu, "ki")
    else:
        qa_result = None
    
    # If no result from Kikuyu, try English
    if not qa_result:
        logger.info(f"JSON-only search with English: '{query[:50]}...'")
        qa_result = search_coffee_qa(query, "en")
    
    if qa_result:
        # Return the Kikuyu answer directly from JSON
        topic = qa_result.get("topic", "Agriculture")
        kikuyu_answer = qa_result.get("answer_ki", "")
        logger.info(f"Found JSON match in topic: {topic}, returning Kikuyu answer")
        return kikuyu_answer
    
    # No match found in JSON
    logger.info("No match found in JSON, returning fallback message")
    return "Ndingĩhota gūgūta īno. Twũgĩire ūrĩa"
