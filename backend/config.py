"""
Configuration management for Kikuyu Chatbot
Loads settings from .env file
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, model_validator
from functools import lru_cache
from typing import List, Optional, Any


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "Kikuyu Voice Chatbot API"
    APP_VERSION: str = "1.0.0"
    ENV: str = "development"
    DEBUG: bool = True
    
    # Database
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "kikuyu_chatbot"
    DB_USER: str = "brian"
    DB_PASSWORD: str = "Admin2026"
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_PREFIX: str = "/api/v1"
    
    # CORS
    CORS_ORIGINS: List[str] = ["*"]
    
    # NLP Settings
    CONFIDENCE_THRESHOLD: float = 0.3
    DEFAULT_LANGUAGE: str = "kik"
    
    # Session
    SESSION_TIMEOUT_HOURS: int = 24
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # OpenAI Settings
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_TTS_VOICE: str = "alloy"
    
    # TTS Engine Settings
    TTS_ENGINE: str = "openai"  # Options: openai, coqui
    AUTO_TTS: bool = True  # Automatically generate TTS for chat responses
    COQUI_TTS_MODEL: str = ""
    COQUI_TTS_VOICE: str = ""
    KHAYA_API_KEY: str = ""
    KHAYA_API_URL: str = "https://api.khayavoice.com/v1/synthesize"
    
    # Groq Settings (alternative to OpenAI)
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    @field_validator('DEBUG', mode='before')
    @classmethod
    def parse_debug(cls, v: Any) -> bool:
        """Parse DEBUG environment variable to boolean"""
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.lower() in ('true', '1', 'yes', 'on', 'debug')
        return True
    
    @property
    def database_url(self) -> str:
        """Construct PostgreSQL connection URL"""
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Global settings instance
settings = get_settings()
