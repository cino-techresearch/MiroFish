"""prepare 의 profile_source provenance 설정 + GeneratedProfileSource 배선 (T-033 / TS-017, FR-009, FR-002).

- 프로필 주입 경로 → project.profile_source == 'file'
- 생성 경로 → project.profile_source == 'generated'
"""

import json
import os

import pytest

import app.services.simulation_manager as sm
from app.services.simulation_manager import SimulationManager, SimulationStatus
from app.models.project import ProjectManager
from tests.fixtures.zep_mock import make_fake_zep_reader


class _NoGen:
    def __init__(self, *a, **k):
        pass

    def generate_profiles_from_entities(self, entities, **k):
        from app.services.oasis_profile_generator import OasisAgentProfile
        return [OasisAgentProfile(user_id=i, user_name=f"u{i}", name=f"n{i}", bio="b", persona="p")
                for i in range(len(entities))]

    def save_profiles(self, profiles, file_path, platform="reddit"):
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump([{"user_id": p.user_id} for p in profiles], f)


def _config_gen(n):
    class _P:
        generation_reasoning = "r"
        agent_configs = [{"agent_id": i} for i in range(n)]

        class event_config:
            initial_posts = []

        def to_json(self):
            return json.dumps({})
    return lambda *a, **k: type("CG", (), {"generate_config": lambda self, **k: _P()})()


@pytest.fixture
def manager(tmp_path, monkeypatch):
    monkeypatch.setattr(SimulationManager, "SIMULATION_DATA_DIR", str(tmp_path / "sims"))
    monkeypatch.setattr(ProjectManager, "PROJECTS_DIR", str(tmp_path / "projects"))
    monkeypatch.setattr(sm, "ZepEntityReader", lambda *a, **k: make_fake_zep_reader("valid", count=3))
    monkeypatch.setattr(sm, "OasisProfileGenerator", _NoGen)
    monkeypatch.setattr(sm, "SimulationConfigGenerator", _config_gen(3))
    return SimulationManager()


def _setup(manager):
    proj = ProjectManager.create_project("P")
    state = manager.create_simulation(project_id=proj.project_id, graph_id="g1",
                                      enable_twitter=False, enable_reddit=True)
    return proj, state


def test_injected_sets_profile_source_file(manager):
    proj, state = _setup(manager)
    sd = manager._get_simulation_dir(state.simulation_id)
    os.makedirs(sd, exist_ok=True)
    profs = [{"user_id": i, "user_name": f"u{i}", "name": f"n{i}", "bio": "b", "persona": "p"} for i in range(3)]
    with open(os.path.join(sd, "injected_profiles.json"), "w", encoding="utf-8") as f:
        json.dump(profs, f)
    result = manager.prepare_simulation(simulation_id=state.simulation_id, simulation_requirement="r", document_text="d")
    assert result.status == SimulationStatus.READY
    assert ProjectManager.get_project(proj.project_id).profile_source == "file"


def test_generated_sets_profile_source_generated(manager):
    proj, state = _setup(manager)
    result = manager.prepare_simulation(simulation_id=state.simulation_id, simulation_requirement="r", document_text="d")
    assert result.status == SimulationStatus.READY
    assert ProjectManager.get_project(proj.project_id).profile_source == "generated"
