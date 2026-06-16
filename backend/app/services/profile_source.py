"""페르소나 레이어 주입을 위한 ProfileSource 추상화 (FR-002).

파이프라인 3단계의 프로필 생성을 "소스"로 추상화해 생성 경로(ZEP 엔티티 기반 LLM)와
주입 경로(중립 JSON)를 분리한다.

- ProfileSource: load_profiles() -> List[OasisAgentProfile] 계약(ABC)
- GeneratedProfileSource: 현행 OasisProfileGenerator 를 위임 래핑하는 어댑터
- FileProfileSource: 중립 JSON 주입(generator 미생성) — T-008에서 구현
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from app.services.oasis_profile_generator import OasisAgentProfile, OasisProfileGenerator


class ProfileSource(ABC):
    """OasisAgentProfile 리스트를 제공하는 소스 추상."""

    @abstractmethod
    def load_profiles(self) -> List[OasisAgentProfile]:
        """페르소나 프로필 리스트를 반환한다."""
        raise NotImplementedError


class GeneratedProfileSource(ProfileSource):
    """현행 ZEP 엔티티 기반 LLM 생성 경로를 래핑하는 어댑터."""

    def __init__(
        self,
        entities: list,
        use_llm: bool = True,
        progress_callback: Optional[callable] = None,
        graph_id: Optional[str] = None,
        parallel_count: int = 5,
        realtime_output_path: Optional[str] = None,
        output_platform: str = "reddit",
        generator: Optional[OasisProfileGenerator] = None,
    ):
        self.entities = entities
        self.use_llm = use_llm
        self.progress_callback = progress_callback
        self.graph_id = graph_id
        self.parallel_count = parallel_count
        self.realtime_output_path = realtime_output_path
        self.output_platform = output_platform
        # generator 미주입 시 graph_id 를 넘겨 현행과 동일하게 생성
        self._generator = generator or OasisProfileGenerator(graph_id=graph_id)

    def load_profiles(self) -> List[OasisAgentProfile]:
        return self._generator.generate_profiles_from_entities(
            entities=self.entities,
            use_llm=self.use_llm,
            progress_callback=self.progress_callback,
            graph_id=self.graph_id,
            parallel_count=self.parallel_count,
            realtime_output_path=self.realtime_output_path,
            output_platform=self.output_platform,
        )
