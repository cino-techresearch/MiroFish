"""e2e: 실제 /api/simulation/prepare 라우트까지 통과 (T-036 / TS-004d, FR-005).

이전 e2e(test_injection_e2e.py)는 prepare 를 manager 직접 호출로 끝냈다(codex Major).
여기서는 주입→prepare(manager)로 산출물을 만든 뒤 실제 /prepare HTTP 라우트가
already-prepared 를 반환하는지 검증해 라우트 + _check_simulation_prepared(read-only)를 닫는다.
"""

import json
import os

import pytest

import app.api.graph as graph_api
import app.api.simulation as sim_api
import app.services.simulation_manager as sm
from app import create_app
from app.config import Config
from app.models.project import ProjectManager
from app.services.simulation_manager import SimulationManager
from app.services.oasis_profile_generator import OasisAgentProfile
from tests.fixtures.zep_mock import make_fake_zep_reader


class _NoGen:
    def __init__(self, *a, **k):
        pass

    def save_profiles(self, profiles, file_path, platform="reddit"):
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump([{"user_id": p.user_id} for p in profiles], f)


def _config_gen(n):
    class _P:
        generation_reasoning = "r"
        agent_configs = [{"agent_id": i} for i in range(n)]

        class event_config:
            initial_posts = []

        def to_json(self):
            return json.dumps({})
    return lambda *a, **k: type("CG", (), {"generate_config": lambda self, **k: _P()})()


@pytest.fixture
def client(tmp_path, monkeypatch):
    sims = str(tmp_path / "sims")
    monkeypatch.setattr(ProjectManager, "PROJECTS_DIR", str(tmp_path / "projects"))
    # manager 와 _check_simulation_prepared(Config.OASIS_SIMULATION_DATA_DIR) 가 같은 dir 를 보게 한다
    monkeypatch.setattr(SimulationManager, "SIMULATION_DATA_DIR", sims)
    monkeypatch.setattr(Config, "OASIS_SIMULATION_DATA_DIR", sims)
    monkeypatch.setattr(graph_api, "validate_graph_id", lambda gid, **k: 3)
    monkeypatch.setattr(sm, "ZepEntityReader", lambda *a, **k: make_fake_zep_reader("valid", count=3))
    monkeypatch.setattr(sm, "OasisProfileGenerator", _NoGen)
    monkeypatch.setattr(sm, "SimulationConfigGenerator", _config_gen(3))
    app = create_app()
    app.config.update(TESTING=True)
    return app.test_client()


def test_prepare_route_returns_already_prepared_for_injected(client):
    # 1) inject → 2) create → 3) upload (모두 실제 라우트)
    pid = client.post("/api/graph/inject/graph", json={"graph_id": "g", "simulation_requirement": "x"}).get_json()["project_id"]
    sid = client.post("/api/simulation/create", json={"project_id": pid, "enable_twitter": True, "enable_reddit": True}).get_json()["data"]["simulation_id"]
    profs = [{"user_id": i, "user_name": f"u{i}", "name": f"n{i}", "bio": "b", "persona": "p"} for i in range(3)]
    assert client.post("/api/simulation/profiles/upload", json={"simulation_id": sid, "profiles": profs}).status_code == 200

    # manager prepare 로 산출물 생성(reddit/twitter profiles + config + state ready)
    res = SimulationManager().prepare_simulation(simulation_id=sid, simulation_requirement="x", document_text="")
    assert res.status.value == "ready"

    # 4) 실제 /prepare 라우트 — 이미 준비됨이므로 동기 200 + already_prepared
    r = client.post("/api/simulation/prepare", json={"simulation_id": sid, "force_regenerate": False})
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    assert body["success"] is True
    assert body["data"]["already_prepared"] is True

    # _check_simulation_prepared 가 read-only — state.json status 가 디스크에서 보존됨
    sim_dir = os.path.join(Config.OASIS_SIMULATION_DATA_DIR, sid)
    state_on_disk = json.load(open(os.path.join(sim_dir, "state.json"), encoding="utf-8"))
    assert state_on_disk["status"] == "ready"


def test_prepare_route_rejects_missing_simulation(client):
    r = client.post("/api/simulation/prepare", json={"simulation_id": "sim_nope"})
    assert r.status_code in (400, 404)
