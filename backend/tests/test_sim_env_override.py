"""시뮬 스크립트 stale-env 우선순위 차단 검증 (FR-001/FR-002 / TS-014).

세 시뮬 스크립트(run_parallel/run_reddit/run_twitter)는 load_dotenv 를
override 없이 호출하면 이미 프로세스에 존재하는 stale LLM_BASE_URL(openrouter)이
.env 값보다 우선해 재지정이 사일런트 무효화된다. override=True 보강을 검증한다.
"""

import os

import pytest
from dotenv import load_dotenv

_SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "scripts")
_SCRIPTS = [
    "run_parallel_simulation.py",
    "run_reddit_simulation.py",
    "run_twitter_simulation.py",
]


@pytest.mark.parametrize("script", _SCRIPTS)
def test_scripts_load_dotenv_with_override(script):
    """TS-014(a): 세 스크립트의 모든 load_dotenv 호출에 override=True 가 있다."""
    path = os.path.join(_SCRIPTS_DIR, script)
    src = open(path).read()
    calls = [l.strip() for l in src.splitlines() if "load_dotenv(" in l and "import" not in l]
    assert calls, f"{script}: load_dotenv 호출을 찾지 못함"
    for call in calls:
        assert "override=True" in call, f"{script}: override=True 누락 — {call}"


def test_override_defeats_stale_process_env(tmp_path, monkeypatch):
    """TS-014(b): override=True 가 stale 프로세스 env 를 .env 값으로 덮어쓴다 (python-dotenv 계약).

    이 동작이 깨지면 스크립트 보강이 무의미하므로 의존하는 계약을 고정한다.
    """
    env_file = tmp_path / ".env"
    env_file.write_text("LLM_BASE_URL=http://127.0.0.1:39281/v1\n")

    monkeypatch.setenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")  # stale

    # override 없이는 stale 가 유지된다 (결함 재현 — RED 계약)
    load_dotenv(str(env_file), override=False)
    assert os.environ["LLM_BASE_URL"] == "https://openrouter.ai/api/v1"

    # override=True 면 내부 서버 값으로 덮어쓴다 (보강 — GREEN 계약)
    load_dotenv(str(env_file), override=True)
    assert os.environ["LLM_BASE_URL"] == "http://127.0.0.1:39281/v1"
