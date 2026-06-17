"""엔티티-0 가드 재정렬 테스트 (T-032 / TS-004d, FR-005).

주입 프로필 경로는 엔티티-0 가드에 선점되지 않아야 한다:
- 주입 + 엔티티0 → generic "엔티티 없음" 이 아니라 cheap pre-check(수 불일치) 사유로 처리
- 주입 + 엔티티 일치 → READY (온톨로지+프로필 동시 주입 happy)
- 비주입(생성) + 엔티티0 → 기존대로 generic 엔티티 없음 FAILED
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

    def generate_profiles_from_entities(self, *a, **k):
        return []

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


def _mgr(tmp_path, monkeypatch, entity_count, n_cfg):
    monkeypatch.setattr(SimulationManager, "SIMULATION_DATA_DIR", str(tmp_path / "sims"))
    monkeypatch.setattr(sm, "ZepEntityReader", lambda *a, **k: make_fake_zep_reader(
        "zero_entity" if entity_count == 0 else "valid", count=entity_count))
    monkeypatch.setattr(sm, "OasisProfileGenerator", _NoGen)
    monkeypatch.setattr(sm, "SimulationConfigGenerator", _config_gen(n_cfg))
    return SimulationManager()


def _inject(mgr, sim_id, ids):
    sd = mgr._get_simulation_dir(sim_id)
    os.makedirs(sd, exist_ok=True)
    profs = [{"user_id": i, "user_name": f"u{i}", "name": f"n{i}", "bio": "b", "persona": "p"} for i in ids]
    with open(os.path.join(sd, "injected_profiles.json"), "w", encoding="utf-8") as f:
        json.dump(profs, f)


def test_injected_with_zero_entities_not_preempted_by_generic_guard(tmp_path, monkeypatch):
    mgr = _mgr(tmp_path, monkeypatch, entity_count=0, n_cfg=0)
    state = mgr.create_simulation(project_id="p", graph_id="g1", enable_twitter=False, enable_reddit=True)
    _inject(mgr, state.simulation_id, [0, 1])  # 2 != 0
    result = mgr.prepare_simulation(simulation_id=state.simulation_id, simulation_requirement="r", document_text="d")
    assert result.status == SimulationStatus.FAILED
    # generic "엔티티 없음" 이 아니라 수 불일치 사유여야 한다 (주입 분기 도달 증명)
    assert "엔티티 수" in result.error or "프로필 수" in result.error


def test_dual_injection_matching_count_ready(tmp_path, monkeypatch):
    mgr = _mgr(tmp_path, monkeypatch, entity_count=3, n_cfg=3)
    state = mgr.create_simulation(project_id="p", graph_id="g_injected", enable_twitter=False, enable_reddit=True)
    _inject(mgr, state.simulation_id, [0, 1, 2])
    result = mgr.prepare_simulation(simulation_id=state.simulation_id, simulation_requirement="r", document_text="d")
    assert result.status == SimulationStatus.READY


def test_generation_path_zero_entities_still_generic_fail(tmp_path, monkeypatch):
    mgr = _mgr(tmp_path, monkeypatch, entity_count=0, n_cfg=0)
    state = mgr.create_simulation(project_id="p", graph_id="g1", enable_twitter=False, enable_reddit=True)
    # injected_profiles.json 없음 → 생성 경로 → 기존 generic 가드
    result = mgr.prepare_simulation(simulation_id=state.simulation_id, simulation_requirement="r", document_text="d")
    assert result.status == SimulationStatus.FAILED
    assert "엔티티" in result.error
