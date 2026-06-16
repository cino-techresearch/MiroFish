"""프로필 저장 형식 golden test (T-021 / TS-021, FR-006).

최종 저장 형식(OASIS 가 실제로 읽는 SoT)을 고정한다:
- Reddit final(_save_reddit_json): 11 필수 + 2 조건부
- Twitter final(_save_twitter_csv): user_id, name, username, user_char, description

realtime↔final 비교:
- Reddit realtime(to_reddit_format)는 final 의 필수 키를 모두 포함(호환).
- Twitter realtime(to_twitter_format)는 final 과 키가 다르다 — codex#4 가 식별한
  기존 코드의 알려진 불일치. final(_save_twitter_csv)이 OASIS SoT 이므로 golden 은 final 기준.
  이 divergence 를 테스트로 명시해 향후 의도치 않은 변경 시 드러나게 한다.
"""

import csv
import json
import os
import tempfile

from app.services.oasis_profile_generator import OasisAgentProfile, OasisProfileGenerator

REDDIT_FINAL_REQUIRED = {
    "user_id", "username", "name", "bio", "persona",
    "karma", "created_at", "age", "gender", "mbti", "country",
}
TWITTER_FINAL = ["user_id", "name", "username", "user_char", "description"]


def _profiles():
    return [OasisAgentProfile(
        user_id=0, user_name="u0", name="N0", bio="b", persona="p",
        age=25, gender="male", mbti="INTJ", country="China",
        profession="Student", interested_topics=["tech"],
    )]


def _gen():
    return OasisProfileGenerator.__new__(OasisProfileGenerator)


def test_reddit_final_golden_fields():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "reddit_profiles.json")
        _gen()._save_reddit_json(_profiles(), p)
        row = json.load(open(p, encoding="utf-8"))[0]
    assert REDDIT_FINAL_REQUIRED <= set(row.keys())
    assert {"profession", "interested_topics"} <= set(row.keys())


def test_twitter_final_golden_header():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "twitter_profiles.csv")
        _gen()._save_twitter_csv(_profiles(), p)
        header = list(csv.DictReader(open(p, encoding="utf-8")).fieldnames)
    assert header == TWITTER_FINAL


def test_reddit_realtime_compatible_with_final():
    rt = _profiles()[0].to_reddit_format()
    # realtime reddit 은 final 필수 키(기본 5개)를 포함해야 호환된다
    assert {"user_id", "username", "name", "bio", "persona"} <= set(rt.keys())


def test_twitter_realtime_diverges_from_final_known():
    # codex#4 문서화: realtime(to_twitter_format) 키 != final(_save_twitter_csv) 키
    rt_keys = set(_profiles()[0].to_twitter_format().keys())
    assert "user_char" not in rt_keys  # final 에만 있는 필드
    assert "friend_count" in rt_keys   # realtime 에만 있는 필드
