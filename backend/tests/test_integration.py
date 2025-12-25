import os

import pytest
from fastapi.testclient import TestClient

from app import app


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("RUN_INTEGRATION_TESTS"),
    reason="Set RUN_INTEGRATION_TESTS=1 with Qdrant + embeddings running locally.",
)
def test_live_repo_analysis_smoke():
    client = TestClient(app)
    response = client.post(
        "/api/repo/analyze",
        json={"repo_url": "https://github.com/octocat/Hello-World", "branch": "main"},
    )
    assert response.status_code == 200
    body = response.json()
    for key in [
        "summary",
        "tech_stack",
        "security_findings",
        "code_smells",
        "improvement_plan",
        "devops_recommendations",
        "source_references",
    ]:
        assert key in body
    assert isinstance(body["source_references"], list)
