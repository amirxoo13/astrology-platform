"""
Unit tests for SwissEphemerisCore using mocked swisseph.
Tests the wrapper logic without needing actual ephemeris files.
"""
import pytest
from unittest.mock import patch, MagicMock
from app.core.swisseph_core import SwissEphemerisCore, PlanetResult, HouseResult


@pytest.fixture
def core():
    return SwissEphemerisCore(ephe_path="/fake/path")


# ─── Mock fixtures ────────────────────────────────────────────────────────────

def _mock_planet_result(lon=10.5, lat=1.0, dist=1.0, speed=1.0):
    # swe.calc_ut returns (tuple_of_6, retflag, serr)
    return (
        (lon, lat, dist, speed, 0.0, 0.0),  # result[0] = position tuple
        0,
        ""
    )


def _mock_house_result():
    cusps = [0.0] + [float(i * 30) for i in range(1, 13)]  # [0, 30, 60, ...]
    ascmc = [295.0, 123.0, 0.0, 0.0]
    return cusps, ascmc


# ─── calc_planet ──────────────────────────────────────────────────────────────

class TestCalcPlanet:
    @patch("app.core.swisseph_core.swe.calc_ut")
    def test_tropical_uses_default_flags(self, mock_calc, core):
        mock_calc.return_value = _mock_planet_result()
        r = core.calc_planet(0, 2451545.0)
        assert isinstance(r, PlanetResult)
        assert r.longitude == 10.5
        assert mock_calc.call_args[0][2] == 2 | 256  # FLG_SWIEPH | FLG_SPEED

    @patch("app.core.swisseph_core.swe.calc_ut")
    def test_sidereal_adds_sidereal_flag(self, mock_calc, core):
        mock_calc.return_value = _mock_planet_result()
        core.calc_planet(0, 2451545.0, sidereal_ayanamsa=1)
        # FLG_SIDEREAL + sidereal_ayanamsa + FLG_SPEED = 65536 + 1 + 256
        called_flags = mock_calc.call_args[0][2]
        assert called_flags == 65536 + 1 + 256

    @patch("app.core.swisseph_core.swe.calc_ut")
    def test_returns_all_position_fields(self, mock_calc, core):
        mock_calc.return_value = (
            (295.123, -1.5, 0.983, 0.95, 0.0, 0.0),
            0,
            ""
        )
        r = core.calc_planet(0, 2451545.0)
        assert r.longitude == 295.123
        assert r.latitude == -1.5
        assert r.distance == 0.983
        assert r.speed_long == 0.95


# ─── calc_special ─────────────────────────────────────────────────────────────

class TestCalcSpecial:
    @patch("app.core.swisseph_core.swe.calc_ut")
    def test_adds_speed_flag(self, mock_calc, core):
        mock_calc.return_value = _mock_planet_result()
        core.calc_special(0, 2451545.0)
        called_flags = mock_calc.call_args[0][2]
        # FLG_SWIEPH + FLG_SPEED = 2 + 256 = 258
        assert called_flags == 2 + 256

    @patch("app.core.swisseph_core.swe.calc_ut")
    def test_sidereal_uses_sidereal_flag(self, mock_calc, core):
        mock_calc.return_value = _mock_planet_result()
        core.calc_special(0, 2451545.0, sidereal_ayanamsa=1)
        called_flags = mock_calc.call_args[0][2]
        assert called_flags == 65536 + 1 + 256


# ─── calc_lilith ──────────────────────────────────────────────────────────────

class TestCalcLilith:
    @patch("app.core.swisseph_core.swe.nod_aps_ut")
    def test_true_lilith_uses_nodbit_oscu(self, mock_nod, core):
        # nod_aps_ut returns (asc_node, dsc_node, perigee, apogee) — apogee at index 3
        mock_nod.return_value = (
            (123.952, 0.0, 0.0024, -0.054, 0.0, 0.0),
            (303.952, 0.0, 0.0024, 0.054, 0.0, 0.0),
            (72.979, 0.0, 0.0024, 0.0, 0.0, 0.0),
            (252.979, 0.0, 0.0024, -0.054, 0.0, 0.0),  # apogee = Lilith
        )
        r = core.calc_lilith(2451545.0, true=True)
        assert r.longitude == 252.979  # apogee at index 3
        # nod_aps_ut: (tjdut, planet, nodbit, flags)
        called_nodbit = mock_nod.call_args[0][2]
        # NODBIT_OSCU | NODBIT_FOPOINT = 2 | 256 = 258
        assert called_nodbit == 258

    @patch("app.core.swisseph_core.swe.nod_aps_ut")
    def test_mean_lilith_uses_nodbit_mean(self, mock_nod, core):
        mock_nod.return_value = (
            (100.0, 0.0, 0.0024, 0.0, 0.0, 0.0),
            (280.0, 0.0, 0.0024, 0.0, 0.0, 0.0),
            (72.979, 0.0, 0.0024, 0.0, 0.0, 0.0),
            (315.5, 0.0, 0.0024, 0.0, 0.0, 0.0),
        )
        r = core.calc_lilith(2451545.0, true=False)
        called_nodbit = mock_nod.call_args[0][2]
        # NODBIT_MEAN | NODBIT_FOPOINT = 1 | 256 = 257
        assert called_nodbit == 257


