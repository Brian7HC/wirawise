"""
Query Logger - Tracks all queries for analytics and improvement
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from collections import Counter
from pathlib import Path


class QueryLogger:
    """
    Logs all queries to enable analytics and KB improvement
    """
    
    def __init__(self, log_dir: str = None):
        if log_dir is None:
            log_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "logs")
        
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Log file path
        self.query_log_file = self.log_dir / "queries.jsonl"
        self.unanswered_file = self.log_dir / "unanswered.jsonl"
        
        # In-memory counters for quick analytics
        self.query_count = 0
        self.topic_counter = Counter()
        self.unanswered_queries = []
        
        # Load existing logs if available
        self._load_existing_logs()
    
    def _load_existing_logs(self):
        """Load existing query logs for analytics"""
        if self.query_log_file.exists():
            try:
                with open(self.query_log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    self.query_count = len(lines)
                    
                    # Load topic counters
                    for line in lines[-1000:]:  # Last 1000 for performance
                        try:
                            entry = json.loads(line)
                            topic = entry.get('topic', 'unknown')
                            if topic:
                                self.topic_counter[topic] += 1
                        except:
                            pass
            except Exception as e:
                print(f"Warning: Could not load existing logs: {e}")
    
    def log_query(self, query: str, response: Dict):
        """
        Log a query and its response
        """
        timestamp = datetime.now().isoformat()
        
        # Determine topic from response
        topic = response.get('topic', 'unknown')
        if topic == 'unknown' and response.get('message_type') == 'greeting':
            topic = 'greeting'
        
        # Check if answered (confidence >= 0.5)
        confidence = response.get('confidence', 0)
        answered = confidence >= 0.5
        
        # Build log entry
        log_entry = {
            'timestamp': timestamp,
            'query': query,
            'language': response.get('language', 'en'),
            'topic': topic,
            'message_type': response.get('message_type', 'unknown'),
            'confidence': confidence,
            'answered': answered,
            'success': response.get('success', False),
            'processing_time_ms': response.get('processing_time_ms', 0)
        }
        
        # Append to query log
        try:
            with open(self.query_log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
            
            # Update counters
            self.query_count += 1
            if topic:
                self.topic_counter[topic] += 1
            
            # Track unanswered queries
            if not answered:
                self.unanswered_queries.append({
                    'query': query,
                    'timestamp': timestamp,
                    'topic': topic,
                    'language': response.get('language')
                })
                
                # Also log to unanswered file
                try:
                    with open(self.unanswered_file, 'a', encoding='utf-8') as f:
                        f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
                except Exception as e:
                    print(f"Warning: Could not log unanswered query: {e}")
                    
        except Exception as e:
            print(f"Warning: Could not log query: {e}")
    
    def get_common_unanswered(self, limit: int = 20) -> List[Dict]:
        """
        Get most common unanswered queries for KB improvement
        """
        query_counter = Counter()
        
        # Read from unanswered file
        if self.unanswered_file.exists():
            try:
                with open(self.unanswered_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            entry = json.loads(line)
                            query = entry.get('query', '')
                            if query:
                                query_counter[query] += 1
                        except:
                            pass
            except Exception as e:
                print(f"Warning: Could not read unanswered queries: {e}")
        
        # Return top unanswered
        return [
            {'query': q, 'count': c}
            for q, c in query_counter.most_common(limit)
        ]
    
    def get_popular_topics(self, limit: int = 30) -> Dict:
        """
        Get popular topics from queries
        """
        return {
            'total_queries': self.query_count,
            'topics': dict(self.topic_counter.most_common(limit)),
            'period': 'all_time'
        }
    
    def get_stats(self) -> Dict:
        """
        Get overall query statistics
        """
        answered_count = 0
        total_confidence = 0.0
        
        if self.query_log_file.exists():
            try:
                with open(self.query_log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            entry = json.loads(line)
                            if entry.get('answered'):
                                answered_count += 1
                            total_confidence += entry.get('confidence', 0)
                        except:
                            pass
            except:
                pass
        
        return {
            'total_queries': self.query_count,
            'answered_queries': answered_count,
            'unanswered_queries': self.query_count - answered_count,
            'answer_rate': answered_count / self.query_count if self.query_count > 0 else 0,
            'avg_confidence': total_confidence / self.query_count if self.query_count > 0 else 0
        }
    
    def export_for_kb_improvement(self, output_path: str = None):
        """
        Export data for KB improvement
        """
        if output_path is None:
            output_path = self.log_dir / "kb_improvement_export.json"
        
        export_data = {
            'generated_at': datetime.now().isoformat(),
            'stats': self.get_stats(),
            'popular_topics': self.get_popular_topics(50),
            'common_unanswered': self.get_common_unanswered(50)
        }
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            return str(output_path)
        except Exception as e:
            print(f"Warning: Could not export data: {e}")
            return None
