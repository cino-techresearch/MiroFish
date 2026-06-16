"""주입 프로필 ↔ agent_configs ↔ initial_posts 정합성 fail-fast 검증 (FR-012).

정상 파이프라인에서는 셋이 모두 동일한 ZEP 엔티티 목록에서 파생되어 자동 정렬되지만,
프로필을 주입하면 정렬이 깨질 수 있다. OASIS 는 프로필 user_id 로 agent 를 찾고
initial_posts.poster_agent_id 는 agent_configs 의 agent_id 를 가리키므로, 다음을 검증한다:

1. 프로필 수 == agent_configs 수
2. 모든 agent_config.agent_id 가 프로필 user_id 집합에 존재
3. 모든 initial_posts.poster_agent_id(None 제외)가 프로필 user_id 집합에 존재

불일치 시 자동 재정렬하지 않고 누락 ID 와 함께 거부한다(사용자 확정 정책: 거부).
"""

from typing import Any, Dict, List


class InjectionConsistencyError(ValueError):
    """주입 데이터가 config/initial_posts 와 정합하지 않을 때 발생."""


def _ids(items: List[Any], key: str) -> List[Any]:
    out = []
    for it in items:
        if isinstance(it, dict):
            out.append(it.get(key))
        else:
            out.append(getattr(it, key, None))
    return out


def validate_injection_consistency(
    profiles: List[Any],
    agent_configs: List[Any],
    initial_posts: List[Dict[str, Any]],
) -> None:
    """주입 정합성을 검증한다. 위반 시 InjectionConsistencyError.

    Args:
        profiles: 주입 프로필(dict 또는 OasisAgentProfile). user_id 보유.
        agent_configs: config 의 agent 설정(dict 또는 객체). agent_id 보유.
        initial_posts: poster_agent_id 를 가진 초기 포스트 dict 리스트.
    """
    errors: List[str] = []

    user_ids = set(_ids(profiles, "user_id"))

    # 1) 개수 정합
    if len(profiles) != len(agent_configs):
        errors.append(
            f"프로필 수({len(profiles)})와 agent_configs 수({len(agent_configs)})가 다릅니다"
        )

    # 2) agent_config 마다 대응 프로필 존재
    missing_for_agents = sorted(
        {aid for aid in _ids(agent_configs, "agent_id") if aid is not None and aid not in user_ids},
        key=str,
    )
    if missing_for_agents:
        errors.append(
            f"agent_id 에 대응하는 프로필 user_id 없음: {missing_for_agents}"
        )

    # 3) initial_posts.poster_agent_id 마다 대응 프로필 존재 (None 제외)
    missing_for_posts = sorted(
        {pid for pid in _ids(initial_posts, "poster_agent_id") if pid is not None and pid not in user_ids},
        key=str,
    )
    if missing_for_posts:
        errors.append(
            f"initial_posts.poster_agent_id 에 대응하는 프로필 user_id 없음: {missing_for_posts}"
        )

    if errors:
        raise InjectionConsistencyError("주입 정합성 검증 실패:\n- " + "\n- ".join(errors))