# ─── calc_nodes ──────────────────────────────────────────────────────────────

class TestCalcNodes:
    @patch("app.core.swisseph_core.swe.calc_ut")
    def test_returns_north_and_south(self, mock_calc, core):
        mock_calc.return_value = (
            (82.456, 0.0, 1.0, -0.002, 0.0, 0.0),
            0,
            ""
        )
        north, south = core.calc_nodes(2451545.0, true=True)
        assert isinstance(north, PlanetResult)
        assert isinstance(south, PlanetResult)
        assert north.longitude == 82.456
        assert south.longitude == (82.456 + 180.0) % 360.0  # 262.456

    @patch("app.core.swisseph_core.swe.calc_ut")
    def test_south_latitude_negated(self, mock_calc, core):
        mock_calc.return_value = (
            (50.0, 2.5, 1.0, 0.5, 0.0, 0.0),
            0,
            ""
        )
        north, south = core.calc_nodes(2451545.0, true=True)
        assert north.latitude == 2.5
        assert south.latitude == -2.5

    @patch("app.core.swisseph_core.swe.calc_ut")
    def test_south_speed_negated(self, mock_calc, core):
        mock_calc.return_value = (
            (50.0, 0.0, 1.0, 0.3, 0.0, 0.0),
            0,
            ""
        )
        north, south = core.calc_nodes(2451545.0, true=True)
        assert north.speed_long == 0.3
        assert south.speed_long == -0.3

    @patch("app.core.swisseph_core.swe.calc_ut")
    def test_mean_node_uses_swe_mean_node(self, mock_calc, core):
        mock_calc.return_value = _mock_planet_result()
        core.calc_nodes(2451545.0, true=False)
        assert mock_calc.call_args[0][1] == 10  # swe.MEAN_NODE


# ─── houses ───────────────────────────────────────────────────────────────────

class TestHouses:
    @patch("app.core.swisseph_core.swe.houses")
    def test_returns_12_cusps_only(self, mock_houses, core):
        cusps_full = [0.0] + [i * 30.0 for i in range(1, 13)]
        mock_houses.return_value = (cusps_full, [295.0, 123.0, 0.0, 0.0])
        result = core.houses(2451545.0, 21.0285, 105.8542, "P")
        assert isinstance(result, HouseResult)
        assert len(result.cusps) == 12
        assert result.cusps[0] == 30.0  # house 1 cusp

    @patch("app.core.swisseph_core.swe.houses")
    def test_ascmc_extracted_correctly(self, mock_houses, core):
        mock_houses.return_value = ([0.0] + [0.0] * 12, [295.5, 123.4, 0.0, 0.0])
        result = core.houses(2451545.0, 21.0285, 105.8542, "K")
        assert result.ascmc[0] == 295.5  # ASC
        assert result.ascmc[1] == 123.4  # MC

    @patch("app.core.swisseph_core.swe.houses")
    def test_hsys_encoded_to_bytes(self, mock_houses, core):
        mock_houses.return_value = ([0.0] + [0.0] * 12, [0.0, 0.0, 0.0, 0.0])
        core.houses(2451545.0, 0.0, 0.0, "W")
        # swe.houses signature: (jd_ut, latitude, longitude, hsys)
        # house system is arg[3]; core converts str to bytes
        assert mock_houses.call_args[0][3] == b"W"


# ─── julday / revjul ──────────────────────────────────────────────────────────

class TestJulday:
    def test_julday_returns_float(self, core):
        jd = core.julday(2000, 1, 1, 12.0)
        assert isinstance(jd, float)
        assert 2451540 < jd < 2451550

    def test_revjul_roundtrip(self, core):
        year, month, day, hour = core.revjul(2451545.0)
        assert year == 2000
        assert month == 1
        assert day == 1
        assert abs(hour - 12.0) < 0.001
