"""Database CRUD operations."""

from sqlalchemy.orm import Session
from sqlalchemy import text, func
from typing import Optional, Dict, List, Tuple
import logging
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class GreetingCRUD:
    """CRUD operations for greeting intents"""
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalize text for matching (remove diacritics, lowercase)"""
        text = text.lower().strip()
        
        # Remove Kikuyu diacritics for fuzzy matching
        replacements = {
            'ĩ': 'i', 'ũ': 'u', 'í': 'i', 'ú': 'u',
            'ē': 'e', 'ã': 'a', 'á': 'a'
        }
        
        for kikuyu_char, basic_char in replacements.items():
            text = text.replace(kikuyu_char, basic_char)
        
        return text
    
    @staticmethod
    def find_intent(
        db: Session, 
        user_input: str, 
        confidence_threshold: float = 0.3
    ) -> Optional[Dict]:
        """
        Find matching intent for user input using PostgreSQL similarity
        
        Args:
            db: Database session
            user_input: User's input text
            confidence_threshold: Minimum confidence score (0.0 to 1.0)
            
        Returns:
            Dict with intent info or None
        """
        normalized_input = GreetingCRUD.normalize_text(user_input)
        
        # Use PostgreSQL similarity matching with pg_trgm
        query = text("""
            SELECT 
                i.intent_id,
                i.intent_name,
                i.category,
                i.subcategory,
                i.formality_level,
                i.politeness_score,
                p.pattern_text,
                GREATEST(
                    SIMILARITY(p.pattern_normalized, :normalized_input),
                    CASE 
                        WHEN p.pattern_normalized ILIKE '%' || :normalized_input || '%' THEN 0.9
                        WHEN :normalized_input ILIKE '%' || p.pattern_normalized || '%' THEN 0.85
                        ELSE 0.0
                    END
                ) as confidence
            FROM patterns p
            JOIN intents i ON p.intent_id = i.intent_id
            WHERE 
                p.pattern_normalized ILIKE '%' || :normalized_input || '%'
                OR :normalized_input ILIKE '%' || p.pattern_normalized || '%'
                OR SIMILARITY(p.pattern_normalized, :normalized_input) > :threshold
            ORDER BY confidence DESC
            LIMIT 1
        """)
        
        result = db.execute(
            query,
            {
                "normalized_input": normalized_input,
                "threshold": confidence_threshold
            }
        ).fetchone()
        
        if result and result[7] >= confidence_threshold:  # confidence column
            return {
                "intent_id": result[0],
                "intent_name": result[1],
                "category": result[2],
                "subcategory": result[3],
                "formality_level": result[4],
                "politeness_score": result[5],
                "matched_pattern": result[6],
                "confidence": float(result[7])
            }
        
        return None
    
    @staticmethod
    def get_response(
        db: Session, 
        intent_id: str,
        formality_preference: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Get response for an intent
        
        Args:
            db: Database session
            intent_id: Intent identifier
            formality_preference: Optional formality filter
            
        Returns:
            Response dict or None
        """
        query_str = """
            SELECT 
                response_id,
                response_text,
                translation,
                literal_meaning,
                audio_file,
                formality,
                politeness_score,
                priority,
                notes,
                usage_context
            FROM responses
            WHERE intent_id = :intent_id
        """
        
        # Add formality filter if specified
        if formality_preference:
            query_str += " AND formality ILIKE :formality"
        
        query_str += " ORDER BY priority ASC, RANDOM() LIMIT 1"
        
        params = {"intent_id": intent_id}
        if formality_preference:
            params["formality"] = f"%{formality_preference}%"
        
        result = db.execute(text(query_str), params).fetchone()
        
        if result:
            return {
                "response_id": result[0],
                "response_text": result[1],
                "translation": result[2],
                "literal_meaning": result[3],
                "audio_file": result[4],
                "formality": result[5],
                "politeness_score": result[6],
                "priority": result[7],
                "notes": result[8],
                "usage_context": result[9]
            }
        
        return None
    
    @staticmethod
    def get_all_responses(db: Session, intent_id: str) -> List[Dict]:
        """Get all responses for an intent"""
        query = text("""
            SELECT 
                response_id, response_text, translation, 
                formality, priority
            FROM responses
            WHERE intent_id = :intent_id
            ORDER BY priority ASC
        """)
        
        results = db.execute(query, {"intent_id": intent_id}).fetchall()
        
        return [
            {
                "response_id": r[0],
                "response_text": r[1],
                "translation": r[2],
                "formality": r[3],
                "priority": r[4]
            }
            for r in results
        ]


