"""Profile 저장 포맷이 OASIS 현행 요구(SoT)와 일치하는지 검증 (T-004 / TS-023).

진실 소스(SoT)는 현행 작동 출력이다:
- Twitter CSV: _save_twitter_csv -> ['user_id', 'name', 'username', 'user_char', 'description']
- Reddit JSON: _save_reddit_json -> 11 필수(user_id, username, name, bio, persona, karma,
  created_at, age, gender, mbti, country) + 2 조건부(profession, interested_topics)

이전 버전은 옛 필드(realname, twitter 8필드)를 기대해 항상 실패했다. 회피(skip)하지 않고
현행 출력에 맞춰 정정 + print->assert 로 변환한다(pytest green, skip 0).
"""

import csv
import json
import os
import tempfile

from app.services.oasis_profile_generator import OasisAgentProfile, OasisProfileGenerator

# 현행 SoT 필드 집합
TWITTER_FIELDS = ["user_id", "name", "username", "user_char", "description"]
REDDIT_REQUIRED_FIELDS = [
    "user_id", "username", "name", "bio", "persona",
    "karma", "created_at", "age", "gender", "mbti", "country",
]
REDDIT_CONDITIONAL_FIELDS = ["profession", "interested_topics"]


def _sample_profiles():
    return [
        OasisAgentProfile(
            user_id=0, user_name="test_user_123", name="Test User",
            bio="A test user for validation",
            persona="Test User is an enthusiastic participant in social discussions.",
            karma=1500, friend_count=100, follower_count=200, statuses_count=500,
            age=25, gender="male", mbti="INTJ", country="China",
            profession="Student", interested_topics=["Technology", "Education"],
            source_entity_uuid="test-uuid-123", source_entity_type="Student",
        ),
        OasisAgentProfile(
            user_id=1, user_name="org_official_456", name="Official Organization",
            bio="Official account for Organization",
            persona="This is an official institutional account.",
            karma=5000, friend_count=50, follower_count=10000, statuses_count=200,
            profession="Organization", interested_topics=["Public Policy"],
            source_entity_uuid="test-uuid-456", source_entity_type="University",
        ),
    ]


def _generator():
    # __init__ 은 LLM_API_KEY 를 요구하므로 우회하고 저장 메서드만 사용한다.
    return OasisProfileGenerator.__new__(OasisProfileGenerator)


def test_twitter_csv_has_sot_header():
    gen = _generator()
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "twitter_profiles.csv")
        gen._save_twitter_csv(_sample_profiles(), path)
        with open(path, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    assert len(rows) == 2
    assert list(rows[0].keys()) == TWITTER_FIELDS


def test_reddit_json_has_required_fields():
    gen = _generator()
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "reddit_profiles.json")
        gen._save_reddit_json(_sample_profiles(), path)
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    assert len(data) == 2
    missing = set(REDDIT_REQUIRED_FIELDS) - set(data[0].keys())
    assert not missing, f"필수 필드 누락: {missing}"


def test_reddit_json_conditional_fields_present_when_provided():
    gen = _generator()
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "reddit_profiles.json")
        gen._save_reddit_json(_sample_profiles(), path)
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    # 샘플은 profession/interested_topics 를 제공하므로 출력에 포함되어야 한다.
    for field in REDDIT_CONDITIONAL_FIELDS:
        assert field in data[0], f"조건부 필드 누락: {field}"


def test_reddit_user_id_preserved():
    """OASIS agent 매칭 키 user_id 가 보존되어야 한다."""
    gen = _generator()
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "reddit_profiles.json")
        gen._save_reddit_json(_sample_profiles(), path)
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    assert [row["user_id"] for row in data] == [0, 1]
