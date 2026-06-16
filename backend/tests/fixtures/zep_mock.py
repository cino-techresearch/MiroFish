"""ZEP 테스트 더블 (NFR-003 / TS-022 지원).

graph_id 동기 검증(FR-003b)과 주입 경로 통합 테스트가 공유하는 FakeZepEntityReader.
실제 Zep 클라우드 호출 없이 6개 상태를 재현한다:

- valid: 엔티티 N개 보유한 FilteredEntities 반환
- zero_entity: 엔티티 0개
- not_found: 그래프 미존재 → ZepNotFoundError
- timeout: 네트워크 타임아웃 → ZepTimeoutError
- server_error: 5xx → ZepServerError
- unauthorized: 범위 밖/권한 없음 → ZepUnauthorizedError

importable 팩토리로 제공해 conftest 수정 없이 어느 테스트에서나 import 해 쓴다.
"""

from typing import List

from app.services.zep_entity_reader import EntityNode, FilteredEntities


class ZepMockError(Exception):
    """ZEP mock 에러 기반 클래스."""


class ZepNotFoundError(ZepMockError):
    pass


class ZepTimeoutError(ZepMockError):
    pass


class ZepServerError(ZepMockError):
    pass


class ZepUnauthorizedError(ZepMockError):
    pass


_STATE_ERRORS = {
    "not_found": ZepNotFoundError,
    "timeout": ZepTimeoutError,
    "server_error": ZepServerError,
    "unauthorized": ZepUnauthorizedError,
}


def make_entities(count: int) -> List[EntityNode]:
    """count 개의 EntityNode 를 생성한다(타입=Person)."""
    return [
        EntityNode(
            uuid=f"uuid-{i}",
            name=f"Entity {i}",
            labels=["Entity", "Person"],
            summary=f"summary {i}",
            attributes={},
        )
        for i in range(count)
    ]


class FakeZepEntityReader:
    """ZepEntityReader 의 filter_defined_entities 를 흉내내는 테스트 더블."""

    def __init__(self, state: str = "valid", count: int = 3):
        self.state = state
        self.count = count
        self.calls = 0

    def filter_defined_entities(self, graph_id, defined_entity_types=None, enrich_with_edges=True):
        self.calls += 1
        if self.state in _STATE_ERRORS:
            raise _STATE_ERRORS[self.state](f"zep mock state={self.state} graph_id={graph_id}")
        n = 0 if self.state == "zero_entity" else self.count
        entities = make_entities(n)
        return FilteredEntities(
            entities=entities,
            entity_types={"Person"} if n else set(),
            total_count=n,
            filtered_count=n,
        )


def make_fake_zep_reader(state: str = "valid", count: int = 3) -> FakeZepEntityReader:
    """상태별 FakeZepEntityReader 를 생성하는 팩토리."""
    valid_states = {"valid", "zero_entity", *_STATE_ERRORS}
    if state not in valid_states:
        raise ValueError(f"알 수 없는 zep mock state: {state} (가능: {sorted(valid_states)})")
    return FakeZepEntityReader(state=state, count=count)
