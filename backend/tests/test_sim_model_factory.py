"""OASIS 시뮬 모델 팩토리 재지정 + gpt-5.5 수용 검증 (FR-002 / TS-002, TS-002b)."""

import os

import pytest

_SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "scripts")
_SCRIPTS = [
    "run_parallel_simulation.py",
    "run_reddit_simulation.py",
    "run_twitter_simulation.py",
]


@pytest.mark.parametrize("script", _SCRIPTS)
def test_scripts_wire_base_url_to_model_factory(script):
    """TS-002: 세 스크립트가 LLM_BASE_URL 을 OPENAI_API_BASE_URL 로 흘리고 ModelFactory.create 를 부른다."""
    src = open(os.path.join(_SCRIPTS_DIR, script)).read()
    assert "LLM_BASE_URL" in src, f"{script}: LLM_BASE_URL 참조 없음"
    assert "OPENAI_API_BASE_URL" in src, f"{script}: OPENAI_API_BASE_URL 설정 없음"
    assert "ModelFactory.create" in src, f"{script}: ModelFactory.create 호출 없음"


def test_camel_accepts_gpt_5_5_model_string(monkeypatch):
    """TS-002b: camel-ai ModelFactory.create 가 'gpt-5.5' 문자열을 예외 없이 수용한다.

    ModelType enum 에는 gpt-5.5 가 없지만 OPENAI 플랫폼은 임의 문자열을 수용해
    OpenAIModel 을 생성한다(검증됨). 미수용으로 회귀하면 config-only 전제가 깨진다.
    env 변경은 monkeypatch 로만 수행해 테스트 종료 시 전역 상태를 복원한다.
    """
    camel = pytest.importorskip("camel.models", reason="camel-ai 미설치")
    from camel.types import ModelPlatformType

    # 환경의 SOCKS 프록시 env 가 httpx 클라이언트 생성을 막지 않도록 제거 (자동 복원)
    for var in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY",
                "http_proxy", "https_proxy", "all_proxy"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "test-fake-key")
    monkeypatch.setenv("OPENAI_API_BASE_URL", "http://127.0.0.1:39281/v1")

    model = camel.ModelFactory.create(
        model_platform=ModelPlatformType.OPENAI,
        model_type="gpt-5.5",
    )
    assert model is not None
    assert "Model" in type(model).__name__