class ConversationCRUD:
    """CRUD operations for conversation logging"""
    
    @staticmethod
    def create_session(db: Session, user_id: Optional[str] = None) -> str:
        """Create a new session"""
        session_id = uuid.uuid4()
        
        query = text("""
            INSERT INTO sessions (session_id, user_id, context, conversation_count)
            VALUES (:session_id, :user_id, :context, 0)
            RETURNING session_id
        """)
        
        result = db.execute(
            query,
            {
                "session_id": session_id,
                "user_id": user_id,
                "context": "{}"
            }
        ).fetchone()
        
        db.commit()
        return str(result[0])
    
    @staticmethod
    def get_session(db: Session, session_id: str) -> Optional[Dict]:
        """Get session by ID"""
        query = text("""
            SELECT session_id, user_id, started_at, last_active, 
                   conversation_count, context
            FROM sessions
            WHERE session_id = :session_id
        """)
        
        result = db.execute(query, {"session_id": session_id}).fetchone()
        
        if result:
            return {
                "session_id": str(result[0]),
                "user_id": result[1],
                "started_at": result[2],
                "last_active": result[3],
                "conversation_count": result[4],
                "context": result[5]
            }
        
        return None
    
    @staticmethod
    def log_conversation(
        db: Session,
        session_id: str,
        user_input: str,
        bot_response: str,
        intent_matched: Optional[str] = None,
        confidence_score: Optional[float] = None,
        response_time_ms: Optional[int] = None,
        user_input_type: str = "text"
    ) -> int:
        """Log a conversation exchange"""
        
        normalized_input = GreetingCRUD.normalize_text(user_input)
        
        query = text("""
            INSERT INTO conversation_logs (
                session_id, user_input, user_input_normalized, user_input_type,
                bot_response, intent_matched, confidence_score, response_time_ms,
                was_successful
            ) VALUES (
                :session_id, :user_input, :normalized, :input_type,
                :bot_response, :intent, :confidence, :response_time,
                :successful
            )
            RETURNING log_id
        """)
        
        result = db.execute(
            query,
            {
                "session_id": session_id,
                "user_input": user_input,
                "normalized": normalized_input,
                "input_type": user_input_type,
                "bot_response": bot_response,
                "intent": intent_matched,
                "confidence": confidence_score,
                "response_time": response_time_ms,
                "successful": intent_matched is not None
            }
        ).fetchone()
        
        # Update session conversation count
        db.execute(
            text("""
                UPDATE sessions 
                SET conversation_count = conversation_count + 1,
                    last_active = CURRENT_TIMESTAMP
                WHERE session_id = :session_id
            """),
            {"session_id": session_id}
        )
        
        db.commit()
        return result[0]
    
    @staticmethod
    def get_conversation_history(
        db: Session, 
        session_id: str, 
        limit: int = 10
    ) -> List[Dict]:
        """Get conversation history for a session"""
        query = text("""
            SELECT 
                user_input, bot_response, intent_matched, 
                confidence_score, created_at
            FROM conversation_logs
            WHERE session_id = :session_id
            ORDER BY created_at DESC
            LIMIT :limit
        """)
        
        results = db.execute(
            query,
            {"session_id": session_id, "limit": limit}
        ).fetchall()
        
        return [
            {
                "user_input": r[0],
                "bot_response": r[1],
                "intent_matched": r[2],
                "confidence": float(r[3]) if r[3] else 0.0,
                "timestamp": r[4].isoformat()
            }
            for r in results
        ]


class VocabularyCRUD:
    """CRUD operations for vocabulary"""
    
    @staticmethod
    def get_word_meaning(db: Session, word: str) -> Optional[str]:
        """Get meaning of a Kikuyu word"""
        normalized_word = GreetingCRUD.normalize_text(word)
        
        query = text("""
            SELECT meaning
            FROM vocabulary
            WHERE LOWER(kikuyu_word) = :word
            LIMIT 1
        """)
        
        result = db.execute(query, {"word": normalized_word}).fetchone()
        return result[0] if result else None
    
    @staticmethod
    def get_pronunciation(db: Session, word: str) -> Optional[str]:
        """Get IPA pronunciation for a word"""
        query = text("""
            SELECT ipa_notation
            FROM pronunciation_map
            WHERE LOWER(kikuyu_word) = :word
            LIMIT 1
        """)
        
        result = db.execute(query, {"word": word.lower()}).fetchone()
        return result[0] if result else None


class AnalyticsCRUD:
    """CRUD operations for analytics"""
    
    @staticmethod
    def update_daily_analytics(db: Session, date: Optional[str] = None):
        """Update analytics for a specific date"""
        if not date:
            date = datetime.now().date()
        
        query = text("""
            INSERT INTO analytics (
                metric_date, total_conversations, successful_matches,
                failed_matches, average_confidence, unique_sessions
            )
            SELECT 
                DATE(:date),
                COUNT(*),
                SUM(CASE WHEN confidence_score > 0.5 THEN 1 ELSE 0 END),
                SUM(CASE WHEN confidence_score <= 0.5 OR confidence_score IS NULL THEN 1 ELSE 0 END),
                AVG(confidence_score),
                COUNT(DISTINCT session_id)
            FROM conversation_logs
            WHERE DATE(created_at) = DATE(:date)
            ON CONFLICT (metric_date) DO UPDATE SET
                total_conversations = EXCLUDED.total_conversations,
                successful_matches = EXCLUDED.successful_matches,
                failed_matches = EXCLUDED.failed_matches,
                average_confidence = EXCLUDED.average_confidence,
                unique_sessions = EXCLUDED.unique_sessions
        """)
        
        db.execute(query, {"date": date})
        db.commit()
    
    @staticmethod
    def get_analytics(db: Session, days: int = 7) -> List[Dict]:
        """Get analytics for last N days"""
        query = text("""
            SELECT 
                metric_date, total_conversations, successful_matches,
                failed_matches, average_confidence, unique_sessions
            FROM analytics
            WHERE metric_date >= CURRENT_DATE - INTERVAL ':days days'
            ORDER BY metric_date DESC
        """)
        
        results = db.execute(query, {"days": days}).fetchall()
        
        return [
            {
                "date": r[0].isoformat(),
                "total_conversations": r[1],
                "successful_matches": r[2],
                "failed_matches": r[3],
                "average_confidence": float(r[4]) if r[4] else 0.0,
                "unique_sessions": r[5]
            }
            for r in results
        ]
