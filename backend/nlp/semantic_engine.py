"""
Semantic Search Engine
Handles embedding generation and semantic matching
Supports both sentence-transformers (primary) and TF-IDF (fallback)
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
import pickle
from pathlib import Path

# Lazy imports for primary method
_model = None
_cosine_sim = None

# Fallback: TF-IDF
_tfidf_vectorizer = None
_tfidf_matrix = None


def _load_dependencies():
    """Load ML dependencies - tries sentence-transformers first"""
    global _model, _cosine_sim
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            from sklearn.metrics.pairwise import cosine_similarity
            _model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
            _cosine_sim = cosine_similarity
            return _model, _cosine_sim, "sentence_transformers"
        except Exception as e:
            print(f"Warning: Could not load sentence-transformers: {e}")
            print("Falling back to TF-IDF semantic search")
            return None, None, "tfidf"
    return _model, _cosine_sim, "sentence_transformers"


class SemanticSearchEngine:
    """Semantic matching for knowledge base"""
    
    def __init__(self, kb_processor, cache_dir: str = "./data/embeddings_cache"):
        self.kb = kb_processor
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Thresholds
        self.high_conf = 0.70
        self.medium_conf = 0.50
        self.low_conf = 0.35
        
        # Method used
        self.method = "sentence_transformers"
        
        # Initialize embeddings
        self._initialize()
    
    def _get_cache_path(self) -> Path:
        return self.cache_dir / 'kb_embeddings.pkl'
    
    def _get_tfidf_cache_path(self) -> Path:
        return self.cache_dir / 'tfidf_embeddings.pkl'
    
    def _initialize(self):
        """Build or load embeddings"""
        # Try sentence-transformers first
        model, cosine_sim, method = _load_dependencies()
        
        if method == "sentence_transformers" and model is not None:
            # Use sentence-transformers
            cache_path = self._get_cache_path()
            
            if cache_path.exists():
                print("Loading sentence-transformer embeddings from cache...")
                self._load_cache()
            else:
                print("Building sentence-transformer embeddings...")
                self._build_embeddings()
                self._save_cache()
            
            self.method = "sentence_transformers"
            print(f"✓ Ready with {len(self.embedding_to_qa)} sentence-transformer embeddings")
        else:
            # Fall back to TF-IDF
            print("Using TF-IDF semantic search")
            self._initialize_tfidf()
    
    def _initialize_tfidf(self):
        """Initialize TF-IDF fallback"""
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        
        cache_path = self._get_tfidf_cache_path()
        
        if cache_path.exists():
            print("Loading TF-IDF from cache...")
            self._load_tfidf_cache()
        else:
            print("Building TF-IDF index...")
            self._build_tfidf_index()
            self._save_tfidf_cache()
        
        self.method = "tfidf"
        print(f"✓ Ready with {len(self.embedding_to_qa)} TF-IDF embeddings")
    
    def _build_tfidf_index(self):
        """Build TF-IDF index"""
        from sklearn.feature_extraction.text import TfidfVectorizer
        
        all_texts = []
        embedding_map = {}
        idx = 0
        
        for qa in self.kb.qa_pairs:
            # English texts
            for text in qa.searchable_en:
                all_texts.append(text)
                embedding_map[idx] = (qa.id, 'en')
                idx += 1
            
            # Kikuyu texts
            for text in qa.searchable_ki:
                all_texts.append(text)
                embedding_map[idx] = (qa.id, 'ki')
                idx += 1
        
        # Create TF-IDF vectorizer with ngrams for better matching
        vectorizer = TfidfVectorizer(
            ngram_range=(1, 3),
            max_features=10000,
            sublinear_tf=True
        )
        
        self.tfidf_matrix = vectorizer.fit_transform(all_texts)
        self.tfidf_vectorizer = vectorizer
        self.texts = all_texts
        self.embedding_to_qa = embedding_map
    
    def _save_tfidf_cache(self):
        """Save TF-IDF to disk"""
        cache_data = {
            'tfidf_matrix': self.tfidf_matrix,
            'texts': self.texts,
            'embedding_to_qa': self.embedding_to_qa,
            'vectorizer_params': self.tfidf_vectorizer.get_params() if self.tfidf_vectorizer else None
        }
        with open(self._get_tfidf_cache_path(), 'wb') as f:
            pickle.dump(cache_data, f)
        print("✓ TF-IDF cached")
    
    def _load_tfidf_cache(self):
        """Load TF-IDF from disk"""
        from sklearn.feature_extraction.text import TfidfVectorizer
        
        with open(self._get_tfidf_cache_path(), 'rb') as f:
            cache_data = pickle.load(f)
        self.tfidf_matrix = cache_data['tfidf_matrix']
        self.texts = cache_data['texts']
        self.embedding_to_qa = cache_data['embedding_to_qa']
        
        # Reconstruct the vectorizer from saved params
        vectorizer_params = cache_data.get('vectorizer_params')
        if vectorizer_params:
            self.tfidf_vectorizer = TfidfVectorizer(**vectorizer_params)
        else:
            # Fallback: recreate with default params
            self.tfidf_vectorizer = TfidfVectorizer(
                ngram_range=(1, 3),
                max_features=10000,
                sublinear_tf=True
            )
    
    def _build_embeddings(self):
        """Generate embeddings using sentence-transformers"""
        model, _ = _load_dependencies()
        
        all_texts = []
        embedding_map = {}
        idx = 0
        
        for qa in self.kb.qa_pairs:
            # English texts
            for text in qa.searchable_en:
                all_texts.append(text)
                embedding_map[idx] = (qa.id, 'en')
                idx += 1
            
            # Kikuyu texts
            for text in qa.searchable_ki:
                all_texts.append(text)
                embedding_map[idx] = (qa.id, 'ki')
                idx += 1
        
        # Generate embeddings
        embeddings = model.encode(all_texts, show_progress_bar=True, convert_to_numpy=True)
        
        self.embeddings = embeddings
        self.texts = all_texts
        self.embedding_to_qa = embedding_map
    
    def _save_cache(self):
        """Save to disk"""
        cache_data = {
            'embeddings': self.embeddings,
            'texts': self.texts,
            'embedding_to_qa': self.embedding_to_qa
        }
        with open(self._get_cache_path(), 'wb') as f:
            pickle.dump(cache_data, f)
        print("✓ Embeddings cached")
    
    def _load_cache(self):
        """Load from disk"""
        with open(self._get_cache_path(), 'rb') as f:
            cache_data = pickle.load(f)
        self.embeddings = cache_data['embeddings']
        self.texts = cache_data['texts']
        self.embedding_to_qa = cache_data['embedding_to_qa']
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search for similar Q&A"""
        
        if self.method == "sentence_transformers":
            return self._search_sentence_transformer(query, top_k)
        else:
            return self._search_tfidf(query, top_k)
    
    def _search_sentence_transformer(self, query: str, top_k: int) -> List[Dict]:
        """Search using sentence-transformers"""
        model, cosine_sim, _ = _load_dependencies()
        
        if model is None:
            return self._search_tfidf(query, top_k)
        
        # Encode query
        query_emb = model.encode([query], convert_to_numpy=True)
        
        # Calculate similarities
        similarities = cosine_sim(query_emb, self.embeddings)[0]
        
        # Get top matches
        top_indices = np.argsort(similarities)[::-1]
        
        results = []
        seen_ids = set()
        
        for idx in top_indices:
            if len(results) >= top_k:
                break
            
            qa_id, lang = self.embedding_to_qa[idx]
            
            if qa_id in seen_ids:
                continue
            seen_ids.add(qa_id)
            
            score = float(similarities[idx])
            qa = self.kb.get_qa_by_id(qa_id)
            
            if qa:
                results.append({
                    'qa_id': qa_id,
                    'score': score,
                    'confidence': self._get_confidence(score),
                    'topic': qa.topic,
                    'question_en': qa.question_en,
                    'question_ki': qa.question_ki,
                    'answer_en': qa.answer_en,
                    'answer_ki': qa.answer_ki,
                    'matched_lang': lang
                })
        
        return results
    
    def _search_tfidf(self, query: str, top_k: int) -> List[Dict]:
        """Search using TF-IDF"""
        from sklearn.metrics.pairwise import cosine_similarity
        
        # Transform query
        query_vec = self.tfidf_vectorizer.transform([query])
        
        # Calculate similarities
        similarities = cosine_similarity(query_vec, self.tfidf_matrix)[0]
        
        # Get top matches
        top_indices = np.argsort(similarities)[::-1]
        
        results = []
        seen_ids = set()
        
        for idx in top_indices:
            if len(results) >= top_k:
                break
            
            qa_id, lang = self.embedding_to_qa[idx]
            
            if qa_id in seen_ids:
                continue
            seen_ids.add(qa_id)
            
            score = float(similarities[idx])
            
            # TF-IDF scores are typically lower, adjust thresholds
            # Map TF-IDF scores to 0-1 range more appropriately
            adjusted_score = min(1.0, score * 1.5)  # Boost scores
            
            qa = self.kb.get_qa_by_id(qa_id)
            
            if qa:
                results.append({
                    'qa_id': qa_id,
                    'score': adjusted_score,
                    'confidence': self._get_confidence(adjusted_score),
                    'topic': qa.topic,
                    'question_en': qa.question_en,
                    'question_ki': qa.question_ki,
                    'answer_en': qa.answer_en,
                    'answer_ki': qa.answer_ki,
                    'matched_lang': lang
                })
        
        return results
    
    def _get_confidence(self, score: float) -> str:
        if score >= self.high_conf:
            return 'high'
        elif score >= self.medium_conf:
            return 'medium'
        elif score >= self.low_conf:
            return 'low'
        return 'very_low'
    
    def find_best(self, query: str) -> Optional[Dict]:
        """Find single best match"""
        results = self.search(query, top_k=1)
        if not results:
            return None
        best = results[0]
        if best['score'] < self.low_conf:
            return None
        return best
    
    def rebuild_index(self):
        """Force rebuild embeddings"""
        # Clear sentence-transformer cache
        cache_path = self._get_cache_path()
        if cache_path.exists():
            cache_path.unlink()
        
        # Clear TF-IDF cache
        tfidf_cache_path = self._get_tfidf_cache_path()
        if tfidf_cache_path.exists():
            tfidf_cache_path.unlink()
        
        # Re-initialize
        self._initialize()
