"""
Document ingestion endpoints
"""
from fastapi import APIRouter, HTTPException, Header, Body
from typing import Optional, Union
import logging

from backend.app.models import IngestRequest, DirectIngestRequest, IngestResponse
from backend.app.config import settings
from backend.services.embedding_service import embedding_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/ingest")
async def ingest_document(
    request: Union[IngestRequest, DirectIngestRequest] = Body(...),
    authorization: Optional[str] = Header(None)
):
    """
    Ingest documents either from a URL or directly
    
    Supports two modes:
    1. URL-based: Scrapes content from the provided URL
    2. Direct: Accepts pre-processed documents with text and metadata
    
    This endpoint:
    1. Processes and chunks the document(s)
    2. Generates embeddings
    3. Stores in vector database
    """
    try:
        # Verify API key
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
        
        api_key = authorization.replace("Bearer ", "")
        if api_key != settings.API_KEY:
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        # Check if it's direct document ingestion
        if isinstance(request, DirectIngestRequest):
            logger.info(f"Direct ingestion of {len(request.documents)} documents")
            
            # Ingest documents directly
            ingested_count = 0
            for doc in request.documents:
                try:
                    await embedding_service.ingest_document(
                        doc_id=doc.id,
                        text=doc.text,
                        metadata=doc.metadata.model_dump()
                    )
                    ingested_count += 1
                except Exception as e:
                    logger.error(f"Error ingesting document {doc.id}: {str(e)}")
            
            return {
                "status": "success",
                "ingested_count": ingested_count,
                "failed_count": len(request.documents) - ingested_count,
                "message": f"Successfully ingested {ingested_count} of {len(request.documents)} documents"
            }
        else:
            # URL-based ingestion
            logger.info(f"Ingesting document from: {request.url}")
            
            # TODO: Implement actual URL-based document ingestion
            # For now, return a mock response
            
            return IngestResponse(
                status="success",
                documents_processed=1,
                chunks_created=5,
                message=f"URL-based ingestion not yet fully implemented. URL: {request.url}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ingesting document: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error ingesting document: {str(e)}"
        )


@router.post("/ingest/batch")
async def ingest_batch(
    urls: list[str],
    source_type: str,
    authorization: Optional[str] = Header(None)
):
    """
    Batch ingest multiple documents
    """
    # Verify API key
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    api_key = authorization.replace("Bearer ", "")
    if api_key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    logger.info(f"Batch ingesting {len(urls)} documents")
    
    # TODO: Implement batch ingestion
    return {
        "status": "success",
        "total_urls": len(urls),
        "processed": 0,
        "failed": 0,
        "message": "Batch ingestion not yet implemented"
    }


@router.get("/sources")
async def list_sources(
    authorization: Optional[str] = Header(None)
):
    """
    List all ingested documentation sources
    """
    # Verify API key
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    api_key = authorization.replace("Bearer ", "")
    if api_key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # TODO: Implement source listing from database
    return {
        "sources": [],
        "total_documents": 0,
        "message": "Source listing not yet implemented"
    }

# Made with Bob
