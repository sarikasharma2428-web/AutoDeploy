from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient

from app import app


class DummyAnalyzer:
    async def analyze_repo(self, **_: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "summary": "ok",
            "summary_references": ["ref-1"],
            "tech_stack": {
                "languages": ["Python"],
                "frameworks": ["FastAPI"],
                "databases": [],
                "tools": [],
                "reference_ids": ["ref-1"],
            },
            "security_findings": [
                {"title": "x", "severity": "low", "description": "y", "reference_id": "ref-1"}
            ],
            "code_smells": [
                {"title": "z", "impact": "low", "description": "w", "reference_id": "ref-1"}
            ],
            "improvement_plan": [
                {
                    "title": "Improve",
                    "impact": "high",
                    "effort": "low",
                    "details": "do it",
                    "reference_id": "ref-1",
                }
            ],
            "devops_recommendations": [
                {
                    "title": "CI",
                    "impact": "medium",
                    "effort": "low",
                    "details": "add ci",
                    "reference_id": "ref-1",
                }
            ],
            "metadata": {},
            "source_references": [
                {
                    "id": "ref-1",
                    "file_path": "README.md",
                    "start_line": 1,
                    "end_line": 10,
                    "snippet": "text",
                }
            ],
        }


@pytest.fixture()
def client(monkeypatch):
    class HealthyQdrant:
        def __init__(self, *args, **kwargs):
            pass

        def get_collections(self):
            return []

    monkeypatch.setattr("app.QdrantClient", HealthyQdrant)
    monkeypatch.setattr("routers.repo_router.get_analyzer", lambda: DummyAnalyzer())
    return TestClient(app)


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["services"]["qdrant"] == "healthy"


def test_analyze_repo_endpoint(monkeypatch):
    monkeypatch.setattr("app.QdrantClient", lambda *args, **kwargs: type("Q", (), {"get_collections": lambda self: []})())
    monkeypatch.setattr("routers.repo_router.get_analyzer", lambda: DummyAnalyzer())
    client = TestClient(app)

    response = client.post(
        "/api/repo/analyze",
        json={"repo_url": "https://github.com/octocat/Hello-World", "branch": "main"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["summary"] == "ok"
    assert data["source_references"][0]["file_path"] == "README.md"

