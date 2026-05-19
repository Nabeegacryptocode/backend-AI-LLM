"""
Test service layer components
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
import numpy as np


class TestVectorService:
    """Test vector database service"""
    
    @pytest.mark.asyncio
    async def test_initialize_service(self, mock_pinecone):
        """Test vector service initialization"""
        from services.vector_service import VectorService
        
        service = VectorService()
        await service.initialize()
        
        assert service.index is not None
    
    @pytest.mark.asyncio
    async def test_upsert_vectors(self, mock_pinecone):
        """Test upserting vectors"""
        from services.vector_service import VectorService
        
        service = VectorService()
        await service.initialize()
        
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
        await service.initialize()
        
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
        await service.initialize()
        
        await service.delete_vectors(["doc1", "doc2"])
        # Should not raise exception
    
    @pytest.mark.asyncio
    async def test_get_stats(self, mock_pinecone):
        """Test getting index statistics"""
        from services.vector_service import VectorService
        
        service = VectorService()
        await service.initialize()
        
        stats = await service.get_stats()
        assert "total_vector_count" in stats


class TestEmbeddingService:
    """Test embedding generation service"""
    
    @pytest.mark.asyncio
    async def test_generate_embedding(self, mock_openai):
        """Test generating single embedding"""
        from services.embedding_service import EmbeddingService
        
        service = EmbeddingService()
        embedding = await service.generate_embedding("Test text")
        
        assert isinstance(embedding, list)
        assert len(embedding) == 1536
    
    @pytest.mark.asyncio
    async def test_generate_embeddings_batch(self, mock_openai):
        """Test generating multiple embeddings"""
        from services.embedding_service import EmbeddingService
        
        service = EmbeddingService()
        texts = ["Text 1", "Text 2", "Text 3"]
        embeddings = await service.generate_embeddings(texts)
        
        assert len(embeddings) == len(texts)
        assert all(len(emb) == 1536 for emb in embeddings)
    
    @pytest.mark.asyncio
    async def test_embedding_empty_text(self, mock_openai):
        """Test handling empty text"""
        from services.embedding_service import EmbeddingService
        
        service = EmbeddingService()
        
        with pytest.raises(ValueError):
            await service.generate_embedding("")
    
    @pytest.mark.asyncio
    async def test_embedding_caching(self, mock_openai):
        """Test embedding caching (if implemented)"""
        from services.embedding_service import EmbeddingService
        
        service = EmbeddingService()
        text = "Test text for caching"
        
        # Generate twice
        emb1 = await service.generate_embedding(text)
        emb2 = await service.generate_embedding(text)
        
        # Should be identical
        assert emb1 == emb2


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
    async def test_generate_answer_no_results(self, mock_openai, mock_pinecone):
        """Test handling when no relevant documents found"""
        # Mock empty search results
        mock_pinecone.return_value.Index.return_value.query.return_value = Mock(matches=[])
        
        from services.rag_service import RAGService
        
        service = RAGService()
        result = await service.generate_answer("Completely unrelated question")
        
        # Should still return an answer (fallback behavior)
        assert "answer" in result
    
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
        collector.record_query(response_time=0.5, tokens_used=100)
        
        metrics = collector.get_metrics()
        assert metrics["total_queries"] == 1
        assert metrics["total_tokens_used"] == 100
    
    def test_record_error(self):
        """Test recording an error"""
        from services.monitoring_service import MetricsCollector
        
        collector = MetricsCollector()
        collector.record_error("TestError")
        
        metrics = collector.get_metrics()
        assert metrics["total_errors"] == 1
        assert "TestError" in metrics["error_types"]
    
    def test_performance_monitor(self):
        """Test performance monitoring context manager"""
        from services.monitoring_service import PerformanceMonitor
        import time
        
        with PerformanceMonitor("test_operation") as monitor:
            time.sleep(0.1)
        
        assert monitor.duration >= 0.1
    
    def test_structured_logger(self):
        """Test structured logging"""
        from services.monitoring_service import StructuredLogger
        
        logger = StructuredLogger("test")
        
        # Should not raise exceptions
        logger.info("Test message", extra={"key": "value"})
        logger.error("Test error", extra={"error": "details"})


class TestDocumentProcessor:
    """Test document processing"""
    
    def test_chunk_text(self):
        """Test text chunking"""
        from scraper.document_processor import DocumentProcessor
        
        processor = DocumentProcessor()
        text = "This is a test. " * 100  # Long text
        
        chunks = processor.chunk_text(text, chunk_size=100, overlap=20)
        
        assert len(chunks) > 1
        assert all(len(chunk) <= 120 for chunk in chunks)  # chunk_size + overlap
    
    def test_clean_text(self):
        """Test text cleaning"""
        from scraper.document_processor import DocumentProcessor
        
        processor = DocumentProcessor()
        dirty_text = "  Test   text\n\n\nwith   extra   spaces  "
        
        clean = processor.clean_text(dirty_text)
        
        assert clean == "Test text with extra spaces"
    
    def test_extract_metadata(self):
        """Test metadata extraction"""
        from scraper.document_processor import DocumentProcessor
        
        processor = DocumentProcessor()
        html = """
        <html>
            <head>
                <title>Test Page</title>
                <meta name="description" content="Test description">
            </head>
            <body>Content</body>
        </html>
        """
        
        metadata = processor.extract_metadata(html, "https://example.com")
        
        assert metadata["title"] == "Test Page"
        assert metadata["url"] == "https://example.com"

# Made with Bob
