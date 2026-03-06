-- Drop existing tables if they exist
DROP TABLE IF EXISTS conversation_logs CASCADE;
DROP TABLE IF EXISTS responses CASCADE;
DROP TABLE IF EXISTS patterns CASCADE;
DROP TABLE IF EXISTS intents CASCADE;
DROP TABLE IF EXISTS pronunciation_map CASCADE;
DROP TABLE IF EXISTS audio_files CASCADE;
DROP TABLE IF EXISTS sessions CASCADE;

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- For fuzzy text matching
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";  -- For UUID generation

-- 1. INTENTS TABLE
CREATE TABLE intents (
    intent_id VARCHAR(100) PRIMARY KEY,
    intent_name VARCHAR(200) NOT NULL,
    category VARCHAR(50) NOT NULL,
    subcategory VARCHAR(50),
    context VARCHAR(100),
    formality_level INTEGER DEFAULT 5,
    politeness_score INTEGER DEFAULT 5,
    cultural_significance TEXT,
    usage_notes TEXT,
    time_range VARCHAR(50),
    age_usage JSONB,
    gender_usage JSONB,
    appropriate_contexts TEXT[],
    inappropriate_contexts TEXT[],
    etiquette_rules TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. PATTERNS TABLE
CREATE TABLE patterns (
    pattern_id SERIAL PRIMARY KEY,
    intent_id VARCHAR(100) REFERENCES intents(intent_id) ON DELETE CASCADE,
    pattern_text TEXT NOT NULL,
    pattern_normalized TEXT NOT NULL,
    language VARCHAR(10) DEFAULT 'kik',
    pattern_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create GIN index for fast text search
CREATE INDEX idx_patterns_normalized ON patterns USING gin(pattern_normalized gin_trgm_ops);
CREATE INDEX idx_patterns_text ON patterns USING gin(to_tsvector('simple', pattern_text));
CREATE INDEX idx_patterns_intent ON patterns(intent_id);

-- 3. RESPONSES TABLE
CREATE TABLE responses (
    response_id VARCHAR(100) PRIMARY KEY,
    intent_id VARCHAR(100) REFERENCES intents(intent_id) ON DELETE CASCADE,
    response_text TEXT NOT NULL,
    translation TEXT,
    literal_meaning TEXT,
    audio_file VARCHAR(500),
    formality VARCHAR(50),
    politeness_score INTEGER DEFAULT 5,
    priority INTEGER DEFAULT 1,
    notes TEXT,
    usage_context VARCHAR(200),
    voice_characteristics JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_responses_intent ON responses(intent_id);
CREATE INDEX idx_responses_priority ON responses(priority);

-- 4. AUDIO FILES TABLE
CREATE TABLE audio_files (
    audio_id SERIAL PRIMARY KEY,
    file_name VARCHAR(255) UNIQUE NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_type VARCHAR(20),
    text_content TEXT,
    speaker_name VARCHAR(100),
    duration_seconds DECIMAL(6,2),
    file_size_kb INTEGER,
    quality VARCHAR(20),
    is_response BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audio_filename ON audio_files(file_name);

-- 5. PRONUNCIATION MAP TABLE
CREATE TABLE pronunciation_map (
    pronunciation_id SERIAL PRIMARY KEY,
    kikuyu_word VARCHAR(100) UNIQUE NOT NULL,
    ipa_notation VARCHAR(200),
    audio_file_id INTEGER REFERENCES audio_files(audio_id),
    syllables JSONB,
    common_misspellings TEXT[],
    tone_pattern VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_pronunciation_word ON pronunciation_map(kikuyu_word);

-- 6. SESSIONS TABLE
CREATE TABLE sessions (
    session_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(100),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    context JSONB,
    conversation_count INTEGER DEFAULT 0,
    user_metadata JSONB
);

CREATE INDEX idx_sessions_user ON sessions(user_id);
CREATE INDEX idx_sessions_last_active ON sessions(last_active);

-- 7. CONVERSATION LOGS TABLE
CREATE TABLE conversation_logs (
    log_id SERIAL PRIMARY KEY,
    session_id UUID REFERENCES sessions(session_id) ON DELETE CASCADE,
    user_input TEXT NOT NULL,
    user_input_normalized TEXT,
    user_input_type VARCHAR(20) DEFAULT 'text',
    intent_matched VARCHAR(100),
    confidence_score DECIMAL(5,4),
    bot_response TEXT NOT NULL,
    response_id VARCHAR(100),
    response_time_ms INTEGER,
    was_successful BOOLEAN DEFAULT TRUE,
    user_feedback VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_logs_session ON conversation_logs(session_id);
CREATE INDEX idx_logs_intent ON conversation_logs(intent_matched);
CREATE INDEX idx_logs_created ON conversation_logs(created_at);

-- 8. ANALYTICS TABLE
CREATE TABLE analytics (
    metric_id SERIAL PRIMARY KEY,
    metric_date DATE DEFAULT CURRENT_DATE UNIQUE,
    total_conversations INTEGER DEFAULT 0,
    successful_matches INTEGER DEFAULT 0,
    failed_matches INTEGER DEFAULT 0,
    average_confidence DECIMAL(5,4),
    average_response_time_ms INTEGER,
    unique_sessions INTEGER DEFAULT 0,
    most_common_intent VARCHAR(100),
    intent_distribution JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_analytics_date ON analytics(metric_date);

-- 9. VOCABULARY TABLE
CREATE TABLE vocabulary (
    vocab_id SERIAL PRIMARY KEY,
    kikuyu_word VARCHAR(100) UNIQUE NOT NULL,
    meaning TEXT NOT NULL,
    category VARCHAR(50),
    part_of_speech VARCHAR(50),
    usage_examples TEXT[],
    related_words TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_vocabulary_word ON vocabulary(kikuyu_word);
CREATE INDEX idx_vocabulary_category ON vocabulary(category);

-- 10. ETIQUETTE RULES TABLE
CREATE TABLE etiquette_rules (
    rule_id SERIAL PRIMARY KEY,
    intent_id VARCHAR(100) REFERENCES intents(intent_id),
    rule_text TEXT NOT NULL,
    rule_type VARCHAR(50),
    severity VARCHAR(20),
    cultural_context TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_etiquette_intent ON etiquette_rules(intent_id);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_intents_updated_at 
    BEFORE UPDATE ON intents
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sessions_last_active
    BEFORE UPDATE ON sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_sessions_last_active();

-- Separate function for sessions
CREATE OR REPLACE FUNCTION update_sessions_last_active()
RETURNS TRIGGER AS $
BEGIN
    NEW.last_active = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$ language 'plpgsql';

-- Function to normalize Kikuyu text
CREATE OR REPLACE FUNCTION normalize_kikuyu_text(text_input TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN lower(
        regexp_replace(
            translate(
                text_input,
                'ĩũíúēãáĨŨÍÚĒÃÁ',
                'iuiueaaiuiueaa'
            ),
            '[^\w\s]', '', 'g'
        )
    );
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function to calculate text similarity
CREATE OR REPLACE FUNCTION calculate_similarity(input_text TEXT, pattern_text TEXT)
RETURNS DECIMAL AS $$
DECLARE
    similarity_score DECIMAL;
BEGIN
    similarity_score := similarity(
        normalize_kikuyu_text(input_text),
        normalize_kikuyu_text(pattern_text)
    );
    RETURN similarity_score;
END;
$$ LANGUAGE plpgsql;