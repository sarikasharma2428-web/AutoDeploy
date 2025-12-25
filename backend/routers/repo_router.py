import logging
from functools import lru_cache
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from services.analysis_pipeline import RepositoryAnalyzer

router = APIRouter()
logger = logging.getLogger(__name__)


class AnalyzeRequest(BaseModel):
    repo_url: str
    branch: str = Field(default="main", description="Git branch to analyze")
    include_tests: bool = Field(
        default=False, description="Include test directories when chunking"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Optional metadata to pass through to the analyzer"
    )

    @field_validator("repo_url")
    @classmethod
    def normalize_repo_url(cls, value: str) -> str:
        url = value.strip()
        if not url:
            raise ValueError("Repository URL is required")

        if not url.startswith(("http://", "https://")):
            url = f"https://{url.lstrip('/')}"

        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("Repository URL must include a hostname")

        # Normalize to https if no scheme provided previously
        return url

class SourceReferenceModel(BaseModel):
    id: str
    file_path: str
    start_line: int
    end_line: int
    snippet: str


class FindingModel(BaseModel):
    title: str
    severity: Optional[str] = None
    impact: Optional[str] = None
    effort: Optional[str] = None
    description: str = ""
    details: Optional[str] = None
    reference_id: str


class TechStackModel(BaseModel):
    languages: List[str] = []
    frameworks: List[str] = []
    databases: List[str] = []
    tools: List[str] = []
    reference_ids: List[str] = []


class AnalysisResponse(BaseModel):
    summary: str
    summary_references: List[str]
    tech_stack: TechStackModel
    security_findings: List[FindingModel]
    code_smells: List[FindingModel]
    improvement_plan: List[FindingModel]
    devops_recommendations: List[FindingModel]
    metadata: Dict[str, Any]
    source_references: List[SourceReferenceModel]


@lru_cache(maxsize=1)
def get_analyzer() -> RepositoryAnalyzer:
    logger.info("Instantiating RepositoryAnalyzer")
    return RepositoryAnalyzer()


@router.post("/repo/analyze", response_model=AnalysisResponse)
async def analyze_repository(request: AnalyzeRequest):
    analyzer = get_analyzer()
    try:
        result = await analyzer.analyze_repo(
            repo_url=str(request.repo_url),
            branch=request.branch,
            include_tests=request.include_tests,
            metadata=request.metadata or {},
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - runtime safeguard
        logger.exception("Repository analysis failed: %s", exc)
        raise HTTPException(status_code=500, detail="Analysis failed") from exc
