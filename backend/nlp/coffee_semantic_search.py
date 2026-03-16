"""
Multilingual Coffee Semantic Search - Kikuyu Agriculture Q&A
Supports both English and Kikuyu questions using semantic embeddings.
"""

import json
import os
import numpy as np
from typing import Optional, Tuple

# Global variables for caching
_model = None
_dataset = None
_embeddings_en = None
_embeddings_ki = None


def _load_dependencies():
    """Lazy load dependencies."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        from sklearn.metrics.pairwise import cosine_similarity
        from langdetect import detect
        _model = {
            'embedder': SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"),
            'cosine_similarity': cosine_similarity,
            'detect': detect
        }
    return _model


def _load_dataset():
    """Load the coffee Q&A dataset."""
    global _dataset
    if _dataset is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        data_file = os.path.join(base_dir, "data", "coffee_qa.json")
        with open(data_file, "r", encoding="utf-8") as f:
            _dataset = json.load(f)
    return _dataset


def _build_embeddings():
    """Build embeddings for all dataset questions (both EN and KI)."""
    global _embeddings_en, _embeddings_ki
    
    if _embeddings_en is None:
        model_data = _load_dependencies()
        embedder = model_data['embedder']
        dataset = _load_dataset()
        
        # Get English questions
        questions_en = [item["question_en"] for item in dataset]
        # Get Kikuyu questions  
        questions_ki = [item["question_ki"] for item in dataset]
        
        # Encode both
        _embeddings_en = embedder.encode(questions_en)
        _embeddings_ki = embedder.encode(questions_ki)
    
    return _embeddings_en, _embeddings_ki


def detect_language(text: str) -> str:
    """Detect if input is English or Kikuyu."""
    try:
        model_data = _load_dependencies()
        lang = model_data['detect'](text)
        if lang == 'en':
            return 'en'
        else:
            return 'ki'  # Default to Kikuyu for non-English
    except:
        return 'en'


def search_coffee_question(user_query: str, threshold: float = 0.45) -> Tuple[str, float]:
    """
    Search for the best matching coffee question using semantic similarity.
    Supports both English and Kikuyu input.
    """
    try:
        _load_dependencies()
    except ImportError:
        return "Semantic search not available. Install sentence-transformers.", 0.0
    
    # Detect language
    lang = detect_language(user_query)
    
    # Get embeddings
    model_data = _load_dependencies()
    embedder = model_data['embedder']
    cosine_sim = model_data['cosine_similarity']
    dataset = _load_dataset()
    embeddings_en, embeddings_ki = _build_embeddings()
    
    # Encode user query
    query_embedding = embedder.encode([user_query])
    
    # Compare against ALL KB questions (both languages)
    all_embeddings = np.vstack([embeddings_en, embeddings_ki])
    
    # Compute similarity
    similarities = cosine_sim(query_embedding, all_embeddings)[0]
    
    # Find best match
    best_idx = np.argmax(similarities)
    best_score = float(similarities[best_idx])
    
    # Map index to dataset (first half = English, second half = Kikuyu)
    n = len(dataset)
    if best_idx < n:
        kb_idx = best_idx
        matched_lang = 'en'
    else:
        kb_idx = best_idx - n
        matched_lang = 'ki'
    
    if best_score < threshold:
        if lang == 'ki':
            return "Nĩ mwĩre niũndũ, ndikũmenya kĩũria gĩaku. Geria kũũria ũngĩ.", best_score
        return "I'm sorry, I couldn't find a good answer. Please try rephrasing.", best_score
    
    # Return answer in the user's language
    entry = dataset[kb_idx]
    answer = entry[f"answer_{lang}"] if lang in ['en', 'ki'] else entry["answer_en"]
    
    return answer, best_score


def search_coffee_question_with_context(user_query: str, threshold: float = 0.45) -> dict:
    """
    Search for the best matching coffee question with full context.
    Returns matched question, answer, score, and detected language.
    """
    try:
        _load_dependencies()
    except ImportError:
        return {
            "question": "",
            "answer": "Semantic search not available. Install sentence-transformers.",
            "confidence": 0.0,
            "matched_question": "",
            "language": "en"
        }
    
    # Detect language
    lang = detect_language(user_query)
    
    # Get embeddings
    model_data = _load_dependencies()
    embedder = model_data['embedder']
    cosine_sim = model_data['cosine_similarity']
    dataset = _load_dataset()
    embeddings_en, embeddings_ki = _build_embeddings()
    
    # Encode user query
    query_embedding = embedder.encode([user_query])
    
    # Compare against ALL KB questions
    all_embeddings = np.vstack([embeddings_en, embeddings_ki])
    
    # Compute similarity
    similarities = cosine_sim(query_embedding, all_embeddings)[0]
    
    # Find best match
    best_idx = np.argmax(similarities)
    best_score = float(similarities[best_idx])
    
    # Map index to dataset
    n = len(dataset)
    if best_idx < n:
        kb_idx = best_idx
        matched_lang = 'en'
    else:
        kb_idx = best_idx - n
        matched_lang = 'ki'
    
    if best_score < threshold:
        return {
            "question": user_query,
            "answer": "Nĩ mwĩre niũndũ, ndikũmenya kĩũria gĩaku." if lang == 'ki' else "I'm sorry, I couldn't find a good answer.",
            "confidence": best_score,
            "matched_question": "",
            "language": lang
        }
    
    entry = dataset[kb_idx]
    return {
        "question": user_query,
        "answer": entry[f"answer_{lang}"] if lang in ['en', 'ki'] else entry["answer_en"],
        "confidence": best_score,
        "matched_question": entry[f"question_{matched_lang}"],
        "language": lang
    }


def initialize():
    """Initialize the semantic search (pre-load embeddings)."""
    try:
        _load_dependencies()
        _load_dataset()
        _build_embeddings()
        return True
    except Exception as e:
        print(f"Failed to initialize semantic search: {e}")
        return False


if __name__ == "__main__":
    print("Multilingual Coffee Semantic Search - Test")
    print("=" * 50)
    
    # Initialize
    initialize()
    
    # Test cases
    test_questions = [
        # English
        ("my tomatoes are getting sick what do I do", "en"),
        ("what fertilizer for beans", "en"),
        ("when to plant corn", "en"),
        # Kikuyu
        ("nyanya ciakwa nĩ mũrĩmu", "ki"),
        ("mbembe nĩ haanda rĩ", "ki"),
        ("kahua irabataraga maai", "ki"),
        # Mixed/broken
        ("fertilizer ya mboco ni igana", "sw"),
    ]
    
    for question, expected_lang in test_questions:
        result = search_coffee_question_with_context(question)
        print(f"\nQ: {question}")
        print(f"Detected: {result['language']} (expected: {expected_lang})")
        print(f"Match: {result['matched_question']}")
        print(f"Answer: {result['answer'][:80]}...")
        print(f"Confidence: {result['confidence']:.2f}")
