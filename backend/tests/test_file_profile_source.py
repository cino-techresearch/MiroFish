"""FileProfileSource 테스트 (T-008 / TS-002, TS-019, FR-002, FR-011).

- 중립 JSON(list[dict]) -> OasisAgentProfile[] 로드
- OasisProfileGenerator(__init__ 시 LLM_API_KEY 요구)를 생성하지 않음
  -> LLM_API_KEY 부재 환경에서도 동작 (TS-019)
"""

import json

import pytest

from app.services.oasis_profile_generator import OasisAgentProfile
from app.services.profile_source import FileProfileSource, ProfileSource


def _neutral(uid):
    return {
        "user_id": uid, "user_name": f"u{uid}", "name": f"n{uid}",
        "bio": "b", "persona": "p", "age": 30, "interested_topics": ["x"],
        "unknown_field": "ignored",
    }


def test_loads_from_list():
    src = FileProfileSource(profiles=[_neutral(0), _neutral(1)])
    out = src.load_profiles()
    assert len(out) == 2
    assert all(isinstance(p, OasisAgentProfile) for p in out)
    assert [p.user_id for p in out] == [0, 1]
    assert out[0].interested_topics == ["x"]


def test_loads_from_json_file(tmp_path):
    f = tmp_path / "injected_profiles.json"
    f.write_text(json.dumps([_neutral(0)]), encoding="utf-8")
    src = FileProfileSource(profiles_path=str(f))
    out = src.load_profiles()
    assert len(out) == 1
    assert out[0].user_name == "u0"


def test_is_profile_source():
    assert isinstance(FileProfileSource(profiles=[]), ProfileSource)


def test_works_without_llm_api_key(monkeypatch):
    """LLM_API_KEY 가 없어도 FileProfileSource 는 동작해야 한다 (FR-011/TS-019)."""
    import app.config as cfg
    monkeypatch.setattr(cfg.Config, "LLM_API_KEY", None, raising=False)
    src = FileProfileSource(profiles=[_neutral(0)])
    out = src.load_profiles()  # OasisProfileGenerator 미생성이므로 예외 없어야 함
    assert out[0].user_id == 0
