# RAG Banking Assistant - Deployment Script
# Run this script in PowerShell to deploy the application

Write-Host "🚀 RAG Banking Assistant Deployment Script" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green

# Check if Docker is running
Write-Host "\n📋 Step 1: Checking Docker..." -ForegroundColor Yellow
try {
    docker --version | Out-Null
    Write-Host "✅ Docker is installed" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not installed or not running" -ForegroundColor Red
    Write-Host "Please install Docker Desktop and try again" -ForegroundColor Red
    exit 1
}

# Check if .env file exists
Write-Host "\n📋 Step 2: Checking environment variables..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "✅ .env file found" -ForegroundColor Green
} else {
    Write-Host "❌ .env file not found" -ForegroundColor Red
    Write-Host "Creating .env template..." -ForegroundColor Yellow
    @"
OPENAI_API_KEY=your_openai_api_key_here
NOMIC_API_KEY=your_nomic_api_key_here
"@ | Out-File -FilePath ".env" -Encoding UTF8
    Write-Host "✅ .env template created. Please add your API keys and run again." -ForegroundColor Green
    exit 1
}

# Check if docs folder has files
Write-Host "\n📋 Step 3: Checking documents..." -ForegroundColor Yellow
if (Test-Path "docs") {
    $docCount = (Get-ChildItem "docs" -Filter "*.pdf", "*.txt").Count
    if ($docCount -gt 0) {
        Write-Host "✅ Found $docCount document(s) in docs folder" -ForegroundColor Green
    } else {
        Write-Host "⚠️  No documents found in docs folder" -ForegroundColor Yellow
        Write-Host "Please add PDF or TXT files to the docs folder" -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠️  docs folder not found, creating it..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path "docs" -Force | Out-Null
    Write-Host "✅ docs folder created. Please add your documents." -ForegroundColor Green
}

# Stop any existing containers
Write-Host "\n📋 Step 4: Cleaning up existing containers..." -ForegroundColor Yellow
docker-compose down 2>$null
Write-Host "✅ Cleanup completed" -ForegroundColor Green

# Build and start services
Write-Host "\n📋 Step 5: Building and starting services..." -ForegroundColor Yellow
Write-Host "This may take a few minutes on first run..." -ForegroundColor Cyan

try {
    docker-compose up --build -d
    Write-Host "✅ Services started successfully" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to start services" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}

# Wait for services to be ready
Write-Host "\n📋 Step 6: Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Check if services are running
Write-Host "\n📋 Step 7: Checking service status..." -ForegroundColor Yellow
$containers = docker ps --format "table {{.Names}}\t{{.Status}}" | Select-String "rag-"
if ($containers) {
    Write-Host "✅ Services are running:" -ForegroundColor Green
    $containers | ForEach-Object { Write-Host "   $_" -ForegroundColor Cyan }
} else {
    Write-Host "❌ Services are not running properly" -ForegroundColor Red
    Write-Host "Check logs with: docker-compose logs" -ForegroundColor Yellow
    exit 1
}

# Index documents if container is ready
Write-Host "\n📋 Step 8: Indexing documents..." -ForegroundColor Yellow
try {
    docker-compose exec rag-app python index.py
    Write-Host "✅ Documents indexed successfully" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Could not index documents automatically" -ForegroundColor Yellow
    Write-Host "You can index them manually later with: docker-compose exec rag-app python index.py" -ForegroundColor Cyan
}

# Success message
Write-Host "\n🎉 Deployment completed successfully!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host "\n📱 Access your application at:" -ForegroundColor Cyan
Write-Host "   🌐 Web Interface: http://localhost:5000" -ForegroundColor White
Write-Host "   🗄️  Qdrant Dashboard: http://localhost:6333/dashboard" -ForegroundColor White

Write-Host "\n🔧 Useful commands:" -ForegroundColor Cyan
Write-Host "   📊 View logs: docker-compose logs -f" -ForegroundColor White
Write-Host "   🛑 Stop services: docker-compose down" -ForegroundColor White
Write-Host "   🔄 Restart services: docker-compose restart" -ForegroundColor White
Write-Host "   📝 Index documents: docker-compose exec rag-app python index.py" -ForegroundColor White

Write-Host "\n✨ Happy querying!" -ForegroundColor Green