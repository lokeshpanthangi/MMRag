# RAG Banking Assistant - Complete Deployment Guide

## 📋 Prerequisites

### Required Software:
1. **Docker Desktop** - [Download here](https://www.docker.com/products/docker-desktop/)
2. **Python 3.8+** - [Download here](https://www.python.org/downloads/)
3. **Git** (optional) - [Download here](https://git-scm.com/downloads)

### Required API Keys:
1. **OpenAI API Key** - [Get from OpenAI](https://platform.openai.com/api-keys)
2. **Nomic API Key** - [Get from Nomic](https://atlas.nomic.ai/)

---

## 🚀 Step-by-Step Deployment

### Step 1: Environment Setup

#### 1.1 Install Docker Desktop
1. Download Docker Desktop from the official website
2. Run the installer and follow the setup wizard
3. Start Docker Desktop
4. Verify installation by opening terminal/PowerShell and running:
   ```bash
   docker --version
   docker-compose --version
   ```

#### 1.2 Clone/Download Project
```bash
# If using Git
git clone <your-repo-url>
cd RAG

# Or download and extract the project folder
```

#### 1.3 Set Up Environment Variables
1. Create a `.env` file in the project root:
   ```bash
   # Windows PowerShell
   New-Item -Path ".env" -ItemType File
   
   # Or create manually in file explorer
   ```

2. Add your API keys to `.env`:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   NOMIC_API_KEY=your_nomic_api_key_here
   ```

### Step 2: Database Setup (Qdrant Vector Database)

#### 2.1 Start Qdrant Database
```bash
# Navigate to project directory
cd d:\Nani\WEEKS\W6D2\RAG

# Start Qdrant database
docker compose -f docker-compose.db.yml up -d
```

#### 2.2 Verify Qdrant is Running
```bash
# Check running containers
docker ps

# You should see qdrant container running on port 6333
```

### Step 3: Python Environment Setup

#### 3.1 Create Virtual Environment (Recommended)
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Windows CMD:
venv\Scripts\activate.bat
```

#### 3.2 Install Dependencies
```bash
# Install required packages
pip install -r requirements.txt
```

### Step 4: Document Processing

#### 4.1 Add Your Documents
1. Place your PDF and TXT files in the `docs/` folder
2. The system supports:
   - `.pdf` files (using PyPDFLoader)
   - `.txt` files (using TextLoader with UTF-8 encoding)

#### 4.2 Index Documents
```bash
# Process and index documents into Qdrant
python index.py
```

**Expected Output:**
```
Loading PDF: docs/your_document.pdf
Loading TXT: docs/your_document.txt
Documents loaded and indexed successfully!
```

### Step 5: Start the Web Application

#### 5.1 Start Flask Server
```bash
# Start the web application
python app.py
```

**Expected Output:**
```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

#### 5.2 Access the Web Interface
1. Open your web browser
2. Navigate to: `http://localhost:5000`
3. You should see the RAG Banking Assistant interface

---

## 🌐 Using the Web Application

### Interface Features:
- **Modern UI** with gradient background and smooth animations
- **Real-time Chat** with typing indicators
- **Source Attribution** showing document names and page numbers
- **Conversation Memory** maintains context across questions
- **Mobile Responsive** design

### How to Use:
1. **Type your question** in the input field
2. **Press Enter** or click "Ask" button
3. **View the response** with source documents
4. **Continue the conversation** - the system remembers context
5. **Clear conversation** using the "Clear" button if needed

### Example Questions:
- "What are the loan eligibility criteria?"
- "Explain the interest rate calculation method"
- "What documents are required for account opening?"

---

## 🐳 Docker Deployment (Production)

### Option 1: Create Dockerfile for the App

Create `Dockerfile`:
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "app.py"]
```

### Option 2: Complete Docker Compose Setup

Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - ./qdrant_storage:/qdrant/storage
    environment:
      - QDRANT__SERVICE__HTTP_PORT=6333

  rag-app:
    build: .
    ports:
      - "5000:5000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - NOMIC_API_KEY=${NOMIC_API_KEY}
    depends_on:
      - qdrant
    volumes:
      - ./docs:/app/docs
```

### Deploy with Docker Compose:
```bash
# Build and start all services
docker-compose up --build -d

# Access the application at http://localhost:5000
```

---

## 🔧 Troubleshooting

### Common Issues:

#### 1. Port Already in Use
```bash
# Stop existing containers
docker-compose -f docker-compose.db.yml down

# Or kill specific port
docker ps
docker stop <container_id>
```

#### 2. API Key Issues
- Verify `.env` file exists and contains valid keys
- Check API key format and permissions
- Restart the application after updating keys

#### 3. Document Loading Errors
- Ensure documents are in `docs/` folder
- Check file permissions
- Verify file formats (PDF/TXT only)

#### 4. Memory/Performance Issues
```bash
# Clear conversation memory
# Use the "Clear" button in the web interface

# Restart services
docker-compose restart
```

---

## 📊 Monitoring and Logs

### View Application Logs:
```bash
# Flask application logs
python app.py  # Shows real-time logs

# Docker container logs
docker logs <container_name>
```

### Check Qdrant Status:
- Web UI: `http://localhost:6333/dashboard`
- API Health: `http://localhost:6333/health`

---

## 🔒 Security Considerations

1. **API Keys**: Never commit `.env` file to version control
2. **Network**: Use proper firewall rules in production
3. **HTTPS**: Configure SSL/TLS for production deployment
4. **Authentication**: Add user authentication for production use

---

## 📈 Scaling and Production

### For Production Deployment:
1. Use environment-specific configurations
2. Implement proper logging and monitoring
3. Set up load balancing for multiple instances
4. Use managed vector database services
5. Implement caching strategies

---

## 🎉 Success!

Your RAG Banking Assistant is now running! You can:
- Ask questions about your documents
- Get responses with source attribution
- Maintain conversation context
- Process both PDF and TXT files
- Enjoy a modern, responsive web interface

**Access URL**: `http://localhost:5000`

Happy querying! 🚀