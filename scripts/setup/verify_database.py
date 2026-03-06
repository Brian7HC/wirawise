#!/usr/bin/env python3
"""
Verify database setup and data integrity
"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "database": os.getenv("DB_NAME", "kikuyu_chatbot"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD")
}

def verify_database():
    print("=" * 70)
    print("🔍 KIKUYU CHATBOT - DATABASE VERIFICATION")
    print("=" * 70)
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Check tables exist
        print("\n📋 Checking tables...")
        tables = ['intents', 'patterns', 'responses', 'vocabulary', 
                  'pronunciation_map', 'sessions', 'conversation_logs', 
                  'analytics', 'audio_files', 'etiquette_rules']
        
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            status = "✓" if count > 0 or table in ['sessions', 'conversation_logs', 'analytics', 'audio_files', 'etiquette_rules'] else "⚠️"
            print(f"   {status} {table:20s} : {count:5d} records")
        
        # Check pg_trgm extension
        print("\n🔧 Checking extensions...")
        cursor.execute("SELECT extname FROM pg_extension WHERE extname = 'pg_trgm'")
        if cursor.fetchone():
            print("   ✓ pg_trgm extension installed")
        else:
            print("   ❌ pg_trgm extension NOT installed")
        
        # Test sample queries
        print("\n🧪 Testing sample queries...")
        
        # Find Thayu greeting
        cursor.execute("""
            SELECT i.intent_name, p.pattern_text
            FROM intents i
            JOIN patterns p ON i.intent_id = p.intent_id
            WHERE p.pattern_text ILIKE '%thayu%'
            LIMIT 1
        """)
        result = cursor.fetchone()
        if result:
            print(f"   ✓ Found pattern: '{result[1]}' for intent '{result[0]}'")
        
        # Get sample response
        cursor.execute("""
            SELECT response_text, translation
            FROM responses
            WHERE intent_id = 'greeting_thayu'
            LIMIT 1
        """)
        result = cursor.fetchone()
        if result:
            print(f"   ✓ Sample response: '{result[0]}'")
            print(f"     Translation: '{result[1]}'")
        
        print("\n" + "=" * 70)
        print("✅ Database verification complete!")
        print("=" * 70)
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    verify_database()