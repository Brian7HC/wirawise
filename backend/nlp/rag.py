"""
Agriculture Knowledge Search using RAG (Retrieval-Augmented Generation)
Uses FAISS vector database with Sentence Transformers embeddings.
"""

from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import json
import logging
import os
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Configuration
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384  # all-MiniLM-L6-v2 outputs 384-dimensional embeddings

# Singleton instances
_embed_model = None
_faiss_index = None
_documents = None
_document_metadata = None


def _get_default_agriculture_data() -> List[Dict]:
    """Get default agriculture knowledge base if no data file exists."""
    return [
        # Maize/Corn farming
        {"text": "Maize should be planted at the start of the rainy season, typically between March and May in Kenya.", "category": "planting", "crop": "maize"},
        {"text": "Maize requires well-drained fertile soils with a pH of 5.5 to 7.0 for optimal growth.", "category": "soil", "crop": "maize"},
        {"text": "The recommended spacing for maize planting is 75cm between rows and 25cm between plants.", "category": "planting", "crop": "maize"},
        {"text": "Fall armyworm is a major pest that attacks maize leaves and can cause significant yield loss if not controlled.", "category": "pests", "crop": "maize"},
        {"text": "Maize varieties suitable for Kenya include H614, H626, H517, and SC tembo.", "category": "varieties", "crop": "maize"},
        {"text": "Apply DAP fertilizer at planting at a rate of 50-60 kg per acre for optimal maize yield.", "category": "fertilizer", "crop": "maize"},
        {"text": "Maize is ready for harvest 4-5 months after planting when the grains are hard and moisture content is below 15%.", "category": "harvest", "crop": "maize"},
        
        # Beans farming
        {"text": "Beans should be planted at the beginning of the rainy season at a spacing of 50cm between rows.", "category": "planting", "crop": "beans"},
        {"text": "Beans require well-drained soil and do not tolerate waterlogging.", "category": "soil", "crop": "beans"},
        {"text": "Common bean varieties in Kenya include Rosecoco, Canadian Wonder, and Mwezi Moja.", "category": "varieties", "crop": "beans"},
        {"text": "Beans fix nitrogen in the soil, improving fertility for subsequent crops like maize.", "category": "soil", "crop": "beans"},
        {"text": " Aphids and bean fly are common pests that attack bean plants.", "category": "pests", "crop": "beans"},
        
        # Tomatoes
        {"text": "Tomatoes require warm temperatures between 20-30°C and full sunlight for optimal production.", "category": "climate", "crop": "tomatoes"},
        {"text": "Tomatoes should be transplanted 6-8 weeks after sowing in the nursery.", "category": "planting", "crop": "tomatoes"},
        {"text": "Recommended tomato spacing is 60cm between rows and 45cm between plants.", "category": "planting", "crop": "tomatoes"},
        {"text": "Tomato blight is a fungal disease that causes brown spots on leaves and fruit rot.", "category": "diseases", "crop": "tomatoes"},
        {"text": "Stake tomato plants to support growth and improve fruit quality.", "category": "planting", "crop": "tomatoes"},
        
        # General farming practices
        {"text": "Crop rotation helps prevent soil depletion and reduces pest and disease buildup.", "category": "general", "crop": "general"},
        {"text": "Composting improves soil structure, water retention, and provides nutrients to crops.", "category": "soil", "crop": "general"},
        {"text": "Integrated pest management combines biological, cultural, and chemical methods for sustainable pest control.", "category": "pests", "crop": "general"},
        {"text": "Mulching helps conserve soil moisture and suppress weed growth.", "category": "general", "crop": "general"},
        {"text": "Drip irrigation is the most efficient method of watering crops, reducing water usage by up to 60%.", "category": "irrigation", "crop": "general"},
        
        # Soil and fertilizer
        {"text": "NPK fertilizer provides nitrogen, phosphorus, and potassium essential for plant growth.", "category": "fertilizer", "crop": "general"},
        {"text": "Soil testing helps determine pH levels and nutrient deficiencies for proper fertilizer application.", "category": "soil", "crop": "general"},
        {"text": "Organic fertilizers like manure improve soil structure and microbial activity.", "category": "fertilizer", "crop": "general"},
        {"text": "Lime can be applied to acidic soils to raise pH levels for better crop growth.", "category": "soil", "crop": "general"},
        
        # Weather and climate
        {"text": "The long rains in Kenya typically occur from March to May.", "category": "climate", "crop": "general"},
        {"text": "Short rains in Kenya occur from October to December.", "category": "climate", "crop": "general"},
        {"text": "Drought-resistant crop varieties are recommended for areas with irregular rainfall.", "category": "varieties", "crop": "general"},
        
        # Livestock
        {"text": "Zero grazing dairy farming involves keeping cattle in stalls and feeding them cultivated fodder.", "category": "livestock", "crop": "general"},
        {"text": "Vaccinate livestock regularly against common diseases like foot and mouth and anthrax.", "category": "livestock", "crop": "general"},
        
        # Sweet potatoes (Waru)
        {"text": "Sweet potatoes (waru) should be planted at the beginning of the rainy season.", "category": "planting", "crop": "sweet_potatoes"},
        {"text": "Sweet potatoes (waru) mature in 3-5 months depending on the variety.", "category": "harvest", "crop": "sweet_potatoes"},
        {"text": "Sweet potatoes (waru) prefer well-drained sandy loam soils.", "category": "soil", "crop": "sweet_potatoes"},
        {"text": "Weevils and aphids are common pests that attack sweet potatoes (waru).", "category": "pests", "crop": "sweet_potatoes"},
        {"text": "Store sweet potatoes (waru) in a cool, dry place to prevent rotting.", "category": "harvest", "crop": "sweet_potatoes"},
        {"text": "Sweet potatoes (waru) are rich in vitamin A and provide good nutrition.", "category": "general", "crop": "sweet_potatoes"},
        
        # Market and post-harvest
        {"text": "Proper storage of harvested grains prevents aflatoxin contamination and pest damage.", "category": "harvest", "crop": "general"},
        {"text": "Value addition through processing increases product value and farmer income.", "category": "general", "crop": "general"},
    ]


