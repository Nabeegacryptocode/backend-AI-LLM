"""
Authentication utilities
"""
from fastapi import HTTPException, Header
from typing import Optional
import logging

from app.config import settings

logger = logging.getLogger(__name__)


async def verify_api_key(authorization: Optional[str] = Header(None)) -> str:
    """
    Verify API key from Authorization header
    
    Args:
        authorization: Authorization header value (Bearer token)
        
    Returns:
        API key if valid
        
    Raises:
        HTTPException: If API key is invalid or missing
    """
    if not authorization:
        logger.warning("Missing authorization header")
        raise HTTPException(
            status_code=401,
            detail="Missing authorization header"
        )
    
    if not authorization.startswith("Bearer "):
        logger.warning("Invalid authorization header format")
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header format. Use: Bearer <api_key>"
        )
    
    api_key = authorization.replace("Bearer ", "")
    
    if api_key != settings.API_KEY:
        logger.warning("Invalid API key attempt")
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    
    return api_key


def generate_api_key() -> str:
    """
    Generate a secure API key
    
    Returns:
        Generated API key
    """
    import secrets
    return secrets.token_urlsafe(32)

# Made with Bob
