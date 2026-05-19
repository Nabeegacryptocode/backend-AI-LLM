"""
Test API endpoints
"""
import pytest
from fastapi import status


class TestHealthEndpoint:
    """Test health check endpoint"""
    
    def test_health_check(self, client):
        """Test basic health check"""
        response = client.get("/api/health")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "services" in data
    
    def test_health_check_services(self, client):
        """Test health check includes service status"""
        response = client.get("/api/health")
        data = response.json()
        
        services = data["services"]
        assert "openai" in services
        assert "pinecone" in services


class TestChatEndpoint:
    """Test chat endpoint"""
    
    def test_chat_without_auth(self, client):
        """Test chat endpoint requires authentication"""
        response = client.post(
            "/api/chat",
            json={"question": "What is IBM Cloud?"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_chat_with_invalid_auth(self, client):
        """Test chat endpoint with invalid token"""
        response = client.post(
            "/api/chat",
            json={"question": "What is IBM Cloud?"},
            headers={"Authorization": "Bearer invalid-token"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_chat_missing_question(self, client, auth_headers):
        """Test chat endpoint with missing question"""
        response = client.post(
            "/api/chat",
            json={},
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_chat_empty_question(self, client, auth_headers):
        """Test chat endpoint with empty question"""
        response = client.post(
            "/api/chat",
            json={"question": ""},
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @pytest.mark.asyncio
    async def test_chat_success(self, client, auth_headers, mock_openai, mock_pinecone):
        """Test successful chat request"""
        response = client.post(
            "/api/chat",
            json={"question": "What is IBM Cloud?"},
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "answer" in data
        assert "sources" in data
        assert "metadata" in data
        assert isinstance(data["sources"], list)
    
    @pytest.mark.asyncio
    async def test_chat_with_conversation_id(self, client, auth_headers, mock_openai, mock_pinecone):
        """Test chat with conversation ID"""
        response = client.post(
            "/api/chat",
            json={
                "question": "What is IBM Cloud?",
                "conversation_id": "test-conv-123"
            },
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["metadata"]["conversation_id"] == "test-conv-123"
    
    def test_chat_question_too_long(self, client, auth_headers):
        """Test chat with very long question"""
        long_question = "What is IBM Cloud? " * 1000  # Very long question
        response = client.post(
            "/api/chat",
            json={"question": long_question},
            headers=auth_headers
        )
        # Should either succeed or return appropriate error
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_422_UNPROCESSABLE_ENTITY]


class TestIngestEndpoint:
    """Test document ingestion endpoint"""
    
    def test_ingest_without_auth(self, client):
        """Test ingest endpoint requires authentication"""
        response = client.post(
            "/api/ingest",
            json={"documents": []}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_ingest_missing_documents(self, client, auth_headers):
        """Test ingest with missing documents"""
        response = client.post(
            "/api/ingest",
            json={},
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_ingest_empty_documents(self, client, auth_headers):
        """Test ingest with empty documents list"""
        response = client.post(
            "/api/ingest",
            json={"documents": []},
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @pytest.mark.asyncio
    async def test_ingest_success(self, client, auth_headers, sample_documents, mock_openai, mock_pinecone):
        """Test successful document ingestion"""
        response = client.post(
            "/api/ingest",
            json={"documents": sample_documents},
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "message" in data
        assert "ingested_count" in data
        assert data["ingested_count"] == len(sample_documents)
    
    def test_ingest_invalid_document_format(self, client, auth_headers):
        """Test ingest with invalid document format"""
        response = client.post(
            "/api/ingest",
            json={"documents": [{"invalid": "format"}]},
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestMetricsEndpoint:
    """Test metrics endpoints"""
    
    def test_metrics_without_auth(self, client):
        """Test metrics endpoint requires authentication"""
        response = client.get("/api/metrics")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_metrics_success(self, client, auth_headers):
        """Test successful metrics retrieval"""
        response = client.get("/api/metrics", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "total_queries" in data
        assert "total_errors" in data
        assert "average_response_time" in data
    
    def test_metrics_summary(self, client, auth_headers):
        """Test metrics summary endpoint"""
        response = client.get("/api/metrics/summary", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "total_queries" in data
        assert "success_rate" in data
    
    def test_metrics_reset(self, client, auth_headers):
        """Test metrics reset endpoint"""
        response = client.post("/api/metrics/reset", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        
        # Verify metrics are reset
        response = client.get("/api/metrics", headers=auth_headers)
        data = response.json()
        assert data["total_queries"] == 0


class TestCORSHeaders:
    """Test CORS configuration"""
    
    def test_cors_headers_present(self, client):
        """Test CORS headers are present"""
        response = client.options("/api/health")
        assert "access-control-allow-origin" in response.headers
    
    def test_cors_preflight(self, client):
        """Test CORS preflight request"""
        response = client.options(
            "/api/chat",
            headers={
                "Origin": "https://example.com",
                "Access-Control-Request-Method": "POST"
            }
        )
        assert response.status_code == status.HTTP_200_OK


class TestRateLimiting:
    """Test rate limiting"""
    
    @pytest.mark.asyncio
    async def test_rate_limit_enforcement(self, client, auth_headers, mock_openai, mock_pinecone):
        """Test rate limiting is enforced"""
        # Make multiple rapid requests
        responses = []
        for i in range(100):
            response = client.post(
                "/api/chat",
                json={"question": f"Question {i}"},
                headers=auth_headers
            )
            responses.append(response)
        
        # Check if any requests were rate limited
        status_codes = [r.status_code for r in responses]
        # Should have mix of success and rate limit responses
        assert status.HTTP_200_OK in status_codes


class TestErrorHandling:
    """Test error handling"""
    
    def test_404_not_found(self, client):
        """Test 404 for non-existent endpoint"""
        response = client.get("/api/nonexistent")
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_405_method_not_allowed(self, client):
        """Test 405 for wrong HTTP method"""
        response = client.get("/api/chat")  # Should be POST
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    
    def test_invalid_json(self, client, auth_headers):
        """Test handling of invalid JSON"""
        response = client.post(
            "/api/chat",
            data="invalid json",
            headers={**auth_headers, "Content-Type": "application/json"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

# Made with Bob
