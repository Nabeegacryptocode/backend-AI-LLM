"""
Pydantic models for request/response validation
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    question: str = Field(..., min_length=1, max_length=1000, description="User's question")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for context")
    max_tokens: Optional[int] = Field(1000, ge=100, le=4000, description="Maximum tokens in response")


class Source(BaseModel):
    """Source document model"""
    title: str = Field(..., description="Document title")
    url: str = Field(..., description="Document URL")
    content: str = Field(..., description="Relevant content snippet")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance score")


class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    answer: str = Field(..., description="Generated answer")
    sources: List[Source] = Field(default_factory=list, description="Source documents")
    conversation_id: str = Field(..., description="Conversation ID")
    tokens_used: int = Field(..., description="Total tokens used")


class DocumentMetadata(BaseModel):
    """Metadata for a document"""
    source: str = Field(..., description="Source URL or identifier")
    title: str = Field(..., description="Document title")
    section: Optional[str] = Field(None, description="Document section")


class Document(BaseModel):
    """Document model for direct ingestion"""
    id: str = Field(..., description="Document ID")
    text: str = Field(..., description="Document text content")
    metadata: DocumentMetadata = Field(..., description="Document metadata")


class IngestRequest(BaseModel):
    """Request model for document ingestion from URL"""
    url: str = Field(..., description="URL to scrape")
    source_type: str = Field(..., description="Type of source (ibm-cloud, ibm-watson, etc.)")
    force_refresh: bool = Field(False, description="Force re-scraping even if already exists")


class DirectIngestRequest(BaseModel):
    """Request model for direct document ingestion"""
    documents: List[Document] = Field(..., description="List of documents to ingest")


class IngestResponse(BaseModel):
    """Response model for document ingestion"""
    status: str = Field(..., description="Status of ingestion")
    documents_processed: int = Field(..., description="Number of documents processed")
    chunks_created: int = Field(..., description="Number of chunks created")
    message: str = Field(..., description="Status message")


class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Current timestamp")
    services: dict = Field(default_factory=dict, description="Status of dependent services")


class SourceInfo(BaseModel):
    """Information about a documentation source"""
    title: str = Field(..., description="Source title")
    url: str = Field(..., description="Source URL")
    source_type: str = Field(..., description="Type of source")
    last_updated: datetime = Field(..., description="Last update timestamp")
    document_count: int = Field(..., description="Number of documents")


class SourcesResponse(BaseModel):
    """Response model for sources endpoint"""
    sources: List[SourceInfo] = Field(default_factory=list, description="List of sources")
    total_documents: int = Field(..., description="Total number of documents")


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")

# Made with Bob