def load_agriculture_data(data_path: Optional[str] = None) -> List[Dict]:
    """Load agriculture knowledge data from JSON file or use defaults."""
    if data_path and os.path.exists(data_path):
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"Loaded {len(data)} documents from {data_path}")
            return data
        except Exception as e:
            logger.warning(f"Failed to load data from {data_path}: {e}")
    
    # Use default data
    logger.info("Using default agriculture knowledge base")
    return _get_default_agriculture_data()


def initialize_rag(data_path: Optional[str] = None):
    """
    Initialize the RAG system by loading documents and creating FAISS index.
    
    Args:
        data_path: Optional path to custom agriculture data JSON file
    """
    global _embed_model, _faiss_index, _documents, _document_metadata
    
    if _faiss_index is not None:
        logger.info("RAG system already initialized")
        return
    
    logger.info("Initializing RAG system...")
    
    # Load embedding model
    logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
    _embed_model = SentenceTransformer(EMBEDDING_MODEL)
    
    # Load documents
    documents_data = load_agriculture_data(data_path)
    _documents = [item["text"] for item in documents_data]
    _document_metadata = documents_data
    
    # Generate embeddings
    logger.info(f"Generating embeddings for {len(_documents)} documents...")
    embeddings = _embed_model.encode(_documents, show_progress_bar=True)
    
    # Create FAISS index
    logger.info(f"Creating FAISS index with {EMBEDDING_DIMENSION} dimensions")
    _faiss_index = faiss.IndexFlatL2(EMBEDDING_DIMENSION)
    _faiss_index.add(embeddings.astype('float32'))
    
    logger.info(f"✅ RAG system initialized with {len(_documents)} documents")


def get_embed_model():
    """Get or initialize the embedding model."""
    global _embed_model
    if _embed_model is None:
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
        _embed_model = SentenceTransformer(EMBEDDING_MODEL)
    return _embed_model


def get_faiss_index():
    """Get or initialize the FAISS index."""
    global _faiss_index
    if _faiss_index is None:
        initialize_rag()
    return _faiss_index


def search_docs(query: str, top_k: int = 5) -> List[Dict]:
    """
    Search agriculture knowledge base for relevant documents.
    
    Args:
        query: Search query text
        top_k: Number of results to return
        
    Returns:
        List of relevant document dictionaries with text and metadata
    """
    global _documents, _document_metadata, _faiss_index
    
    if _faiss_index is None:
        initialize_rag()
    
    try:
        embed_model = get_embed_model()
        
        # Encode query
        query_vec = embed_model.encode([query])
        
        # Search index
        D, I = _faiss_index.search(query_vec.astype('float32'), k=min(top_k, len(_documents)))
        
        # Return results with metadata
        results = []
        for idx in I[0]:
            if idx < len(_document_metadata):
                result = {
                    "text": _documents[idx],
                    "category": _document_metadata[idx].get("category", "general"),
                    "crop": _document_metadata[idx].get("crop", "general"),
                    "score": float(D[0][list(I[0]).index(idx)])
                }
                results.append(result)
        
        logger.debug(f"Search for '{query[:50]}...' returned {len(results)} results")
        return results
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        return []


def search_by_category(category: str, crop: Optional[str] = None, top_k: int = 10) -> List[Dict]:
    """
    Search documents by category and optionally by crop type.
    
    Args:
        category: Category to filter (planting, pests, diseases, fertilizer, etc.)
        crop: Optional crop type to filter (maize, beans, tomatoes, etc.)
        top_k: Maximum number of results
        
    Returns:
        List of matching documents
    """
    global _document_metadata, _documents
    
    if _document_metadata is None:
        initialize_rag()
    
    results = []
    for i, doc in enumerate(_document_metadata):
        # Check category match
        if doc.get("category", "").lower() != category.lower():
            continue
        
        # Check crop match if specified
        if crop and doc.get("crop", "").lower() != crop.lower():
            continue
        
        results.append({
            "text": _documents[i],
            "category": doc.get("category", "general"),
            "crop": doc.get("crop", "general"),
            "index": i
        })
        
        if len(results) >= top_k:
            break
    
    return results


# Convenience function for easier imports
search_agriculture = search_docs
