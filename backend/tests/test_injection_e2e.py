"""주입 end-to-end endpoint chain 테스트 (T-030 / TS-004d, TS-020, FR-005, FR-012).

실제 Flask 라우트 체인을 통과한다: /inject/graph -> /simulation/create -> /profiles/upload
-> (SimulationManager.prepare_simulation). 개별 모듈이 아니라 통합 경로를 검증한다.
"""

import json
import os

import pytest

import app.api.graph as graph_api
import app.services.simulation_manager as sm
from app import create_app
from app.models.project import ProjectManager, ProjectStatus
from app.services.simulation_manager import SimulationManager, SimulationStatus
from app.services.oasis_profile_generator import OasisAgentProfile
from tests.fixtures.zep_mock import make_fake_zep_reader


class _NoGen:
    def __init__(self, *a, **k):
        pass

    def generate_profiles_from_entities(self, entities, **k):
        return [OasisAgentProfile(user_id=i, user_name=f"u{i}", name=f"n{i}", bio="b", persona="p")
                for i in range(len(entities))]

    def save_profiles(self, profiles, file_path, platform="reddit"):
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump([{"user_id": p.user_id} for p in profiles], f)


def _config_gen(n):
    class _P:
        generation_reasoning = "r"
        agent_configs = [{"agent_id": i} for i in range(n)]

        class event_config:
            initial_posts = [{"poster_agent_id": 0}]

        def to_json(self):
            return json.dumps({})
    return lambda *a, **k: type("CG", (), {"generate_config": lambda self, **k: _P()})()


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setattr(ProjectManager, "PROJECTS_DIR", str(tmp_path / "projects"))
    monkeypatch.setattr(SimulationManager, "SIMULATION_DATA_DIR", str(tmp_path / "sims"))
    # inject 엔드포인트의 graph_id 동기 검증 통과 (ZEP 없이)
    monkeypatch.setattr(graph_api, "validate_graph_id", lambda gid, **k: 3)
    # prepare 의 ZEP/생성기/config 를 mock
    monkeypatch.setattr(sm, "ZepEntityReader", lambda *a, **k: make_fake_zep_reader("valid", count=3))
    monkeypatch.setattr(sm, "OasisProfileGenerator", _NoGen)
    monkeypatch.setattr(sm, "SimulationConfigGenerator", _config_gen(3))
    app = create_app()
    app.config.update(TESTING=True)
    return app.test_client()


def test_full_injection_chain_reaches_ready(env):
    client = env

    # 1) graph_id 주입 → 경량 project
    r1 = client.post("/api/graph/inject/graph", json={
        "graph_id": "mirofish_e2e", "simulation_requirement": "예측",
    })
    assert r1.status_code == 200, r1.get_data(as_text=True)
    project_id = r1.get_json()["project_id"]
    assert r1.get_json()["source_type"] == "injected"

    # 2) 시뮬레이션 생성 (graph_id 는 project 에서)
    r2 = client.post("/api/simulation/create", json={
        "project_id": project_id, "enable_twitter": False, "enable_reddit": True,
    })
    assert r2.status_code == 200, r2.get_data(as_text=True)
    simulation_id = r2.get_json()["data"]["simulation_id"]

    # 3) 중립 JSON 프로필 주입 (0-based 연속, 엔티티 수 3과 일치)
    profiles = [{"user_id": i, "user_name": f"u{i}", "name": f"n{i}", "bio": "b", "persona": "p"} for i in range(3)]
    r3 = client.post("/api/simulation/profiles/upload", json={
        "simulation_id": simulation_id, "profiles": profiles,
    })
    assert r3.status_code == 200, r3.get_data(as_text=True)
    assert r3.get_json()["count"] == 3
    # 업로드는 injected_profiles.json 으로 저장 → prepare 가 같은 파일을 읽는다
    sim_dir = SimulationManager()._get_simulation_dir(simulation_id)
    assert os.path.exists(os.path.join(sim_dir, "injected_profiles.json"))

    # 4) prepare → 주입 경로로 READY 도달 (생성 LLM 0회)
    result = SimulationManager().prepare_simulation(
        simulation_id=simulation_id, simulation_requirement="예측", document_text="",
    )
    assert result.status == SimulationStatus.READY
    assert ProjectManager.get_project(project_id).profile_source == "file"
    # 변환 산출물 생성
    assert os.path.exists(os.path.join(sim_dir, "reddit_profiles.json"))


def test_chain_rejects_count_mismatch(env):
    client = env
    pid = client.post("/api/graph/inject/graph", json={"graph_id": "g", "simulation_requirement": "x"}).get_json()["project_id"]
    sid = client.post("/api/simulation/create", json={"project_id": pid, "enable_twitter": False, "enable_reddit": True}).get_json()["data"]["simulation_id"]
    # 2개만 주입 (엔티티 3개와 불일치)
    client.post("/api/simulation/profiles/upload", json={
        "simulation_id": sid,
        "profiles": [{"user_id": i, "user_name": f"u{i}", "name": f"n{i}", "bio": "b", "persona": "p"} for i in range(2)],
    })
    result = SimulationManager().prepare_simulation(simulation_id=sid, simulation_requirement="x", document_text="")
    assert result.status == SimulationStatus.FAILED
