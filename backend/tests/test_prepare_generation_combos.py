"""prepare 생성 경로 조합 + extracted_text degraded 테스트 (T-017 / TS-004a, TS-004b, TS-016, FR-005, FR-003).

온톨로지 주입(graph_id 재사용)은 inject 엔드포인트(T-012)에서 처리되고, prepare 는
graph_id 로 엔티티를 균일하게 읽는다 → "온톨로지 주입 + 프로필 생성"과 "생성 + 생성"은
prepare 레벨에서 동일 경로다. 여기서는 생성 경로가 4조합 중 생성측을 충족하고,
extracted_text 미제공(document_text='') 시에도 READY 에 도달함을 검증한다.
"""

import json
import os

import pytest

import app.services.simulation_manager as sm
from app.services.simulation_manager import SimulationManager, SimulationStatus
from app.services.oasis_profile_generator import OasisAgentProfile
from tests.fixtures.zep_mock import make_fake_zep_reader


class _FakeGen:
    """엔티티 수만큼 프로필을 생성하는 가짜 생성기 (LLM 미호출)."""

    def __init__(self, *a, **k):
        pass

    def generate_profiles_from_entities(self, entities, **k):
        return [
            OasisAgentProfile(user_id=i, user_name=f"u{i}", name=f"n{i}", bio="b", persona="p")
            for i in range(len(entities))
        ]

    def save_profiles(self, profiles, file_path, platform="reddit"):
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump([{"user_id": p.user_id} for p in profiles], f)


class _FakeParams:
    generation_reasoning = "fake"

    def to_json(self):
        return json.dumps({"agent_configs": []})


class _FakeConfigGen:
    last_document_text = None

    def generate_config(self, **kwargs):
        _FakeConfigGen.last_document_text = kwargs.get("document_text")
        return _FakeParams()


@pytest.fixture
def manager(tmp_path, monkeypatch):
    monkeypatch.setattr(SimulationManager, "SIMULATION_DATA_DIR", str(tmp_path / "sims"))
    monkeypatch.setattr(sm, "ZepEntityReader", lambda *a, **k: make_fake_zep_reader("valid", count=3))
    monkeypatch.setattr(sm, "OasisProfileGenerator", _FakeGen)
    monkeypatch.setattr(sm, "SimulationConfigGenerator", _FakeConfigGen)
    return SimulationManager()


def test_generation_path_reaches_ready_with_profiles(manager):
    """TS-004a/TS-004b 생성측: 엔티티 수 == 생성 프로필 수, READY 도달."""
    state = manager.create_simulation(project_id="proj_x", graph_id="g1",
                                      enable_twitter=False, enable_reddit=True)
    result = manager.prepare_simulation(
        simulation_id=state.simulation_id,
        simulation_requirement="req",
        document_text="doc",
    )
    assert result.status == SimulationStatus.READY
    assert result.profiles_count == 3  # 주입 graph_id 엔티티 수와 일치


def test_extracted_text_missing_degraded_still_ready(manager):
    """TS-016: document_text='' (extracted_text 미제공) → degraded 진행, READY 도달."""
    state = manager.create_simulation(project_id="proj_x", graph_id="g1",
                                      enable_twitter=False, enable_reddit=True)
    result = manager.prepare_simulation(
        simulation_id=state.simulation_id,
        simulation_requirement="req",
        document_text="",
    )
    assert result.status == SimulationStatus.READY
    # config 생성에 빈 document_text 가 그대로 전달됨(degraded)
    assert _FakeConfigGen.last_document_text == ""
