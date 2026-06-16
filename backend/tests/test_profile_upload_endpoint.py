"""프로필 업로드 엔드포인트 + 업로드 보안 테스트 (T-014 / TS-009a~d, FR-004, NFR-004).

POST /api/simulation/profiles/upload:
- 중립 JSON 프로필을 injected_profiles.json 으로 저장
- 보안: 크기 초과(413) / 비-JSON 확장자(400) / 스키마 위반(400) / 경로 traversal(400)
"""

import io
import json
import os

import pytest

from app import create_app
from app.services.simulation_manager import SimulationManager


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(SimulationManager, "SIMULATION_DATA_DIR", str(tmp_path / "sims"))
    app = create_app()
    app.config.update(TESTING=True)
    return app.test_client()


@pytest.fixture
def sim_id():
    # 업로드는 존재하는 simulation 에만 허용되므로 먼저 생성한다
    state = SimulationManager().create_simulation(project_id="proj_x", graph_id="g1")
    return state.simulation_id


def _valid(uid):
    return {"user_id": uid, "user_name": f"u{uid}", "name": f"n{uid}", "bio": "b", "persona": "p"}


def test_valid_upload_writes_injected_profiles(client, sim_id):
    resp = client.post("/api/simulation/profiles/upload", json={
        "simulation_id": sim_id, "profiles": [_valid(0), _valid(1)],
    })
    assert resp.status_code == 200, resp.get_data(as_text=True)
    body = resp.get_json()
    assert body["count"] == 2
    path = os.path.join(SimulationManager.SIMULATION_DATA_DIR, sim_id, "injected_profiles.json")
    assert os.path.exists(path)
    assert len(json.load(open(path, encoding="utf-8"))) == 2


def test_schema_violation_rejected(client, sim_id):
    bad = _valid(0); del bad["persona"]
    resp = client.post("/api/simulation/profiles/upload", json={
        "simulation_id": sim_id, "profiles": [bad],
    })
    assert resp.status_code == 400


def test_upload_to_missing_simulation_404(client):
    resp = client.post("/api/simulation/profiles/upload", json={
        "simulation_id": "sim_does_not_exist", "profiles": [_valid(0)],
    })
    assert resp.status_code == 404


def test_path_traversal_rejected(client):
    resp = client.post("/api/simulation/profiles/upload", json={
        "simulation_id": "../../etc", "profiles": [_valid(0)],
    })
    assert resp.status_code == 400


def test_bad_extension_rejected(client, sim_id):
    data = {
        "simulation_id": sim_id,
        "file": (io.BytesIO(b"not json"), "profiles.txt"),
    }
    resp = client.post("/api/simulation/profiles/upload", data=data,
                       content_type="multipart/form-data")
    assert resp.status_code == 400


def test_oversize_rejected(client):
    client.application.config["MAX_CONTENT_LENGTH"] = 50
    big = [_valid(i) for i in range(50)]
    resp = client.post("/api/simulation/profiles/upload", json={
        "simulation_id": "sim_abc", "profiles": big,
    })
    assert resp.status_code == 413
