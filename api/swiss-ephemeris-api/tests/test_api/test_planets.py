"""
Integration tests for the /api/v1/planets endpoint.
Extracted from test_all_endpoints.py for separation of concerns.
"""

import os
import pytest
from fastapi.testclient import TestClient


def _ephe_has_files() -> bool:
    ephe_path = os.environ.get("EPHE_PATH", "./ephe")
    candidates = ["sepl_18.se1", "semo_18.se1", "seas_18.se1"]
    return any(os.path.isfile(os.path.join(ephe_path, f)) for f in candidates)


EPHE_AVAILABLE = _ephe_has_files()


@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)


class TestRootEndpoint:
    def test_root_returns_agpl_notice(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["license"] == "AGPL-3.0-or-later"
        assert "AGPL" in data["notice"]
        assert "source" in data["notice"].lower() or "github" in data["notice"].lower()

    def test_root_has_required_fields(self, client):
        resp = client.get("/")
        data = resp.json()
        assert "name" in data
        assert "version" in data
        assert "license" in data
        assert "docs" in data


class TestHealthEndpoint:
    def test_health_returns_status(self, client):
        resp = client.get("/health")
        assert resp.status_code in [200, 503]
        data = resp.json()
        assert "status" in data
        assert "ephe_path" in data


@pytest.mark.skipif(not EPHE_AVAILABLE, reason="Ephemeris files not found")
class TestPlanetsEndpoint:
    def test_valid_request_returns_positions(self, client):
        payload = {
            "datetime": "1990-01-15T12:00:00",
            "timezone": "UTC",
            "latitude": 21.0285,
            "longitude": 105.8542,
        }
        resp = client.post("/api/v1/planets", json=payload)
        if resp.status_code == 200:
            data = resp.json()
            assert "positions" in data
            assert "ascendant" in data
            assert "medium_coeli" in data

    def test_response_includes_license(self, client):
        payload = {
            "datetime": "1990-01-15T12:00:00",
            "timezone": "UTC",
            "latitude": 21.0285,
            "longitude": 105.8542,
        }
        resp = client.post("/api/v1/planets", json=payload)
        if resp.status_code == 200:
            data = resp.json()
            assert "license" in data
            assert data["license"] == "AGPL-3.0-or-later"

    def test_single_planet_request(self, client):
        payload = {
            "datetime": "1990-01-15T12:00:00",
            "timezone": "UTC",
            "latitude": 21.0285,
            "longitude": 105.8542,
            "planets": ["SUN"],
        }
        resp = client.post("/api/v1/planets", json=payload)
        if resp.status_code == 200:
            data = resp.json()
            assert len(data["positions"]) == 1
            assert data["positions"][0]["planet"] == "SUN"


class TestPlanetsValidation:
    def test_invalid_latitude_rejected(self, client):
        payload = {
            "datetime": "1990-01-15T12:00:00",
            "timezone": "UTC",
            "latitude": 999,
            "longitude": 105.8542,
        }
        resp = client.post("/api/v1/planets", json=payload)
        assert resp.status_code == 422

    def test_unknown_planet_rejected(self, client):
        payload = {
            "datetime": "1990-01-15T12:00:00",
            "timezone": "UTC",
            "latitude": 21.0285,
            "longitude": 105.8542,
            "planets": ["INVALID_PLANET"],
        }
        resp = client.post("/api/v1/planets", json=payload)
        assert resp.status_code == 422
        assert "INVALID_PLANET" in resp.text

    def test_invalid_timezone_rejected(self, client):
        payload = {
            "datetime": "1990-01-15T12:00:00",
            "timezone": "NotATimezone",
            "latitude": 21.0285,
            "longitude": 105.8542,
        }
        resp = client.post("/api/v1/planets", json=payload)
        assert resp.status_code == 422

    @pytest.mark.skipif(not EPHE_AVAILABLE, reason="Ephemeris files not found")
    def test_historical_timezone_alias_accepted(self, client):
        payload = {
            "datetime": "1990-01-15T12:00:00",
            "timezone": "Asia/Saigon",
            "latitude": 21.0285,
            "longitude": 105.8542,
        }
        resp = client.post("/api/v1/planets", json=payload)
        assert resp.status_code == 200
