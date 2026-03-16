"""
Knowledge Base Processor
Processes the comprehensive Q&A JSON into searchable format
"""

import json
import os
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class QAPair:
    """Single Q&A entry from knowledge base"""
    id: str
    topic: str
    question_en: str
    question_ki: str
    answer_en: str
    answer_ki: str
    searchable_en: List[str] = field(default_factory=list)
    searchable_ki: List[str] = field(default_factory=list)


@dataclass
class GreetingIntent:
    """Greeting entry from knowledge base"""
    intent_id: str
    intent_name: str
    patterns: List[str]
    responses: List[Dict]
    formality_level: int
    politeness_score: int


class KnowledgeBaseProcessor:
    """Processes JSON knowledge base into structured objects"""
    
    def __init__(self, kb_path: str):
        self.kb_path = kb_path
        self.qa_pairs: List[QAPair] = []
        self.greetings: List[GreetingIntent] = []
        self.metadata: Dict = {}
        self._load()
    
    def _load(self):
        """Load and process JSON file"""
        with open(self.kb_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.metadata = data.get('metadata', {})
        self._process_greetings(data.get('greetings', {}))
        self._process_topics(data.get('topics', []))
        
        print(f"✓ Loaded {len(self.qa_pairs)} Q&A pairs")
        print(f"✓ Loaded {len(self.greetings)} greeting intents")
    
    def _process_greetings(self, greetings_data: Dict):
        """Process greeting intents"""
        intents = greetings_data.get('intents', [])
        for intent in intents:
            greeting = GreetingIntent(
                intent_id=intent['intent_id'],
                intent_name=intent['intent_name'],
                patterns=intent['patterns'],
                responses=intent['responses'],
                formality_level=intent.get('formality_level', 5),
                politeness_score=intent.get('politeness_score', 5)
            )
            self.greetings.append(greeting)
    
    def _process_topics(self, topics: List[Dict]):
        """Process topic Q&A pairs"""
        qa_id = 0
        for topic_data in topics:
            topic_name = topic_data.get('topic', 'General')
            qa_pairs = topic_data.get('qa_pairs', [])
            
            for qa in qa_pairs:
                qa_id += 1
                
                # Create searchable texts
                searchable_en = self._create_searchable_texts(
                    qa.get('question_en', ''),
                    qa.get('answer_en', '')
                )
                searchable_ki = self._create_searchable_texts(
                    qa.get('question_ki', ''),
                    qa.get('answer_ki', '')
                )
                
                pair = QAPair(
                    id=f"{topic_name.lower()}_{qa_id:03d}",
                    topic=topic_name,
                    question_en=qa.get('question_en', ''),
                    question_ki=qa.get('question_ki', ''),
                    answer_en=qa.get('answer_en', ''),
                    answer_ki=qa.get('answer_ki', ''),
                    searchable_en=searchable_en,
                    searchable_ki=searchable_ki
                )
                self.qa_pairs.append(pair)
    
    def _create_searchable_texts(self, question: str, answer: str) -> List[str]:
        """Create searchable variations"""
        texts = [question]
        clean_q = question.replace('?', '').replace('.', '').strip()
        if clean_q != question:
            texts.append(clean_q)
        first_sentence = answer.split('.')[0] if '.' in answer else answer[:100]
        texts.append(f"{question} {first_sentence}")
        return texts
    
    def get_qa_by_id(self, qa_id: str) -> Optional[QAPair]:
        """Get Q&A by ID"""
        for qa in self.qa_pairs:
            if qa.id == qa_id:
                return qa
        return None
    
    def get_qa_by_topic(self, topic: str) -> List[QAPair]:
        """Get all Q&A for a topic"""
        return [qa for qa in self.qa_pairs if qa.topic.lower() == topic.lower()]
    
    def get_all_topics(self) -> List[str]:
        """Get all topics"""
        return list(set(qa.topic for qa in self.qa_pairs))
    
    def check_greeting(self, text: str) -> Optional[Tuple[GreetingIntent, Dict]]:
        """Check if text matches a greeting"""
        text_lower = text.lower().strip()
        for greeting in self.greetings:
            for pattern in greeting.patterns:
                if pattern.lower() in text_lower or text_lower in pattern.lower():
                    best_response = min(greeting.responses, key=lambda r: r.get('priority', 999))
                    return (greeting, best_response)
        return None
