"""T-040 통합 정리 검증: _check FAILED 오판 + 정합성 실패 산출물 정리 + user_id 0-기반.

- validate_profiles: user_id 가 0-기반 연속이 아니면 거부 (에러 메시지 약속 강제)
- _check_simulation_prepared: status=failed 는 prepared 로 보지 않음(재-prepare 가능)
- prepare 정합성 실패: config_generated=False + simulation_config.json 제거
"""

import json
import os

import pytest

import app.api.simulation as sim_api
import app.services.simulation_manager as sm
from app.config import Config
from app.services.profile_validator import validate_profiles, ProfileValidationError
from app.services.simulation_manager import SimulationManager, SimulationStatus
from tests.fixtures.zep_mock import make_fake_zep_reader


def _p(uid):
    return {"user_id": uid, "user_name": f"u{uid}", "name": f"n{uid}", "bio": "b", "persona": "p"}


def test_validate_profiles_rejects_non_zero_based():
    with pytest.raises(ProfileValidationError) as ei:
        validate_profiles([_p(1), _p(2), _p(3)])  # 1-기반 → 거부
    assert "0-기반" in str(ei.value)


def test_validate_profiles_accepts_zero_based():
    validate_profiles([_p(0), _p(1), _p(2)])  # 예외 없음


def test_check_simulation_prepared_failed_not_prepared(tmp_path, monkeypatch):
    monkeypatch.setattr(Config, "OASIS_SIMULATION_DATA_DIR", str(tmp_path))
    sid = "sim_failed"
    sd = os.path.join(str(tmp_path), sid)
    os.makedirs(sd)
    # FAILED + config_generated=True + 파일 존재여도 prepared 가 아니어야 한다
    json.dump({"status": "failed", "config_generated": True}, open(os.path.join(sd, "state.json"), "w"))
    json.dump({}, open(os.path.join(sd, "simulation_config.json"), "w"))
    json.dump([{"user_id": 0}], open(os.path.join(sd, "reddit_profiles.json"), "w"))
    json.dump([], open(os.path.join(sd, "twitter_profiles.csv"), "w"))
    prepared, _info = sim_api._check_simulation_prepared(sid)
    assert prepared is False


class _NoGen:
    def __init__(self, *a, **k):
        pass

    def save_profiles(self, profiles, file_path, platform="reddit"):
        json.dump([{"user_id": p.user_id} for p in profiles], open(file_path, "w"))


def _cfg(agent_ids):
    class _P:
        generation_reasoning = "r"
        agent_configs = [{"agent_id": i} for i in agent_ids]

        class event_config:
            initial_posts = []

        def to_json(self):
            return json.dumps({})
    return lambda *a, **k: type("CG", (), {"generate_config": lambda self, **k: _P()})()


def test_consistency_failure_cleans_partial_config(tmp_path, monkeypatch):
    monkeypatch.setattr(SimulationManager, "SIMULATION_DATA_DIR", str(tmp_path / "sims"))
    monkeypatch.setattr(sm, "ZepEntityReader", lambda *a, **k: make_fake_zep_reader("valid", count=3))
    monkeypatch.setattr(sm, "OasisProfileGenerator", _NoGen)
    # agent_configs 가 프로필과 불일치(poster 없음/개수는 맞으나 id 어긋남) → 정합성 실패 유도
    monkeypatch.setattr(sm, "SimulationConfigGenerator", _cfg([0, 1, 9]))
    mgr = SimulationManager()
    state = mgr.create_simulation(project_id="p", graph_id="g1", enable_twitter=False, enable_reddit=True)
    sd = mgr._get_simulation_dir(state.simulation_id)
    os.makedirs(sd, exist_ok=True)
    json.dump([_p(i) for i in range(3)], open(os.path.join(sd, "injected_profiles.json"), "w"))

    result = mgr.prepare_simulation(simulation_id=state.simulation_id, simulation_requirement="r", document_text="d")
    assert result.status == SimulationStatus.FAILED
    assert result.config_generated is False
    # 부분 산출물 제거됨
    assert not os.path.exists(os.path.join(sd, "simulation_config.json"))
