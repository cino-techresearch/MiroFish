"""Regression tests: oasis_profile_generator uses English country values (T-003).

Verifies that:
- rule-based profiles emit "China" (not the former Chinese string)
- _save_reddit_json fallback country is "China"
- _normalize_gender still maps English values correctly
- No CJK characters remain in the source file
"""

import ast
import os
import json
import re
import tempfile

import pytest


# ---------------------------------------------------------------------------
# Helpers / minimal stubs to avoid importing heavy dependencies
# ---------------------------------------------------------------------------

def _import_module():
    """Import the module under test without triggering heavy side-effects."""
    import importlib.util
    module_path = os.path.join(
        os.path.dirname(__file__),
        "..", "app", "services", "oasis_profile_generator.py"
    )
    module_path = os.path.abspath(module_path)
    spec = importlib.util.spec_from_file_location("oasis_profile_generator", module_path)
    mod = importlib.util.module_from_spec(spec)
    return mod, spec, module_path


SOURCE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "app", "services", "oasis_profile_generator.py")
)


# ---------------------------------------------------------------------------
# 1. Source-level: zero CJK characters
# ---------------------------------------------------------------------------

def test_no_cjk_in_source():
    """Source file must contain zero CJK characters after T-003 translation."""
    cjk_re = re.compile(r'[一-鿿]')
    with open(SOURCE_PATH, encoding="utf-8") as fh:
        source = fh.read()
    matches = cjk_re.findall(source)
    assert matches == [], f"CJK characters found in source: {matches[:20]}"


# ---------------------------------------------------------------------------
# 2. Syntax: the file must parse without errors
# ---------------------------------------------------------------------------

def test_source_parses():
    """Source file must be syntactically valid Python."""
    with open(SOURCE_PATH, encoding="utf-8") as fh:
        source = fh.read()
    ast.parse(source)  # raises SyntaxError on failure


# ---------------------------------------------------------------------------
# 3. Rule-based: mediaoutlet and organization profiles use "China"
# ---------------------------------------------------------------------------

class _MinimalConfig:
    LLM_API_KEY = "fake-key"
    LLM_BASE_URL = None
    LLM_MODEL_NAME = "gpt-4o"
    ZEP_API_KEY = None


def _make_generator():
    """Instantiate OasisProfileGenerator with minimal stubs."""
    import unittest.mock as mock

    # Patch heavy imports so __init__ can run without real API keys
    with mock.patch("app.services.oasis_profile_generator.Config", _MinimalConfig), \
         mock.patch("app.services.oasis_profile_generator.OpenAI") as mock_openai, \
         mock.patch("app.services.oasis_profile_generator.Zep"):
        mock_openai.return_value = mock.MagicMock()
        from app.services.oasis_profile_generator import OasisProfileGenerator
        gen = OasisProfileGenerator.__new__(OasisProfileGenerator)
        gen.api_key = "fake"
        gen.base_url = None
        gen.model_name = "gpt-4o"
        gen.client = mock.MagicMock()
        gen.zep_client = None
        gen.graph_id = None
        return gen


def test_rule_based_mediaoutlet_country_is_china():
    gen = _make_generator()
    profile = gen._generate_profile_rule_based(
        entity_name="TestMedia",
        entity_type="mediaoutlet",
        entity_summary="A test media outlet.",
        entity_attributes={}
    )
    assert profile["country"] == "China", (
        f"Expected 'China', got {profile['country']!r}"
    )


def test_rule_based_university_country_is_china():
    gen = _make_generator()
    profile = gen._generate_profile_rule_based(
        entity_name="TestUniversity",
        entity_type="university",
        entity_summary="A test university.",
        entity_attributes={}
    )
    assert profile["country"] == "China", (
        f"Expected 'China', got {profile['country']!r}"
    )


def test_rule_based_student_country_from_list():
    gen = _make_generator()
    profile = gen._generate_profile_rule_based(
        entity_name="Alice",
        entity_type="student",
        entity_summary="A student.",
        entity_attributes={}
    )
    # Should be one of the English country names in COUNTRIES list
    assert isinstance(profile["country"], str)
    assert not re.search(r'[一-鿿]', profile["country"]), (
        f"country contains CJK: {profile['country']!r}"
    )


# ---------------------------------------------------------------------------
# 4. _save_reddit_json: fallback country is "China" not "中国"
# ---------------------------------------------------------------------------

def test_save_reddit_json_fallback_country():
    """Profile with no country set should be saved as 'China'."""
    gen = _make_generator()

    from app.services.oasis_profile_generator import OasisAgentProfile

    profile = OasisAgentProfile(
        user_id=0,
        user_name="test_user_001",
        name="Test User",
        bio="A test bio.",
        persona="A test persona.",
        country=None,  # deliberately absent
    )

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as tmp:
        tmp_path = tmp.name

    try:
        gen._save_reddit_json([profile], tmp_path)
        with open(tmp_path, encoding="utf-8") as fh:
            data = json.load(fh)
        assert data[0]["country"] == "China", (
            f"Expected 'China', got {data[0]['country']!r}"
        )
    finally:
        os.unlink(tmp_path)


# ---------------------------------------------------------------------------
# 5. _normalize_gender: English values pass through correctly
# ---------------------------------------------------------------------------

def test_normalize_gender_english_values():
    gen = _make_generator()
    assert gen._normalize_gender("male") == "male"
    assert gen._normalize_gender("female") == "female"
    assert gen._normalize_gender("other") == "other"
    assert gen._normalize_gender(None) == "other"
    assert gen._normalize_gender("") == "other"
    assert gen._normalize_gender("unknown_value") == "other"
