#!/bin/bash

echo "=========================================="
echo "🧪 KIKUYU CHATBOT API - TEST SUITE"
echo "=========================================="

API_BASE="http://localhost:8000/api/v1"

# Test 1: Health Check
echo -e "\n1️⃣  Testing Health Check..."
curl -s $API_BASE/health | jq -r '.status, .database.connected'

# Test 2: Traditional Greeting (Thayu)
echo -e "\n2️⃣  Testing Traditional Greeting (Thayu)..."
curl -s -X POST $API_BASE/chat/text \
  -H "Content-Type: application/json" \
  -d '{"text": "Thayu"}' | jq -r '.intent_name, .response_text, .confidence'

# Test 3: Morning Greeting
echo -e "\n3️⃣  Testing Morning Greeting..."
curl -s -X POST $API_BASE/chat/text \
  -H "Content-Type: application/json" \
  -d '{"text": "Good morning"}' | jq -r '.intent_name, .response_text'

# Test 4: English Hello
echo -e "\n4️⃣  Testing English Hello..."
curl -s -X POST $API_BASE/chat/text \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello"}' | jq -r '.intent_name, .response_text'

# Test 5: Thank You
echo -e "\n5️⃣  Testing Thank You..."
curl -s -X POST $API_BASE/chat/text \
  -H "Content-Type: application/json" \
  -d '{"text": "Ngatho"}' | jq -r '.intent_name, .response_text'

# Test 6: How are you
echo -e "\n6️⃣  Testing How Are You..."
curl -s -X POST $API_BASE/chat/text \
  -H "Content-Type: application/json" \
  -d '{"text": "How are you"}' | jq -r '.intent_name, .response_text'

# Test 7: Goodbye
echo -e "\n7️⃣  Testing Goodbye..."
curl -s -X POST $API_BASE/chat/text \
  -H "Content-Type: application/json" \
  -d '{"text": "Goodbye"}' | jq -r '.intent_name, .response_text'

# Test 8: Vocabulary Lookup
echo -e "\n8️⃣  Testing Vocabulary Lookup (thayu)..."
curl -s $API_BASE/vocabulary/thayu | jq -r '.word, .meaning'

# Test 9: Unknown Input
echo -e "\n9️⃣  Testing Unknown Input..."
curl -s -X POST $API_BASE/chat/text \
  -H "Content-Type: application/json" \
  -d '{"text": "xyz123abc"}' | jq -r '.success, .response_text'

# Test 10: Session Creation
echo -e "\n🔟 Testing Session Creation..."
SESSION_RESPONSE=$(curl -s -X POST $API_BASE/session/create)
SESSION_ID=$(echo $SESSION_RESPONSE | jq -r '.session_id')
echo "Created session: $SESSION_ID"

# Test 11: Chat with Session
echo -e "\n1️⃣1️⃣  Testing Chat with Session..."
curl -s -X POST $API_BASE/chat/text \
  -H "Content-Type: application/json" \
  -d "{\"text\": \"Thayu\", \"session_id\": \"$SESSION_ID\"}" | jq -r '.session_id, .response_text'

# Test 12: Get Conversation History
echo -e "\n1️⃣2️⃣  Testing Conversation History..."
curl -s $API_BASE/session/$SESSION_ID/history | jq -r '.total_count'

# Test 13: Analytics
echo -e "\n1️⃣3️⃣  Testing Analytics..."
curl -s $API_BASE/analytics | jq -r '.period, .data[0].total_conversations'

echo ""
echo "=========================================="
echo "✅ All tests completed!"
echo "=========================================="
