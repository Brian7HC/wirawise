#!/usr/bin/env python3
"""
Seed script to load greetings.json into PostgreSQL database
"""

import json
import psycopg2
from psycopg2.extras import Json
from pathlib import Path
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration from .env
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "database": os.getenv("DB_NAME", "kikuyu_chatbot"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD")
}

def load_json_file(file_path: str) -> dict:
    """Load greetings JSON file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: File not found: {file_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON: {e}")
        sys.exit(1)

def connect_to_db():
    """Connect to PostgreSQL database"""
    try:
        print(f"Connecting to database: {DB_CONFIG['database']}@{DB_CONFIG['host']}...")
        conn = psycopg2.connect(**DB_CONFIG)
        print("✓ Connected successfully")
        return conn
    except psycopg2.Error as e:
        print(f"❌ Error connecting to database: {e}")
        print(f"Database config: {DB_CONFIG['database']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}")
        sys.exit(1)

def seed_intents(cursor, intents_data):
    """Seed intents table"""
    print("\n📥 Seeding intents...")
    count = 0
    
    for intent in intents_data:
        try:
            cursor.execute("""
                INSERT INTO intents (
                    intent_id, intent_name, category, subcategory, context,
                    formality_level, politeness_score, cultural_significance,
                    usage_notes, time_range, age_usage, gender_usage,
                    appropriate_contexts, inappropriate_contexts, etiquette_rules
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (intent_id) DO UPDATE SET
                    intent_name = EXCLUDED.intent_name,
                    category = EXCLUDED.category,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                intent.get("intent_id"),
                intent.get("intent_name"),
                intent.get("category"),
                intent.get("subcategory"),
                intent.get("context"),
                intent.get("formality_level", 5),
                intent.get("politeness_score", 5),
                intent.get("cultural_significance"),
                intent.get("usage_notes"),
                intent.get("time_range"),
                Json(intent.get("age_usage", {})),
                Json(intent.get("gender_usage", {})),
                intent.get("appropriate_contexts", []),
                intent.get("inappropriate_contexts", []),
                intent.get("etiquette_rules", [])
            ))
            count += 1
        except Exception as e:
            print(f"   ⚠️  Error with intent {intent.get('intent_id')}: {e}")
    
    print(f"   ✓ Seeded {count} intents")
    return count

def seed_patterns(cursor, intents_data):
    """Seed patterns table"""
    print("\n📥 Seeding patterns...")
    count = 0
    
    for intent in intents_data:
        intent_id = intent.get("intent_id")
        patterns = intent.get("patterns", [])
        
        for pattern in patterns:
            try:
                # Normalize pattern for matching
                normalized = pattern.lower().strip()
                
                cursor.execute("""
                    INSERT INTO patterns (
                        intent_id, pattern_text, pattern_normalized, language
                    ) VALUES (%s, %s, %s, %s)
                """, (
                    intent_id,
                    pattern,
                    normalized,
                    'kik'
                ))
                count += 1
            except Exception as e:
                print(f"   ⚠️  Error with pattern '{pattern}': {e}")
    
    print(f"   ✓ Seeded {count} patterns")
    return count

def seed_responses(cursor, intents_data):
    """Seed responses table"""
    print("\n📥 Seeding responses...")
    count = 0
    
    for intent in intents_data:
        intent_id = intent.get("intent_id")
        responses = intent.get("responses", [])
        
        for response in responses:
            try:
                cursor.execute("""
                    INSERT INTO responses (
                        response_id, intent_id, response_text, translation,
                        literal_meaning, audio_file, formality, politeness_score,
                        priority, notes, usage_context, voice_characteristics
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (response_id) DO UPDATE SET
                        response_text = EXCLUDED.response_text,
                        translation = EXCLUDED.translation
                """, (
                    response.get("response_id"),
                    intent_id,
                    response.get("text"),
                    response.get("translation"),
                    response.get("literal_meaning"),
                    response.get("audio_file"),
                    response.get("formality"),
                    response.get("politeness_score", 5),
                    response.get("priority", 1),
                    response.get("notes"),
                    response.get("usage_context"),
                    Json(response.get("voice_characteristics", {}))
                ))
                count += 1
            except Exception as e:
                print(f"   ⚠️  Error with response {response.get('response_id')}: {e}")
    
    print(f"   ✓ Seeded {count} responses")
    return count

