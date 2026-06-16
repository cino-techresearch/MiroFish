"""graph_id 동기 검증 테스트 (T-011 / TS-005, TS-012, TS-022, FR-003b).

주입 시점에 ZEP 존재+엔티티≥1 을 동기로 확정한다. 실패(없음/엔티티0/타임아웃/5xx/
권한없음)는 GraphInjectionError 로 거부한다. 검증기는 read-only — 어떤 파일/상태도
생성하지 않는다.
"""

import pytest

from app.services.graph_injection import validate_graph_id, GraphInjectionError
from tests.fixtures.zep_mock import make_fake_zep_reader


def test_valid_graph_returns_entity_count():
    reader = make_fake_zep_reader("valid", count=4)
    count = validate_graph_id("g1", reader=reader)
    assert count == 4


@pytest.mark.parametrize("state", ["not_found", "timeout", "server_error", "unauthorized"])
def test_error_states_rejected(state):
    reader = make_fake_zep_reader(state)
    with pytest.raises(GraphInjectionError):
        validate_graph_id("g1", reader=reader)


def test_zero_entity_rejected():
    reader = make_fake_zep_reader("zero_entity")
    with pytest.raises(GraphInjectionError) as ei:
        validate_graph_id("g1", reader=reader)
    assert "엔티티" in str(ei.value) or "entit" in str(ei.value).lower()


def test_empty_graph_id_rejected():
    with pytest.raises(GraphInjectionError):
        validate_graph_id("", reader=make_fake_zep_reader("valid"))
