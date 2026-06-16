"""정합성 happy-path + cheap pre-check 테스트 (T-031 / TS-020, FR-012).

- 0-based 연속 user_id + 프로필수==엔티티수 자연 주입은 prepare 가 READY 에 도달해야 한다.
- 프로필수 != 엔티티수면 config LLM 호출 *이전* 에 fail-fast 로 거부(cheap pre-check).
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


class _ConfigGen:
    called = False

    def generate_config(self, **k):
        _ConfigGen.called = True
        n = 3

        class _P:
            generation_reasoning = "r"
            agent_configs = [{"agent_id": i} for i in range(n)]

            class event_config:
                initial_posts = [{"poster_agent_id": 0}, {"poster_agent_id": 2}]

            def to_json(self):
                return json.dumps({})
        return _P()


@pytest.fixture
def manager(tmp_path, monkeypatch):
    monkeypatch.setattr(SimulationManager, "SIMULATION_DATA_DIR", str(tmp_path / "sims"))
    monkeypatch.setattr(sm, "ZepEntityReader", lambda *a, **k: make_fake_zep_reader("valid", count=3))
    monkeypatch.setattr(sm, "OasisProfileGenerator", _NoGen)
    monkeypatch.setattr(sm, "SimulationConfigGenerator", lambda *a, **k: _ConfigGen())
    _ConfigGen.called = False
    return SimulationManager()


def _inject(manager, sim_id, ids):
    sim_dir = manager._get_simulation_dir(sim_id)
    os.makedirs(sim_dir, exist_ok=True)
    profs = [{"user_id": i, "user_name": f"u{i}", "name": f"n{i}", "bio": "b", "persona": "p"} for i in ids]
    with open(os.path.join(sim_dir, "injected_profiles.json"), "w", encoding="utf-8") as f:
        json.dump(profs, f)


def test_natural_injection_zero_based_reaches_ready(manager):
    state = manager.create_simulation(project_id="p", graph_id="g1", enable_twitter=False, enable_reddit=True)
    _inject(manager, state.simulation_id, [0, 1, 2])  # 0-based 연속, 엔티티 3개와 일치
    result = manager.prepare_simulation(simulation_id=state.simulation_id, simulation_requirement="r", document_text="d")
    assert result.status == SimulationStatus.READY


def test_count_mismatch_rejected_before_config(manager):
    state = manager.create_simulation(project_id="p", graph_id="g1", enable_twitter=False, enable_reddit=True)
    _inject(manager, state.simulation_id, [0, 1])  # 2개 != 엔티티 3개
    result = manager.prepare_simulation(simulation_id=state.simulation_id, simulation_requirement="r", document_text="d")
    assert result.status == SimulationStatus.FAILED
    # config LLM 호출 이전에 거부되어야 한다 (cheap pre-check)
    assert _ConfigGen.called is False
