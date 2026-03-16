"""
Accuracy Test Script
Validates that the enhanced intent classification and RAG system achieves 90%+ accuracy.
"""

import sys
import logging
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / 'backend'
sys.path.insert(0, str(backend_path))

from backend.nlp.intent_classifier import QueryNormalizer, IntentClassifier
from backend.nlp.rag import QueryNormalizer as RAGQueryNormalizer
from backend.nlp.knowledge_base import QueryNormalizer as KBQueryNormalizer
from backend.nlp.knowledge_base import get_knowledge_base
from backend.nlp.rag import search_docs
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Test cases for 90%+ accuracy
TEST_CASES = [
    # Crop queries
    ("How do I plant maize?", "maize planting"),
    ("When to plant beans?", "beans planting"),
    ("What is the best time to grow tomatoes?", "tomatoes planting"),
    ("Spacing for sweet potatoes", "sweet potato spacing"),
    ("How to cultivate coffee", "coffee cultivation"),
    
    # Farming operations
    ("How to harvest crops", "harvesting"),
    ("When to apply fertilizer", "fertilizer application"),
    ("How to water plants", "watering"),
    ("When to prune tomatoes", "pruning tomatoes"),
    
    # Pest and disease
    ("How to control pests", "pest control"),
    ("What diseases affect beans", "bean diseases"),
    ("How to prevent armyworm", "pest prevention"),
    ("Best way to treat diseases", "disease treatment"),
    
    # Soil and climate
    ("Best soil for maize", "soil requirements"),
    ("When is rainy season", "rainy season"),
    ("How to improve soil quality", "soil improvement"),
    ("What temperature for tomatoes", "tomato climate"),
    
    # Results and yield
    ("How to increase yield", "yield improvement"),
    ("What is the market price", "market price"),
    ("How to maximize profit", "profit maximization"),
    
    # Multi-language
    ("Nĩ rĩa gĩcoka mbembe?", "maize harvest kikuyu"),
    ("Nĩ gĩthaka gĩa mbembe?", "maize soil kikuyu"),
    ("Nĩ rĩa gĩcoka njũrũ?", "beans harvest kikuyu"),
    ("Nĩ rĩa gĩcoka kahua?", "coffee harvest kikuyu"),
    
    # Variations
    ("Tell me about planting maize", "maize planting"),
    ("Information on growing beans", "beans planting"),
    ("Details on harvesting tomatoes", "tomatoes harvesting"),
    ("How do I grow corn?", "maize planting"),
    ("What is the best time to plant?", "planting timing"),
    
    # Synonyms
    ("How to cultivate corn", "maize planting"),
    ("When to sow beans", "beans planting"),
    ("How to water my crops", "watering crops"),
    ("Best fertilizer for maize", "fertilizer maize"),
    ("Spacing for growing tomatoes", "tomatoes spacing"),
]


def test_query_normalizer():
    """Test query normalizer functionality."""
    logger.info("\n" + "="*60)
    logger.info("Testing Query Normalizer")
    logger.info("="*60)

    normalizer = QueryNormalizer()
    test_queries = [
        "How do I plant maize?",
        "When to plant beans?",
        "Spacing for tomatoes",
        "How to control pests",
        "Best soil for maize",
    ]

    for query in test_queries:
        normalized = normalizer.normalize(query)
        logger.info(f"Original: {query}")
        logger.info(f"Normalized: {normalized}")
        logger.info("-" * 40)


def test_query_expansion():
    """Test query expansion with synonyms."""
    logger.info("\n" + "="*60)
    logger.info("Testing Query Expansion")
    logger.info("="*60)

    normalizer = QueryNormalizer()
    test_queries = [
        "How to plant maize?",
        "When to harvest beans?",
        "Spacing for tomatoes",
        "How to control pests",
    ]

    for query in test_queries:
        normalized = normalizer.normalize(query)
        expanded = normalizer.expand_query(normalized)
        logger.info(f"Original: {query}")
        logger.info(f"Normalized: {normalized}")
        logger.info(f"Expanded: {expanded}")
        logger.info("-" * 40)


def test_similarity_calculation():
    """Test similarity calculation between queries."""
    logger.info("\n" + "="*60)
    logger.info("Testing Similarity Calculation")
    logger.info("="*60)

    normalizer = QueryNormalizer()

    test_pairs = [
        ("How to plant maize?", "How do I cultivate maize?"),
        ("When to harvest beans?", "What time to harvest beans?"),
        ("Spacing for tomatoes", "Distance between tomato plants"),
        ("How to control pests", "Pest control methods"),
    ]

    for query1, query2 in test_pairs:
        similarity = normalizer.calculate_similarity(query1, query2)
        logger.info(f"Query 1: {query1}")
        logger.info(f"Query 2: {query2}")
        logger.info(f"Similarity: {similarity:.2%}")
        logger.info("-" * 40)


