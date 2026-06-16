"""ProfileSource 추상화 + GeneratedProfileSource 어댑터 테스트 (T-007 / TS-010).

GeneratedProfileSource 는 현행 OasisProfileGenerator.generate_profiles_from_entities 를
위임 호출하고 그 결과(OasisAgentProfile 리스트)를 그대로 반환해야 한다.
"""

from unittest.mock import MagicMock

import pytest

from app.services.profile_source import ProfileSource, GeneratedProfileSource


def test_profile_source_is_abstract():
    with pytest.raises(TypeError):
        ProfileSource()  # type: ignore[abstract]


def test_generated_source_delegates_to_generator():
    sentinel = [object(), object()]
    fake_gen = MagicMock()
    fake_gen.generate_profiles_from_entities.return_value = sentinel

    entities = ["e1", "e2"]
    source = GeneratedProfileSource(
        entities=entities,
        use_llm=True,
        graph_id="g1",
        parallel_count=5,
        output_platform="reddit",
        generator=fake_gen,
    )
    result = source.load_profiles()

    assert result is sentinel
    kwargs = fake_gen.generate_profiles_from_entities.call_args.kwargs
    assert kwargs["entities"] == entities
    assert kwargs["use_llm"] is True
    assert kwargs["graph_id"] == "g1"
    assert kwargs["output_platform"] == "reddit"


def test_generated_source_is_profile_source():
    fake_gen = MagicMock()
    fake_gen.generate_profiles_from_entities.return_value = []
    source = GeneratedProfileSource(entities=[], generator=fake_gen)
    assert isinstance(source, ProfileSource)
