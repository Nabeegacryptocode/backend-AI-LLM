"""
Integration tests for end-to-end workflows
"""
import pytest
from fastapi import status
import time
from unittest.mock import patch


class TestEndToEndWorkflow:
    """Test complete end-to-end workflows"""
    
    @pytest.mark.asyncio
    async def test_complete_rag_pipeline(self, client, auth_headers, sample_documents, mock_openai, mock_pinecone):
        """Test complete RAG pipeline from ingestion to query"""
        
        # Step 1: Ingest documents
        ingest_response = client.post(
            "/api/ingest",
            json={"documents": sample_documents},
            headers=auth_headers
        )
        assert ingest_response.status_code == status.HTTP_200_OK
        
        # Step 2: Query the system
        chat_response = client.post(
            "/api/chat",
            json={"question": "What is IBM Cloud?"},
            headers=auth_headers
        )
        assert chat_response.status_code == status.HTTP_200_OK
        
        data = chat_response.json()
        assert "answer" in data
        assert len(data["sources"]) > 0
    
    @pytest.mark.asyncio
    async def test_conversation_flow(self, client, auth_headers, mock_openai, mock_pinecone):
        """Test multi-turn conversation"""
        conversation_id = "test-conv-456"
        
        # First question
        response1 = client.post(
            "/api/chat",
            json={
                "question": "What is IBM Cloud?",
                "conversation_id": conversation_id
            },
            headers=auth_headers
        )
        assert response1.status_code == status.HTTP_200_OK
        
        # Follow-up question
        response2 = client.post(
            "/api/chat",
            json={
                "question": "How do I deploy containers on it?",
                "conversation_id": conversation_id
            },
            headers=auth_headers
        )
        assert response2.status_code == status.HTTP_200_OK
        
        # Both should have same conversation ID
        assert response1.json()["metadata"]["conversation_id"] == conversation_id
        assert response2.json()["metadata"]["conversation_id"] == conversation_id
    
    @pytest.mark.asyncio
    async def test_metrics_tracking(self, client, auth_headers, mock_openai, mock_pinecone):
        """Test that metrics are properly tracked"""
        
        # Make some requests
        for i in range(5):
            client.post(
                "/api/chat",
                json={"question": f"Question {i}"},
                headers=auth_headers
            )
        
        # Check metrics
        metrics_response = client.get("/api/metrics", headers=auth_headers)
        assert metrics_response.status_code == status.HTTP_200_OK
        
        metrics = metrics_response.json()
        assert metrics["total_queries"] >= 5
    
    def test_health_monitoring(self, client):
        """Test health check monitoring"""
        response = client.get("/api/health")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["status"] == "healthy"
        assert all(service in ["configured", "healthy"] for service in data["services"].values())


