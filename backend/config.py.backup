from pathlib import Path
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    APP_NAME: str = Field(default="AutoDeployX API", env="APP_NAME")
    VERSION: str = Field(default="1.0.0", env="VERSION")
    DEBUG: bool = Field(default=False, env="DEBUG")
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_DIR: str = Field(default="logs", env="LOG_DIR")

    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        env="CORS_ORIGINS",
    )

    CLONE_DIR: str = Field(default="./tmp/repos", env="CLONE_DIR")
    MAX_REPO_SIZE_MB: int = Field(default=500, env="MAX_REPO_SIZE_MB")
    CLONE_DEPTH: int = Field(default=1, env="CLONE_DEPTH")
    CLONE_TIMEOUT: int = Field(default=300, env="CLONE_TIMEOUT")
    MAX_FILE_SIZE_MB: int = Field(default=5, env="MAX_FILE_SIZE_MB")

    ALLOWED_EXTENSIONS: List[str] = [
        ".py",
        ".js",
        ".ts",
        ".tsx",
        ".java",
        ".go",
        ".rs",
        ".cpp",
        ".c",
        ".h",
        ".hpp",
        ".cs",
        ".rb",
        ".php",
        ".swift",
        ".kt",
        ".scala",
        ".r",
        ".m",
        ".sh",
        ".sql",
        ".yaml",
        ".yml",
        ".json",
        ".xml",
        ".html",
        ".css",
        ".scss",
        ".md",
        ".txt",
        ".toml",
        ".ini",
        ".conf",
        ".env.example",
        ".gitignore",
        ".dockerignore",
        "Dockerfile",
        "Makefile",
        "README",
    ]

    EXCLUDED_DIRS: List[str] = [
        "node_modules",
        ".git",
        "__pycache__",
        ".pytest_cache",
        "venv",
        "env",
        ".venv",
        "dist",
        "build",
        "target",
        ".idea",
        ".vscode",
        "coverage",
        ".next",
        ".cache",
        "vendor",
        "tmp",
        "temp",
        "logs",
    ]

    QDRANT_HOST: str = Field(default="localhost", env="QDRANT_HOST")
    QDRANT_PORT: int = Field(default=6333, env="QDRANT_PORT")
    QDRANT_GRPC_PORT: int = Field(default=6334, env="QDRANT_GRPC_PORT")

    EMBEDDING_MODEL_NAME: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        env="EMBEDDING_MODEL_NAME",
    )
    EMBEDDING_DIMENSION: int = Field(default=384, env="EMBEDDING_DIMENSION")
    EMBEDDING_BATCH_SIZE: int = Field(default=32, env="EMBEDDING_BATCH_SIZE")

    CHUNK_SIZE: int = Field(default=1200, env="CHUNK_SIZE")
    CHUNK_OVERLAP: int = Field(default=120, env="CHUNK_OVERLAP")

    RAG_TOP_K: int = Field(default=15, env="RAG_TOP_K")
    RAG_SCORE_THRESHOLD: float = Field(default=0.55, env="RAG_SCORE_THRESHOLD")

    LOCAL_LLM_PATH: str = Field(default="", env="LOCAL_LLM_PATH")
    LOCAL_LLM_N_CTX: int = Field(default=4096, env="LOCAL_LLM_N_CTX")
    LOCAL_LLM_N_THREADS: int = Field(default=4, env="LOCAL_LLM_N_THREADS")

    OPENAI_API_KEY: str = Field(default="", env="OPENAI_API_KEY")
    OPENAI_MODEL: str = Field(default="gpt-4o-mini", env="OPENAI_MODEL")

    HUGGINGFACE_API_KEY: str = Field(default="", env="HUGGINGFACE_API_KEY")
    HUGGINGFACE_MODEL: str = Field(
        default="mistralai/Mistral-7B-Instruct-v0.2",
        env="HUGGINGFACE_MODEL",
    )

    LLM_MAX_TOKENS: int = Field(default=1024, env="LLM_MAX_TOKENS")
    LLM_TEMPERATURE: float = Field(default=0.0, env="LLM_TEMPERATURE")
    LLM_TOP_P: float = Field(default=0.95, env="LLM_TOP_P")

    PROMETHEUS_METRICS_PATH: str = Field(default="/metrics", env="PROMETHEUS_METRICS_PATH")

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _split_cors(cls, value):
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


settings = Settings()

Path(settings.CLONE_DIR).mkdir(parents=True, exist_ok=True)
Path(settings.LOG_DIR).mkdir(parents=True, exist_ok=True)