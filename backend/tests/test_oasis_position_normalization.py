"""주입 프로필의 OASIS 위치 정규화 검증 (T-043 / FR-005, FR-012).

OASIS 는 agent_id 를 프로필 *위치*(0..N-1)로 부여하므로, 임의 입력 user_id 를
위치로 정규화해야 get_agent(poster_agent_id) 가 성립한다. 임의 *개수* 는 여전히 허용.
"""

import json
import os

import pytest

import app.services.simulation_manager as sm
from app.services.simulation_manager import SimulationManager, SimulationStatus
from app.services.oasis_profile_generator import OasisAgentProfile
from tests.fixtures.zep_mock import make_fake_zep_reader


class _NoGen:
    def __init__(self, *a, **k):
        pass

    def save_profiles(self, profiles, file_path, platform="reddit"):
        # 저장 user_id 가 위치로 정규화됐는지 확인 가능하도록 user_id 기록
        json.dump([{"user_id": p.user_id} for p in profiles], open(file_path, "w"))


class _CfgFromProfiles:
    """실 생성기처럼 agent_profiles 의 user_id 로 agent_config 파생."""
    last_num = None

    def generate_config(self, **k):
        aps = k.get("agent_profiles") or []
        ids = [p.user_id for p in aps]
        _CfgFromProfiles.last_num = len(ids)

        class _P:
            generation_reasoning = "r"
            agent_configs = [{"agent_id": i} for i in ids]

            class event_config:
                initial_posts = [{"poster_agent_id": i} for i in ids]

            def to_json(self):
                return json.dumps({})
        return _P()


@pytest.fixture
def manager(tmp_path, monkeypatch):
    monkeypatch.setattr(SimulationManager, "SIMULATION_DATA_DIR", str(tmp_path / "sims"))
    monkeypatch.setattr(sm, "ZepEntityReader", lambda *a, **k: make_fake_zep_reader("valid", count=3))
    monkeypatch.setattr(sm, "OasisProfileGenerator", _NoGen)
    monkeypatch.setattr(sm, "SimulationConfigGenerator", lambda *a, **k: _CfgFromProfiles())
    return SimulationManager()


def _inject(manager, sim_id, ids):
    sd = manager._get_simulation_dir(sim_id)
    os.makedirs(sd, exist_ok=True)
    profs = [{"user_id": i, "user_name": f"u{i}", "name": f"n{i}", "bio": "b", "persona": "p"} for i in ids]
    json.dump(profs, open(os.path.join(sd, "injected_profiles.json"), "w"))
    return sd


def test_arbitrary_user_ids_normalized_to_position(manager):
    state = manager.create_simulation(project_id="p", graph_id="g1", enable_twitter=False, enable_reddit=True)
    sd = _inject(manager, state.simulation_id, [10, 25, 99])  # 임의 id
    result = manager.prepare_simulation(simulation_id=state.simulation_id, simulation_requirement="r", document_text="d")
    assert result.status == SimulationStatus.READY
    # 저장된 reddit_profiles.json 의 user_id 가 위치 0..N-1 로 정규화됐는지
    saved = json.load(open(os.path.join(sd, "reddit_profiles.json"), encoding="utf-8"))
    assert [r["user_id"] for r in saved] == [0, 1, 2]


def test_arbitrary_count_uses_profile_count_for_time_config(manager):
    # 엔티티 3개 그래프에 프로필 5개 주입 → agent/time 기준이 프로필 수(5)
    state = manager.create_simulation(project_id="p", graph_id="g1", enable_twitter=False, enable_reddit=True)
    _inject(manager, state.simulation_id, [7, 8, 9, 10, 11])
    result = manager.prepare_simulation(simulation_id=state.simulation_id, simulation_requirement="r", document_text="d")
    assert result.status == SimulationStatus.READY
    assert result.profiles_count == 5
    assert _CfgFromProfiles.last_num == 5  # time_config 도 프로필 수 기준