def seed_vocabulary(cursor, vocabulary_data):
    """Seed vocabulary table"""
    print("\n📥 Seeding vocabulary...")
    count = 0
    
    # Add common words
    common_words = vocabulary_data.get("common_words", {})
    for word, meaning in common_words.items():
        try:
            cursor.execute("""
                INSERT INTO vocabulary (
                    kikuyu_word, meaning, category, part_of_speech
                ) VALUES (%s, %s, %s, %s)
                ON CONFLICT (kikuyu_word) DO UPDATE SET
                    meaning = EXCLUDED.meaning
            """, (
                word,
                meaning,
                'common_words',
                None
            ))
            count += 1
        except Exception as e:
            print(f"   ⚠️  Error with word '{word}': {e}")
    
    # Add kinship terms
    kinship_terms = vocabulary_data.get("kinship_address_terms", {})
    for word, meaning in kinship_terms.items():
        try:
            cursor.execute("""
                INSERT INTO vocabulary (
                    kikuyu_word, meaning, category, part_of_speech
                ) VALUES (%s, %s, %s, %s)
                ON CONFLICT (kikuyu_word) DO UPDATE SET
                    meaning = EXCLUDED.meaning
            """, (
                word,
                meaning,
                'kinship_terms',
                'noun'
            ))
            count += 1
        except Exception as e:
            print(f"   ⚠️  Error with kinship term '{word}': {e}")
    
    # Add professional titles
    professional_titles = vocabulary_data.get("professional_titles", {})
    for word, meaning in professional_titles.items():
        try:
            cursor.execute("""
                INSERT INTO vocabulary (
                    kikuyu_word, meaning, category, part_of_speech
                ) VALUES (%s, %s, %s, %s)
                ON CONFLICT (kikuyu_word) DO UPDATE SET
                    meaning = EXCLUDED.meaning
            """, (
                word,
                meaning,
                'professional_titles',
                'noun'
            ))
            count += 1
        except Exception as e:
            pass
    
    print(f"   ✓ Seeded {count} vocabulary entries")
    return count

def seed_pronunciation(cursor, pronunciation_data):
    """Seed pronunciation map table"""
    print("\n📥 Seeding pronunciation map...")
    count = 0
    
    common_phrases_ipa = pronunciation_data.get("common_phrases_ipa", {})
    
    for phrase, ipa in common_phrases_ipa.items():
        try:
            cursor.execute("""
                INSERT INTO pronunciation_map (
                    kikuyu_word, ipa_notation, syllables
                ) VALUES (%s, %s, %s)
                ON CONFLICT (kikuyu_word) DO UPDATE SET
                    ipa_notation = EXCLUDED.ipa_notation
            """, (
                phrase,
                ipa,
                Json([])  # We can add syllable breakdown later
            ))
            count += 1
        except Exception as e:
            print(f"   ⚠️  Error with pronunciation '{phrase}': {e}")
    
    print(f"   ✓ Seeded {count} pronunciation entries")
    return count

def verify_seeding(cursor):
    """Verify that data was seeded correctly"""
    print("\n🔍 Verifying seeded data...")
    
    tables = ['intents', 'patterns', 'responses', 'vocabulary', 'pronunciation_map']
    
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"   ✓ {table}: {count} records")

def main():
    """Main seeding function"""
    print("=" * 70)
    print("🇰🇪  KIKUYU CHATBOT - DATABASE SEEDING")
    print("=" * 70)
    
    # Check if .env exists
    if not os.path.exists('.env'):
        print("\n❌ Error: .env file not found!")
        print("Please create a .env file with database credentials.")
        sys.exit(1)
    
    # Load greetings data
    print("\n📖 Loading greetings.json...")
    greetings_file = "data/intents/greetings.json"
    
    if not os.path.exists(greetings_file):
        print(f"❌ Error: {greetings_file} not found!")
        sys.exit(1)
    
    data = load_json_file(greetings_file)
    greetings = data.get("greetings", {})
    print(f"   ✓ Loaded {len(greetings.get('intents', []))} intents from JSON")
    
    # Connect to database
    conn = connect_to_db()
    cursor = conn.cursor()
    
    try:
        # Start transaction
        print("\n" + "=" * 70)
        print("🚀 Starting database seeding...")
        print("=" * 70)
        
        # Seed all data
        total_intents = seed_intents(cursor, greetings.get("intents", []))
        total_patterns = seed_patterns(cursor, greetings.get("intents", []))
        total_responses = seed_responses(cursor, greetings.get("intents", []))
        total_vocab = seed_vocabulary(cursor, greetings.get("vocabulary", {}))
        total_pronunciation = seed_pronunciation(cursor, greetings.get("pronunciation_guide", {}))
        
        # Verify
        verify_seeding(cursor)
        
        # Commit transaction
        conn.commit()
        
        print("\n" + "=" * 70)
        print("✅ DATABASE SEEDING COMPLETED SUCCESSFULLY")
        print("=" * 70)
        print(f"\n📊 Summary:")
        print(f"   • Intents:       {total_intents}")
        print(f"   • Patterns:      {total_patterns}")
        print(f"   • Responses:     {total_responses}")
        print(f"   • Vocabulary:    {total_vocab}")
        print(f"   • Pronunciation: {total_pronunciation}")
        print(f"\n✓ Database is ready for use!")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Error during seeding: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()