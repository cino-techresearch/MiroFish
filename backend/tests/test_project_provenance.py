"""Project provenance 필드 테스트 (T-010 / TS-017, FR-009).

주입 project 를 일반 생성 project 와 구분하기 위해 source_type/ontology_source/
profile_source 를 기록한다. 기존 project.json(필드 없음)도 역호환되어야 한다.
"""

from app.models.project import Project, ProjectStatus


def _base_dict(**over):
    d = {
        "project_id": "proj_x",
        "name": "p",
        "status": "graph_completed",
        "created_at": "t",
        "updated_at": "t",
    }
    d.update(over)
    return d


def test_default_source_type_is_generated():
    p = Project.from_dict(_base_dict())
    assert p.source_type == "generated"
    assert p.ontology_source is None
    assert p.profile_source is None


def test_to_dict_includes_provenance():
    p = Project.from_dict(_base_dict())
    d = p.to_dict()
    assert "source_type" in d
    assert "ontology_source" in d
    assert "profile_source" in d


def test_injected_provenance_roundtrip():
    p = Project.from_dict(_base_dict(
        source_type="injected",
        ontology_source="zep_graph",
        profile_source="file",
    ))
    assert p.source_type == "injected"
    d = p.to_dict()
    p2 = Project.from_dict(d)
    assert p2.source_type == "injected"
    assert p2.ontology_source == "zep_graph"
    assert p2.profile_source == "file"


def test_legacy_dict_without_provenance_still_loads():
    # 기존 project.json 에는 provenance 키가 없다 — 역호환 보장.
    legacy = _base_dict()
    assert "source_type" not in legacy
    p = Project.from_dict(legacy)
    assert p.source_type == "generated"
    assert isinstance(p.status, ProjectStatus)
