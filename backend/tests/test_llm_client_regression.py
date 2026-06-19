"""LLMClient 경유 호출지점 무회귀 smoke (NFR-002a / TS-007).

base_url 재지정은 공통 LLMClient(TS-004)로 보증된다. 본 테스트는 LLMClient 를 경유하는
3개 서비스 모듈이 import/심볼 노출에서 회귀하지 않음만 확인한다 (시그니처/동작 무변경).
"""

import importlib

import pytest

_MODULES = [
    ("app.services.report_agent", "ReportAgent"),
    ("app.services.zep_tools", "ZepToolsService"),
    ("app.services.ontology_generator", "OntologyGenerator"),
]


@pytest.mark.parametrize("module_name,symbol", _MODULES)
def test_llm_consumer_modules_import(module_name, symbol):
    mod = importlib.import_module(module_name)
    assert hasattr(mod, symbol), f"{module_name}.{symbol} 누락 (회귀)"


def test_llmclient_signature_unchanged():
    """LLMClient.chat / chat_json 시그니처가 보존된다."""
    import inspect

    from app.utils.llm_client import LLMClient

    chat = inspect.signature(LLMClient.chat)
    assert {"messages", "temperature", "max_tokens", "response_format"} <= set(chat.parameters)
    chat_json = inspect.signature(LLMClient.chat_json)
    assert {"messages", "temperature", "max_tokens"} <= set(chat_json.parameters)
