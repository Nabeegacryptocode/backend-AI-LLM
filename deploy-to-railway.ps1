# Railway Deployment Script for Windows PowerShell
# This script helps you deploy the IBM Docs LLM backend to Railway

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  IBM Docs LLM - Railway Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Railway CLI is installed
Write-Host "Checking for Railway CLI..." -ForegroundColor Yellow
$railwayInstalled = Get-Command railway -ErrorAction SilentlyContinue

if (-not $railwayInstalled) {
    Write-Host "Railway CLI not found. Installing..." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Please run this command in PowerShell as Administrator:" -ForegroundColor Red
    Write-Host "iwr https://railway.app/install.ps1 | iex" -ForegroundColor Green
    Write-Host ""
    Write-Host "After installation, run this script again." -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ Railway CLI found" -ForegroundColor Green
Write-Host ""

# Login to Railway
Write-Host "Step 1: Login to Railway" -ForegroundColor Cyan
Write-Host "This will open your browser for authentication..." -ForegroundColor Yellow
railway login

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Login failed. Please try again." -ForegroundColor Red
    exit 1
}

Write-Host "✓ Logged in successfully" -ForegroundColor Green
Write-Host ""

# Initialize or link project
Write-Host "Step 2: Initialize Railway Project" -ForegroundColor Cyan
Write-Host "Choose an option:" -ForegroundColor Yellow
Write-Host "1. Create a new project" -ForegroundColor White
Write-Host "2. Link to existing project" -ForegroundColor White
$choice = Read-Host "Enter choice (1 or 2)"

if ($choice -eq "1") {
    railway init
} elseif ($choice -eq "2") {
    railway link
} else {
    Write-Host "✗ Invalid choice" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Project initialized" -ForegroundColor Green
Write-Host ""

# Set environment variables
Write-Host "Step 3: Set Environment Variables" -ForegroundColor Cyan
Write-Host "Setting up required environment variables..." -ForegroundColor Yellow
Write-Host ""

# Generate API key
$apiKey = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})
Write-Host "Generated API Key: $apiKey" -ForegroundColor Green
Write-Host "IMPORTANT: Save this key for WordPress plugin configuration!" -ForegroundColor Red
Write-Host ""

# Set variables from template
Write-Host "Setting OpenAI API Key..." -ForegroundColor Yellow
railway variables set OPENAI_API_KEY="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"

Write-Host "Setting Pinecone API Key..." -ForegroundColor Yellow
railway variables set PINECONE_API_KEY="pcsk_4QR1Sd_4ZBPgiE51J7aJ4zFPvTgYb6uuKQuYSwv8qvWkinTKHJyTUhbheUXNCCs2pz9bFn"

Write-Host "Setting Pinecone Environment..." -ForegroundColor Yellow
railway variables set PINECONE_ENVIRONMENT="us-west1-gcp"

Write-Host "Setting Pinecone Index Name..." -ForegroundColor Yellow
railway variables set PINECONE_INDEX_NAME="ibm-docs"

Write-Host "Setting API Key..." -ForegroundColor Yellow
railway variables set API_KEY="$apiKey"

Write-Host "Setting CORS Origins..." -ForegroundColor Yellow
railway variables set ALLOWED_ORIGINS='["*"]'

Write-Host "Setting Environment..." -ForegroundColor Yellow
railway variables set ENVIRONMENT="production"

Write-Host "Setting Log Level..." -ForegroundColor Yellow
railway variables set LOG_LEVEL="INFO"

Write-Host "✓ Environment variables set" -ForegroundColor Green
Write-Host ""

# Deploy
Write-Host "Step 4: Deploy to Railway" -ForegroundColor Cyan
Write-Host "Deploying application..." -ForegroundColor Yellow
railway up

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Deployment failed. Check logs with: railway logs" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Deployment successful" -ForegroundColor Green
Write-Host ""

# Generate domain
Write-Host "Step 5: Generate Domain" -ForegroundColor Cyan
Write-Host "Generating public domain..." -ForegroundColor Yellow
railway domain

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Deployment Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Note your deployment URL from above" -ForegroundColor White
Write-Host "2. Test the API: curl https://your-app.railway.app/api/health" -ForegroundColor White
Write-Host "3. Save your API Key: $apiKey" -ForegroundColor White
Write-Host "4. Configure WordPress plugin with URL and API Key" -ForegroundColor White
Write-Host "5. Initialize Pinecone: python scripts/setup_pinecone.py" -ForegroundColor White
Write-Host "6. Ingest docs: python scripts/ingest_ibm_docs.py --sections overview --max-pages 20" -ForegroundColor White
Write-Host ""
Write-Host "View logs: railway logs" -ForegroundColor Cyan
Write-Host "View dashboard: railway open" -ForegroundColor Cyan
Write-Host ""
