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

    # user_id 는 0-기반 연속이어야 한다 (OASIS agent_id=0..N-1 와 매칭되기 위함).
    # 타입/중복 에러가 없을 때만 연속성 검사(중복/타입 에러가 우선).
    if not errors and seen_user_ids:
        expected = set(range(len(profiles)))
        if seen_user_ids != expected:
            errors.append(
                f"user_id 는 0-기반 연속이어야 합니다 (0..{len(profiles) - 1}). "
                f"받은 집합: {sorted(seen_user_ids)}"
            )

    if errors:
        raise ProfileValidationError("주입 프로필 검증 실패:\n- " + "\n- ".join(errors))
