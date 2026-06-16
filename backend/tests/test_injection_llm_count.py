"""주입 레이어 LLM 0회 검증 (T-022 / TS-001, TS-003, TS-004d, NFR-002).

온톨로지 주입(graph_id 재사용) + 프로필 주입(중립 JSON) 조합에서 prepare 가
프로필 레이어의 LLM 생성기(OasisProfileGenerator)를 전혀 호출하지 않음을 단언한다.
(config 생성 LLM 은 NFR-002 측정 대상 아님 — fake 로 대체)
"""

import json
import os

import pytest

import app.services.simulation_manager as sm
from app.services.simulation_manager import SimulationManager, SimulationStatus
from tests.fixtures.zep_mock import make_fake_zep_reader
from tests.fixtures.llm_mock import make_spy_llm


class _CountingGen:
    """generate 가 호출되면 LLM 사용으로 간주 — 주입 경로에서 0이어야 한다."""
    generate_calls = 0

    def __init__(self, *a, **k):
        pass

    def generate_profiles_from_entities(self, *a, **k):
        _CountingGen.generate_calls += 1
        return []

    def save_profiles(self, profiles, file_path, platform="reddit"):
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump([{"user_id": p.user_id} for p in profiles], f)


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


@pytest.fixture
def manager(tmp_path, monkeypatch):
    monkeypatch.setattr(SimulationManager, "SIMULATION_DATA_DIR", str(tmp_path / "sims"))
    monkeypatch.setattr(sm, "ZepEntityReader", lambda *a, **k: make_fake_zep_reader("valid", count=3))
    monkeypatch.setattr(sm, "OasisProfileGenerator", _CountingGen)
    monkeypatch.setattr(sm, "SimulationConfigGenerator", lambda *a, **k: type("CG", (), {"generate_config": lambda self, **k: _Params()})())
    _CountingGen.generate_calls = 0
    return SimulationManager()


def test_injected_layers_zero_profile_llm(manager):
    state = manager.create_simulation(project_id="p", graph_id="g_injected",
                                      enable_twitter=False, enable_reddit=True)
    sim_dir = manager._get_simulation_dir(state.simulation_id)
    os.makedirs(sim_dir, exist_ok=True)
    profs = [{"user_id": i, "user_name": f"u{i}", "name": f"n{i}", "bio": "b", "persona": "p"} for i in range(3)]
    with open(os.path.join(sim_dir, "injected_profiles.json"), "w", encoding="utf-8") as f:
        json.dump(profs, f)

    result = manager.prepare_simulation(simulation_id=state.simulation_id,
                                        simulation_requirement="r", document_text="d")
    assert result.status == SimulationStatus.READY
    # 프로필 레이어 LLM 생성 호출 0회 (NFR-002)
    assert _CountingGen.generate_calls == 0


def test_spy_llm_helper_available():
    # SpyLLMClient 가 카운트 도구로 사용 가능함을 확인 (조합 카운트 인프라)
    spy = make_spy_llm()
    assert spy.call_count == 0
