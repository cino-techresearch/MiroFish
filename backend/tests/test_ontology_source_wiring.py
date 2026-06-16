"""ontology_source production 배선 검증 (T-037 / FR-001).

- /inject/graph 가 ZepGraphOntologySource 로 project.ontology 를 채운다(배선 증명).
- /ontology/generate 가 LLMOntologySource 를 사용한다(import/참조 증명).
"""

import pytest

import app.api.graph as graph_api
from app import create_app
from app.models.project import ProjectManager


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(ProjectManager, "PROJECTS_DIR", str(tmp_path / "projects"))
    monkeypatch.setattr(graph_api, "validate_graph_id", lambda gid, **k: 3)
    app = create_app()
    app.config.update(TESTING=True)
    return app.test_client()


def test_inject_uses_zep_graph_ontology_source(client, monkeypatch):
    calls = {}

    class _FakeSource:
        def __init__(self, graph_id, reader=None):
            calls["graph_id"] = graph_id

        def load(self):
            calls["loaded"] = True
            return {"entity_types": [{"name": "Person"}], "edge_types": [], "source": "zep_graph"}

    monkeypatch.setattr(graph_api, "ZepGraphOntologySource", _FakeSource)
    resp = client.post("/api/graph/inject/graph", json={"graph_id": "g_x", "simulation_requirement": "r"})
    assert resp.status_code == 200
    pid = resp.get_json()["project_id"]
    # ZepGraphOntologySource 가 실제로 호출되어 project.ontology 를 채웠다
    assert calls.get("loaded") is True
    assert calls.get("graph_id") == "g_x"
    proj = ProjectManager.get_project(pid)
    assert proj.ontology and proj.ontology.get("source") == "zep_graph"


def test_generate_path_references_llm_ontology_source():
    # /ontology/generate 가 OntologyGenerator 직접 호출 대신 LLMOntologySource 를 쓰도록 배선됨
    import inspect
    src = inspect.getsource(graph_api)
    assert "LLMOntologySource(" in src
    assert "ZepGraphOntologySource(" in src
