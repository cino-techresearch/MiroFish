"""ZEP mock 테스트 더블 자체 검증 (T-002 / TS-022 지원).

graph_id 동기 검증·주입 경로 테스트가 공유할 FakeZepEntityReader 가
6개 상태(valid/not_found/zero_entity/timeout/server_error/unauthorized)를
의도대로 재현하는지 확인한다.
"""

import pytest

from app.services.zep_entity_reader import EntityNode, FilteredEntities
from tests.fixtures.zep_mock import (
    make_fake_zep_reader,
    make_entities,
    ZepNotFoundError,
    ZepTimeoutError,
    ZepServerError,
    ZepUnauthorizedError,
)


def test_make_entities_builds_entity_nodes():
    ents = make_entities(3)
    assert len(ents) == 3
    assert all(isinstance(e, EntityNode) for e in ents)
    assert ents[0].get_entity_type() == "Person"


def test_valid_state_returns_entities():
    reader = make_fake_zep_reader("valid", count=4)
    result = reader.filter_defined_entities("g1")
    assert isinstance(result, FilteredEntities)
    assert result.filtered_count == 4
    assert len(result.entities) == 4


def test_zero_entity_state():
    reader = make_fake_zep_reader("zero_entity")
    result = reader.filter_defined_entities("g1")
    assert result.filtered_count == 0
    assert result.entities == []


@pytest.mark.parametrize(
    "state,exc",
    [
        ("not_found", ZepNotFoundError),
        ("timeout", ZepTimeoutError),
        ("server_error", ZepServerError),
        ("unauthorized", ZepUnauthorizedError),
    ],
)
def test_error_states_raise(state, exc):
    reader = make_fake_zep_reader(state)
    with pytest.raises(exc):
        reader.filter_defined_entities("g1")
