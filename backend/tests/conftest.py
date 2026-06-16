"""ramralph layered-injection 테스트 공유 fixture (T-001 / NFR-003).

신규 레이어(OntologySource/ProfileSource/주입 경로) 테스트가 공유하는 기본 fixture 를
여기에 모은다. ZEP/LLM mock 등 무거운 fixture 는 tests/fixtures/ 하위 모듈에서
정의하고 pytest_plugins 로 등록한다(T-002/T-003에서 추가).
"""

import pytest

from app.config import Config


@pytest.fixture
def app_config():
    """Flask Config 객체를 노출하는 기본 fixture."""
    return Config
