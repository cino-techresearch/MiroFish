"""FR-006/FR-007/FR-013: locale.py defaults to 'en', no 'zh' references."""

import importlib
import types
import unittest.mock as mock

import pytest


def test_get_locale_default_en_no_request_context():
    """get_locale() outside request context returns 'en' by default."""
    from app.utils import locale as loc_mod

    # Clear any thread-local locale to simulate a fresh thread
    if hasattr(loc_mod._thread_local, 'locale'):
        del loc_mod._thread_local.locale

    result = loc_mod.get_locale()
    assert result == 'en', f"Expected 'en', got {result!r}"


def test_get_locale_unknown_accept_language_falls_back_to_en():
    """get_locale() with an unregistered Accept-Language header returns 'en'."""
    from app.utils import locale as loc_mod

    fake_request = mock.MagicMock()
    fake_request.headers.get.return_value = 'xx'  # unknown locale

    with mock.patch('app.utils.locale.has_request_context', return_value=True), \
         mock.patch('app.utils.locale.request', fake_request):
        result = loc_mod.get_locale()

    assert result == 'en', f"Expected 'en' fallback, got {result!r}"


def test_get_language_instruction_default_en():
    """get_language_instruction() defaults to English instruction."""
    from app.utils import locale as loc_mod

    if hasattr(loc_mod._thread_local, 'locale'):
        del loc_mod._thread_local.locale

    instruction = loc_mod.get_language_instruction()
    assert 'English' in instruction, f"Expected English instruction, got {instruction!r}"


def test_no_zh_in_translations():
    """zh locale must not be loaded (zh.json was deleted)."""
    from app.utils import locale as loc_mod

    assert 'zh' not in loc_mod._translations, "'zh' locale should not be loaded"


def test_no_zh_in_languages():
    """languages registry must not contain 'zh'."""
    from app.utils import locale as loc_mod

    assert 'zh' not in loc_mod._languages, "'zh' must be removed from languages registry"
