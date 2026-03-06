#!/bin/bash

# Kikuyu Chatbot - Database Initialization Script

echo "=========================================="
echo "🇰🇪  Kikuyu Chatbot - Database Setup"
echo "=========================================="

# Load .env file
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "❌ .env file not found!"
    exit 1
fi

# Check if PostgreSQL is running
if ! pg_isready -q; then
    echo "❌ PostgreSQL is not running!"
    echo "Please start PostgreSQL and try again."
    exit 1
fi

echo ""
echo "📦 Step 1: Creating database..."
createdb $DB_NAME 2>/dev/null || echo "   ⚠️  Database already exists"

echo ""
echo "📋 Step 2: Running schema..."
psql -d $DB_NAME -f database/schema.sql

echo ""
echo "🌱 Step 3: Seeding data..."
python scripts/setup/seed_greetings.py

echo ""
echo "=========================================="
echo "✅ Database setup complete!"
echo "=========================================="
