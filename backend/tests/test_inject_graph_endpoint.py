"""graph_id 주입 엔드포인트 테스트 (T-012 / TS-001, TS-013, TS-017, FR-003, FR-009).

POST /api/graph/inject/graph:
- graph_id + simulation_requirement 받아 경량 project 발급(status=GRAPH_COMPLETED, source_type=injected)
- simulation_requirement 미제공 → 400 거부
- 검증 실패(없는 graph_id) → 400 + project 미생성(부수효과 없음)
"""

import pytest

import app.api.graph as graph_api
from app import create_app
from app.models.project import ProjectManager, ProjectStatus
from app.services.graph_injection import GraphInjectionError


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(ProjectManager, "PROJECTS_DIR", str(tmp_path / "projects"))
    app = create_app()
    app.config.update(TESTING=True)
    return app.test_client()


def test_inject_graph_creates_lightweight_project(client, monkeypatch):
    monkeypatch.setattr(graph_api, "validate_graph_id", lambda gid, **kw: 5)
    resp = client.post("/api/graph/inject/graph", json={
        "graph_id": "mirofish_abc", "simulation_requirement": "예측 시나리오",
    })
    assert resp.status_code == 200, resp.get_data(as_text=True)
    body = resp.get_json()
    assert body["graph_id"] == "mirofish_abc"
    assert body["status"] == ProjectStatus.GRAPH_COMPLETED.value
    assert body["source_type"] == "injected"
    # 영속화 확인
    proj = ProjectManager.get_project(body["project_id"])
    assert proj.graph_id == "mirofish_abc"
    assert proj.status == ProjectStatus.GRAPH_COMPLETED
    assert proj.source_type == "injected"
    assert proj.simulation_requirement == "예측 시나리오"


def test_missing_requirement_rejected(client, monkeypatch):
    monkeypatch.setattr(graph_api, "validate_graph_id", lambda gid, **kw: 5)
    resp = client.post("/api/graph/inject/graph", json={"graph_id": "mirofish_abc"})
    assert resp.status_code == 400


def test_invalid_graph_rejected_no_side_effect(client, monkeypatch):
    def _boom(gid, **kw):
        raise GraphInjectionError("없는 graph_id")
    monkeypatch.setattr(graph_api, "validate_graph_id", _boom)

    before = set(ProjectManager.list_projects()) if hasattr(ProjectManager, "list_projects") else None
    resp = client.post("/api/graph/inject/graph", json={
        "graph_id": "nope", "simulation_requirement": "x",
    })
    assert resp.status_code == 400
    # 부수효과 없음: 생성된 project 없음
    import os
    projects_dir = ProjectManager.PROJECTS_DIR
    created = os.listdir(projects_dir) if os.path.isdir(projects_dir) else []
    assert created == []
