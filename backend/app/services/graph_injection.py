"""graph_id 주입 동기 검증 (FR-003b, NFR-004).

주입 시점에 대상 ZEP 그래프의 존재와 엔티티 보유(≥1)를 동기로 확정한다.
실패(없음/엔티티0/타임아웃/5xx/권한없음/범위밖)는 즉시 GraphInjectionError 로 거부한다.

이 함수는 read-only 다 — project/SimulationState/Task 등 어떤 부수효과도 만들지 않는다.
부수효과 미생성(거부 시)은 호출하는 엔드포인트(T-012)가 이 검증을 커밋 이전에 수행함으로써 보장된다.
"""

from typing import Any, Optional


class GraphInjectionError(ValueError):
    """주입하려는 graph_id 가 검증을 통과하지 못했을 때 발생."""


def validate_graph_id(graph_id: str, reader: Optional[Any] = None) -> int:
    """graph_id 를 동기 검증하고 엔티티 수를 반환한다.

    Args:
        graph_id: 재사용할 기존 ZEP 그래프 ID.
        reader: filter_defined_entities(graph_id) 를 제공하는 객체. 미주입 시 ZepEntityReader.

    Returns:
        그래프의 엔티티 수(≥1).

    Raises:
        GraphInjectionError: graph_id 가 비었거나, ZEP 조회 실패, 또는 엔티티 0개.
    """
    if not graph_id or not str(graph_id).strip():
        raise GraphInjectionError("graph_id 가 비어 있습니다")

    if reader is None:
        from app.services.zep_entity_reader import ZepEntityReader

        reader = ZepEntityReader()

    try:
        filtered = reader.filter_defined_entities(graph_id)
    except GraphInjectionError:
        raise
    except Exception as exc:  # ZEP not_found/timeout/5xx/unauthorized 등 모두 거부로 환산
        raise GraphInjectionError(
            f"graph_id '{graph_id}' 검증 실패 (ZEP 조회 오류): {exc}"
        ) from exc

    count = getattr(filtered, "filtered_count", None)
    if count is None:
        count = len(getattr(filtered, "entities", []))
    if count <= 0:
        raise GraphInjectionError(
            f"graph_id '{graph_id}' 에 사용 가능한 엔티티가 없습니다 (엔티티 0개)"
        )
    return count
