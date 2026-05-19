"""
Middleware for monitoring and logging
"""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging

from services.monitoring_service import get_metrics_collector

logger = logging.getLogger(__name__)


class MonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware to monitor all requests"""
    
    async def dispatch(self, request: Request, call_next):
        """
        Monitor request and response
        
        Args:
            request: Incoming request
            call_next: Next middleware/endpoint
            
        Returns:
            Response
        """
        # Start timing
        start_time = time.time()
        
        # Get endpoint path
        endpoint = f"{request.method} {request.url.path}"
        
        # Process request
        response = None
        error = None
        success = True
        
        try:
            response = await call_next(request)
            
            # Check if response indicates error
            if response.status_code >= 400:
                success = False
                error = f"HTTP {response.status_code}"
            
        except Exception as e:
            success = False
            error = str(e)
            logger.error(f"Request failed: {endpoint} - {error}")
            raise
        
        finally:
            # Calculate duration
            duration = time.time() - start_time
            
            # Record metrics
            collector = get_metrics_collector()
            collector.record_query(
                endpoint=endpoint,
                duration=duration,
                success=success,
                error=error
            )
            
            # Log request
            logger.info(
                f"{endpoint} - {duration:.3f}s - "
                f"Status: {response.status_code if response else 'Error'}"
            )
        
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for detailed request logging"""
    
    async def dispatch(self, request: Request, call_next):
        """
        Log request details
        
        Args:
            request: Incoming request
            call_next: Next middleware/endpoint
            
        Returns:
            Response
        """
        # Log request
        logger.debug(
            f"Request: {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )
        
        # Process request
        response = await call_next(request)
        
        # Log response
        logger.debug(f"Response: {response.status_code}")
        
        return response

# Made with Bob
