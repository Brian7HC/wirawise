"""
Main FastAPI application for Kikuyu Voice Chatbot
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
import os
from datetime import datetime

from backend.config import settings
from backend.api.routes import router as api_router
from backend.database.connection import test_connection, get_db_info

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan events for startup and shutdown
    """
    # Startup
    logger.info("=" * 70)
    logger.info(f"🇰🇪 {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info("=" * 70)
    
    # Test database connection
    logger.info("Testing database connection...")
    if test_connection():
        db_info = get_db_info()
        logger.info(f"✅ Database connected: {db_info.get('database')}@{db_info.get('host')}")
        logger.info(f"   PostgreSQL version: {db_info.get('version', 'Unknown')[:50]}...")
    else:
        logger.error("❌ Database connection failed!")
    
    logger.info(f"Environment: {settings.ENV}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"API will be available at: http://{settings.API_HOST}:{settings.API_PORT}")
    logger.info(f"API documentation: http://{settings.API_HOST}:{settings.API_PORT}/docs")
    
    # Warm up MMS for Kikuyu
    logger.info("Warming up Kikuyu speech recognition (Meta MMS)...")
    try:
        from backend.stt.mms_engine import load_mms_model
        load_mms_model()  # Pre-load model
        logger.info("✅ Meta MMS ready for Kikuyu speech")
    except Exception as e:
        logger.warning(f"⚠️  MMS warmup failed: {e}")
    
    # Pre-load translation model for fast responses (now uses Groq, no pre-load needed)
    logger.info("Translation will be handled by Groq LLM...")
    logger.info("✅ Translation ready (Groq-based)")
    
    logger.info("=" * 70)
    
    yield
    
    # Shutdown
    logger.info("Shutting down Kikuyu Chatbot API...")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    🇰🇪 **Kikuyu Voice Chatbot API**
    
    A conversational AI system for the Kikuyu (Gĩgĩkũyũ) language.
    
    ## Features
    
    * 🗣️ **Text Chat**: Send text in Kikuyu or English and get culturally appropriate responses
    * 📚 **Vocabulary**: Look up Kikuyu words and their meanings
    * 📊 **Analytics**: Track conversation metrics and performance
    * 🎯 **Intent Recognition**: Advanced pattern matching with PostgreSQL
    
    ## Greetings Categories
    
    * Traditional greetings (Thayu)
    * Time-specific greetings (morning, afternoon, evening)
    * Context-specific greetings (work, group, formal)
    * Kinship-based greetings
    * Professional title greetings
    
    ## Cultural Context
    
    The chatbot follows Kikuyu cultural etiquette rules:
    - Respects age hierarchy
    - Adapts formality based on context
    - Uses appropriate terms of address
    - Follows traditional greeting conventions
    
    Based on research by Nancy I. Karia-Maina (2014) on pragmatic and linguistic etiquette 
    in Gikuyu language speakers.
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={
        "name": "Kikuyu Chatbot Project",
        "url": "https://github.com/yourusername/kikuyu-voice-chatbot",
    },
    license_info={
        "name": "MIT License",
    },
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": "Validation Error",
            "detail": exc.errors(),
            "timestamp": datetime.now().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "Internal Server Error",
            "detail": str(exc) if settings.DEBUG else "An error occurred",
            "timestamp": datetime.now().isoformat()
        }
    )


# Include API router
app.include_router(
    api_router,
    prefix=settings.API_PREFIX,
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"}
    }
)

# Create audio directory if it doesn't exist
audio_dir = os.path.join(os.path.dirname(__file__), "..", "data", "audio", "responses")
os.makedirs(audio_dir, exist_ok=True)

# Serve audio files
app.mount("/api/v1/audio", StaticFiles(directory="data/audio"), name="audio")

# Serve frontend static files
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint - API information"""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "environment": settings.ENV,
        "api_docs": "/docs",
        "api_base": settings.API_PREFIX,
        "greeting": "Thayu! (Peace be upon you)",
        "endpoints": {
            "chat": f"{settings.API_PREFIX}/chat/text",
            "health": f"{settings.API_PREFIX}/health",
            "vocabulary": f"{settings.API_PREFIX}/vocabulary/{{word}}",
            "analytics": f"{settings.API_PREFIX}/analytics"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "backend.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