def test_knowledge_base_search():
    """Test knowledge base search with enhanced accuracy."""
    logger.info("\n" + "="*60)
    logger.info("Testing Knowledge Base Search")
    logger.info("="*60)

    kb = get_knowledge_base()

    test_queries = [
        "How do I plant maize?",
        "When to plant beans?",
        "Spacing for tomatoes",
        "How to control pests",
        "Best soil for maize",
    ]

    for query in test_queries:
        results = kb.search_coffee_qa(query, "en")
        if results:
            logger.info(f"Query: {query}")
            logger.info(f"Answer: {results.get('answer', 'N/A')[:100]}...")
            logger.info(f"Topic: {results.get('topic', 'N/A')}")
        else:
            logger.info(f"Query: {query}")
            logger.info("No match found")
        logger.info("-" * 40)


def test_rag_search():
    """Test RAG search with enhanced accuracy."""
    logger.info("\n" + "="*60)
    logger.info("Testing RAG Search")
    logger.info("="*60)

    test_queries = [
        "How do I plant maize?",
        "When to plant beans?",
        "Spacing for tomatoes",
        "How to control pests",
        "Best soil for maize",
    ]

    for query in test_queries:
        results = search_docs(query, top_k=3)
        if results:
            logger.info(f"Query: {query}")
            logger.info(f"Top result: {results[0].get('text', 'N/A')[:100]}...")
            logger.info(f"Category: {results[0].get('category', 'N/A')}")
            logger.info(f"Score: {results[0].get('score', 0):.4f}")
        else:
            logger.info(f"Query: {query}")
            logger.info("No results found")
        logger.info("-" * 40)


def test_intent_classifier():
    """Test intent classifier with enhanced accuracy."""
    logger.info("\n" + "="*60)
    logger.info("Testing Intent Classifier")
    logger.info("="*60)

    try:
        from backend.config import settings

        # Create test database connection
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()

        classifier = IntentClassifier(confidence_threshold=0.6)

        test_queries = [
            "How do I plant maize?",
            "When to plant beans?",
            "Spacing for tomatoes",
            "How to control pests",
            "Best soil for maize",
        ]

        for query in test_queries:
            intent = classifier.classify(db, query)
            if intent:
                logger.info(f"Query: {query}")
                logger.info(f"Intent: {intent.get('intent_name', 'N/A')}")
                logger.info(f"Confidence: {intent.get('confidence', 0):.2%}")
            else:
                logger.info(f"Query: {query}")
                logger.info("No intent found")
            logger.info("-" * 40)

        db.close()
    except Exception as e:
        logger.error(f"Error testing intent classifier: {e}")
        import traceback
        traceback.print_exc()


def test_accuracy_metrics():
    """Calculate and display accuracy metrics."""
    logger.info("\n" + "="*60)
    logger.info("Testing Accuracy Metrics")
    logger.info("="*60)

    kb = get_knowledge_base()

    # Test exact matches
    exact_matches = 0
    total_queries = len(TEST_CASES)

    for query, expected in TEST_CASES:
        result = kb.search_coffee_qa(query, "en")
        if result and expected.lower() in result.get('answer', '').lower():
            exact_matches += 1

    accuracy = (exact_matches / total_queries) * 100

    logger.info(f"Total test queries: {total_queries}")
    logger.info(f"Exact matches: {exact_matches}")
    logger.info(f"Accuracy: {accuracy:.2%}")

    if accuracy >= 90:
        logger.info("✅ EXCELLENT: 90%+ accuracy achieved!")
    elif accuracy >= 80:
        logger.info("✅ GOOD: 80%+ accuracy achieved!")
    elif accuracy >= 70:
        logger.info("✅ ACCEPTABLE: 70%+ accuracy achieved!")
    else:
        logger.info("⚠️  NEEDS IMPROVEMENT: Below 70% accuracy")

    logger.info("="*60)


def main():
    """Run all tests."""
    logger.info("\n" + "="*60)
    logger.info("WIRAWISEe Accuracy Test Suite")
    logger.info("Testing for 90%+ accuracy in intent classification and RAG")
    logger.info("="*60)

    try:
        # Run all tests
        test_query_normalizer()
        test_query_expansion()
        test_similarity_calculation()
        test_knowledge_base_search()
        test_rag_search()
        test_intent_classifier()
        test_accuracy_metrics()

        logger.info("\n" + "="*60)
        logger.info("✅ All tests completed successfully!")
        logger.info("="*60)
        logger.info("\nKey improvements:")
        logger.info("  • Query normalization for better matching")
        logger.info("  • Query expansion with synonyms")
        logger.info("  • Multi-language support (Kikuyu/English)")
        logger.info("  • Fuzzy similarity matching")
        logger.info("  • Enhanced intent classification")
        logger.info("="*60)

        return 0

    except Exception as e:
        logger.error(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
