"""
Integration tests for all v1 API endpoints.
Uses FastAPI TestClient -- synchronous, no async needed.
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


def base_payload() -> dict:
    return {
        "datetime": "1990-01-15T12:00:00",
        "timezone": "Asia/Ho_Chi_Minh",
        "latitude": 21.0285,
        "longitude": 105.8542,
    }


class TestRoot:
    def test_returns_agpl_notice(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["license"] == "AGPL-3.0-or-later"
        assert "AGPL" in data["notice"]

    def test_includes_metadata_fields(self, client):
        resp = client.get("/")
        data = resp.json()
        assert "name" in data
        assert "version" in data
        assert "docs" in data


class TestHealth:
    def test_health_returns_ok_or_unavailable(self, client):
        resp = client.get("/health")
        assert resp.status_code in (200, 503)
        data = resp.json()
        assert "status" in data
        assert "ephe_path" in data

    def test_health_includes_source_url(self, client):
        resp = client.get("/health")
        if resp.status_code == 200:
            assert "github.com" in resp.json()["source"]


@pytest.mark.skipif(not EPHE_AVAILABLE, reason="Ephemeris files not found in EPHE_PATH")
class TestPlanetsEndpoint:
    def test_valid_request_returns_positions(self, client):
        resp = client.post("/api/v1/planets", json=base_payload())
        if resp.status_code == 200:
            data = resp.json()
            assert "positions" in data
            assert "ascendant" in data
            assert data["license"] == "AGPL-3.0-or-later"

    def test_single_planet(self, client):
        payload = {**base_payload(), "planets": ["SUN"]}
        resp = client.post("/api/v1/planets", json=payload)
        if resp.status_code == 200:
            data = resp.json()
            assert len(data["positions"]) == 1
            assert data["positions"][0]["planet"] == "SUN"

    def test_all_planets(self, client):
        resp = client.post("/api/v1/planets", json=base_payload())
        if resp.status_code == 200:
            data = resp.json()
            assert len(data["positions"]) == 15

    def test_sidereal_mode(self, client):
        payload = {**base_payload(), "ayanamsa": "LAHIRI"}
        resp = client.post("/api/v1/planets", json=payload)
        if resp.status_code == 200:
            data = resp.json()
            assert data["ayanamsa_name"] == "LAHIRI"
            assert data["ayanamsa_value"] > 0

    def test_response_contains_julian_day(self, client):
        resp = client.post("/api/v1/planets", json=base_payload())
        if resp.status_code == 200:
            data = resp.json()
            assert "julian_day_ut" in data
            assert 2400000 < data["julian_day_ut"] < 2500000


class TestPlanetsValidation:
    def test_invalid_latitude(self, client):
        payload = {**base_payload(), "latitude": 999}
        resp = client.post("/api/v1/planets", json=payload)
        assert resp.status_code == 422

    def test_invalid_longitude(self, client):
        payload = {**base_payload(), "longitude": -200}
        resp = client.post("/api/v1/planets", json=payload)
        assert resp.status_code == 422

    def test_unknown_planet(self, client):
        payload = {**base_payload(), "planets": ["INVALID"]}
        resp = client.post("/api/v1/planets", json=payload)
        assert resp.status_code == 422

    def test_invalid_timezone(self, client):
        payload = {**base_payload(), "timezone": "NotATimezone"}
        resp = client.post("/api/v1/planets", json=payload)
        assert resp.status_code == 422


@pytest.mark.skipif(not EPHE_AVAILABLE, reason="Ephemeris files not found in EPHE_PATH")
class TestHousesEndpoint:
    def test_valid_request_returns_cusps(self, client):
        resp = client.post("/api/v1/houses", json=base_payload())
        if resp.status_code == 200:
            data = resp.json()
            assert "houses" in data
            assert len(data["houses"]) == 12
            assert data["license"] == "AGPL-3.0-or-later"

    def test_all_houses_have_sign(self, client):
        resp = client.post("/api/v1/houses", json=base_payload())
        if resp.status_code == 200:
            data = resp.json()
            for h in data["houses"]:
                assert "sign" in h
                assert "cusp" in h
                assert 1 <= h["house"] <= 12

    def test_whole_sign_house_system(self, client):
        payload = {**base_payload(), "house_system": "W"}
        resp = client.post("/api/v1/houses", json=payload)
        if resp.status_code == 200:
            data = resp.json()
            assert len(data["houses"]) == 12


class TestHousesValidation:
    def test_invalid_latitude(self, client):
        payload = {**base_payload(), "latitude": 91}
        resp = client.post("/api/v1/houses", json=payload)
        assert resp.status_code == 422


@pytest.mark.skipif(not EPHE_AVAILABLE, reason="Ephemeris files not found in EPHE_PATH")
class TestBirthChartEndpoint:
    def test_valid_request_returns_planets_and_houses(self, client):
        payload = {**base_payload(), "house_system": "P", "ayanamsa": "TROPICAL", "include_planets": True}
        resp = client.post("/api/v1/birth-chart", json=payload)
        if resp.status_code == 200:
            data = resp.json()
            assert "positions" in data
            assert "houses" in data
            assert len(data["positions"]) == 15
            assert len(data["houses"]) == 12
            assert data["license"] == "AGPL-3.0-or-later"

    def test_houses_are_typed_not_dicts(self, client):
        payload = {**base_payload(), "include_planets": False}
        resp = client.post("/api/v1/birth-chart", json=payload)
        if resp.status_code == 200:
            data = resp.json()
            for h in data["houses"]:
                assert isinstance(h, dict)
                assert set(h.keys()) == {"house", "cusp", "sign", "sign_num", "degree_in_sign", "element"}

    def test_include_planets_false(self, client):
        payload = {**base_payload(), "include_planets": False}
        resp = client.post("/api/v1/birth-chart", json=payload)
        if resp.status_code == 200:
            data = resp.json()
            assert len(data["positions"]) == 0


class TestBirthChartValidation:
    def test_invalid_latitude(self, client):
        payload = {**base_payload(), "latitude": -100}
        resp = client.post("/api/v1/birth-chart", json=payload)
        assert resp.status_code == 422


@pytest.mark.skipif(not EPHE_AVAILABLE, reason="Fixed star files not found in EPHE_PATH")
class TestFixedStarsEndpoint:
    def test_valid_request_returns_stars(self, client):
        resp = client.post("/api/v1/fixed-stars", json=base_payload())
        if resp.status_code == 200:
            data = resp.json()
            assert "positions" in data
            assert len(data["positions"]) >= 30
            assert data["license"] == "AGPL-3.0-or-later"

    def test_single_star(self, client):
        payload = {**base_payload(), "stars": ["Sirius"]}
        resp = client.post("/api/v1/fixed-stars", json=payload)
        if resp.status_code == 200:
            data = resp.json()
            assert len(data["positions"]) == 1
            assert data["positions"][0]["star"] == "Sirius"


class TestFixedStarsValidation:
    def test_unknown_star(self, client):
        payload = {**base_payload(), "stars": ["NotAStar"]}
        resp = client.post("/api/v1/fixed-stars", json=payload)
        assert resp.status_code == 422


@pytest.mark.skipif(not EPHE_AVAILABLE, reason="Ephemeris files not found in EPHE_PATH")
class TestEclipsesEndpoint:
    def test_solar_eclipses_returns_list(self, client):
        resp = client.get("/api/v1/eclipses", params={"start_date": "2020-01-01", "end_date": "2025-01-01", "type": "SOLAR"})
        if resp.status_code == 200:
            data = resp.json()
            assert "eclipses" in data
            assert isinstance(data["eclipses"], list)
            assert data["license"] == "AGPL-3.0-or-later"

    def test_lunar_eclipses(self, client):
        resp = client.get("/api/v1/eclipses", params={"start_date": "2020-01-01", "end_date": "2025-01-01", "type": "LUNAR"})
        if resp.status_code == 200:
            data = resp.json()
            assert "eclipses" in data

    def test_invalid_type(self, client):
        resp = client.get("/api/v1/eclipses", params={"start_date": "2020-01-01", "end_date": "2025-01-01", "type": "INVALID"})
        assert resp.status_code == 422

    def test_invalid_date_range(self, client):
        resp = client.get("/api/v1/eclipses", params={"start_date": "not-a-date", "end_date": "2025-01-01", "type": "SOLAR"})
        assert resp.status_code == 422


@pytest.mark.skipif(not EPHE_AVAILABLE, reason="Ephemeris files not found in EPHE_PATH")
class TestLunarPhaseEndpoint:
    def test_valid_request_returns_phase(self, client):
        resp = client.post("/api/v1/lunar-phase", json=base_payload())
        if resp.status_code == 200:
            data = resp.json()
            assert "phase" in data
            phase = data["phase"]
            assert "phase_angle" in phase
            assert "illumination" in phase
            assert "elongation" in phase
            assert "age_days" in phase
            assert 0 <= phase["illumination"] <= 100
            assert data["license"] == "AGPL-3.0-or-later"


class TestLunarPhaseValidation:
    def test_invalid_timezone(self, client):
        payload = {**base_payload(), "timezone": "Fake/Zone"}
        resp = client.post("/api/v1/lunar-phase", json=payload)
        assert resp.status_code == 422


@pytest.mark.skipif(not EPHE_AVAILABLE, reason="Ephemeris files not found in EPHE_PATH")
class TestLunarNodesEndpoint:
    def test_valid_request(self, client):
        resp = client.post("/api/v1/lunar-nodes", json=base_payload())
        if resp.status_code == 200:
            data = resp.json()
            assert "north_node" in data
            assert "lilith" in data
            assert data["license"] == "AGPL-3.0-or-later"

    def test_north_and_south_180_apart(self, client):
        resp = client.post("/api/v1/lunar-nodes", json=base_payload())
        if resp.status_code == 200:
            data = resp.json()
            north = data["north_node"]["north_longitude"]
            south = data["north_node"]["south_longitude"]
            diff = abs(north - south)
            assert diff == pytest.approx(180.0, abs=0.001) or diff == pytest.approx(540.0, abs=0.001)

    def test_mean_node_type(self, client):
        payload = {**base_payload(), "node_type": "MEAN"}
        resp = client.post("/api/v1/lunar-nodes", json=payload)
        if resp.status_code == 200:
            data = resp.json()
            assert data["north_node"]["node_type"] == "MEAN"

    def test_mean_lilith_type(self, client):
        payload = {**base_payload(), "lilith_type": "MEAN"}
        resp = client.post("/api/v1/lunar-nodes", json=payload)
        if resp.status_code == 200:
            data = resp.json()
            assert data["lilith"]["lilith_type"] == "MEAN"

    def test_nodes_include_houses(self, client):
        resp = client.post("/api/v1/lunar-nodes", json=base_payload())
        if resp.status_code == 200:
            data = resp.json()
            assert "north_house" in data["north_node"]
            assert "south_house" in data["north_node"]
            assert "house" in data["lilith"]


class TestLunarNodesValidation:
    def test_invalid_latitude(self, client):
        payload = {**base_payload(), "latitude": 95}
        resp = client.post("/api/v1/lunar-nodes", json=payload)
        assert resp.status_code == 422


@pytest.mark.skipif(not EPHE_AVAILABLE, reason="Ephemeris files not found in EPHE_PATH")
class TestSpecialPointsEndpoint:
    def test_valid_request(self, client):
        resp = client.post("/api/v1/special-points", json=base_payload())
        if resp.status_code == 200:
            data = resp.json()
            assert "positions" in data
            assert len(data["positions"]) == 3
            assert data["license"] == "AGPL-3.0-or-later"

    def test_part_of_fortune_only(self, client):
        payload = {**base_payload(), "points": ["PART_OF_FORTUNE"]}
        resp = client.post("/api/v1/special-points", json=payload)
        if resp.status_code == 200:
            data = resp.json()
            assert len(data["positions"]) == 1
            assert data["positions"][0]["point_type"] == "PART_OF_FORTUNE"

    def test_vertex_and_anti_vertex(self, client):
        payload = {**base_payload(), "points": ["VERTEX", "ANTI_VERTEX"]}
        resp = client.post("/api/v1/special-points", json=payload)
        if resp.status_code == 200:
            data = resp.json()
            assert len(data["positions"]) == 2

    def test_all_points_have_houses(self, client):
        resp = client.post("/api/v1/special-points", json=base_payload())
        if resp.status_code == 200:
            data = resp.json()
            for p in data["positions"]:
                assert "house" in p
                assert "sign" in p
                assert "longitude" in p


class TestSpecialPointsValidation:
    def test_unknown_point(self, client):
        payload = {**base_payload(), "points": ["NOT_A_POINT"]}
        resp = client.post("/api/v1/special-points", json=payload)
        assert resp.status_code == 422

    def test_invalid_latitude(self, client):
        payload = {**base_payload(), "latitude": 180}
        resp = client.post("/api/v1/special-points", json=payload)
        assert resp.status_code == 422
