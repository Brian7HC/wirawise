"""
Guardrails to keep conversation on-topic and safe
"""

from typing import Dict, Optional
from dataclasses import dataclass

@dataclass
class GuardrailResult:
    allowed: bool
    reason: Optional[str]
    redirect_message: Optional[str]
    suggested_queries: list

class Guardrails:
    """
    Enforce boundaries on what the chatbot responds to
    """
    
    def __init__(self):
        # Topics we DO handle
        self.supported_topics = ['coffee', 'potato', 'cabbage']
        
        # Topics we DON'T handle but can redirect
        self.redirect_topics = {
            'maize': "For maize farming, contact your county agricultural office or try iShamba Kenya.",
            'beans': "For beans farming, we recommend contacting KALRO or your local extension officer.",
            'dairy': "For dairy farming, try the Kenya Dairy Board resources or contact your cooperative.",
            'livestock': "For livestock questions, contact your county veterinary officer.",
            'loans': "For agricultural loans, try Kenya Commercial Bank's Mobigrow or Equity Bank's agricultural products.",
            'weather': "For weather forecasts, check Kenya Meteorological Department or tune to your local radio."
        }
        
        # Completely off-topic (polite decline)
        self.off_topic_response = {
            'en': """I'm WIRAWISE, a coffee farming assistant. I can only help with questions about:

☕ **Coffee Farming** - varieties, planting, diseases, harvesting, processing
🥔 **Potato Farming** - varieties, planting, diseases, harvesting
🥬 **Cabbage Farming** - varieties, planting, diseases, harvesting

Please ask me something about these crops!

**Popular questions you can ask:**
• Which coffee variety should I plant?
• How do I treat Coffee Berry Disease?
• When is the best time to harvest coffee?""",
            
            'ki': """Niĩ nĩ WIRAWISE, mũteithia wa ũrĩmi wa kahũa. No ngũteithie tu na ciũria cia:

☕ **Ũrĩmi wa Kahũa** - mĩthemba, kũhanda, mĩrimũ, kũgetha, gũthondeka
🥔 **Ũrĩmi wa Waru** - mĩthemba, kũhanda, mĩrimũ, kũgetha
🥬 **Ũrĩmi wa Kabichi** - mĩthemba, kũhanda, mĩrimũ, kũgetha

Njũria ũndũ ũhoro wa mĩmera ĩyo!

**Ciũria ũngĩũria:**
• Nĩ mũthemba ũrĩkũ wa kahũa njagĩrĩire kũhanda?
• Nĩ ndĩhonanie atĩa mũrimũ wa CBD?
• Nĩ hĩndĩinja ya kũgetha kahũa?"""
        }
        
        # Harmful content detection
        self.harmful_patterns = [
            'kill', 'poison', 'destroy neighbor', 'steal', 'illegal',
            'burn farm', 'sabotage'
        ]
    
    def check_query(self, query: str, routing_result) -> GuardrailResult:
        """
        Check if query passes guardrails
        """
        query_lower = query.lower()
        
        # 1. Check for harmful content
        if self._is_harmful(query_lower):
            return GuardrailResult(
                allowed=False,
                reason="harmful_content",
                redirect_message="I cannot help with that request. Please ask about farming practices only.",
                suggested_queries=[]
            )
        
        # 2. Check if supported topic
        if routing_result.intent.value in ['coffee_question', 'potato_question', 'cabbage_question', 'greeting', 'emergency']:
            return GuardrailResult(
                allowed=True,
                reason=None,
                redirect_message=None,
                suggested_queries=[]
            )
        
        # 3. Check if can redirect
        if routing_result.intent.value == 'general_farming':
            redirect_msg = self._get_redirect_message(query_lower)
            return GuardrailResult(
                allowed=False,
                reason="different_topic",
                redirect_message=redirect_msg,
                suggested_queries=self._get_coffee_suggestions()
            )
        
        # 4. Off-topic
        if routing_result.intent.value == 'off_topic':
            return GuardrailResult(
                allowed=False,
                reason="off_topic",
                redirect_message=None,  # Will use default off-topic response
                suggested_queries=self._get_coffee_suggestions()
            )
        
        # 5. Unclear - allow but flag
        return GuardrailResult(
            allowed=True,
            reason="unclear_but_allowed",
            redirect_message=None,
            suggested_queries=[]
        )
    
    def _is_harmful(self, query: str) -> bool:
        """Check for harmful content"""
        return any(pattern in query for pattern in self.harmful_patterns)
    
    def _get_redirect_message(self, query: str) -> str:
        """Get redirect message for unsupported topic"""
        for topic, message in self.redirect_topics.items():
            if topic in query:
                return f"I specialize in coffee, potato, and cabbage farming. {message}\n\nFor coffee questions, I'm here to help!"
        
        return "I specialize in coffee, potato, and cabbage farming. For other crops, please contact your local agricultural extension officer."
    
    def _get_coffee_suggestions(self) -> list:
        """Get suggested coffee questions"""
        return [
            "Which coffee variety is best for my area?",
            "How do I treat Coffee Berry Disease?",
            "When should I apply fertilizer?",
            "How do I know when coffee is ready to harvest?",
            "What is the current price of coffee?"
        ]
    
    def get_off_topic_response(self, language: str) -> str:
        """Get off-topic response in specified language"""
        return self.off_topic_response.get(language, self.off_topic_response['en'])