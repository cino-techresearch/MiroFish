"""온톨로지 레이어 주입을 위한 Source 추상화 (FR-001).

파이프라인 1+2단계(온톨로지 정의 생성 + ZEP 그래프 구축)를 "소스"로 추상화해
생성 경로(LLM)와 주입 경로(기존 graph_id 재사용)를 분리한다.

- OntologySource: load() -> ontology dict 계약(ABC)
- LLMOntologySource: 현행 OntologyGenerator.generate 를 위임 래핑하는 어댑터
- ZepGraphOntologySource: 완성된 graph_id 재사용(생성/빌드 미호출) — T-006에서 구현
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from app.services.ontology_generator import OntologyGenerator


class OntologySource(ABC):
    """온톨로지 dict 를 제공하는 소스 추상.

    load() 는 `{"entity_types": [...], "edge_types": [...], ...}` 형태의
    온톨로지 정의 dict 를 반환한다.
    """

    @abstractmethod
    def load(self) -> Dict[str, Any]:
        """온톨로지 정의 dict 를 반환한다."""
        raise NotImplementedError


class LLMOntologySource(OntologySource):
    """현행 LLM 생성 경로를 래핑하는 어댑터.

    출력은 OntologyGenerator.generate 와 동일하다(어댑터 동일 출력 보장).
    """

    def __init__(
        self,
        document_texts: List[str],
        simulation_requirement: str,
        additional_context: Optional[str] = None,
        generator: Optional[OntologyGenerator] = None,
    ):
        self.document_texts = document_texts
        self.simulation_requirement = simulation_requirement
        self.additional_context = additional_context
        self._generator = generator or OntologyGenerator()

    def load(self) -> Dict[str, Any]:
        return self._generator.generate(
            self.document_texts,
            self.simulation_requirement,
            self.additional_context,
        )
