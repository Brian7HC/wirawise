"""
Intelligent fallback when exact answer not in dataset
"""

from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class FallbackResponse:
    response: str
    confidence: float
    source: str  # 'partial_match', 'category_suggestion', 'expert_redirect'
    related_questions: List[str]

class SmartFallback:
    """
    Provides intelligent responses when exact match not found
    """
    
    def __init__(self, search_engine):
        self.search_engine = search_engine
        
        # Category-based fallback responses
        self.category_info = {
            'varieties': {
                'en': """I don't have the exact answer, but here's what I know about coffee varieties in Kenya:

**Main Varieties:**
• **Ruiru 11** - Disease resistant, compact, high yielding (recommended for most farmers)
• **Batian** - Newer variety, disease tolerant, good quality
• **SL 28 & SL 34** - Traditional varieties, best quality but disease susceptible
• **K7** - Good for low altitude areas

For specific variety recommendations for your area, contact Coffee Research Institute at 020-2022924.""",
                
                'ki': """Ndigĩkĩrĩire ũcokio ũrĩa wĩ mahĩtia, no nĩ kĩĩ njũũĩ ũhoro wa mĩthemba ya kahũa Kenya:

**Mĩthemba Mĩnene:**
• **Ruiru 11** - Ĩgitĩraga mĩrimũ, nĩ nini, ĩciaraga mũno
• **Batian** - Mũthemba mũerũ, ĩgitĩraga mĩrimũ
• **SL 28 na SL 34** - Mĩthemba ya tene, mũcamo mũthaka
• **K7** - Njega kũndũ gũtarĩ ĩrĩma

Hũũra Coffee Research Institute: 020-2022924."""
            },
            
            'diseases': {
                'en': """I don't have the exact answer, but here's general guidance on coffee diseases:

**Most Common Diseases:**
1. **Coffee Berry Disease (CBD)** - Black spots on berries → Spray copper fungicide
2. **Coffee Leaf Rust (CLR)** - Orange spots under leaves → Spray copper hydroxide
3. **Bacterial Blight** - Brown wilting → Remove affected branches
4. **Root Rot** - Yellowing, wilting → Improve drainage

**General Treatment:**
• Remove affected parts
• Spray copper-based fungicide
• Improve air circulation through pruning
• Consult extension officer for severe cases

For urgent help: Contact Coffee Research Institute at 020-2022924""",
                
                'ki': """Ndigĩkĩrĩire ũcokio ũrĩa wĩ mahĩtia, no nĩ ũrori ũhoro wa mĩrimũ ya kahũa:

**Mĩrimũ ĩrĩa ĩrĩ mĩingĩ:**
1. **CBD** - Mathĩna mĩirũ mbegũ-inĩ → Haka dawa ya copper
2. **CLR** - Matũnda ma machungwa nthĩ ya mathangũ → Haka copper hydroxide
3. **Bacterial Blight** - Kũhoha na kũgarũka brown → Ruta honge irĩa irwarũ
4. **Root Rot** - Kũgarũka ma ngoikoni → Thondeka mũhũmũ wa maaĩ

**Ũhonokio:**
• Ruta iria irwarũ
• Haka dawa ya copper
• Ceha nĩguo rũhuho rũhĩtũke
• Hũũra mũrutani angĩkorwo mũũru

Haraka: Hũũra Coffee Research Institute 020-2022924"""
            },
            
            'fertilizer': {
                'en': """I don't have the exact answer, but here's general fertilizer guidance:

**Basic Coffee Fertilizer Program:**
• **At Planting:** 200g DAP + 5kg manure per hole
• **Young Trees (1-3 years):** 100-300g NPK 17:17:17 per tree (increase yearly)
• **Mature Trees:** 400-600g NPK per year, split into 2 applications
• **Top Dressing:** 200g CAN, 6-8 weeks after NPK

**When to Apply:**
• First: March-April (long rains start)
• Second: September-October (short rains start)

**Important:** Never apply to dry soil or put fertilizer touching the stem!

For soil testing and specific recommendations, contact your county agricultural office.""",
                
                'ki': """Ndigĩkĩrĩire ũcokio ũrĩa wĩ mahĩtia, no nĩ ũrori ũhoro wa mboleo:

**Mũtaratara wa Mboleo:**
• **Kũhanda:** 200g DAP + 5kg thumu o irima
• **Mĩtĩ mĩnini (mĩaka 1-3):** 100-300g NPK 17:17:17 o mũtĩ
• **Mĩtĩ mĩkũrũ:** 400-600g NPK o mwaka, mĩrĩ 2
• **Top Dressing:** 200g CAN, wiki 6-8 thutha wa NPK

**Hĩndĩ ya kwĩkĩra:**
• Ya mbere: March-April
• Ya keerĩ: September-October

**Menyerera:** Ndũkaĩkĩre mboleo tĩĩri mũũmũ kana ĩgũthĩnia gĩtina!

Hũũra agriculture office ya county yaku."""
            },
            
            'harvesting': {
                'en': """I don't have the exact answer, but here's general harvesting guidance:

**When to Harvest:**
• Coffee is ready when berries turn bright red
• Different trees mature at different times
• Harvest every 7-10 days during peak season

**How to Harvest:**
• Pick ONLY fully ripe (red) cherries
• Never pick green, overripe, or diseased berries
• Use clean containers
• Deliver to factory SAME DAY

**Quality Tips:**
• Morning picking gives better quality
• Don't mix ripe and unripe
• Avoid dropping berries on ground
• Keep cool and ventilated

For specific timing in your area, check with your factory or cooperative.""",
                
                'ki': """Ndigĩkĩrĩire ũcokio ũrĩa wĩ mahĩtia, no nĩ ũrori ũhoro wa kũgetha:

**Hĩndĩ ya Kũgetha:**
• Kahũa gakinyu rĩrĩa mbegũ ĩtuĩka njirũ
• Mĩtĩ ĩtiganĩte hĩndĩ cia kũkinyia
• Getha o thikũ 7-10 hĩndĩ ya magetha

**Ũrĩa wa Kũgetha:**
• Tua TU mbegũ njirũ
• Ndũkatue njĩrũrĩa, ngũrũ, kana irwarũ
• Hũthĩra ciondo itheru
• Twara factory O ŨMŨTHĨ

**Mũcamo Mwega:**
• Kũgetha rũciinĩ nĩ kwega
• Ndũkatũkanĩe njirũ na njĩrũrĩa
• Ndũkagũthie nthĩ
• Rĩka ĩhehu

Ũria factory kana cooperative yaku hĩndĩ njega ya kũgetha bũrũri waku."""
            }
        }
        
        # Expert contact information
        self.expert_contacts = {
            'coffee_research': {
                'name': 'Coffee Research Institute (CRI)',
                'phone': '020-2022924',
                'location': 'Ruiru, off Thika Road',
                'services': 'Seedlings, disease diagnosis, training'
            },
            'county_agriculture': {
                'name': 'County Agricultural Office',
                'services': 'Extension services, soil testing, farmer groups'
            }
        }
    
    def get_fallback_response(
        self, 
        query: str, 
        routing_result,
        search_result: Dict,
        language: str = 'en'
    ) -> FallbackResponse:
        """
        Generate intelligent fallback when no exact match
        """
        
        # 1. If we have a partial match (confidence 0.3-0.5), use it with disclaimer
        if search_result.get('confidence', 0) >= 0.3:
            return self._partial_match_response(search_result, language)
        
        # 2. If we detected a category, give category-specific guidance
        if routing_result.sub_category:
            return self._category_fallback(routing_result.sub_category, language)
        
        # 3. If we detected entities, try to help based on those
        if routing_result.detected_entities:
            return self._entity_based_fallback(routing_result.detected_entities, language)
        
        # 4. General helpful response
        return self._general_fallback(language)
    
    def _partial_match_response(self, search_result: Dict, language: str) -> FallbackResponse:
        """Use partial match with disclaimer"""
        
        disclaimer = {
            'en': "I found a related answer that might help:\n\n",
            'ki': "Nĩkuona ũcokio ũrĩa ũngĩteithia:\n\n"
        }
        
        suffix = {
            'en': "\n\n---\n*If this doesn't fully answer your question, please rephrase or ask more specifically.*",
            'ki': "\n\n---\n*Angĩkorwo ũũ ũtarĩ ũcokio ũrĩa wĩ mahĩtia, geria kũũria na njĩra ĩngĩ.*"
        }
        
        response = disclaimer[language] + search_result['response'] + suffix[language]
        
        return FallbackResponse(
            response=response,
            confidence=search_result['confidence'],
            source='partial_match',
            related_questions=self._get_related_questions(search_result, language)
        )
    
    def _category_fallback(self, category: str, language: str) -> FallbackResponse:
        """Provide category-specific general info"""
        
        if category in self.category_info:
            response = self.category_info[category][language]
        else:
            response = self._general_fallback(language).response
        
        return FallbackResponse(
            response=response,
            confidence=0.4,
            source='category_suggestion',
            related_questions=self._get_category_questions(category, language)
        )
    
    def _entity_based_fallback(self, entities: List[str], language: str) -> FallbackResponse:
        """Try to help based on detected entities"""
        
        # Check for disease entities
        diseases = [e for e in entities if e.startswith('disease:')]
        if diseases:
            return self._category_fallback('diseases', language)
        
        # Check for variety entities
        varieties = [e for e in entities if e.startswith('variety:')]
        if varieties:
            return self._category_fallback('varieties', language)
        
        # Check for plant part (might indicate disease/pest)
        parts = [e for e in entities if e.startswith('part:')]
        if parts:
            response = {
                'en': f"I see you're asking about problems with {parts[0].split(':')[1]}. This could be related to disease or pests. Can you describe the symptoms more? For example:\n\n• What color are the affected areas?\n• When did you first notice it?\n• How many trees are affected?\n\nOr ask me directly: 'What causes black spots on coffee leaves?'",
                'ki': f"Nĩkuona ũkũũria ũhoro wa mathĩna ma {parts[0].split(':')[1]}. Ũũ no ũkorwo nĩ mũrimũ kana tũtambi. No ũhũrĩre kĩmenyithĩrio? Kwa mũhiano:\n\n• Rangi nĩ ũrĩkũ?\n• Wambĩrĩrie kuona rĩ?\n• Mĩtĩ ĩgana ĩranyitĩka?\n\nKana njũrie: 'Nĩ kĩĩ gĩtũmaga mathĩna mĩirũ mathangũ-inĩ?'"
            }
            return FallbackResponse(
                response=response[language],
                confidence=0.3,
                source='entity_based',
                related_questions=[]
            )
        
        return self._general_fallback(language)
    
    def _general_fallback(self, language: str) -> FallbackResponse:
        """General helpful response"""
        
        response = {
            'en': """I couldn't find a specific answer to your question.

**Here's how I can help:**

📋 **Ask me about:**
• Coffee varieties (Ruiru 11, Batian, SL28, etc.)
• Planting and spacing
• Diseases and pests
• Fertilizer application
• Pruning and care
• Harvesting and processing
• Current prices and marketing

💡 **Try asking:**
• "Which coffee variety is best for high altitude?"
• "How do I treat CBD?"
• "When should I apply fertilizer?"

📞 **For expert help:**
Coffee Research Institute: 020-2022924""",
            
            'ki': """Ndigĩkĩĩte ũcokio wa kĩũria gĩaku.

**Nĩ ngũteithie na:**

📋 **Njũrie ũhoro wa:**
• Mĩthemba ya kahũa (Ruiru 11, Batian, SL28)
• Kũhanda na ũtaganũ
• Mĩrimũ na tũtambi
• Kwĩkĩra mboleo
• Gũceha na kũmenyerera
• Kũgetha na gũthondeka
• Bei na thoko

💡 **Geria kũũria:**
• "Nĩ mũthemba ũrĩkũ mwega kũndũ kũrĩ ĩrĩma?"
• "Nĩ ndĩhonanie atĩa CBD?"
• "Nĩ ndĩĩkĩre mboleo rĩ?"

📞 **Ũteithio:**
Coffee Research Institute: 020-2022924"""
        }
        
        return FallbackResponse(
            response=response[language],
            confidence=0.1,
            source='general_fallback',
            related_questions=self._get_popular_questions(language)
        )
    
    def _get_related_questions(self, search_result: Dict, language: str) -> List[str]:
        """Get related questions based on match"""
        # Would query the KB for related questions
        return []
    
    def _get_category_questions(self, category: str, language: str) -> List[str]:
        """Get popular questions for category"""
        questions = {
            'varieties': {
                'en': ["Which coffee variety is best for my area?", "What is the difference between Ruiru 11 and Batian?", "Where can I buy certified seedlings?"],
                'ki': ["Nĩ mũthemba ũrĩkũ mwega bũrũri wakwa?", "Kũhaana gwa Ruiru 11 na Batian nĩ kũrĩkũ?", "No ngũre kũ mĩũngũrũa ĩrĩa ĩrĩ certified?"]
            },
            'diseases': {
                'en': ["How do I treat CBD?", "What causes orange spots on leaves?", "Why are my berries dropping?"],
                'ki': ["Nĩ ndĩhonanie atĩa CBD?", "Nĩ kĩĩ gĩtũmaga matũnda ma machungwa mathangũ-inĩ?", "Mbegũ ciakwa nĩkĩĩ ciragũa?"]
            },
            'fertilizer': {
                'en': ["What fertilizer should I use?", "When should I apply fertilizer?", "How much fertilizer per tree?"],
                'ki': ["Nĩ mboleo ĩrĩkũ njagĩrĩire kũhũthĩra?", "Nĩ ndĩĩkĩre mboleo rĩ?", "Mboleo ĩgana o mũtĩ?"]
            },
            'harvesting': {
                'en': ["When is coffee ready to harvest?", "How do I get AA grade?", "How to dry coffee properly?"],
                'ki': ["Kahũa gakinyu kũgethwo rĩ?", "Nĩ ndĩreke atĩa kuona grade ya AA?", "Nĩ ndĩũmithie atĩa kahũa?"]
            }
        }
        return questions.get(category, {}).get(language, [])
    
    def _get_popular_questions(self, language: str) -> List[str]:
        """Get general popular questions"""
        questions = {
            'en': [
                "Which coffee variety should I plant?",
                "How do I treat Coffee Berry Disease?",
                "When should I apply fertilizer?",
                "What is the current coffee price?",
                "How do I know when coffee is ready to harvest?"
            ],
            'ki': [
                "Nĩ mũthemba ũrĩkũ wa kahũa njagĩrĩire kũhanda?",
                "Nĩ ndĩhonanie atĩa mũrimũ wa CBD?",
                "Nĩ ndĩĩkĩre mboleo rĩ?",
                "Bei ya kahũa nĩ ĩrĩkũ rĩu?",
                "Nĩ ndĩmenya atĩa kahũa gakinyu kũgethwo?"
            ]
        }
        return questions[language]