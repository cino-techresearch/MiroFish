"""chat_json 응답 파싱 검증 (FR-005 / TS-005).

이 파일은 응답 래핑(markdown fence / <think> 블록) 파싱만 mock 으로 검증한다.
내부 서버의 response_format=json_object 지원 여부(OQ-3)는 여기서 단정하지 않고,
Final Acceptance 의 라이브 smoke(FA-005: 실서버로 chat_json 1회 호출)가 실증한다.
즉 파싱 계약은 본 단위 테스트, json_object 지원은 FA-005 라이브 증거로 분리한다.
"""

import pytest


def _make_client(monkeypatch, content):
    """canned content 를 반환하는 OpenAI 더블로 LLMClient 를 만든다."""
    import app.utils.llm_client as mod

    class _Msg:
        def __init__(self, c):
            self.message = type("M", (), {"content": c})()

    class _Resp:
        def __init__(self, c):
            self.choices = [_Msg(c)]

    class _Completions:
        def create(self, **kwargs):
            return _Resp(content)

    class _Chat:
        completions = _Completions()

    class _FakeOpenAI:
        def __init__(self, *a, **k):
            self.chat = _Chat()

    monkeypatch.setattr(mod, "OpenAI", _FakeOpenAI)
    return mod.LLMClient(api_key="k", base_url="http://x/v1", model="m")


def test_chat_json_plain(monkeypatch):
    client = _make_client(monkeypatch, '{"status": "ok"}')
    assert client.chat_json([{"role": "user", "content": "x"}]) == {"status": "ok"}


def test_chat_json_markdown_fence(monkeypatch):
    client = _make_client(monkeypatch, '```json\n{"status": "ok"}\n```')
    assert client.chat_json([{"role": "user", "content": "x"}]) == {"status": "ok"}


def test_chat_json_strips_think_block(monkeypatch):
    client = _make_client(monkeypatch, '<think>reasoning here</think>\n{"status": "ok"}')
    assert client.chat_json([{"role": "user", "content": "x"}]) == {"status": "ok"}


def test_chat_strips_think_block(monkeypatch):
    client = _make_client(monkeypatch, '<think>plan</think>hello world')
    assert client.chat([{"role": "user", "content": "x"}]) == "hello world"


def test_chat_json_invalid_raises(monkeypatch):
    client = _make_client(monkeypatch, "not json at all")
    with pytest.raises(ValueError):
        client.chat_json([{"role": "user", "content": "x"}])
