"""주입 정합성 fail-fast 검증기 테스트 (T-015 / TS-020, FR-012).

OASIS 는 프로필 user_id 로 agent 를 매칭하고 initial_posts.poster_agent_id 는
agent_configs 의 agent_id 를 가리킨다. 주입 프로필 수/user_id 가 어긋나면
시뮬레이션이 깨지므로 주입 시점에 거부한다(자동 재정렬 없음).
"""

import pytest

from app.services.injection_consistency import (
    validate_injection_consistency,
    InjectionConsistencyError,
)


def _profiles(ids):
    return [{"user_id": i, "user_name": f"u{i}", "name": f"n{i}", "bio": "b", "persona": "p"} for i in ids]


def _agent_configs(ids):
    return [{"agent_id": i} for i in ids]


def _posts(poster_ids):
    return [{"poster_agent_id": pid} for pid in poster_ids]


def test_consistent_passes():
    validate_injection_consistency(
        _profiles([0, 1, 2]), _agent_configs([0, 1, 2]), _posts([0, 2])
    )


def test_count_mismatch_rejected():
    with pytest.raises(InjectionConsistencyError) as ei:
        validate_injection_consistency(
            _profiles([0, 1]), _agent_configs([0, 1, 2]), _posts([0])
        )
    assert "수" in str(ei.value) or "count" in str(ei.value).lower()


def test_post_references_missing_profile_rejected():
    with pytest.raises(InjectionConsistencyError) as ei:
        validate_injection_consistency(
            _profiles([0, 1, 2]), _agent_configs([0, 1, 2]), _posts([0, 5])
        )
    assert "5" in str(ei.value)


def test_agent_config_without_profile_rejected():
    with pytest.raises(InjectionConsistencyError) as ei:
        validate_injection_consistency(
            _profiles([0, 1]), _agent_configs([0, 9]), _posts([0])
        )
    assert "9" in str(ei.value)


def test_none_poster_ids_ignored():
    # poster_agent_id 가 None 인 포스트는 매칭 대상에서 제외(아직 미할당).
    validate_injection_consistency(
        _profiles([0, 1]), _agent_configs([0, 1]), _posts([0, None])
    )
