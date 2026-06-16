"""중립 JSON 프로필 fail-fast 검증기 (FR-006).

주입되는 중립 JSON 프로필(OasisAgentProfile 스키마)이 OASIS 에서 깨지지 않도록
주입 시점에 검증한다. 위반은 명확한 메시지와 함께 즉시 거부한다.

필수 필드: user_id(int), user_name(str), name(str), bio(str), persona(str)
"""

from typing import Any, List

# (필드명, 기대 타입) — 필수 필드만. 선택 필드는 OasisAgentProfile 기본값으로 보강된다.
REQUIRED_FIELDS = (
    ("user_id", int),
    ("user_name", str),
    ("name", str),
    ("bio", str),
    ("persona", str),
)


class ProfileValidationError(ValueError):
    """주입 프로필이 검증을 통과하지 못했을 때 발생."""


def validate_profiles(profiles: Any) -> None:
    """중립 JSON 프로필 리스트를 검증한다. 위반 시 ProfileValidationError.

    Args:
        profiles: 프로필 dict 의 리스트

    Raises:
        ProfileValidationError: 리스트가 아니거나 필수 필드 누락/타입 불일치/user_id 중복.
    """
    if not isinstance(profiles, list):
        raise ProfileValidationError(
            f"프로필은 리스트여야 합니다 (받은 타입: {type(profiles).__name__})"
        )
    if len(profiles) == 0:
        raise ProfileValidationError("프로필이 비어 있습니다 (최소 1개 프로필 필요)")

    errors: List[str] = []
    seen_user_ids: set = set()

    for idx, profile in enumerate(profiles):
        if not isinstance(profile, dict):
            errors.append(f"[{idx}] 프로필 항목은 객체여야 합니다 (받은 타입: {type(profile).__name__})")
            continue

        for field_name, expected_type in REQUIRED_FIELDS:
            if field_name not in profile:
                errors.append(f"[{idx}] 필수 필드 누락: {field_name}")
                continue
            value = profile[field_name]
            # bool 은 int 의 서브타입이므로 user_id 에 bool 이 들어오면 거부
            if expected_type is int and isinstance(value, bool):
                errors.append(f"[{idx}] 필드 타입 불일치: user_id 는 int 여야 합니다 (bool 불가)")
            elif not isinstance(value, expected_type):
                errors.append(
                    f"[{idx}] 필드 타입 불일치: {field_name} 는 {expected_type.__name__} 여야 합니다 "
                    f"(받은 타입: {type(value).__name__})"
                )

        uid = profile.get("user_id")
        if isinstance(uid, int) and not isinstance(uid, bool):
            if uid in seen_user_ids:
                errors.append(f"[{idx}] user_id 중복: {uid}")
            seen_user_ids.add(uid)

    # FR-005 재설계: agent_config 가 주입 프로필에서 파생되므로 0-기반 연속 제약은 불필요.
    # user_id 는 고유하기만 하면 임의 정수 허용(agent_id 로 그대로 사용됨).

    if errors:
        raise ProfileValidationError("주입 프로필 검증 실패:\n- " + "\n- ".join(errors))
