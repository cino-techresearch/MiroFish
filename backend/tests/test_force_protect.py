"""주입본 보호 + _check_simulation_prepared 부작용 제거 테스트 (T-019 / TS-014, TS-015, FR-007).

- TS-015: _check_simulation_prepared 는 read-only — state.json 을 mutate 하지 않는다.
- TS-014: 주입 프로필 존재 시 prepare 재실행이 injected_profiles.json 을 덮어쓰지 않는다.
"""

import json
import os

import pytest

import app.api.simulation as sim_api
import app.services.simulation_manager as sm
from app.config import Config
from app.services.simulation_manager import SimulationManager, SimulationStatus
from tests.fixtures.zep_mock import make_fake_zep_reader


def _write(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)


def test_check_simulation_prepared_no_side_effect(tmp_path, monkeypatch):
    monkeypatch.setattr(Config, "OASIS_SIMULATION_DATA_DIR", str(tmp_path))
    sim_id = "sim_chk"
    sd = os.path.join(str(tmp_path), sim_id)
    os.makedirs(sd)
    _write(os.path.join(sd, "state.json"), {"status": "preparing", "config_generated": True})
    _write(os.path.join(sd, "simulation_config.json"), {})
    _write(os.path.join(sd, "reddit_profiles.json"), [{"user_id": 0}])
    _write(os.path.join(sd, "twitter_profiles.csv"), [])

    prepared, info = sim_api._check_simulation_prepared(sim_id)
    assert prepared is True
    # 디스크의 state.json 은 여전히 preparing 이어야 한다 (부작용 없음)
    on_disk = json.load(open(os.path.join(sd, "state.json"), encoding="utf-8"))
    assert on_disk["status"] == "preparing"


class _NoGen:
    def __init__(self, *a, **k):
        pass

    def save_profiles(self, profiles, file_path, platform="reddit"):
        _write(file_path, [{"user_id": p.user_id} for p in profiles])


class _Params:
    generation_reasoning = "r"

    def __init__(self):
        self.agent_configs = [{"agent_id": i} for i in range(3)]

        class _EC:
            pass
        self.event_config = _EC()
        self.event_config.initial_posts = []

    def to_json(self):
        return json.dumps({})


def test_injected_profiles_not_overwritten_on_reprepare(tmp_path, monkeypatch):
    monkeypatch.setattr(SimulationManager, "SIMULATION_DATA_DIR", str(tmp_path / "sims"))
    monkeypatch.setattr(sm, "ZepEntityReader", lambda *a, **k: make_fake_zep_reader("valid", count=3))
    monkeypatch.setattr(sm, "OasisProfileGenerator", _NoGen)
    monkeypatch.setattr(sm, "SimulationConfigGenerator", lambda *a, **k: type("CG", (), {"generate_config": lambda self, **k: _Params()})())
    mgr = SimulationManager()
    state = mgr.create_simulation(project_id="p", graph_id="g1", enable_twitter=False, enable_reddit=True)
    sd = mgr._get_simulation_dir(state.simulation_id)
    injected = os.path.join(sd, "injected_profiles.json")
    original = [{"user_id": i, "user_name": f"u{i}", "name": f"n{i}", "bio": "b", "persona": "p"} for i in range(3)]
    _write(injected, original)

    mgr.prepare_simulation(simulation_id=state.simulation_id, simulation_requirement="r", document_text="d")
    # 재실행(force 재준비 모사)
    mgr.prepare_simulation(simulation_id=state.simulation_id, simulation_requirement="r", document_text="d")

    # 주입본은 그대로여야 한다
    assert json.load(open(injected, encoding="utf-8")) == original
