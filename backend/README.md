# AutoDeployX

An enterprise-grade AIOps platform that analyzes GitHub repositories using advanced AI/ML techniques including vector embeddings, RAG (Retrieval-Augmented Generation), and LLM-based code analysis.

## 📋 Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Development](#development)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)

## ✨ Features

### Phase 1 & 2 (Current Implementation)

- 🔍 **Intelligent Repository Crawling**: Clone and analyze any public GitHub repository
- 📊 **Multi-Language Support**: Detect and parse 25+ programming languages
- 🧩 **Semantic Code Chunking**: Context-aware code segmentation using AST parsing
- 🔮 **Vector Embeddings**: Generate embeddings using sentence-transformers
- 🗃️ **Vector Database**: Store and search code chunks using Qdrant
- 🤖 **LLM Analysis**: Deep code analysis using quantized Llama 2/3 models
- 📈 **Architecture Detection**: Automatic identification of design patterns and architecture
- 🔒 **Security Analysis**: Identify potential vulnerabilities and security issues
- 💡 **Code Quality Assessment**: Detect code smells and suggest improvements
- ⚙️ **DevOps Recommendations**: Suggest CI/CD, containerization, and infrastructure improvements

### Phase 3 (Upcoming)

- 🎨 Modern animated React UI
- 📊 Interactive analysis dashboards
- 🔍 Code explorer with syntax highlighting
- 📱 Responsive design

### Phase 4 (Upcoming)

- 🐳 Docker containerization
- ☸️ Kubernetes orchestration
- 🏗️ Terraform infrastructure
- 📊 Prometheus + Grafana monitoring
- 🚀 CI/CD pipelines

## 🏗️ Architecture

```
┌─────────────┐
│   Frontend  │ (Phase 3)
│   React UI  │
└──────┬──────┘
       │
┌──────▼──────────────────────────────────────┐
│           FastAPI Backend                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │  Repo    │  │ Analysis │  │  Health  │ │
│  │  Router  │  │  Router  │  │  Check   │ │
│  └──────────┘  └──────────┘  └──────────┘ │
└──────┬──────────────┬─────────────────────┘
       │              │
┌──────▼──────┐  ┌───▼────────┐
│  PostgreSQL │  │   Redis    │
│  (Metadata) │  │  (Cache)   │
└─────────────┘  └────────────┘
       │              │
┌──────▼──────────────▼─────────────────┐
│         Services Layer                │
│  ┌─────────┐  ┌─────────┐  ┌───────┐ │
│  │ Cloner  │  │ Chunker │  │  LLM  │ │
│  │ Reader  │  │Embedder │  │Engine │ │
│  └─────────┘  └─────────┘  └───────┘ │
└───────┬────────────┬──────────────────┘
        │            │
┌───────▼──────┐  ┌──▼────────────┐
│   Qdrant     │  │ LLM Models    │
│ Vector DB    │  │ (Llama 2/3)   │
└──────────────┘  └───────────────┘
```

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI 0.109
- **Language**: Python 3.11+
- **Database**: PostgreSQL 15
- **Cache**: Redis 7
- **Vector DB**: Qdrant
- **ORM**: SQLAlchemy 2.0

### AI/ML Stack
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2)
- **LLM**: Llama 2 7B (Q4_K_M quantized)
- **Inference**: llama-cpp-python
- **Vector Search**: Qdrant with HNSW index

### Infrastructure
- **Containerization**: Docker
- **Orchestration**: Kubernetes (k3s/EKS)
- **IaC**: Terraform
- **Monitoring**: Prometheus + Grafana
- **CI/CD**: GitHub Actions

## 📦 Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Qdrant (latest)
- 8GB+ RAM (for LLM inference)
- 10GB+ free disk space (for models)

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/github-repo-analyzer.git
cd github-repo-analyzer
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Setup Services with Docker

```bash
# Start all required services
docker-compose up -d

# Or start individually:
docker run -d --name postgres \
  -e POSTGRES_DB=repo_analyzer \
  -e POSTGRES_USER=analyzer \
  -e POSTGRES_PASSWORD=analyzer123 \
  -p 5432:5432 postgres:15

docker run -d --name redis \
  -p 6379:6379 redis:7-alpine

docker run -d --name qdrant \
  -p 6333:6333 -p 6334:6334 \
  qdrant/qdrant
```

### 5. Download LLM Model

```bash
mkdir -p models
cd models

# Download Llama 2 7B Chat (Q4_K_M) - ~4.5GB
wget https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q4_K_M.gguf

# Alternative: Use curl
curl -L https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q4_K_M.gguf -o llama-2-7b-chat.Q4_K_M.gguf

cd ..
```

