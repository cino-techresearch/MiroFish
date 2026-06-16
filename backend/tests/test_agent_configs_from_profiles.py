"""agent_config 를 주입 프로필에서 파생 (T-042 / FR-005, 재설계 핵심).

agent_id = profile.user_id (임의 정수), entity_type 파생, LLM 미호출.
"""

from app.services.simulation_config_generator import SimulationConfigGenerator, AgentActivityConfig
from app.services.oasis_profile_generator import OasisAgentProfile


def _gen():
    return SimulationConfigGenerator.__new__(SimulationConfigGenerator)


def test_agent_configs_derived_from_profiles():
    profiles = [
        OasisAgentProfile(user_id=10, user_name="u10", name="N10", bio="b", persona="p",
                          source_entity_type="Student"),
        OasisAgentProfile(user_id=99, user_name="u99", name="N99", bio="b", persona="p"),
    ]
    configs = _gen()._agent_configs_from_profiles(profiles)
    assert [c.agent_id for c in configs] == [10, 99]          # user_id 그대로
    assert all(isinstance(c, AgentActivityConfig) for c in configs)
    assert configs[0].entity_type == "student"                # source_entity_type 파생
    assert configs[1].entity_type == "person"                 # 기본값
    assert configs[0].entity_name == "N10"


def test_count_matches_profiles_not_entities():
    profiles = [OasisAgentProfile(user_id=i, user_name=f"u{i}", name=f"n{i}", bio="b", persona="p")
                for i in range(7)]
    configs = _gen()._agent_configs_from_profiles(profiles)
    assert len(configs) == 7  # 엔티티 수 무관, 프로필 수와 일치
