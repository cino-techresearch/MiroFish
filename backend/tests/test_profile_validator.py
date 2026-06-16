"""중립 JSON 프로필 검증기 테스트 (T-009 / TS-006, TS-007).

fail-fast 규칙:
- 필수 필드(user_id, user_name, name, bio, persona) 누락 → 거부
- 타입 불일치(user_id 가 int 아님 등) → 거부
- user_id 중복 → 거부
- 정상 → 통과
"""

import pytest

from app.services.profile_validator import validate_profiles, ProfileValidationError


def _valid(uid=0):
    return {
        "user_id": uid,
        "user_name": f"user{uid}",
        "name": f"Name {uid}",
        "bio": "bio",
        "persona": "persona",
    }


def test_valid_profiles_pass():
    validate_profiles([_valid(0), _valid(1)])  # 예외 없어야 함


def test_missing_required_field_rejected():
    bad = _valid(0)
    del bad["persona"]
    with pytest.raises(ProfileValidationError) as ei:
        validate_profiles([bad])
    assert "persona" in str(ei.value)


def test_type_mismatch_rejected():
    bad = _valid(0)
    bad["user_id"] = "not-an-int"
    with pytest.raises(ProfileValidationError) as ei:
        validate_profiles([bad])
    assert "user_id" in str(ei.value)


def test_duplicate_user_id_rejected():
    with pytest.raises(ProfileValidationError) as ei:
        validate_profiles([_valid(0), _valid(0)])
    assert "user_id" in str(ei.value).lower() or "중복" in str(ei.value)


def test_non_list_rejected():
    with pytest.raises(ProfileValidationError):
        validate_profiles({"user_id": 0})  # type: ignore[arg-type]
