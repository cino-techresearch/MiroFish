"""prepare 주입 정합성 연결 테스트 (T-018 / TS-020, FR-012).

프로필 주입 경로에서 config 생성 후, 주입 프로필 수/user_id 가 agent_configs·
initial_posts.poster_agent_id 와 불일치하면 prepare 가 fail-fast 로 FAILED 처리한다.
"""

import json
import os

import pytest

import app.services.simulation_manager as sm
from app.services.simulation_manager import SimulationManager, SimulationStatus
from tests.fixtures.zep_mock import make_fake_zep_reader


class _NoGen:
    def __init__(self, *a, **k):
        pass

    def save_profiles(self, profiles, file_path, platform="reddit"):
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump([{"user_id": p.user_id} for p in profiles], f)


class _Params:
    def __init__(self, agent_ids, poster_ids):
        self.agent_configs = [{"agent_id": i} for i in agent_ids]

        class _EC:
            pass
        self.event_config = _EC()
        self.event_config.initial_posts = [{"poster_agent_id": p} for p in poster_ids]
        self.generation_reasoning = "r"

    def to_json(self):
        return json.dumps({"agent_configs": [a["agent_id"] for a in self.agent_configs]})


def _make_config_gen(agent_ids, poster_ids):
    class _CG:
        def generate_config(self, **k):
            return _Params(agent_ids, poster_ids)
    return _CG


@pytest.fixture
def manager(tmp_path, monkeypatch):
    monkeypatch.setattr(SimulationManager, "SIMULATION_DATA_DIR", str(tmp_path / "sims"))
    monkeypatch.setattr(sm, "ZepEntityReader", lambda *a, **k: make_fake_zep_reader("valid", count=3))
    monkeypatch.setattr(sm, "OasisProfileGenerator", _NoGen)
    return SimulationManager()


def _inject(manager, sim_id, n):
    sim_dir = manager._get_simulation_dir(sim_id)
    os.makedirs(sim_dir, exist_ok=True)
    profs = [{"user_id": i, "user_name": f"u{i}", "name": f"n{i}", "bio": "b", "persona": "p"}
             for i in range(n)]
    with open(os.path.join(sim_dir, "injected_profiles.json"), "w", encoding="utf-8") as f:
        json.dump(profs, f)


def test_consistent_injection_reaches_ready(manager, monkeypatch):
    monkeypatch.setattr(sm, "SimulationConfigGenerator", _make_config_gen([0, 1, 2], [0, 2]))
    state = manager.create_simulation(project_id="p", graph_id="g1",
                                      enable_twitter=False, enable_reddit=True)
    _inject(manager, state.simulation_id, 3)
    result = manager.prepare_simulation(simulation_id=state.simulation_id,
                                        simulation_requirement="r", document_text="d")
    assert result.status == SimulationStatus.READY


def test_inconsistent_injection_fails_fast(manager, monkeypatch):
    # 주입 3개인데 agent_configs 2개 + poster_agent_id=5(없는 프로필) → 불일치
    monkeypatch.setattr(sm, "SimulationConfigGenerator", _make_config_gen([0, 1], [5]))
    state = manager.create_simulation(project_id="p", graph_id="g1",
                                      enable_twitter=False, enable_reddit=True)
    _inject(manager, state.simulation_id, 3)
    result = manager.prepare_simulation(simulation_id=state.simulation_id,
                                        simulation_requirement="r", document_text="d")
    assert result.status == SimulationStatus.FAILED
    assert result.error and ("정합" in result.error or "5" in result.error)
