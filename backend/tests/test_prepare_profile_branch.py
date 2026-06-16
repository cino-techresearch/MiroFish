"""prepare_simulation 의 ProfileSource 분기 테스트 (T-016 / TS-004c, TS-004d, FR-005).

injected_profiles.json 이 sim_dir 에 있으면 prepare 는 OasisProfileGenerator 로
프로필을 생성하지 않고(LLM 0회) 주입본을 로드해 reddit/twitter 로 변환 저장한다.
"""

import json
import os

import pytest

import app.services.simulation_manager as sm
from app.services.simulation_manager import SimulationManager, SimulationStatus
from app.services.oasis_profile_generator import OasisAgentProfile
from tests.fixtures.zep_mock import make_fake_zep_reader


class _NoGenerate:
    """generate 경로가 호출되면 실패 — 주입 경로에서 생성이 일어나지 않음을 증명."""
    instantiated = False

    def __init__(self, *a, **k):
        _NoGenerate.instantiated = True

    def generate_profiles_from_entities(self, *a, **k):
        raise AssertionError("주입 경로에서 프로필 생성이 호출되면 안 된다")

    def save_profiles(self, profiles, file_path, platform="reddit"):
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump([{"user_id": p.user_id, "user_name": p.user_name} for p in profiles],
                      f, ensure_ascii=False)


class _FakeParams:
    generation_reasoning = "fake"

    def __init__(self, n=3):
        # 주입 정합성 검증(FR-012)과 일치하도록 agent_configs/initial_posts 제공
        self.agent_configs = [{"agent_id": i} for i in range(n)]

        class _EC:
            pass
        self.event_config = _EC()
        self.event_config.initial_posts = []

    def to_json(self):
        return json.dumps({"agent_configs": [a["agent_id"] for a in self.agent_configs]})


class _FakeConfigGen:
    def generate_config(self, **kwargs):
        return _FakeParams()


@pytest.fixture
def manager(tmp_path, monkeypatch):
    monkeypatch.setattr(SimulationManager, "SIMULATION_DATA_DIR", str(tmp_path / "sims"))
    monkeypatch.setattr(sm, "ZepEntityReader", lambda *a, **k: make_fake_zep_reader("valid", count=3))
    monkeypatch.setattr(sm, "OasisProfileGenerator", _NoGenerate)
    monkeypatch.setattr(sm, "SimulationConfigGenerator", _FakeConfigGen)
    _NoGenerate.instantiated = False
    return SimulationManager()


def _write_injected(manager, sim_id, n):
    sim_dir = manager._get_simulation_dir(sim_id)
    os.makedirs(sim_dir, exist_ok=True)
    profs = [{"user_id": i, "user_name": f"u{i}", "name": f"n{i}", "bio": "b", "persona": "p"}
             for i in range(n)]
    with open(os.path.join(sim_dir, "injected_profiles.json"), "w", encoding="utf-8") as f:
        json.dump(profs, f)


def test_injected_profiles_skip_generation(manager):
    state = manager.create_simulation(project_id="proj_x", graph_id="g1",
                                      enable_twitter=False, enable_reddit=True)
    _write_injected(manager, state.simulation_id, 3)

    result = manager.prepare_simulation(
        simulation_id=state.simulation_id,
        simulation_requirement="req",
        document_text="doc",
    )

    assert result.status == SimulationStatus.READY
    assert result.profiles_count == 3
    # 생성기는 인스턴스화(=실제 생성)되지 않아야 한다
    assert _NoGenerate.instantiated is False
    # 변환 산출물(reddit_profiles.json) 작성됨
    sim_dir = manager._get_simulation_dir(state.simulation_id)
    assert os.path.exists(os.path.join(sim_dir, "reddit_profiles.json"))


def test_generated_path_still_used_without_injection(manager):
    state = manager.create_simulation(project_id="proj_x", graph_id="g1",
                                      enable_twitter=False, enable_reddit=True)
    # injected_profiles.json 없음 → 생성 경로 → _NoGenerate.generate 가 AssertionError 발생
    with pytest.raises(AssertionError):
        manager.prepare_simulation(
            simulation_id=state.simulation_id,
            simulation_requirement="req",
            document_text="doc",
        )
    assert _NoGenerate.instantiated is True
