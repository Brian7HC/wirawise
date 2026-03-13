#!/usr/bin/env python3
"""
Seed script to add agriculture intent patterns to the database.
Run this after the main greeting seeds to add farming question detection.
"""

import json
import os
import sys

# Add parent directory to path - use absolute path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import text
from backend.database.connection import get_db


def normalize_text(text: str) -> str:
    """Normalize Kikuyu text for matching."""
    text = text.lower().strip()
    replacements = {
        'ĩ': 'i', 'ũ': 'u', 'í': 'i', 'ú': 'u',
        'ē': 'e', 'ã': 'a', 'á': 'a', 'ĕ': 'e'
    }
    for kikuyu_char, basic_char in replacements.items():
        text = text.replace(kikuyu_char, basic_char)
    return text


def seed_agriculture_intents(db):
    """Add agriculture intent and patterns to database."""
    
    # Load agriculture intent data - use absolute path
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_path = os.path.join(base_dir, 'data', 'intents', 'agriculture.json')
    
    with open(data_path, 'r', encoding='utf-8') as f:
        agriculture_data = json.load(f)
    
    intent_info = agriculture_data['agriculture_intent']['intent']
    training_examples = agriculture_data['agriculture_intent']['training_examples']
    
    intent_id = intent_info['intent_id']
    
    # Check if intent already exists
    existing = db.execute(
        text("SELECT intent_id FROM intents WHERE intent_id = :intent_id"),
        {"intent_id": intent_id}
    ).fetchone()
    
    if existing:
        print(f"Intent '{intent_id}' already exists. Updating patterns...")
        # Delete existing patterns for this intent
        db.execute(text("DELETE FROM patterns WHERE intent_id = :intent_id"), {"intent_id": intent_id})
    else:
        print(f"Creating new intent: {intent_id}")
        # Insert intent
        db.execute(text("""
            INSERT INTO intents (
                intent_id, intent_name, category, formality_level, 
                politeness_score, usage_notes
            ) VALUES (
                :intent_id, :intent_name, :category, 5, 5, :usage_notes
            )
        """), {
            "intent_id": intent_id,
            "intent_name": intent_info['intent_name'],
            "category": intent_info['category'],
            "usage_notes": "Agriculture and farming questions - triggers AI-powered response"
        })
    
    # Insert patterns
    print(f"Inserting {len(training_examples)} training patterns...")
    for example in training_examples:
        pattern_text = example['pattern']
        pattern_normalized = normalize_text(example['normalized'])
        
        db.execute(text("""
            INSERT INTO patterns (intent_id, pattern_text, pattern_normalized, language, pattern_type)
            VALUES (:intent_id, :pattern_text, :pattern_normalized, 'kik', 'training_example')
        """), {
            "intent_id": intent_id,
            "pattern_text": pattern_text,
            "pattern_normalized": pattern_normalized
        })
    
    # Add a default fallback response for agriculture questions
    existing_response = db.execute(
        text("SELECT response_id FROM responses WHERE intent_id = :intent_id"),
        {"intent_id": intent_id}
    ).fetchone()
    
    if not existing_response:
        print("Adding default agriculture response...")
        db.execute(text("""
            INSERT INTO responses (
                response_id, intent_id, response_text, translation,
                formality, priority
            ) VALUES (
                :response_id, :intent_id, :response_text, :translation,
                'neutral', 1
            )
        """), {
            "response_id": "agri_default",
            "intent_id": intent_id,
            "response_text": "Nĩ wega, ndingĩrima ũrĩa wĩhĩra.",
            "translation": "Okay, let me help you with your farming question.",
            "translation": "Let me help you with your farming question."
        })
    
    db.commit()
    print(f"✅ Agriculture intent '{intent_id}' seeded successfully!")
    print(f"   - {len(training_examples)} training patterns added")


def seed_agriculture_keywords(db):
    """Add agriculture keywords for fallback detection."""
    
    keywords = [
        "mbembe", "ĩrĩa", "mabembe", "gĩthaka", "boro", "mboro",
        "mbura", "thambi", "ngwacoka", "ngĩgũra", "ngĩtũma",
        "irio", "mĩrĩo", "ĩrĩa", "mbĩrĩ", "mĩtĩ", "ĩcemanio",
        "ngũgũra", "ngethereka", "gĩthaka", "mbemebe"
    ]
    
    print("Adding agriculture keywords to vocabulary...")
    
    for word in keywords:
        normalized = normalize_text(word)
        
        # Check if word already exists
        existing = db.execute(
            text("SELECT vocab_id FROM vocabulary WHERE LOWER(kikuyu_word) = :word"),
            {"word": normalized}
        ).fetchone()
        
        if not existing:
            db.execute(text("""
                INSERT INTO vocabulary (kikuyu_word, meaning, category)
                VALUES (:word, :meaning, 'agriculture')
            """), {
                "word": word,
                "meaning": f"Agriculture term: {word}"
            })
    
    db.commit()
    print(f"✅ Added {len(keywords)} agriculture keywords to vocabulary")


def main():
    """Main entry point."""
    print("=" * 60)
    print("Seeding Agriculture Intents")
    print("=" * 60)
    
    db = next(get_db())
    
    try:
        seed_agriculture_intents(db)
        seed_agriculture_keywords(db)
        print("\n" + "=" * 60)
        print("✅ All agriculture seeds completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error seeding agriculture data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
