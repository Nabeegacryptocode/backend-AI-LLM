"""
Test service layer components
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock


class TestVectorService:
    """Test vector database service"""
    
    def test_initialize_service(self, mock_pinecone):
        """Test vector service initialization"""
        from services.vector_service import VectorService
        
        service = VectorService()
        service.initialize()
        
        assert service.index is not None
    
    @pytest.mark.asyncio
    async def test_upsert_vectors(self, mock_pinecone):
        """Test upserting vectors"""
        from services.vector_service import VectorService
        
        service = VectorService()
        service.initialize()
        
        vectors = [
            {
                "id": "doc1",
                "values": [0.1] * 1536,
                "metadata": {"text": "Test document"}
            }
        ]
        
        result = await service.upsert_vectors(vectors)
        assert result["upserted_count"] == 1
    
    @pytest.mark.asyncio
    async def test_search_vectors(self, mock_pinecone):
        """Test vector search"""
        from services.vector_service import VectorService
        
        service = VectorService()
        service.initialize()
        
        query_vector = [0.1] * 1536
        results = await service.search(query_vector, top_k=5)
        
        assert len(results) > 0
        assert "id" in results[0]
        assert "score" in results[0]
        assert "metadata" in results[0]
    
    @pytest.mark.asyncio
    async def test_delete_vectors(self, mock_pinecone):
        """Test deleting vectors"""
        from services.vector_service import VectorService
        
        service = VectorService()
        service.initialize()
        
        result = await service.delete_vectors(["doc1", "doc2"])
        assert result["deleted_count"] == 2
    
    @pytest.mark.asyncio
    async def test_get_index_stats(self, mock_pinecone):
        """Test getting index statistics"""
        from services.vector_service import VectorService
        
        service = VectorService()
        service.initialize()
        
        stats = await service.get_index_stats()
        assert "total_vector_count" in stats


class TestEmbeddingService:
    """Test embedding generation service"""
    
    @pytest.mark.asyncio
    async def test_embed_document(self, mock_openai):
        """Test embedding single document"""
        from services.embedding_service import EmbeddingService
        
        service = EmbeddingService()
        result = await service.embed_document(
            content="Test text",
            metadata={"title": "Test", "url": "https://example.com"}
        )
        
        assert "id" in result
        assert "values" in result
        assert "metadata" in result
        assert len(result["values"]) == 1536
    
    @pytest.mark.asyncio
    async def test_embed_documents_batch(self, mock_openai):
        """Test embedding multiple documents"""
        from services.embedding_service import EmbeddingService
        
        service = EmbeddingService()
        documents = [
            {"content": "Text 1", "metadata": {"title": "Doc 1"}},
            {"content": "Text 2", "metadata": {"title": "Doc 2"}},
            {"content": "Text 3", "metadata": {"title": "Doc 3"}}
        ]
        results = await service.embed_documents_batch(documents)
        
        assert len(results) == len(documents)
        assert all("values" in r for r in results)
    
    @pytest.mark.asyncio
    async def test_search_similar(self, mock_openai, mock_pinecone):
        """Test searching similar documents"""
        from services.embedding_service import EmbeddingService
        
        service = EmbeddingService()
        results = await service.search_similar("Test query", top_k=5)
        
        assert isinstance(results, list)


class TestRAGService:
    """Test RAG (Retrieval Augmented Generation) service"""
    
    @pytest.mark.asyncio
    async def test_generate_answer(self, mock_openai, mock_pinecone):
        """Test generating answer with RAG"""
        from services.rag_service import RAGService
        
        service = RAGService()
        result = await service.generate_answer("What is IBM Cloud?")
        
        assert "answer" in result
        assert "sources" in result
        assert "metadata" in result
        assert isinstance(result["sources"], list)
    
    @pytest.mark.asyncio
    async def test_generate_answer_with_context(self, mock_openai, mock_pinecone):
        """Test generating answer with conversation context"""
        from services.rag_service import RAGService
        
        service = RAGService()
        result = await service.generate_answer(
            "What is IBM Cloud?",
            conversation_id="test-123"
        )
        
        assert result["metadata"]["conversation_id"] == "test-123"
    
    @pytest.mark.asyncio
    async def test_source_attribution(self, mock_openai, mock_pinecone):
        """Test that sources are properly attributed"""
        from services.rag_service import RAGService
        
        service = RAGService()
        result = await service.generate_answer("What is IBM Cloud?")
        
        sources = result["sources"]
        assert len(sources) > 0
        
        for source in sources:
            assert "url" in source
            assert "title" in source
            assert "relevance_score" in source
    
    @pytest.mark.asyncio
    async def test_metadata_tracking(self, mock_openai, mock_pinecone):
        """Test metadata is properly tracked"""
        from services.rag_service import RAGService
        
        service = RAGService()
        result = await service.generate_answer("What is IBM Cloud?")
        
        metadata = result["metadata"]
        assert "model" in metadata
        assert "tokens_used" in metadata
        assert "response_time" in metadata


class TestMonitoringService:
    """Test monitoring and metrics service"""
    
    def test_metrics_collector_initialization(self):
        """Test metrics collector initializes correctly"""
        from services.monitoring_service import MetricsCollector
        
        collector = MetricsCollector()
        metrics = collector.get_metrics()
        
        assert metrics["total_queries"] == 0
        assert metrics["total_errors"] == 0
    
    def test_record_query(self):
        """Test recording a query"""
        from services.monitoring_service import MetricsCollector
        
        collector = MetricsCollector()
        collector.record_query(
            endpoint="/api/chat",
            duration=0.5,
            success=True,
            tokens_used=100
        )
        
        metrics = collector.get_metrics()
        assert metrics["total_queries"] == 1
        assert metrics["token_usage"]["total_tokens"] == 100
    
    def test_record_query_with_error(self):
        """Test recording a failed query"""
        from services.monitoring_service import MetricsCollector
        
        collector = MetricsCollector()
        collector.record_query(
            endpoint="/api/chat",
            duration=0.5,
            success=False,
            error="Test error"
        )
        
        metrics = collector.get_metrics()
        assert metrics["total_errors"] == 1
    
    def test_performance_monitor(self):
        """Test performance monitoring context manager"""
        from services.monitoring_service import PerformanceMonitor
        import time
        
        with PerformanceMonitor("test_operation") as monitor:
            time.sleep(0.1)
        
        assert monitor.duration is not None
        assert monitor.duration >= 0.1
    
    def test_structured_logger(self):
        """Test structured logging"""
        from services.monitoring_service import StructuredLogger
        
        logger = StructuredLogger("test")
        
        # Should not raise exceptions
        logger.info("Test message", extra_field="value")
        logger.error("Test error", error_code=500)
    
    def test_get_summary(self):
        """Test getting metrics summary"""
        from services.monitoring_service import MetricsCollector
        
        collector = MetricsCollector()
        collector.record_query("/api/chat", 0.5, True, 100)
        collector.record_query("/api/chat", 0.3, True, 50)
        
        summary = collector.get_summary()
        assert summary["total_queries"] == 2
        assert summary["total_errors"] == 0
        assert summary["avg_response_time"] > 0


class TestDocumentProcessor:
    """Test document processing"""
    
    def test_chunk_text(self):
        """Test text chunking"""
        from scraper.document_processor import DocumentProcessor
        
        processor = DocumentProcessor()
        text = "This is a test. " * 100  # Long text
        
        chunks = processor.chunk_text(text, chunk_size=100)
        
        assert len(chunks) > 1
        assert all(len(chunk) <= 120 for chunk in chunks)  # chunk_size + some overlap
    
    def test_clean_text(self):
        """Test text cleaning"""
        from scraper.document_processor import DocumentProcessor
        
        processor = DocumentProcessor()
        dirty_text = "  Test   text\n\n\nwith   extra   spaces  "
        
        clean = processor.clean_text(dirty_text)
        
        assert clean == "Test text with extra spaces"
    
    def test_process_document(self):
        """Test document processing"""
        from scraper.document_processor import DocumentProcessor
        
        processor = DocumentProcessor()
        
        # Test basic processing
        text = "This is a test document with some content."
        chunks = processor.chunk_text(text, chunk_size=20)
        
        assert len(chunks) >= 1
        assert all(isinstance(chunk, str) for chunk in chunks)

# Made with Bob
