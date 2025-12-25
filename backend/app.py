import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from qdrant_client import QdrantClient

from config import settings
from routers import repo_router


def _configure_logging() -> None:
    log_path = Path(settings.LOG_DIR) / "backend.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_path),
        ],
    )


_configure_logging()
logger = logging.getLogger("autodeployx.api")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="LLM-assisted repository analyzer",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1_000)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Process-Time"] = f"{time.perf_counter() - start:.6f}"
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.DEBUG else "Unexpected error",
            "path": str(request.url),
        },
    )


Instrumentator().instrument(app).expose(app, endpoint=settings.PROMETHEUS_METRICS_PATH)

app.include_router(repo_router.router, prefix="/api", tags=["Repository Analysis"])


@app.get("/")
async def root():
    return {
        "message": "AutoDeployX backend ready",
        "version": settings.VERSION,
        "docs": "/api/docs",
    }


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    services = {"api": "healthy"}
    qdrant_status = "healthy"
    try:
        client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
        client.get_collections()
    except Exception as exc:  # pragma: no cover - connectivity
        qdrant_status = f"unhealthy: {exc}"
        logger.warning("Qdrant health check failed: %s", exc)
    services["qdrant"] = qdrant_status

    return {
        "status": "healthy" if qdrant_status == "healthy" else "degraded",
        "version": settings.VERSION,
        "services": services,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )