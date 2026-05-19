"""
Metrics and monitoring endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
import logging

from app.models import ErrorResponse
from services.monitoring_service import get_metrics_collector
from app.utils.auth import verify_api_key

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/metrics")
async def get_metrics(api_key: str = Depends(verify_api_key)):
    """
    Get application metrics
    
    Returns comprehensive metrics including:
    - Query statistics
    - Token usage
    - Error rates
    - Performance data
    """
    try:
        collector = get_metrics_collector()
        metrics = collector.get_metrics()
        
        return {
            "status": "success",
            "metrics": metrics
        }
        
    except Exception as e:
        logger.error(f"Error getting metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/summary")
async def get_metrics_summary(api_key: str = Depends(verify_api_key)):
    """
    Get metrics summary
    
    Returns high-level overview of system performance
    """
    try:
        collector = get_metrics_collector()
        summary = collector.get_summary()
        
        return {
            "status": "success",
            "summary": summary
        }
        
    except Exception as e:
        logger.error(f"Error getting metrics summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/endpoint/{endpoint_name}")
async def get_endpoint_metrics(
    endpoint_name: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Get metrics for a specific endpoint
    """
    try:
        collector = get_metrics_collector()
        stats = collector.get_endpoint_stats(endpoint_name)
        
        return {
            "status": "success",
            "endpoint": endpoint_name,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting endpoint metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/metrics/reset")
async def reset_metrics(api_key: str = Depends(verify_api_key)):
    """
    Reset all metrics
    
    Requires admin authentication
    """
    try:
        collector = get_metrics_collector()
        collector.reset_metrics()
        
        return {
            "status": "success",
            "message": "Metrics reset successfully"
        }
        
    except Exception as e:
        logger.error(f"Error resetting metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Made with Bob
