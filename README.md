# IBM Docs LLM Backend API

FastAPI-based backend service for the IBM Documentation LLM system.

## Quick Start

### 1. Set up Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

```bash
# Copy example env file
copy .env.example .env

# Edit .env and add your API keys:
# - OPENAI_API_KEY
# - PINECONE_API_KEY
# - API_KEY (generate a secure random key)
```

### 3. Generate API Key

```python
# Run this in Python to generate a secure API key
import secrets
print(secrets.token_urlsafe(32))
```

### 4. Run the API Server

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at `http://localhost:8000`

### 5. Test the API

```bash
# Health check
curl http://localhost:8000/api/health

# Test chat endpoint (replace YOUR_API_KEY)
curl -X POST http://localhost:8000/api/chat \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"question\": \"What is IBM Cloud?\"}"
```

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration
│   ├── models.py            # Pydantic models
│   ├── api/                 # API endpoints
│   │   ├── chat.py
│   │   ├── health.py
│   │   └── ingest.py
│   └── utils/               # Utilities
│       ├── auth.py
│       └── logger.py
├── services/                # Business logic
│   ├── llm_service.py
│   ├── vector_service.py
│   ├── embedding_service.py
│   └── cache_service.py
├── scraper/                 # Documentation scrapers
│   ├── base_scraper.py
│   ├── ibm_cloud_scraper.py
│   └── document_processor.py
├── tests/                   # Tests
├── requirements.txt
└── .env.example
```

## Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `API_KEY` | API key for authentication | Yes | - |
| `OPENAI_API_KEY` | OpenAI API key | Yes | - |
| `PINECONE_API_KEY` | Pinecone API key | Yes | - |
| `PINECONE_ENVIRONMENT` | Pinecone environment | Yes | - |
| `LLM_MODEL` | OpenAI model to use | No | gpt-4-turbo-preview |
| `EMBEDDING_MODEL` | Embedding model | No | text-embedding-3-small |
| `TOP_K_RESULTS` | Number of results to retrieve | No | 5 |
| `CHUNK_SIZE` | Document chunk size | No | 800 |

See `.env.example` for all available variables.

## Development

### Running Tests

```bash
pytest tests/ -v --cov=app
```

### Code Formatting

```bash
# Install dev dependencies
pip install black isort flake8

# Format code
black app/ services/ scraper/
isort app/ services/ scraper/

# Lint
flake8 app/ services/ scraper/
```

### Adding New Endpoints

1. Create endpoint file in `app/api/`
2. Define Pydantic models in `app/models.py`
3. Include router in `app/main.py`
4. Add tests in `tests/`

## Deployment

### Using Docker

```bash
# Build image
docker build -t ibm-docs-llm-api .

# Run container
docker run -p 8000:8000 --env-file .env ibm-docs-llm-api
```

### Using Railway

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

### Using Render

1. Connect your GitHub repository
2. Set environment variables in Render dashboard
3. Deploy automatically on push

## Troubleshooting

### Import Errors

The import errors you see in VSCode are expected before installing dependencies. Run:

```bash
pip install -r requirements.txt
```

### OpenAI API Errors

- Verify your API key is correct
- Check you have sufficient credits
- Ensure you're using a supported model

### Pinecone Connection Issues

- Verify API key and environment
- Check index exists: `pinecone.list_indexes()`
- Ensure index dimension matches embedding model (1536 for text-embedding-3-small)

## Next Steps

1. Set up Pinecone vector database
2. Implement document scraping
3. Ingest IBM documentation
4. Test RAG pipeline
5. Deploy to production

## Support

For issues and questions:
- Check the main [README.md](../README.md)
- Review [ARCHITECTURE.md](../ARCHITECTURE.md)
- See [IMPLEMENTATION_GUIDE.md](../IMPLEMENTATION_GUIDE.md)