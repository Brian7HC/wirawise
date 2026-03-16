"""Knowledge Base module for Kenya agriculture data."""

from backend.nlp.language_utils import normalize_text_for_matching
import json
import logging
import os
from typing import Dict, Any, List, Optional
from difflib import SequenceMatcher
import string
import re

logger = logging.getLogger(__name__)


class QueryNormalizer:
    """Query normalizer for enhanced matching accuracy."""

    SYNONYMS = {
        'maize': ['corn', 'mbembe', 'ĩrĩa', 'mabembe', 'maize (corn)'],
        'beans': ['beans', 'njũrũ', 'njuru', 'beans (njuru)'],
        'tomatoes': ['tomatoes', 'tomato', 'tomato'],
        'sweet potato': ['sweet potato', 'waru', 'waru (sweet potato)'],
        'coffee': ['coffee', 'kahua', 'kahūa'],
        'crops': ['crops', 'plants', 'ĩrĩa', 'mbembe', 'mabembe'],
        'planting': ['planting', 'ngĩgũra', 'ngũgũra', 'planting (ngĩgũra)'],
        'harvest': ['harvest', 'ngethereka', 'ngwacoka', 'harvest (ngethereka)'],
        'soil': ['soil', 'gĩthaka', 'thambi', 'soil (gĩthaka)'],
        'fertilizer': ['fertilizer', 'boro', 'mboro', 'fertilizer (boro)'],
        'rain': ['rain', 'mbura', 'rain (mbura)'],
        'season': ['season', 'thambi', 'season (thambi)'],
        'water': ['water', 'mũthũngũri', 'water (mũthũngũri)'],
        'pests': ['pests', 'nyĩrĩ', 'pest control', 'pests (nyĩrĩ)'],
        'diseases': ['diseases', 'irĩa cia gũthiira', 'disease control', 'diseases (irĩa cia gũthiira)'],
        'weather': ['weather', 'mũtĩrĩri', 'weather (mũtĩrĩri)'],
        'price': ['price', 'rĩa gĩcoka', 'price (rĩa gĩcoka)'],
        'market': ['market', 'rĩa gĩcoka', 'market (rĩa gĩcoka)'],
        'yield': ['yield', 'rĩa gĩcoka', 'yield (rĩa gĩcoka)'],
        'grow': ['grow', 'ngĩgũra', 'ngũgũra', 'grow (ngĩgũra)'],
        'cultivate': ['cultivate', 'ngĩgũra', 'ngũgũra', 'cultivate (ngĩgũra)'],
    }

    @staticmethod
    def normalize(text: str) -> str:
        """Normalize text for better matching."""
        if not text:
            return ""

        text = text.lower().strip()
        text = text.translate(str.maketrans('', '', string.punctuation))
        text = re.sub(r'\s+', ' ', text)

        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'is', 'are', 'was', 'were',
                      'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
                      'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can',
                      'of', 'to', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as',
                      'it', 'its', 'this', 'that', 'these', 'those', 'i', 'you', 'he',
                      'she', 'we', 'they', 'what', 'which', 'who', 'whom', 'when', 'where',
                      'how', 'why', 'all', 'any', 'both', 'each', 'few', 'more', 'most',
                      'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same',
                      'so', 'than', 'too', 'very', 'just', 'now', 'then', 'also', 'get'}

        words = text.split()
        filtered_words = [w for w in words if w not in stop_words and len(w) > 2]

        return ' '.join(filtered_words)

    @staticmethod
    def expand_query(query: str) -> List[str]:
        """Expand query with synonyms and related terms."""
        if not query:
            return [query]

        normalized_query = QueryNormalizer.normalize(query)
        expanded_queries = [normalized_query]

        words = normalized_query.split()
        for word in words:
            if word in QueryNormalizer.SYNONYMS:
                for synonym in QueryNormalizer.SYNONYMS[word]:
                    expanded_query = normalized_query.replace(word, synonym)
                    if expanded_query not in expanded_queries:
                        expanded_queries.append(expanded_query)

        return expanded_queries

    @staticmethod
    def calculate_similarity(text1: str, text2: str) -> float:
        """Calculate similarity between two texts."""
        if not text1 or not text2:
            return 0.0

        seq_similarity = SequenceMatcher(None, text1, text2).ratio()

        words1 = set(text1.split())
        words2 = set(text2.split())
        if words1 or words2:
            overlap = len(words1 & words2) / max(len(words1), len(words2))
        else:
            overlap = 0.0

        if words1 and words2:
            jaccard = len(words1 & words2) / len(words1 | words2)
        else:
            jaccard = 0.0

        similarity = 0.4 * seq_similarity + 0.3 * overlap + 0.3 * jaccard

        return similarity

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
        """
        Search the Q&A section for relevant answers with enhanced accuracy.
        Priority: Exact match > Fuzzy match > Substring match > Keyword match

        Args:
            query: Search query
            language: Language of query ("en" or "ki")

        Returns:
            Dictionary with question, answer, and topic or None
        """
        topics = self.data.get('topics', [])

        if not topics:
            logger.warning(f"No topics found in knowledge base. Available keys: {list(self.data.keys())}")
            return None

        logger.info(f"Searching Q&A with query: '{query[:50]}...' (language: {language})")
        logger.info(f"Number of topics: {len(topics)}")

        # Detect primary topic from query
        query_lower = query.lower()
        topic_boost = {}
        
        # Define topic keywords for each crop
        topic_keywords = {
            'coffee': ['coffee', 'kahua', 'kahūa', 'café'],
            'potato': ['potato', 'waru', 'irio', 'chips'],
            'cabbage': ['cabbage', 'kabichi', 'mboga', 'greens']
        }
        
        # Detect which topic the query is about
        for topic_name, keywords in topic_keywords.items():
            for keyword in keywords:
                if keyword in query_lower:
                    topic_boost[topic_name] = topic_boost.get(topic_name, 0) + 2
                    break
        
        logger.info(f"Detected topic boost: {topic_boost}")

        # Normalize query for exact/fuzzy matching
        normalized_query = self._normalize_for_matching(query)
        logger.info(f"Normalized query: {normalized_query}")

        # Build flat list of all Q&A pairs
        all_qa_pairs = []
        for topic in topics:
            topic_name = topic.get('topic', 'unknown').lower()
            for qa in topic.get('qa_pairs', []):
                all_qa_pairs.append({
                    'topic': topic_name,
                    'qa': qa
                })

        # ==== PRIORITY 1: EXACT MATCH (after normalization) ====
        for item in all_qa_pairs:
            qa = item['qa']
            question_key = f"question_{language}"
            
            if question_key not in qa:
                continue
            
            kb_question_normalized = self._normalize_for_matching(qa[question_key])
            
            if normalized_query == kb_question_normalized:
                answer_key = f"answer_{language}"
                logger.info(f"EXACT MATCH found: {qa[question_key][:50]}...")
                return {
                    'question': qa.get(question_key, ''),
                    'answer': qa.get(answer_key, ''),
                    'question_ki': qa.get('question_ki', ''),
                    'answer_ki': qa.get('answer_ki', ''),
                    'topic': item['topic']
                }

        # ==== PRIORITY 2: FUZZY MATCH (85%+ similarity) ====
        best_fuzzy_match = None
        best_fuzzy_score = 0
        
        for item in all_qa_pairs:
            qa = item['qa']
            question_key = f"question_{language}"
            
            if question_key not in qa:
                continue
            
            kb_question_normalized = self._normalize_for_matching(qa[question_key])
            
            # Calculate fuzzy similarity
            similarity = SequenceMatcher(None, normalized_query, kb_question_normalized).ratio()
            
            if similarity >= 0.80:  # 80% threshold for fuzzy match
                # Detect topic from the KB question content itself, not just the section
                kb_question_text = qa[question_key].lower()
                content_topic = self._detect_topic_from_text(kb_question_text)
                
                # Use content-based topic for boost, fallback to section topic
                effective_topic = content_topic if content_topic else item['topic']
                topic_bonus = topic_boost.get(effective_topic, 0) * 3
                
                score = (similarity * 10) + topic_bonus
                
                if score > best_fuzzy_score:
                    best_fuzzy_score = score
                    answer_key = f"answer_{language}"
                    best_fuzzy_match = {
                        'question': qa.get(question_key, ''),
                        'answer': qa.get(answer_key, ''),
                        'question_ki': qa.get('question_ki', ''),
                        'answer_ki': qa.get('answer_ki', ''),
                        'topic': effective_topic,
                        'confidence': similarity
                    }
                    logger.info(f"FUZZY MATCH (score={similarity:.2f}, content_topic={content_topic}, topic_bonus={topic_bonus}): {qa[question_key][:50]}...")
        
        if best_fuzzy_match:
            return best_fuzzy_match
    
    def _detect_topic_from_text(self, text: str) -> Optional[str]:
        """Detect topic from text content, independent of JSON section."""
        text_lower = text.lower()
        
        # Coffee keywords in both English and Kikuyu
        coffee_keywords = ['coffee', 'kahua', 'kahūa', 'café']
        
        # Potato keywords
        potato_keywords = ['potato', 'waru', 'irio', 'chips', 'irish']
        
        # Cabbage keywords  
        cabbage_keywords = ['cabbage', 'kabichi', 'mboga', 'greens']
        
        for kw in coffee_keywords:
            if kw in text_lower:
                return 'coffee'
        
        for kw in potato_keywords:
            if kw in text_lower:
                return 'potato'
        
        for kw in cabbage_keywords:
            if kw in text_lower:
                return 'cabbage'
        
        return None

        # ==== PRIORITY 3: SUBSTRING MATCH ====
        for item in all_qa_pairs:
            qa = item['qa']
            question_key = f"question_{language}"
            
            if question_key not in qa:
                continue
            
            question = qa[question_key].lower()
            
            # Check if query is contained in question or vice versa
            if normalized_query in question or question in normalized_query:
                answer_key = f"answer_{language}"
                score = 5  # Good score for substring match
                score += topic_boost.get(item['topic'], 0)
                
                logger.info(f"SUBSTRING MATCH in topic {item['topic']}")
                return {
                    'question': qa.get(question_key, ''),
                    'answer': qa.get(answer_key, ''),
                    'question_ki': qa.get('question_ki', ''),
                    'answer_ki': qa.get('answer_ki', ''),
                    'topic': item['topic']
                }

        # ==== PRIORITY 4: KEYWORD MATCH ====
        best_match = None
        best_match_score = 0
        best_match_topic = None

        # Normalize and expand query
        expanded_queries = QueryNormalizer.expand_query(QueryNormalizer.normalize(query))

        for expanded_query in expanded_queries:
            query_words = set(expanded_query.lower().split())

            for item in all_qa_pairs:
                qa = item['qa']
                question_key = f"question_{language}"
                answer_key = f"answer_{language}"

                if question_key not in qa:
                    continue

                question = qa[question_key].lower()
                question_words = set(question.split())

                # Filter out very common words
                stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'do', 'does', 'did',
                             'what', 'which', 'when', 'where', 'how', 'why', 'who', 'and', 'or',
                             'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'it', 'that', 'this'}
                query_words_filtered = query_words - stop_words
                question_words_filtered = question_words - stop_words

                if query_words_filtered and question_words_filtered:
                    common_words = query_words_filtered.intersection(question_words_filtered)
                    if len(common_words) >= 1:
                        match_score = len(common_words)
                        match_score += topic_boost.get(item['topic'], 0)
                        
                        if match_score > best_match_score:
                            best_match_score = match_score
                            best_match_topic = item['topic']
                            best_match = {
                                'question': qa.get(question_key, ''),
                                'answer': qa.get(answer_key, ''),
                                'question_ki': qa.get('question_ki', ''),
                                'answer_ki': qa.get('answer_ki', ''),
                                'topic': item['topic']
                            }

        # Return best keyword match if found
        if best_match:
            logger.info(f"Keyword match found with score {best_match_score} in topic {best_match_topic}")
            return best_match

        logger.info("No matching Q&A found")
        return None
    
    def _normalize_for_matching(self, text: str) -> str:
        """Normalize text for exact/fuzzy matching - handles Kikuyu diacritics."""
        return normalize_text_for_matching(text)
    
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