class TestErrorRecovery:
    """Test error handling and recovery"""
    
    @pytest.mark.asyncio
    async def test_openai_api_failure(self, client, auth_headers, mock_pinecone):
        """Test handling of OpenAI API failures"""
        with patch('openai.OpenAI') as mock:
            mock.return_value.chat.completions.create.side_effect = Exception("API Error")
            
            response = client.post(
                "/api/chat",
                json={"question": "Test question"},
                headers=auth_headers
            )
            
            # Should return error response
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    
    @pytest.mark.asyncio
    async def test_pinecone_connection_failure(self, client, auth_headers, mock_openai):
        """Test handling of Pinecone connection failures"""
        with patch('pinecone.Pinecone') as mock:
            mock.side_effect = Exception("Connection Error")
            
            response = client.post(
                "/api/chat",
                json={"question": "Test question"},
                headers=auth_headers
            )
            
            # Should handle gracefully
            assert response.status_code in [status.HTTP_500_INTERNAL_SERVER_ERROR, status.HTTP_503_SERVICE_UNAVAILABLE]
    
    def test_invalid_api_key_handling(self, client):
        """Test handling of invalid API keys"""
        response = client.post(
            "/api/chat",
            json={"question": "Test"},
            headers={"Authorization": "Bearer invalid"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestPerformance:
    """Test performance characteristics"""
    
    @pytest.mark.asyncio
    async def test_response_time(self, client, auth_headers, mock_openai, mock_pinecone):
        """Test that responses are within acceptable time"""
        start_time = time.time()
        
        response = client.post(
            "/api/chat",
            json={"question": "What is IBM Cloud?"},
            headers=auth_headers
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        assert response.status_code == status.HTTP_200_OK
        assert response_time < 5.0  # Should respond within 5 seconds
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, client, auth_headers, mock_openai, mock_pinecone):
        """Test handling of concurrent requests"""
        import concurrent.futures
        
        def make_request():
            return client.post(
                "/api/chat",
                json={"question": "Test question"},
                headers=auth_headers
            )
        
        # Make 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            responses = [f.result() for f in futures]
        
        # All should succeed
        assert all(r.status_code == status.HTTP_200_OK for r in responses)
    
    @pytest.mark.asyncio
    async def test_large_document_ingestion(self, client, auth_headers, mock_openai, mock_pinecone):
        """Test ingesting large number of documents"""
        # Create 100 documents
        documents = [
            {
                "id": f"doc{i}",
                "text": f"This is document {i} with some content.",
                "metadata": {"source": f"https://example.com/doc{i}"}
            }
            for i in range(100)
        ]
        
        response = client.post(
            "/api/ingest",
            json={"documents": documents},
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["ingested_count"] == 100


class TestDataIntegrity:
    """Test data integrity and consistency"""
    
    @pytest.mark.asyncio
    async def test_source_attribution_accuracy(self, client, auth_headers, mock_openai, mock_pinecone):
        """Test that sources are accurately attributed"""
        response = client.post(
            "/api/chat",
            json={"question": "What is IBM Cloud?"},
            headers=auth_headers
        )
        
        data = response.json()
        sources = data["sources"]
        
        # Each source should have required fields
        for source in sources:
            assert "url" in source
            assert "title" in source
            assert "relevance_score" in source
            assert 0 <= source["relevance_score"] <= 1
    
    @pytest.mark.asyncio
    async def test_metadata_consistency(self, client, auth_headers, mock_openai, mock_pinecone):
        """Test metadata consistency across requests"""
        response = client.post(
            "/api/chat",
            json={"question": "Test question"},
            headers=auth_headers
        )
        
        metadata = response.json()["metadata"]
        
        # Required metadata fields
        assert "model" in metadata
        assert "tokens_used" in metadata
        assert "response_time" in metadata
        assert metadata["tokens_used"] > 0
        assert metadata["response_time"] > 0


class TestSecurityIntegration:
    """Test security features integration"""
    
    def test_authentication_required_all_endpoints(self, client):
        """Test that all protected endpoints require authentication"""
        protected_endpoints = [
            ("/api/chat", "POST", {"question": "Test"}),
            ("/api/ingest", "POST", {"documents": []}),
            ("/api/metrics", "GET", None),
            ("/api/metrics/summary", "GET", None),
        ]
        
        for endpoint, method, data in protected_endpoints:
            if method == "POST":
                response = client.post(endpoint, json=data)
            else:
                response = client.get(endpoint)
            
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_cors_security(self, client):
        """Test CORS security configuration"""
        # Test with allowed origin
        response = client.post(
            "/api/chat",
            json={"question": "Test"},
            headers={
                "Origin": "https://allowed-site.com",
                "Authorization": f"Bearer test-key"
            }
        )
        
        # Should have CORS headers
        assert "access-control-allow-origin" in response.headers
    
    def test_input_sanitization(self, client, auth_headers):
        """Test that inputs are properly sanitized"""
        # Try SQL injection
        response = client.post(
            "/api/chat",
            json={"question": "'; DROP TABLE users; --"},
            headers=auth_headers
        )
        
        # Should handle safely
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_422_UNPROCESSABLE_ENTITY]
        
        # Try XSS
        response = client.post(
            "/api/chat",
            json={"question": "<script>alert('xss')</script>"},
            headers=auth_headers
        )
        
        # Should handle safely
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_422_UNPROCESSABLE_ENTITY]


class TestWordPressIntegration:
    """Test WordPress plugin integration scenarios"""
    
    @pytest.mark.asyncio
    async def test_wordpress_chat_request(self, client, auth_headers, mock_openai, mock_pinecone):
        """Test typical WordPress plugin chat request"""
        # Simulate request from WordPress plugin
        response = client.post(
            "/api/chat",
            json={
                "question": "How do I deploy a container?",
                "conversation_id": "wp-session-123"
            },
            headers={
                **auth_headers,
                "Origin": "https://wordpress-site.com",
                "User-Agent": "WordPress/6.0"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Response should be WordPress-friendly
        assert "answer" in data
        assert "sources" in data
        assert isinstance(data["answer"], str)
    
    def test_wordpress_cors_headers(self, client):
        """Test CORS headers for WordPress requests"""
        response = client.options(
            "/api/chat",
            headers={
                "Origin": "https://wordpress-site.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Authorization, Content-Type"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers

# Made with Bob
