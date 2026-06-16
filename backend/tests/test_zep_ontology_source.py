"""ZepGraphOntologySource 테스트 (T-006 / TS-001, FR-001).

완성된 graph_id 를 재사용한다 — 온톨로지 LLM 생성/그래프 빌드를 호출하지 않고
기존 그래프의 엔티티 타입에서 온톨로지 dict 를 구성한다.
"""

import pytest

from app.services.ontology_source import OntologySource, ZepGraphOntologySource
from tests.fixtures.zep_mock import make_fake_zep_reader


def test_is_ontology_source():
    src = ZepGraphOntologySource("g1", reader=make_fake_zep_reader("valid", count=2))
    assert isinstance(src, OntologySource)


def test_load_reuses_graph_entities_no_llm():
    reader = make_fake_zep_reader("valid", count=3)
    src = ZepGraphOntologySource("g1", reader=reader)
    onto = src.load()
    # 엔티티 타입에서 entity_types 구성, edge_types 비움, 출처 표시
    assert {e["name"] for e in onto["entity_types"]} == {"Person"}
    assert onto["edge_types"] == []
    assert onto["source"] == "zep_graph"
    assert onto["graph_id"] == "g1"
    # graph_id 재사용 경로는 ZEP 조회만 — reader 가 1회 호출됨(LLM/build 없음)
    assert reader.calls == 1


def test_load_zero_entity_graph():
    reader = make_fake_zep_reader("zero_entity")
    src = ZepGraphOntologySource("g1", reader=reader)
    onto = src.load()
    assert onto["entity_types"] == []
