"""
Pytest configuration and fixtures
"""
import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app
from app.config import settings


@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Authentication headers for API requests"""
    return {"Authorization": f"Bearer {settings.API_KEY}"}


@pytest.fixture
def mock_openai():
    """Mock OpenAI API calls"""
    with patch('openai.OpenAI') as mock:
        # Mock embeddings
        mock_client = Mock()
        mock_client.embeddings.create.return_value = Mock(
            data=[Mock(embedding=[0.1] * 1536)]
        )
        
        # Mock chat completions
        mock_client.chat.completions.create.return_value = Mock(
            choices=[Mock(
                message=Mock(content="This is a test response from the LLM.")
            )],
            usage=Mock(
                prompt_tokens=100,
                completion_tokens=50,
                total_tokens=150
            )
        )
        
        mock.return_value = mock_client
        yield mock


@pytest.fixture
def mock_pinecone():
    """Mock Pinecone API calls"""
    with patch('pinecone.Pinecone') as mock:
        mock_client = Mock()
        mock_index = Mock()
        
        # Mock query results
        mock_index.query.return_value = Mock(
            matches=[
                Mock(
                    id="doc1",
                    score=0.95,
                    metadata={
                        "text": "IBM Cloud is a cloud computing platform.",
                        "source": "https://cloud.ibm.com/docs",
                        "title": "IBM Cloud Overview"
                    }
                ),
                Mock(
                    id="doc2",
                    score=0.88,
                    metadata={
                        "text": "IBM Cloud provides infrastructure and platform services.",
                        "source": "https://cloud.ibm.com/docs/overview",
                        "title": "Cloud Services"
                    }
                )
            ]
        )
        
        # Mock upsert
        mock_index.upsert.return_value = Mock(upserted_count=1)
        
        # Mock delete
        mock_index.delete.return_value = {}
        
        # Mock describe_index_stats
        mock_index.describe_index_stats.return_value = Mock(
            total_vector_count=100,
            namespaces={"default": Mock(vector_count=100)}
        )
        
        mock_client.Index.return_value = mock_index
        mock.return_value = mock_client
        
        yield mock


@pytest.fixture
def sample_documents():
    """Sample documents for testing"""
    return [
        {
            "id": "doc1",
            "text": "IBM Cloud is a comprehensive cloud computing platform that provides infrastructure, platform, and software services.",
            "metadata": {
                "source": "https://cloud.ibm.com/docs",
                "title": "IBM Cloud Overview",
                "section": "overview"
            }
        },
        {
            "id": "doc2",
            "text": "Kubernetes on IBM Cloud provides a managed container orchestration service for deploying and managing containerized applications.",
            "metadata": {
                "source": "https://cloud.ibm.com/docs/containers",
                "title": "Kubernetes Service",
                "section": "containers"
            }
        }
    ]


@pytest.fixture
def sample_questions():
    """Sample questions for testing"""
    return [
        "What is IBM Cloud?",
        "How do I deploy a container on IBM Cloud?",
        "What services does IBM Cloud provide?",
        "How do I set up Kubernetes on IBM Cloud?",
        "What is the pricing for IBM Cloud services?"
    ]


@pytest.fixture(autouse=True)
def reset_metrics():
    """Reset metrics before each test"""
    from services.monitoring_service import metrics_collector
    metrics_collector.reset()
    yield


@pytest.fixture
def mock_scraper():
    """Mock web scraper"""
    with patch('scraper.base_scraper.AsyncWebScraper') as mock:
        mock_instance = Mock()
        mock_instance.scrape_page.return_value = {
            "url": "https://cloud.ibm.com/docs",
            "title": "IBM Cloud Documentation",
            "content": "This is sample documentation content.",
            "links": ["https://cloud.ibm.com/docs/overview"]
        }
        mock.return_value = mock_instance
        yield mock


@pytest.fixture
def test_env_vars(monkeypatch):
    """Set test environment variables"""
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("PINECONE_API_KEY", "test-pinecone-key")
    monkeypatch.setenv("PINECONE_ENVIRONMENT", "test-env")
    monkeypatch.setenv("API_KEY", "test-api-key")
    monkeypatch.setenv("ENVIRONMENT", "test")

# Made with Bob
