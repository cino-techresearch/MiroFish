"""LLM mock + 호출 카운트 spy 자체 검증 (T-003 / TS-001, TS-003 지원).

주입 레이어 LLM 0회(NFR-002) 검증 테스트가 공유할 SpyLLMClient 가
chat/chat_json 호출 횟수를 정확히 집계하는지 확인한다.
"""

from tests.fixtures.llm_mock import SpyLLMClient, make_spy_llm


def test_spy_starts_at_zero():
    spy = make_spy_llm()
    assert spy.call_count == 0


def test_chat_json_increments_count():
    spy = make_spy_llm(return_value={"entity_types": [], "edge_types": []})
    out = spy.chat_json(messages=[{"role": "user", "content": "x"}])
    assert out == {"entity_types": [], "edge_types": []}
    assert spy.call_count == 1


def test_chat_increments_count():
    spy = make_spy_llm()
    spy.chat(messages=[{"role": "user", "content": "x"}])
    spy.chat(messages=[{"role": "user", "content": "y"}])
    assert spy.call_count == 2


def test_is_spy_instance():
    assert isinstance(make_spy_llm(), SpyLLMClient)
