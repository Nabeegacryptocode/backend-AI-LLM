"""
Chat endpoints for question answering
"""
from fastapi import APIRouter, HTTPException, Header
from typing import Optional
import logging

from app.models import ChatRequest, ChatResponse, Source
from app.config import settings
from services.rag_service import rag_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Process a chat request using RAG pipeline
    
    This endpoint:
    1. Generates embedding for the question
    2. Retrieves relevant documents from vector DB
    3. Constructs context from retrieved documents
    4. Generates response using LLM
    5. Returns answer with source citations
    """
    try:
        # Verify API key
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
        
        api_key = authorization.replace("Bearer ", "")
        if api_key != settings.API_KEY:
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        logger.info(f"Processing chat request: {request.question[:50]}...")
        
        # Use RAG service to generate answer
        result = await rag_service.generate_answer(
            question=request.question,
            conversation_id=request.conversation_id,
            max_tokens=request.max_tokens
        )
        
        # Format sources for response
        sources = [
            Source(
                title=src["title"],
                url=src["url"],
                content=src["content"],
                relevance_score=src["relevance_score"]
            )
            for src in result["sources"]
        ]
        
        response = ChatResponse(
            answer=result["answer"],
            sources=sources,
            conversation_id=result["conversation_id"],
            tokens_used=result["tokens_used"]
        )
        
        logger.info(f"Chat request processed successfully. Retrieved {result['retrieved_docs']} docs, used {result['tokens_used']} tokens")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    authorization: Optional[str] = Header(None)
):
    """
    Retrieve conversation history
    """
    # Verify API key
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    api_key = authorization.replace("Bearer ", "")
    if api_key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # TODO: Implement conversation history retrieval
    return {
        "conversation_id": conversation_id,
        "messages": [],
        "created_at": "2024-01-01T00:00:00Z",
        "message": "Conversation history not yet implemented"
    }

# Made with Bob
