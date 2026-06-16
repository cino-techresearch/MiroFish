"""OntologySource 추상화 + LLMOntologySource 어댑터 테스트 (T-005 / TS-010).

LLMOntologySource 는 현행 OntologyGenerator.generate 를 위임 호출하고
그 반환 dict 를 그대로 돌려줘야 한다(어댑터 동일 출력).
"""

from unittest.mock import MagicMock

import pytest

from app.services.ontology_source import OntologySource, LLMOntologySource


def test_ontology_source_is_abstract():
    """OntologySource 는 추상 — 직접 인스턴스화 불가."""
    with pytest.raises(TypeError):
        OntologySource()  # type: ignore[abstract]


def test_llm_source_delegates_to_generator():
    """LLMOntologySource.load() 가 generator.generate 에 위임하고 결과를 그대로 반환."""
    expected = {"entity_types": [{"name": "Person"}], "edge_types": []}
    fake_gen = MagicMock()
    fake_gen.generate.return_value = expected

    source = LLMOntologySource(
        document_texts=["doc1"],
        simulation_requirement="req",
        additional_context="ctx",
        generator=fake_gen,
    )
    result = source.load()

    assert result == expected
    fake_gen.generate.assert_called_once_with(["doc1"], "req", "ctx")


def test_llm_source_is_ontology_source():
    fake_gen = MagicMock()
    fake_gen.generate.return_value = {"entity_types": [], "edge_types": []}
    source = LLMOntologySource(["d"], "r", generator=fake_gen)
    assert isinstance(source, OntologySource)
