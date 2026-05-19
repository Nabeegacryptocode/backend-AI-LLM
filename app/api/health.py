"""
Health check endpoints
"""
from fastapi import APIRouter
from datetime import datetime
import logging

from app.models import HealthResponse
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    Returns the status of the API and its dependencies
    """
    services_status = {}
    
    # Check OpenAI API
    try:
        # Simple check - just verify key is set
        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.startswith("sk-"):
            services_status["openai"] = "configured"
        else:
            services_status["openai"] = "not_configured"
    except Exception as e:
        logger.error(f"OpenAI health check failed: {e}")
        services_status["openai"] = "error"
    
    # Check Pinecone
    try:
        if settings.PINECONE_API_KEY:
            services_status["pinecone"] = "configured"
        else:
            services_status["pinecone"] = "not_configured"
    except Exception as e:
        logger.error(f"Pinecone health check failed: {e}")
        services_status["pinecone"] = "error"
    
    
    
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.utcnow(),
        services=services_status
    )


@router.get("/ping")
async def ping():
    """Simple ping endpoint"""
    return {"status": "pong", "timestamp": datetime.utcnow().isoformat()}

# Made with Bob
