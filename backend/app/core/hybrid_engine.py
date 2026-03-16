"""
Hybrid Search Engine
Combines semantic search with keyword matching and intelligent routing
"""

import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from app.core.intelligent_router import IntelligentRouter, QueryIntent
from backend.nlp.semantic_engine import SemanticSearchEngine
from backend.nlp.kb_processor import KnowledgeBaseProcessor


class HybridSearchEngine:
    """
    Hybrid search that combines:
    1. Semantic search (sentence-transformers/TF-IDF)
    2. Keyword/exact match
    3. Intelligent routing for categorization
    4. Fallback mechanisms
    """
    
    def __init__(self, kb_path: str):
        print("🔧 Initializing Hybrid Search Engine...")
        
        # Initialize knowledge base
        self.kb = KnowledgeBaseProcessor(kb_path)
        
        # Initialize semantic search
        self.semantic_search = SemanticSearchEngine(self.kb)
        
        # Initialize intelligent router
        self.router = IntelligentRouter()
        
        # Load additional data for exact matching
        self._load_exact_match_data()
        
        print("✅ Hybrid Search Engine ready!")
    
    def _load_exact_match_data(self):
        """Load data for exact/keyword matching"""
        # Use the knowledge base directly for exact matching
        self.exact_match_data = {}
        
        # Index all QA pairs from the knowledge base processor
        for qa in self.kb.qa_pairs:
            # Index by English question
            self.exact_match_data[qa.question_en.lower()] = qa
            
            # Index by Kikuyu question
            self.exact_match_data[qa.question_ki.lower()] = qa
            
            # Also index key terms from questions for fuzzy matching
            words_en = qa.question_en.lower().split()
            words_ki = qa.question_ki.lower().split()
            
            # Add important words
            important_words = [w for w in words_en if len(w) > 3] + [w for w in words_ki if len(w) > 3]
            for word in important_words:
                if word not in self.exact_match_data:
                    self.exact_match_data[word] = qa
        
        print(f"✅ Indexed {len(self.exact_match_data)} exact match entries")
    
    def search(self, query: str) -> Dict:
        """
        Main search method - returns structured result
        """
        query_lower = query.lower().strip()
        
        # 1. Try exact match first (highest priority)
        exact_result = self._try_exact_match(query_lower)
        if exact_result and exact_result.get('confidence', 0) >= 0.9:
            return exact_result
        
        # 2. Try semantic search
        semantic_result = self._try_semantic_search(query)
        
        # 3. Combine and rank results
        final_result = self._combine_results(exact_result, semantic_result, query)
        
        return final_result
    
    def _try_exact_match(self, query: str) -> Optional[Dict]:
        """Try to find exact match in our indexed data"""
        # Direct lookup
        if query in self.exact_match_data:
            item = self.exact_match_data[query]
            if isinstance(item, list):
                # Multiple matches, pick first (could be improved)
                item = item[0]
            
            return self._format_result(item, query, 0.95, 'exact_match')
        
        # Check if any keyword matches exactly
        words = query.split()
        for word in words:
            if word in self.exact_match_data:
                item = self.exact_match_data[word]
                if isinstance(item, list):
                    item = item[0]  # Take first match
                
                return self._format_result(item, query, 0.8, 'keyword_match')
        
        return None
    
    def _try_semantic_search(self, query: str) -> Dict:
        """Try semantic search"""
        # Get best match from semantic search
        best = self.semantic_search.find_best(query)
        
        if best:
            # Get the full QA object
            qa = self.kb.get_qa_by_id(best['qa_id'])
            if qa:
                return self._format_semantic_result(qa, query, best)
        
        # Return low confidence result if nothing found
        return {
            'success': False,
            'response': "",
            'confidence': 0.0,
            'match_type': 'semantic_search',
            'topic': None
        }
    
    def _combine_results(self, exact_result: Optional[Dict], 
                        semantic_result: Dict, 
                        query: str) -> Dict:
        """Combine and rank results from different search methods"""
        
        # If we have a high confidence exact match, use it
        if exact_result and exact_result.get('confidence', 0) >= 0.9:
            exact_result['match_type'] = 'exact_match'
            return exact_result
        
        # If we have a good semantic result, use it
        if semantic_result.get('confidence', 0) >= 0.5:
            # Boost confidence if it also matches routing
            routing = self.router.route_query(query)
            if routing.confidence > 0.5:
                semantic_result['confidence'] = min(
                    semantic_result['confidence'] + 0.1, 1.0
                )
            
            return semantic_result
        
        # If we have a low confidence exact match, use it over very low semantic
        if exact_result and exact_result.get('confidence', 0) >= 0.6:
            if semantic_result.get('confidence', 0) < 0.4:
                exact_result['match_type'] = 'exact_match'
                return exact_result
        
        # Otherwise return semantic result (even if low confidence)
        return semantic_result
    
    def _format_result(self, item, query: str, confidence: float, 
                      match_type: str) -> Dict:
        """Format result from exact match data (handles both dict and QAPair)"""
        # Determine language based on query
        kikuyu_chars = ['ĩ', 'ũ', 'ī', 'ū', 'ñ', 'Ỳ']
        lang = 'ki' if any(c in query.lower() for c in kikuyu_chars) else 'en'
        
        # Check if item is a QAPair object or a dict
        if hasattr(item, 'question_en'):  # It's a QAPair object
            answer = item.answer_ki if lang == 'ki' else item.answer_en
            topic = getattr(item, 'topic', None)
            matched_question = item.question_ki if lang == 'ki' else item.question_en
            qa_id = getattr(item, 'id', None)
        else:  # It's a dict
            answer_key = f'answer_{lang}'
            if answer_key not in item:
                answer_key = 'answer_en'
            answer = item.get(answer_key, '')
            topic = item.get('category', item.get('topic'))
            matched_question = item.get(f'question_primary_{lang}', 
                                       item.get('question_primary_en', ''))
            qa_id = item.get('id')
        
        return {
            'success': True,
            'response': answer,
            'confidence': confidence,
            'match_type': match_type,
            'topic': topic,
            'matched_question': matched_question,
            'qa_id': qa_id,
            'language': lang,
            'confidence_level': self._get_confidence_level(confidence)
        }
    
    def _format_semantic_result(self, qa_obj, query: str, semantic_result: Dict) -> Dict:
        """Format result from semantic search"""
        # Detect language
        from app.core.production_engine import ProductionCoffeeEngine
        # Simple detection for now
        kikuyu_chars = ['ĩ', 'ũ', 'ī', 'ū', 'ñ', 'Ỳ']
        lang = 'ki' if any(c in query.lower() for c in kikuyu_chars) else 'en'
        
        # Get answer
        answer = qa_obj.answer_ki if lang == 'ki' and hasattr(qa_obj, 'answer_ki') else qa_obj.answer_en
        
        return {
            'success': True,
            'response': answer,
            'confidence': semantic_result.get('score', 0.0),
            'match_type': 'semantic_search',
            'topic': getattr(qa_obj, 'topic', None),
            'matched_question': qa_obj.question_ki if lang == 'ki' else qa_obj.question_en,
            'qa_id': qa_obj.id,
            'language': lang,
            'confidence_level': self._get_confidence_level(semantic_result.get('score', 0.0))
        }
    
    def _get_confidence_level(self, score: float) -> str:
        """Convert numeric score to confidence level"""
        if score >= 0.8:
            return 'high'
        elif score >= 0.6:
            return 'medium'
        elif score >= 0.4:
            return 'low'
        else:
            return 'very_low'
    
    def get_qa_count(self) -> int:
        """Get total number of Q&A pairs"""
        return self.kb.get_qa_count()


# Initialize function for easy startup
def initialize_hybrid_engine(kb_path: str = None) -> HybridSearchEngine:
    """Initialize and return hybrid search engine"""
    if kb_path is None:
        # Default path
        base_dir = Path(__file__).parent.parent.parent
        kb_path = str(base_dir / "data" / "knowledge" / "comprehensive_qa.json")
    
    return HybridSearchEngine(kb_path)