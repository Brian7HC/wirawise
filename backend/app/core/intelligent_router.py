"""
Intelligent Query Router with Guardrails
Handles: exact match, fuzzy match, semantic match, fallback, and out-of-scope
"""

import json
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class QueryIntent(Enum):
    GREETING = "greeting"
    COFFEE_QUESTION = "coffee_question"
    POTATO_QUESTION = "potato_question"
    CABBAGE_QUESTION = "cabbage_question"
    GENERAL_FARMING = "general_farming"
    OFF_TOPIC = "off_topic"
    EMERGENCY = "emergency"
    PRICING = "pricing"
    UNCLEAR = "unclear"

@dataclass
class RoutingResult:
    intent: QueryIntent
    confidence: float
    sub_category: Optional[str]
    detected_entities: List[str]
    suggested_action: str

class IntelligentRouter:
    """
    Routes queries to appropriate handlers with guardrails
    """
    
    def __init__(self):
        # Coffee-related keywords (English + Kikuyu)
        self.coffee_keywords = {
            'en': [
                'coffee', 'kahawa', 'ruiru', 'batian', 'sl28', 'sl34', 'k7',
                'cbd', 'clr', 'rust', 'berry', 'berries', 'cherry', 'cherries',
                'pruning', 'prune', 'harvest', 'picking', 'processing',
                'pulping', 'fermentation', 'drying', 'parchment', 'green bean',
                'arabica', 'robusta', 'factory', 'cooperative', 'auction',
                'grade', 'aa', 'ab', 'pb', 'cupping', 'roasting',
                'shade', 'mulch', 'mulching', 'spacing', 'seedling', 'nursery',
                'grafting', 'flowering', 'blossom'
            ],
            'ki': [
                'kahũa', 'kahua', 'mbegũ', 'mbegu', 'mũtĩ', 'muti',
                'gũceha', 'guceha', 'kũgetha', 'kugetha', 'mũrimũ', 'murimu',
                'mĩthemba', 'mithemba', 'kũhanda', 'kuhanda', 'mboleo',
                'mũceng\'i', 'mucengi', 'nathari', 'factory', 'thoko',
                'mahũa', 'mahua', 'honge', 'mathangũ', 'mathangu'
            ]
        }
        
        # Potato keywords
        self.potato_keywords = {
            'en': ['potato', 'potatoes', 'irish potato', 'tuber', 'spud'],
            'ki': ['waru', 'ciambũrũ']
        }
        
        # Cabbage keywords  
        self.cabbage_keywords = {
            'en': ['cabbage', 'cabbages', 'brassica', 'head cabbage'],
            'ki': ['kabichi', 'kabici']
        }
        
        # Emergency keywords
        self.emergency_keywords = {
            'en': [
                'dying', 'dead', 'all dying', 'emergency', 'help', 'urgent',
                'disaster', 'destroyed', 'lost', 'ruined', 'crisis',
                'what do i do', 'save my'
            ],
            'ki': [
                'kũa', 'kua', 'rakua', 'haraka', 'teithia', 'nĩndeteithie',
                'thĩna mũnene', 'yothe', 'ciothe'
            ]
        }
        
        # Off-topic indicators
        self.off_topic_keywords = [
            'weather forecast', 'politics', 'football', 'music', 'movie',
            'recipe', 'cook coffee', 'make coffee drink', 'boyfriend', 'girlfriend',
            'loan', 'mpesa', 'betting', 'news', 'president', 'election',
            'car', 'phone', 'computer', 'game', 'play'
        ]
        
        # General farming (might redirect)
        self.general_farming_keywords = [
            'maize', 'beans', 'tomato', 'onion', 'sukuma', 'kale',
            'cow', 'goat', 'chicken', 'pig', 'dairy', 'livestock',
            'irrigation', 'borehole', 'tank', 'greenhouse'
        ]
        
        # Coffee sub-categories
        self.coffee_categories = {
            'varieties': ['variety', 'varieties', 'ruiru', 'batian', 'sl28', 'sl34', 'k7', 'mũthemba', 'mithemba', 'which type', 'best type'],
            'planting': ['plant', 'planting', 'seedling', 'nursery', 'spacing', 'hole', 'handa', 'kuhanda', 'nathari'],
            'diseases': ['disease', 'sick', 'cbd', 'rust', 'clr', 'fungus', 'black spot', 'yellow', 'murimu', 'mũrimũ', 'rotten', 'dying'],
            'pests': ['pest', 'insect', 'bug', 'borer', 'antestia', 'mite', 'tutambi', 'tũtambi', 'dudu'],
            'fertilizer': ['fertilizer', 'manure', 'npk', 'can', 'dap', 'foliar', 'mboleo', 'thumu', 'nutrient'],
            'pruning': ['prune', 'pruning', 'cut', 'trim', 'ceha', 'gũceha', 'guceha', 'branch'],
            'harvesting': ['harvest', 'pick', 'picking', 'ripe', 'mature', 'getha', 'kũgetha', 'kugetha', 'ready'],
            'processing': ['process', 'pulp', 'ferment', 'dry', 'wash', 'parchment', 'thondeka', 'gũthondeka'],
            'marketing': ['price', 'sell', 'market', 'auction', 'grade', 'bei', 'thoko', 'gũra', 'factory', 'cooperative'],
            'general_care': ['care', 'maintain', 'grow', 'manage', 'water', 'irrigation', 'menyerera', 'kũmenyerera']
        }
    
    def route_query(self, query: str) -> RoutingResult:
        """
        Analyze query and determine routing
        """
        query_lower = query.lower().strip()
        
        # 1. Check for greeting first
        if self._is_greeting(query_lower):
            return RoutingResult(
                intent=QueryIntent.GREETING,
                confidence=1.0,
                sub_category=None,
                detected_entities=[],
                suggested_action="respond_greeting"
            )
        
        # 2. Check for emergency
        if self._is_emergency(query_lower):
            return RoutingResult(
                intent=QueryIntent.EMERGENCY,
                confidence=0.95,
                sub_category=self._detect_coffee_category(query_lower),
                detected_entities=self._extract_entities(query_lower),
                suggested_action="respond_emergency"
            )
        
        # 3. Check for off-topic
        if self._is_off_topic(query_lower):
            return RoutingResult(
                intent=QueryIntent.OFF_TOPIC,
                confidence=0.9,
                sub_category=None,
                detected_entities=[],
                suggested_action="redirect_politely"
            )
        
        # 4. Check for coffee question
        coffee_score = self._calculate_topic_score(query_lower, 'coffee')
        if coffee_score > 0.3:
            return RoutingResult(
                intent=QueryIntent.COFFEE_QUESTION,
                confidence=min(coffee_score, 1.0),
                sub_category=self._detect_coffee_category(query_lower),
                detected_entities=self._extract_entities(query_lower),
                suggested_action="search_kb"
            )
        
        # 5. Check for potato question
        potato_score = self._calculate_topic_score(query_lower, 'potato')
        if potato_score > 0.3:
            return RoutingResult(
                intent=QueryIntent.POTATO_QUESTION,
                confidence=min(potato_score, 1.0),
                sub_category=None,
                detected_entities=self._extract_entities(query_lower),
                suggested_action="search_kb"
            )
        
        # 6. Check for cabbage question
        cabbage_score = self._calculate_topic_score(query_lower, 'cabbage')
        if cabbage_score > 0.3:
            return RoutingResult(
                intent=QueryIntent.CABBAGE_QUESTION,
                confidence=min(cabbage_score, 1.0),
                sub_category=None,
                detected_entities=self._extract_entities(query_lower),
                suggested_action="search_kb"
            )
        
        # 7. Check for general farming (redirect)
        if self._is_general_farming(query_lower):
            return RoutingResult(
                intent=QueryIntent.GENERAL_FARMING,
                confidence=0.7,
                sub_category=None,
                detected_entities=[],
                suggested_action="redirect_with_suggestion"
            )
        
        # 8. Unclear - but might be coffee related
        # Try to understand context
        return RoutingResult(
            intent=QueryIntent.UNCLEAR,
            confidence=0.3,
            sub_category=None,
            detected_entities=self._extract_entities(query_lower),
            suggested_action="ask_clarification"
        )
    
    def _is_greeting(self, query: str) -> bool:
        """Check if query is a greeting"""
        greeting_patterns = [
            r'^hi\b', r'^hello\b', r'^hey\b', r'^good\s*(morning|afternoon|evening)',
            r'^thayu', r'^thaayu', r'^wĩ\s*mwega', r'^wi\s*mwega',
            r'^ũhoro', r'^uhoro', r'^nĩ\s*wega', r'^ni\s*wega',
            r'^habari', r'^mambo', r'^sasa', r'^niaje'
        ]
        return any(re.match(pattern, query) for pattern in greeting_patterns)
    
    def _is_emergency(self, query: str) -> bool:
        """Check if query indicates emergency"""
        for keywords in self.emergency_keywords.values():
            if any(kw in query for kw in keywords):
                return True
        return False
    
    def _is_off_topic(self, query: str) -> bool:
        """Check if query is off-topic"""
        # Must NOT contain any farming keywords
        all_farming_keywords = (
            self.coffee_keywords['en'] + self.coffee_keywords['ki'] +
            self.potato_keywords['en'] + self.potato_keywords['ki'] +
            self.cabbage_keywords['en'] + self.cabbage_keywords['ki'] +
            self.general_farming_keywords
        )
        
        has_farming_keyword = any(kw in query for kw in all_farming_keywords)
        has_off_topic = any(kw in query for kw in self.off_topic_keywords)
        
        return has_off_topic and not has_farming_keyword
    
    def _is_general_farming(self, query: str) -> bool:
        """Check if about farming but not our crops"""
        return any(kw in query for kw in self.general_farming_keywords)
    
    def _calculate_topic_score(self, query: str, topic: str) -> float:
        """Calculate how likely query is about a topic"""
        if topic == 'coffee':
            keywords = self.coffee_keywords
        elif topic == 'potato':
            keywords = self.potato_keywords
        elif topic == 'cabbage':
            keywords = self.cabbage_keywords
        else:
            return 0.0
        
        all_keywords = keywords['en'] + keywords['ki']
        matches = sum(1 for kw in all_keywords if kw in query)
        
        # Boost for exact topic mention
        if topic in query or (topic == 'coffee' and ('kahũa' in query or 'kahua' in query)):
            matches += 3
        
        # Normalize
        return min(matches / 3.0, 1.0)
    
    def _detect_coffee_category(self, query: str) -> Optional[str]:
        """Detect which coffee sub-category"""
        best_category = None
        best_score = 0
        
        for category, keywords in self.coffee_categories.items():
            score = sum(1 for kw in keywords if kw in query)
            if score > best_score:
                best_score = score
                best_category = category
        
        return best_category
    
    def _extract_entities(self, query: str) -> List[str]:
        """Extract relevant entities from query"""
        entities = []
        
        # Varieties
        varieties = ['ruiru 11', 'ruiru11', 'batian', 'sl28', 'sl 28', 'sl34', 'sl 34', 'k7']
        for v in varieties:
            if v in query:
                entities.append(f"variety:{v}")
        
        # Diseases
        diseases = ['cbd', 'clr', 'rust', 'blight', 'rot']
        for d in diseases:
            if d in query:
                entities.append(f"disease:{d}")
        
        # Plant parts
        parts = ['leaf', 'leaves', 'berry', 'berries', 'root', 'stem', 'branch']
        for p in parts:
            if p in query:
                entities.append(f"part:{p}")
        
        return entities