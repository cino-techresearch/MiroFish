"""기존 기본 경로 회귀 테스트 (T-020 / TS-008, FR-007, NFR-001).

주입 기능(신규 엔드포인트/분기) 추가 후에도 기존 4개 엔드포인트의 기본 경로
입출력 계약이 동일해야 한다. ZEP/LLM 없이 결정적으로 검증 가능한 계약만 단언한다.
"""

import pytest

from app import create_app
from app.models.project import ProjectManager, ProjectStatus


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(ProjectManager, "PROJECTS_DIR", str(tmp_path / "projects"))
    app = create_app()
    app.config.update(TESTING=True)
    return app.test_client()


def test_health_intact(client):
    assert client.get("/health").status_code == 200


def test_build_requires_project_id(client):
    # 기존 계약: project_id 없으면 400
    resp = client.post("/api/graph/build", json={})
    assert resp.status_code == 400


def test_build_unknown_project_404(client):
    resp = client.post("/api/graph/build", json={"project_id": "proj_nope"})
    assert resp.status_code == 404


def test_get_unknown_project_404(client):
    assert client.get("/api/graph/project/proj_nope").status_code == 404


def test_reset_unknown_project_404(client):
    assert client.post("/api/graph/project/proj_nope/reset").status_code == 404


def test_generated_project_reset_contract_unchanged(client):
    # 일반(generated) project 의 reset 기본 동작이 그대로 유지되는지
    p = ProjectManager.create_project("Normal")
    p.status = ProjectStatus.GRAPH_COMPLETED
    p.ontology = {"entity_types": [], "edge_types": []}
    ProjectManager.save_project(p)
    resp = client.post(f"/api/graph/project/{p.project_id}/reset")
    assert resp.status_code == 200
    assert ProjectManager.get_project(p.project_id).status == ProjectStatus.ONTOLOGY_GENERATED
