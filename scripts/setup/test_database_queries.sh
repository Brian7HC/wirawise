#!/bin/bash

# Database credentials
export PGPASSWORD=Admin2026

echo "=========================================="
echo "🧪 KIKUYU CHATBOT - DATABASE TESTS"
echo "=========================================="

# Test 1: Check Thayu greeting
echo -e "\n1️⃣  Test: Find 'Thayu' greeting patterns"
psql -U brian -d kikuyu_chatbot -h localhost -c "
SELECT i.intent_name, p.pattern_text 
FROM intents i 
JOIN patterns p ON i.intent_id = p.intent_id 
WHERE p.pattern_text ILIKE '%thayu%' 
LIMIT 3;
"

# Test 2: Get responses for Thayu
echo -e "\n2️⃣  Test: Get responses for Thayu greeting"
psql -U brian -d kikuyu_chatbot -h localhost -c "
SELECT r.response_text, r.translation, r.formality 
FROM responses r 
WHERE r.intent_id = 'greeting_thayu' 
ORDER BY r.priority 
LIMIT 2;
"

# Test 3: Test fuzzy matching with pg_trgm
echo -e "\n3️⃣  Test: Fuzzy text matching (searching 'nikwega')"
psql -U brian -d kikuyu_chatbot -h localhost -c "
SELECT 
    pattern_text,
    SIMILARITY(pattern_normalized, 'nikwega') as similarity_score
FROM patterns
WHERE SIMILARITY(pattern_normalized, 'nikwega') > 0.3
ORDER BY similarity_score DESC
LIMIT 5;
"

# Test 4: Vocabulary lookup
echo -e "\n4️⃣  Test: Vocabulary lookup"
psql -U brian -d kikuyu_chatbot -h localhost -c "
SELECT kikuyu_word, meaning, category 
FROM vocabulary 
WHERE kikuyu_word IN ('thayu', 'ngatho', 'mwega')
ORDER BY kikuyu_word;
"

# Test 5: Count by category
echo -e "\n5️⃣  Test: Intents grouped by category"
psql -U brian -d kikuyu_chatbot -h localhost -c "
SELECT category, COUNT(*) as count 
FROM intents 
GROUP BY category 
ORDER BY count DESC;
"

# Test 6: Pronunciation lookup
echo -e "\n6️⃣  Test: Pronunciation (IPA) lookup"
psql -U brian -d kikuyu_chatbot -h localhost -c "
SELECT kikuyu_word, ipa_notation 
FROM pronunciation_map 
WHERE kikuyu_word IN ('Thayu', 'Ngatho', 'Nikwega')
LIMIT 3;
"

echo ""
echo "=========================================="
echo "✅ All database tests completed!"
echo "=========================================="
