"""LLM 설정 내부 서버 재지정 + 키 보안 검증 (FR-001/FR-007/NFR-001 / TS-001, TS-006).

내부 OpenAI 호환 서버로의 재지정이 Config 로딩 경로에 정확히 반영되는지,
그리고 실제 API 키가 git 추적/예시 파일로 새지 않는지 검증한다.
"""

import os
import subprocess
import sys

import pytest

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_ENV_PATH = os.path.join(_PROJECT_ROOT, ".env")
_ENV_EXAMPLE = os.path.join(_PROJECT_ROOT, ".env.example")


def test_config_reads_env_without_dotenv_file():
    """TS-001(CI-runnable): .env 파일 없이도 Config 가 env 의 base_url/model 을 읽는다.

    config.py 가 모듈 로드 시 호출하는 dotenv.load_dotenv 를 no-op 으로 패치한 별도 프로세스에서
    env 만 주입해 검증한다(.env 존재/부재와 무관 — CI 에서도 실행됨). 핵심 repoint 계약(env→Config)이
    skipif 로 CI 에서 빠지지 않도록 보장한다.
    """
    code = (
        "import dotenv; dotenv.load_dotenv = lambda *a, **k: None;"
        "from app.config import Config;"
        "print(Config.LLM_BASE_URL); print(Config.LLM_MODEL_NAME)"
    )
    env = dict(os.environ)
    env["LLM_BASE_URL"] = "http://internal.test:39281/v1"
    env["LLM_MODEL_NAME"] = "gpt-5.5"
    env["LLM_API_KEY"] = "test-key"
    r = subprocess.run(
        [sys.executable, "-c", code],
        cwd=_BACKEND_DIR, env=env, capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stderr
    base, model = r.stdout.strip().splitlines()[-2:]
    assert base == "http://internal.test:39281/v1", f"Config가 env base_url 미반영: {base}"
    assert model == "gpt-5.5"
    assert "openrouter" not in base.lower()


@pytest.mark.skipif(not os.path.exists(_ENV_PATH), reason="로컬 .env 없음 (CI)")
def test_config_loads_internal_server_from_env():
    """TS-001: Config 가 실제 .env 의 내부 서버 base_url(/v1)/model(gpt-5.5)을 로딩한다.

    config.py 는 모듈 로드 시 .env 를 override 로딩하므로, 별도 프로세스에서 fresh import 해
    Config 통합 결과를 검증한다 (전역 모듈 reload 오염 회피).
    """
    code = (
        "from app.config import Config;"
        "print(Config.LLM_BASE_URL);print(Config.LLM_MODEL_NAME)"
    )
    r = subprocess.run(
        [sys.executable, "-c", code],
        cwd=_BACKEND_DIR, capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stderr
    base, model = r.stdout.strip().splitlines()[-2:]
    assert base.endswith("/v1"), f"base_url 에 /v1 누락: {base}"
    assert "openrouter" not in base.lower()
    assert model == "gpt-5.5"


@pytest.mark.skipif(not os.path.exists(_ENV_PATH), reason="로컬 .env 없음 (CI)")
def test_live_env_points_to_internal_server():
    """TS-001(라이브): 실제 .env 가 내부 서버(/v1)를 가리키고 openrouter 가 없다."""
    text = open(_ENV_PATH).read()
    active = [
        l for l in text.splitlines()
        if l.strip() and not l.strip().startswith("#")
    ]
    base = next((l.split("=", 1)[1].strip() for l in active if l.startswith("LLM_BASE_URL=")), "")
    assert base.endswith("/v1"), f"base_url 에 /v1 누락: {base}"
    assert "openrouter" not in text.lower(), "라이브 .env 에 openrouter 잔존"


@pytest.mark.skipif(not os.path.exists(_ENV_PATH), reason="로컬 .env 없음 (CI)")
def test_env_is_gitignored():
    """TS-006/NFR-001: .env 와 .env.bak 이 git-ignored 다."""
    for name in (".env", ".env.bak"):
        r = subprocess.run(
            ["git", "check-ignore", name],
            cwd=_PROJECT_ROOT, capture_output=True, text=True,
        )
        assert r.returncode == 0, f"{name} 이 git-ignored 아님"


def test_env_example_has_no_real_key():
    """TS-006: .env.example 은 placeholder 만 — 실제 키 값이 없다."""
    text = open(_ENV_EXAMPLE).read()
    for line in text.splitlines():
        if line.strip().startswith("#") or "=" not in line:
            continue
        if line.startswith(("LLM_API_KEY=", "LLM_BOOST_API_KEY=", "ZEP_API_KEY=")):
            val = line.split("=", 1)[1].strip()
            assert val in ("your_api_key_here", "your_zep_api_key_here"), (
                f".env.example 에 실제 키로 보이는 값: {line.split('=')[0]}"
            )
