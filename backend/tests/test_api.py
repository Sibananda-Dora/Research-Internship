import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'code', 'phase-2-training'))
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from main import app

client = TestClient(app)


def test_root():
    resp = client.get("/")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "Cognitive Digital Twin" in data.get("service", str(data))


def test_districts():
    resp = client.get("/api/districts")
    assert resp.status_code == 200
    data = resp.json()
    assert "districts" in data
    assert len(data["districts"]) == 30
    assert "Ganjam" in data["districts"]


def test_history():
    resp = client.get("/api/history/Ganjam/Kharif")
    assert resp.status_code == 200
    data = resp.json()
    assert "records" in data
    assert len(data["records"]) > 0
    assert "year" in data["records"][0]
    assert "yield_q_acre" in data["records"][0]


@pytest.mark.parametrize("district,season,year", [
    ("Ganjam", "Kharif", 2024),
    ("Angul", "Kharif", 2023),
    ("Cuttack", "Rabi", 2024),
])
def test_telemetry(district, season, year):
    resp = client.get(f"/api/telemetry/{district}/{year}/{season}")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "telemetry" in data
    assert "PRECTOTCORR" in data["telemetry"]
    assert len(data["telemetry"]["PRECTOTCORR"]) == 12


def test_predict():
    resp = client.get("/api/predict/Ganjam/2024/Kharif?query_type=full_diagnosis")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "predicted_yield" in data
    assert "failure_probability" in data
    assert "trace" in data


def test_predict_coordinate():
    resp = client.post("/api/predict/coordinate", json={
        "latitude": 20.5,
        "longitude": 84.4,
        "year": 2024,
        "season": "Kharif"
    })
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "predicted_yield" in data
    assert data["district"] == "Kandhamal"


def test_simulate():
    modifiers = [1.0] * 12
    resp = client.post("/api/simulate", json={
        "district": "Ganjam",
        "season": "Kharif",
        "year": 2024,
        "precip_modifiers": modifiers,
        "temp_modifiers": [0.0] * 12,
        "wetness_modifiers": [0.0] * 12,
        "humidity_modifiers": [0.0] * 12
    })
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "predicted_yield" in data


def test_simulate_invalid_modifier_length():
    resp = client.post("/api/simulate", json={
        "district": "Ganjam",
        "season": "Kharif",
        "year": 2024,
        "precip_modifiers": [1.0] * 5,
        "temp_modifiers": [0.0] * 12,
        "wetness_modifiers": [0.0] * 12,
        "humidity_modifiers": [0.0] * 12
    })
    assert resp.status_code == 422


def test_pipeline_version():
    resp = client.get("/api/pipeline/version")
    assert resp.status_code == 200
    data = resp.json()
    keys = data.keys()
    assert any("version" in k.lower() or "model" in k.lower() for k in keys)


def test_unknown_district_returns_error():
    resp = client.get("/api/predict/Faketrict/2024/Kharif?query_type=full_diagnosis")
    assert resp.status_code >= 400, f"Expected error status, got {resp.status_code}"


def test_missing_fields_returns_422():
    resp = client.post("/api/predict/coordinate", json={"latitude": 20.5})
    assert resp.status_code == 422
