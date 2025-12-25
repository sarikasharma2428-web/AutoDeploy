import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API Configuration
    VERSION: str = "1.0.0"
    APP_NAME: str = "AutoDeployX API"
    API_PREFIX: str = "/api"
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Logging
    LOG_DIR: str = os.getenv("LOG_DIR", "logs")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://frontend:3000",
        "*"
    ]
    
    # File Processing
    MAX_FILE_SIZE_MB: int = 10
    
    # Comprehensive list of allowed extensions for code analysis
    ALLOWED_EXTENSIONS: List[str] = [
        # Programming languages
        '.py', '.js', '.ts', '.jsx', '.tsx',
        '.java', '.go', '.rs', '.cpp', '.c', '.h', '.hpp',
        '.cs', '.rb', '.php', '.swift', '.kt', '.scala',
        '.r', '.m', '.dart', '.lua', '.pl', '.sh', '.bash',
        
        # Web
        '.html', '.htm', '.css', '.scss', '.sass', '.less',
        '.vue', '.svelte',
        
        # Config & Data
        '.json', '.yaml', '.yml', '.toml', '.xml',
        '.ini', '.conf', '.config', '.env',
        
        # Documentation
        '.md', '.txt', '.rst', '.adoc',
        
        # Database
        '.sql', '.prisma',
        
        # DevOps
        '.dockerfile', '.tf', '.hcl',
        
        # Other
        '.graphql', '.proto'
    ]
    
    EXCLUDED_DIRS: List[str] = [
        'node_modules', 'venv', '.venv', 'env', '.env',
        '__pycache__', '.git', '.svn', '.hg',
        'dist', 'build', 'target', 'bin', 'obj',
        '.idea', '.vscode', '.pytest_cache',
        'vendor', 'packages', '.next', '.nuxt',
        'coverage', '.coverage', 'htmlcov'
    ]
    
    # Qdrant Configuration
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "qdrant")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))
    QDRANT_COLLECTION: str = "repo_analysis"
    EMBEDDING_DIM: int = 384
    
    # LLM Configuration
    LOCAL_LLM_PATH: str = os.getenv("LOCAL_LLM_PATH", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    HUGGINGFACE_API_KEY: str = os.getenv("HUGGINGFACE_API_KEY", "")
    HUGGINGFACE_MODEL: str = os.getenv("HUGGINGFACE_MODEL", "")
    
    # Embedding Model
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Prometheus
    PROMETHEUS_METRICS_PATH: str = os.getenv("PROMETHEUS_METRICS_PATH", "/metrics")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()


