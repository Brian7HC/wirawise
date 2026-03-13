"""
Knowledge Base module for real Kenya agriculture data.
Uses curated data from reliable sources (FAO, KALRO, Wikipedia, Kenya Meteorology).
"""

import json
import logging
import os
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Singleton knowledge base
_knowledge_base = None


def get_knowledge_base() -> Dict[str, Any]:
    """Get or initialize the knowledge base."""
    global _knowledge_base
    if _knowledge_base is None:
        _knowledge_base = KnowledgeBase()
    return _knowledge_base


class KnowledgeBase:
    """Real Kenya agriculture knowledge base."""
    
    def __init__(self):
        self.data = self._load_data()
        logger.info(f"Knowledge base loaded with {len(self.data.get('crops', {}))} crops")
    
    def _load_data(self) -> Dict[str, Any]:
        """Load knowledge base from JSON file."""
        base_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'data', 'knowledge', 'comprehensive_qa.json'
        )
        
        try:
            with open(base_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"Loaded knowledge base from {base_path}")
                return data
        except FileNotFoundError:
            logger.warning(f"Knowledge base file not found: {base_path}")
            return {"error": "Knowledge base not found"}
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing knowledge base: {e}")
            return {"error": "Invalid knowledge base format"}
    
    def search_coffee_qa(self, query: str, language: str = "en") -> Optional[Dict[str, Any]]:
        """Search the Q&A section for relevant answers."""
        topics = self.data.get('topics', [])
        
        if not topics:
            logger.warning(f"No topics found in knowledge base. Available keys: {list(self.data.keys())}")
            return None
        
        logger.info(f"Searching Q&A with query: '{query[:50]}...' (language: {language})")
        logger.info(f"Number of topics: {len(topics)}")
        
        query_lower = query.lower()
        
        # Search through all topics' Q&A
        best_match = None
        best_match_score = 0
        
        for topic in topics:
            topic_name = topic.get('topic', 'unknown')
            qa_pairs = topic.get('qa_pairs', [])
            
            for qa in qa_pairs:
                question_key = f"question_{language}"
                answer_key = f"answer_{language}"
                
                if question_key not in qa:
                    continue
                    
                question = qa[question_key].lower()
                
                # Check for direct substring match first (exact match gets highest score)
                if query_lower == question:
                    logger.info(f"Exact match found in topic {topic_name}")
                    return {
                        'question': qa.get(question_key, ''),
                        'answer': qa.get(answer_key, ''),
                        'question_ki': qa.get('question_ki', ''),
                        'answer_ki': qa.get('answer_ki', ''),
                        'topic': topic_name
                    }
                
                # Check if query is contained in question or vice versa
                if query_lower in question or question in query_lower:
                    logger.info(f"Substring match found in topic {topic_name}")
                    return {
                        'question': qa.get(question_key, ''),
                        'answer': qa.get(answer_key, ''),
                        'question_ki': qa.get('question_ki', ''),
                        'answer_ki': qa.get('answer_ki', ''),
                        'topic': topic_name
                    }
                
                # Keyword matching - check for significant word overlap
                query_words = set(query_lower.split())
                question_words = set(question.split())
                
                # Filter out very common words
                stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'do', 'does', 'did', 
                             'what', 'which', 'when', 'where', 'how', 'why', 'who', 'and', 'or',
                             'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'it', 'that', 'this'}
                query_words = query_words - stop_words
                question_words = question_words - stop_words
                
                if query_words and question_words:
                    common_words = query_words.intersection(question_words)
                    # Score based on how many significant words match
                    if len(common_words) >= 1:
                        match_score = len(common_words)
                        if match_score > best_match_score:
                            best_match_score = match_score
                            best_match = {
                                'question': qa.get(question_key, ''),
                                'answer': qa.get(answer_key, ''),
                                'question_ki': qa.get('question_ki', ''),
                                'answer_ki': qa.get('answer_ki', ''),
                                'topic': topic_name
                            }
        
        # Return best keyword match if found
        if best_match:
            logger.info(f"Keyword match found with score {best_match_score}")
            return best_match
        
        logger.info("No matching Q&A found")
        return None
    
    def get_crop_info(self, crop_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific crop."""
        crops = self.data.get('crops', {})
        
        # Normalize crop name for matching
        crop_lower = crop_name.lower()
        
        # Direct lookup
        if crop_lower in crops:
            return crops[crop_lower]
        
        # Search in crop names
        for key, value in crops.items():
            if crop_lower in key or key in crop_lower:
                return value
        
        return None
    
    def get_fertilizer_info(self, fertilizer_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific fertilizer."""
        fertilizers = self.data.get('fertilizers', {})
        
        fert_lower = fertilizer_name.lower()
        
        if fert_lower in fertilizers:
            return fertilizers[fert_lower]
        
        for key, value in fertilizers.items():
            if fert_lower in key or key in fert_lower:
                return value
        
        return None
    
    def get_seasonal_activities(self, month: str = None) -> Dict[str, Any]:
        """Get seasonal activities, optionally for a specific month."""
        calendar = self.data.get('seasonal_calendar', {})
        
        if month:
            return calendar.get(month.lower(), {})
        
        return calendar
    
    def get_region_info(self, region: str = None) -> Dict[str, Any]:
        """Get region information."""
        regions = self.data.get('regions', {})
        
        if region:
            region_lower = region.lower()
            for key, value in regions.items():
                if region_lower in key or key in region_lower:
                    return value
            return {}
        
        return regions
    
    def get_sources(self) -> List[Dict[str, Any]]:
        """Get source information."""
        return self.data.get('sources', [])
    
    def search(self, query: str) -> Dict[str, Any]:
        """Search the knowledge base for relevant information."""
        query_lower = query.lower()
        results = {
            'crops': [],
            'fertilizers': [],
            'seasons': [],
            'general': []
        }
        
        # Search crops
        crops = self.data.get('crops', {})
        for crop_key, crop_data in crops.items():
            if any(term in crop_key.lower() or 
                   term in crop_data.get('kikuyu_name', '').lower() or
                   term in crop_data.get('scientific_name', '').lower()
                   for term in query_lower.split()):
                results['crops'].append({crop_key: crop_data})
        
        # Search fertilizers
        fertilizers = self.data.get('fertilizers', {})
        for fert_key, fert_data in fertilizers.items():
            if any(term in fert_key.lower() or 
                   term in fert_data.get('full_name', '').lower()
                   for term in query_lower.split()):
                results['fertilizers'].append({fert_key: fert_data})
        
        # Search general info
        general = self.data.get('farming_practices', {})
        for practice, details in general.items():
            if any(term in practice.lower() or term in str(details).lower()
                   for term in query_lower.split()):
                results['general'].append({practice: details})
        
        return results
    
    def format_crop_response(self, crop_name: str, language: str = "kikuyu") -> str:
        """Format crop information as a response."""
        crop_info = self.get_crop_info(crop_name)
        
        if not crop_info:
            return None
        
        # Build response based on available data
        parts = []
        
        if 'kikuyu_name' in crop_info:
            kikuyu_name = crop_info['kikuyu_name']
            parts.append(f"Crop: {crop_info.get('scientific_name', 'Unknown')} (Kikuyu: {kikuyu_name})")
        
        if 'seasons' in crop_info:
            seasons = crop_info['seasons']
            parts.append(f"Planting seasons: Long rains (March-April), Short rains (October-November)")
        
        if 'fertilizer' in crop_info:
            fert = crop_info['fertilizer']
            parts.append("Recommended fertilizer:")
            for fert_name, rate in fert.items():
                parts.append(f"  - {fert_name}: {rate}")
        
        if 'spacing' in crop_info:
            parts.append(f"Spacing: {crop_info['spacing']}")
        
        if 'maturity' in crop_info:
            parts.append(f"Maturity: {crop_info['maturity']} days")
        
        if 'soil_requirements' in crop_info:
            parts.append(f"Soil: {crop_info['soil_requirements']}")
        
        return "\n".join(parts)
    
    def format_fertilizer_response(self, fertilizer_name: str) -> str:
        """Format fertilizer information as a response."""
        fert_info = self.get_fertilizer_info(fertilizer_name)
        
        if not fert_info:
            return None
        
        parts = []
        
        if 'full_name' in fert_info:
            parts.append(f"Full name: {fert_info['full_name']}")
        
        if 'composition' in fert_info:
            parts.append(f"Composition: {fert_info['composition']}")
        
        if 'use' in fert_info:
            parts.append(f"Use: {fert_info['use']}")
        
        if 'price_range_kes' in fert_info:
            parts.append(f"Price: KES {fert_info['price_range_kes']} per 50kg bag")
        
        if 'application' in fert_info:
            parts.append(f"Application: {fert_info['application']}")
        
        return "\n".join(parts)


def get_crop_info(crop_name: str) -> Optional[Dict[str, Any]]:
    """Convenience function to get crop info."""
    kb = get_knowledge_base()
    return kb.get_crop_info(crop_name)


def get_fertilizer_info(fertilizer_name: str) -> Optional[Dict[str, Any]]:
    """Convenience function to get fertilizer info."""
    kb = get_knowledge_base()
    return kb.get_fertilizer_info(fertilizer_name)


def search_knowledge(query: str) -> Dict[str, Any]:
    """Convenience function to search knowledge base."""
    kb = get_knowledge_base()
    return kb.search(query)


def search_coffee_qa(query: str, language: str = "en") -> Optional[Dict[str, Any]]:
    """Convenience function to search coffee Q&A."""
    kb = get_knowledge_base()
    return kb.search_coffee_qa(query, language)
