"""pytest 인프라 sanity 테스트 (T-001 / TS-000).

conftest.py 의 공유 fixture 와 pytest 설정([tool.pytest.ini_options])이
정상 동작하는지 확인한다.
"""


def test_app_config_fixture(app_config):
    """conftest 의 app_config fixture 가 주입되고 Config 를 노출한다."""
    assert app_config is not None
    assert hasattr(app_config, "LLM_MODEL_NAME")


def test_app_package_importable():
    """pytest 설정(pythonpath)으로 app 패키지가 import 가능하다."""
    import app  # noqa: F401
    from app.config import Config

    assert Config is not None
