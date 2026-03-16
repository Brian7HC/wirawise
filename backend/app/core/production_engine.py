"""
Production-ready coffee chatbot engine
Combines all components
"""

import json
import time
from typing import Dict, Optional
from pathlib import Path

from app.core.hybrid_engine import HybridSearchEngine
from app.core.intelligent_router import IntelligentRouter, QueryIntent
from app.core.guardrails import Guardrails
from app.core.smart_fallback import SmartFallback
from app.core.query_logger import QueryLogger
from app.core.seasonal_tips import SeasonalRecommendations

class ProductionCoffeeEngine:
    """
    Complete production engine with:
    - Intelligent routing
    - Guardrails
    - Smart fallback
    - Query logging
    - Seasonal context
    """
    
    def __init__(self, kb_path: str):
        print("🚀 Initializing Production Coffee Engine...")
        
        # Core components
        self.search_engine = HybridSearchEngine(kb_path)
        self.router = IntelligentRouter()
        self.guardrails = Guardrails()
        self.fallback = SmartFallback(self.search_engine)
        self.logger = QueryLogger()
        self.seasonal = SeasonalRecommendations()
        
        print("✅ All systems ready!")
    
    def process_query(
        self, 
        query: str, 
        language: str = 'auto',
        include_seasonal: bool = True,
        user_location: str = None
    ) -> Dict:
        """
        Main entry point - process any user query
        """
        start_time = time.time()
        
        # 1. Route the query
        routing = self.router.route_query(query)
        
        # 2. Detect language if auto
        if language == 'auto':
            language = self._detect_language(query)
        
        # 3. Check guardrails
        guardrail_check = self.guardrails.check_query(query, routing)
        
        if not guardrail_check.allowed:
            response = self._handle_guardrail_block(guardrail_check, routing, language)
            self._log_and_finalize(query, response, start_time)
            return response
        
        # 4. Handle based on intent
        if routing.intent == QueryIntent.GREETING:
            response = self._handle_greeting(query, language)
        
        elif routing.intent == QueryIntent.EMERGENCY:
            response = self._handle_emergency(query, routing, language)
        
        elif routing.intent in [QueryIntent.COFFEE_QUESTION, QueryIntent.POTATO_QUESTION, QueryIntent.CABBAGE_QUESTION]:
            response = self._handle_topic_question(query, routing, language)
        
        elif routing.intent == QueryIntent.UNCLEAR:
            response = self._handle_unclear(query, routing, language)
        
        else:
            response = self._handle_other(query, routing, language)
        
        # 5. Add seasonal tips if relevant
        if include_seasonal and response.get('success') and routing.intent in [QueryIntent.COFFEE_QUESTION, QueryIntent.EMERGENCY]:
            seasonal_tip = self.seasonal.get_current_tips(language)
            response['seasonal_tip'] = seasonal_tip
        
        # 6. Log and finalize
        self._log_and_finalize(query, response, start_time)
        
        return response
    
    def _detect_language(self, query: str) -> str:
        """Detect query language"""
        kikuyu_markers = ['ĩ', 'ũ', 'ī', 'ū', 'nĩ', 'atĩa', 'kũ', 'kahũa', 'gũ', 'mũ']
        query_lower = query.lower()
        
        if any(marker in query_lower for marker in kikuyu_markers):
            return 'ki'
        return 'en'
    
    def _handle_greeting(self, query: str, language: str) -> Dict:
        """Handle greeting"""
        result = self.search_engine.search(query)
        
        if result.get('match_type') == 'greeting':
            return {
                'success': True,
                'message_type': 'greeting',
                'response': result['response'],
                'language': language,
                'confidence': 1.0
            }
        
        # Fallback greeting
        greetings = {
            'en': "Hello! I'm WIRAWISE, your coffee farming assistant. How can I help you today?",
            'ki': "Wĩ mwega! Niĩ nĩ WIRAWISE, mũteithia waku wa ũrĩmi wa kahũa. Nĩ ngũteithie atĩa ũmũthĩ?"
        }
        
        return {
            'success': True,
            'message_type': 'greeting',
            'response': greetings[language],
            'language': language,
            'confidence': 1.0
        }
    
    def _handle_emergency(self, query: str, routing, language: str) -> Dict:
        """Handle emergency queries with priority"""
        # Search with emergency priority
        result = self.search_engine.search(query)
        
        # Add emergency header
        emergency_header = {
            'en': "🚨 **EMERGENCY RESPONSE** 🚨\n\n",
            'ki': "🚨 **ŨCOKIO WA HARAKA** 🚨\n\n"
        }
        
        if result.get('success') and result.get('confidence', 0) >= 0.4:
            response = emergency_header[language] + result['response']
            
            # Add emergency contact
            emergency_footer = {
                'en': "\n\n---\n**Need immediate help?** Contact Coffee Research Institute: 020-2022924",
                'ki': "\n\n---\n**Ũkĩbatara ũteithio wa haraka?** Hũũra Coffee Research Institute: 020-2022924"
            }
            response += emergency_footer[language]
            
            return {
                'success': True,
                'message_type': 'emergency',
                'response': response,
                'language': language,
                'confidence': result['confidence'],
                'topic': result.get('topic'),
                'emergency': True
            }
        
        # Emergency fallback
        fallback = self.fallback.get_fallback_response(query, routing, result, language)
        
        return {
            'success': True,
            'message_type': 'emergency',
            'response': emergency_header[language] + fallback.response,
            'language': language,
            'confidence': fallback.confidence,
            'emergency': True
        }
    
    def _handle_topic_question(self, query: str, routing, language: str) -> Dict:
        """Handle coffee/potato/cabbage questions"""
        # Search knowledge base
        result = self.search_engine.search(query)
        
        # High confidence - direct answer
        if result.get('success') and result.get('confidence', 0) >= 0.5:
            return {
                'success': True,
                'message_type': 'answer',
                'response': result['response'],
                'language': language,
                'confidence': result['confidence'],
                'confidence_level': result.get('confidence_level'),
                'match_type': result.get('match_type'),
                'topic': result.get('topic'),
                'matched_question': result.get('matched_question'),
                'qa_id': result.get('qa_id')
            }
        
        # Low confidence - use smart fallback
        fallback = self.fallback.get_fallback_response(query, routing, result, language)
        
        return {
            'success': True,
            'message_type': 'fallback',
            'response': fallback.response,
            'language': language,
            'confidence': fallback.confidence,
            'source': fallback.source,
            'related_questions': fallback.related_questions
        }
    
    def _handle_unclear(self, query: str, routing, language: str) -> Dict:
        """Handle unclear queries - try to help anyway"""
        # Try search first
        result = self.search_engine.search(query)
        
        if result.get('success') and result.get('confidence', 0) >= 0.4:
            return self._handle_topic_question(query, routing, language)
        
        # Ask clarification
        clarification = {
            'en': f"""I'm not sure I understand your question. 

Could you please tell me more about what you need help with?

**I can help with:**
• ☕ Coffee farming (planting, diseases, harvesting, prices)
• 🥔 Potato farming
• 🥬 Cabbage farming

**Try asking something like:**
• "How do I plant coffee?"
• "What causes black spots on coffee berries?"
• "When should I harvest my coffee?"

Or just type the topic you're interested in!""",
            
            'ki': f"""Ndingĩmenya wega kĩũria gĩaku.

No ũhũrĩre wega ũrĩa ũkwenda ũteithio?

**Nĩ ngũteithie na:**
• ☕ Ũrĩmi wa kahũa
• 🥔 Ũrĩmi wa waru
• 🥬 Ũrĩmi wa kabichi

**Geria kũũria ta:**
• "Nĩ ndĩrahande atĩa kahũa?"
• "Nĩ kĩĩ gĩtũmaga mathĩna mĩirũ mbegũ-inĩ?"
• "Nĩ ndĩragethe rĩ kahũa?"

Kana andĩka tu topic ĩrĩa ũkwenda!"""
        }
        
        return {
            'success': True,
            'message_type': 'clarification',
            'response': clarification[language],
            'language': language,
            'confidence': 0.0,
            'needs_clarification': True
        }
    
    def _handle_guardrail_block(self, guardrail_check, routing, language: str) -> Dict:
        """Handle blocked queries"""
        
        if guardrail_check.reason == 'off_topic':
            response = self.guardrails.get_off_topic_response(language)
        elif guardrail_check.redirect_message:
            response = guardrail_check.redirect_message
        else:
            response = self.guardrails.get_off_topic_response(language)
        
        return {
            'success': False,
            'message_type': 'off_topic',
            'response': response,
            'language': language,
            'confidence': 0.0,
            'suggested_queries': guardrail_check.suggested_queries
        }
    
    def _handle_other(self, query: str, routing, language: str) -> Dict:
        """Handle any other query type"""
        return self._handle_unclear(query, routing, language)
    
    def _log_and_finalize(self, query: str, response: Dict, start_time: float):
        """Log query and add timing"""
        # Add processing time
        response['processing_time_ms'] = (time.time() - start_time) * 1000
        
        # Log query
        try:
            self.logger.log_query(query, response)
        except Exception as e:
            print(f"Warning: Failed to log query: {e}")