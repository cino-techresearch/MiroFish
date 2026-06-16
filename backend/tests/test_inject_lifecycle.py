"""주입 project 라이프사이클 가드 테스트 (T-013 / TS-018, FR-010).

source_type=injected project 는 ontology/text 가 없으므로 /build force·/reset 이
graph_id 를 날리거나 textNotFound 로 실패하면 안 된다. 명확히 거부하고 graph_id 를 보존한다.
/delete 와 일반 project 동작은 영향받지 않는다.
"""

import pytest

from app import create_app
from app.models.project import Project, ProjectManager, ProjectStatus


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(ProjectManager, "PROJECTS_DIR", str(tmp_path / "projects"))
    app = create_app()
    app.config.update(TESTING=True)
    return app.test_client()


def _make_injected():
    p = ProjectManager.create_project("Injected")
    p.graph_id = "mirofish_inj"
    p.status = ProjectStatus.GRAPH_COMPLETED
    p.simulation_requirement = "req"
    p.source_type = "injected"
    p.ontology_source = "zep_graph"
    ProjectManager.save_project(p)
    return p


def test_build_force_rejected_for_injected(client):
    p = _make_injected()
    resp = client.post("/api/graph/build", json={"project_id": p.project_id, "force": True})
    assert resp.status_code == 400
    # graph_id 가 보존되어야 한다 (날아가면 안 됨)
    reloaded = ProjectManager.get_project(p.project_id)
    assert reloaded.graph_id == "mirofish_inj"
    assert reloaded.status == ProjectStatus.GRAPH_COMPLETED


def test_reset_rejected_for_injected(client):
    p = _make_injected()
    resp = client.post(f"/api/graph/project/{p.project_id}/reset")
    assert resp.status_code == 400
    reloaded = ProjectManager.get_project(p.project_id)
    assert reloaded.graph_id == "mirofish_inj"


def test_delete_works_for_injected(client):
    p = _make_injected()
    resp = client.delete(f"/api/graph/project/{p.project_id}")
    assert resp.status_code == 200
    assert ProjectManager.get_project(p.project_id) is None


def test_reset_still_works_for_generated(client):
    p = ProjectManager.create_project("Normal")
    p.status = ProjectStatus.GRAPH_COMPLETED
    p.ontology = {"entity_types": [], "edge_types": []}
    p.graph_id = "g_normal"
    ProjectManager.save_project(p)
    resp = client.post(f"/api/graph/project/{p.project_id}/reset")
    assert resp.status_code == 200
    reloaded = ProjectManager.get_project(p.project_id)
    assert reloaded.status == ProjectStatus.ONTOLOGY_GENERATED