### 6. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings
```

### 7. Initialize Database

```bash
# Create tables
python -c "from utils.database import engine, Base; from models.database_models import *; Base.metadata.create_all(bind=engine)"
```

### 8. Run Application

```bash
# Development mode
uvicorn app:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

## ⚙️ Configuration

Key configuration options in `.env`:

```bash
# Application
DEBUG=True
PORT=8000
WORKERS=4

# Database
DATABASE_URL=postgresql://analyzer:analyzer123@localhost:5432/repo_analyzer

# Repository Settings
MAX_REPO_SIZE_MB=500
CLONE_TIMEOUT=300

# Embedding Model
EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384

# LLM Settings
LLM_MODEL_FILE=llama-2-7b-chat.Q4_K_M.gguf
LLM_CONTEXT_LENGTH=8192
LLM_TEMPERATURE=0.3

# RAG Settings
RAG_TOP_K=20
RAG_SCORE_THRESHOLD=0.7
```

## 📚 Usage

### API Workflow

1. **Submit Repository**

```bash
curl -X POST "http://localhost:8000/api/v1/repo/submit" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/fastapi/fastapi",
    "branch": "main",
    "include_tests": false,
    "deep_analysis": true
  }'
```

Response:
```json
{
  "job_id": "uuid-here",
  "repo_url": "https://github.com/fastapi/fastapi",
  "status": "pending",
  "estimated_time": 300,
  "message": "Repository submitted successfully"
}
```

2. **Check Status**

```bash
curl "http://localhost:8000/api/v1/repo/status/{job_id}"
```

3. **Start Analysis**

```bash
curl -X POST "http://localhost:8000/api/v1/analyze/start" \
  -H "Content-Type: application/json" \
  -d '{"job_id": "your-job-id"}'
```

4. **Get Results**

```bash
curl "http://localhost:8000/api/v1/analyze/result/{job_id}"
```

### Python Client Example

```python
import requests
import time

# Submit repository
response = requests.post(
    "http://localhost:8000/api/v1/repo/submit",
    json={
        "repo_url": "https://github.com/user/repo",
        "branch": "main"
    }
)
job_id = response.json()["job_id"]

# Wait for processing
while True:
    status = requests.get(f"http://localhost:8000/api/v1/repo/status/{job_id}")
    if status.json()["status"] == "completed":
        break
    time.sleep(2)

# Start analysis
requests.post(
    "http://localhost:8000/api/v1/analyze/start",
    json={"job_id": job_id}
)

# Get results
results = requests.get(f"http://localhost:8000/api/v1/analyze/result/{job_id}")
print(results.json())
```

## 📖 API Documentation

Interactive API documentation available at:

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **OpenAPI JSON**: http://localhost:8000/api/openapi.json

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/repo/submit` | Submit repository for analysis |
| GET | `/api/v1/repo/status/{job_id}` | Get job status |
| GET | `/api/v1/repo/info/{job_id}` | Get repository metadata |
| DELETE | `/api/v1/repo/{job_id}` | Delete job |
| POST | `/api/v1/analyze/start` | Start full analysis |
| GET | `/api/v1/analyze/result/{job_id}` | Get analysis results |
| GET | `/api/v1/analyze/summary/{job_id}` | Get analysis summary |
| GET | `/health` | Health check |
| GET | `/metrics` | Prometheus metrics |

## 🔧 Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=. --cov-report=html
```

### Code Quality

```bash
# Format code
black .

# Lint
flake8 .

# Type checking
mypy .
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## 🚀 Deployment

### Docker Deployment

```bash
# Build image
docker build -t repo-analyzer:latest .

# Run container
docker run -d \
  -p 8000:8000 \
  --env-file .env \
  repo-analyzer:latest
```

### Kubernetes Deployment

```bash
# Apply manifests
kubectl apply -f k8s/

# Check status
kubectl get pods -n repo-analyzer
```

### AWS Deployment (Free Tier)

See `terraform/` directory for infrastructure as code.

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

## 📊 Monitoring

Access monitoring dashboards:

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000
- **Application Metrics**: http://localhost:8000/metrics

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- FastAPI framework
- Sentence Transformers
- Llama.cpp
- Qdrant vector database
- The open-source community

## 📧 Contact

- **Author**: Your Name
- **Email**: your.email@example.com
- **GitHub**: [@yourusername](https://github.com/yourusername)

## 🗺️ Roadmap

- [x] Phase 1: Backend skeleton + repository cloning
- [x] Phase 2: LLM processing pipeline
- [ ] Phase 3: Frontend UI + Docker
- [ ] Phase 4: Kubernetes + Terraform + CI/CD
- [ ] Phase 5: Advanced features (custom models, fine-tuning, team collaboration)

---

**Note**: This is an educational/demonstration project. For production use, implement proper security, authentication, rate limiting, and monitoring.