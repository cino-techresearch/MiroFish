"""LLM 테스트 더블 + 호출 카운트 spy (NFR-002 / TS-001, TS-003 지원).

주입된 레이어의 LLM 호출 0회를 단언하기 위해, LLMClient 를 대체하는 SpyLLMClient 를
제공한다. chat/chat_json 호출마다 call_count 를 증가시킨다.

importable 팩토리로 제공해 conftest 수정 없이 어느 테스트에서나 import 해 쓴다.
"""

from typing import Any, Dict, List, Optional


class SpyLLMClient:
    """LLMClient 호환 인터페이스를 가진 호출 카운트 spy.

    실제 네트워크 호출 없이 canned 값을 반환하며, 호출 횟수를 집계한다.
    """

    def __init__(self, return_value: Optional[Any] = None):
        self.call_count = 0
        self.calls: List[Dict[str, Any]] = []
        self._return_value = return_value if return_value is not None else {}

    def chat_json(self, messages, temperature: float = 0.3, max_tokens: int = 4096, **kwargs):
        self.call_count += 1
        self.calls.append({"kind": "chat_json", "messages": messages})
        return self._return_value

    def chat(self, messages, temperature: float = 0.7, max_tokens: int = 2048, **kwargs):
        self.call_count += 1
        self.calls.append({"kind": "chat", "messages": messages})
        if isinstance(self._return_value, str):
            return self._return_value
        return ""


def make_spy_llm(return_value: Optional[Any] = None) -> SpyLLMClient:
    """SpyLLMClient 를 생성하는 팩토리."""
    return SpyLLMClient(return_value=return_value)
