"""LLM 클라이언트 생성 시 내부 서버 base_url 전달 검증 (FR-004/NFR-002b / TS-004, TS-010).

LLMClient 와 LLMClient 를 우회해 직접 OpenAI 를 만드는 2곳
(oasis_profile_generator, simulation_config_generator)이 모두 내부 서버 base_url 로
OpenAI 클라이언트를 생성하는지, openai.OpenAI 를 mock 해 인자를 검증한다.
"""


class _RecordingOpenAI:
    """openai.OpenAI 대체 — 생성 인자를 기록한다."""

    last_kwargs = None

    def __init__(self, *args, **kwargs):
        type(self).last_kwargs = kwargs


def test_llmclient_passes_internal_base_url(monkeypatch):
    """TS-004: LLMClient 가 주어진 base_url 로 OpenAI 를 생성한다."""
    import app.utils.llm_client as mod

    monkeypatch.setattr(mod, "OpenAI", _RecordingOpenAI)
    _RecordingOpenAI.last_kwargs = None

    mod.LLMClient(api_key="k", base_url="http://127.0.0.1:39281/v1", model="gpt-5.5")

    assert _RecordingOpenAI.last_kwargs["base_url"] == "http://127.0.0.1:39281/v1"


def test_profile_generator_uses_config_base_url(monkeypatch):
    """TS-010: OasisProfileGenerator 가 Config.LLM_BASE_URL 로 OpenAI 를 생성한다."""
    import app.services.oasis_profile_generator as mod

    monkeypatch.setattr(mod.Config, "LLM_BASE_URL", "http://internal.test/v1", raising=False)
    monkeypatch.setattr(mod, "OpenAI", _RecordingOpenAI)
    _RecordingOpenAI.last_kwargs = None

    mod.OasisProfileGenerator(api_key="k")

    assert _RecordingOpenAI.last_kwargs["base_url"] == "http://internal.test/v1"


def test_sim_config_generator_uses_config_base_url(monkeypatch):
    """TS-010: SimulationConfigGenerator 가 Config.LLM_BASE_URL 로 OpenAI 를 생성한다."""
    import app.services.simulation_config_generator as mod

    monkeypatch.setattr(mod.Config, "LLM_BASE_URL", "http://internal.test/v1", raising=False)
    monkeypatch.setattr(mod, "OpenAI", _RecordingOpenAI)
    _RecordingOpenAI.last_kwargs = None

    mod.SimulationConfigGenerator(api_key="k")

    assert _RecordingOpenAI.last_kwargs["base_url"] == "http://internal.test/v1"
