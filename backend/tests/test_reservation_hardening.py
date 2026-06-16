"""T-041 비차단 유보 하드닝 검증.

- validate_profiles 빈 리스트 거부
- twitter CSV formula injection escaping
(업로드 simulation 존재검증은 test_profile_upload_endpoint.py::test_upload_to_missing_simulation_404)
"""

import csv
import os
import tempfile

import pytest

from app.services.profile_validator import validate_profiles, ProfileValidationError
from app.services.oasis_profile_generator import OasisAgentProfile, OasisProfileGenerator


def test_validate_profiles_rejects_empty_list():
    with pytest.raises(ProfileValidationError) as ei:
        validate_profiles([])
    assert "비어" in str(ei.value)


def test_twitter_csv_escapes_formula_injection():
    gen = OasisProfileGenerator.__new__(OasisProfileGenerator)
    profiles = [OasisAgentProfile(
        user_id=0, user_name="u0", name="=cmd|calc", bio="=HYPERLINK(1)", persona="x",
    )]
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "twitter_profiles.csv")
        gen._save_twitter_csv(profiles, path)
        rows = list(csv.DictReader(open(path, encoding="utf-8")))
    # = 로 시작하던 셀은 선행 작은따옴표로 escape 되어야 한다
    assert rows[0]["name"].startswith("'=")
    assert rows[0]["user_char"].startswith("'=")
