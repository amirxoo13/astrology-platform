import pytest
from app.utils.datetime_utils import parse_iso_with_tz, jd_to_iso, datetime_to_jd
from datetime import datetime, timezone


class TestParseIsoWithTz:
    def test_utc_datetime(self):
        jd = parse_iso_with_tz("2020-01-15T12:00:00", "UTC")
        # JD for 2020 is ~2458864
        assert 2450000 < jd < 2460000
        assert isinstance(jd, float)

    def test_timezone_ho_chi_minh(self):
        # UTC+7 — same moment in HCMC should be earlier JD than UTC
        jd_hcmc = parse_iso_with_tz("2020-01-15T12:00:00", "Asia/Ho_Chi_Minh")
        jd_utc = parse_iso_with_tz("2020-01-15T12:00:00", "UTC")
        # HCMC is UTC+7, so JD should be slightly lower
        assert jd_hcmc < jd_utc

    def test_historical_timezone_aliases(self):
        assert parse_iso_with_tz("2020-01-15T12:00:00", "Asia/Saigon") == pytest.approx(
            parse_iso_with_tz("2020-01-15T12:00:00", "Asia/Ho_Chi_Minh")
        )
        assert parse_iso_with_tz("2020-01-15T12:00:00", "Europe/Kiev") == pytest.approx(
            parse_iso_with_tz("2020-01-15T12:00:00", "Europe/Kyiv")
        )

    def test_invalid_timezone_raises(self):
        # Invalid timezone names now raise ValueError
        with pytest.raises(ValueError):
            parse_iso_with_tz("2020-01-15T12:00:00", "Invalid/Zone")


class TestJdToIso:
    def test_roundtrip(self):
        # Known JD for 2000-01-01 12:00:00 UTC = JD 2451545.0
        jd = 2451545.0
        iso = jd_to_iso(jd)
        assert "2000-01-01" in iso

    def test_ends_with_z(self):
        jd = 2451545.0
        iso = jd_to_iso(jd)
        assert iso.endswith("Z")

    def test_format_is_iso(self):
        jd = 2451545.0
        iso = jd_to_iso(jd)
        # Should be parseable as ISO
        from datetime import datetime
        # strip 'Z' and parse
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        assert dt.year == 2000
        assert dt.month == 1
        assert dt.day == 1


class TestDatetimeToJd:
    def test_naive_utc(self):
        dt = datetime(2000, 1, 1, 12, 0, 0)
        jd = datetime_to_jd(dt)
        assert jd == pytest.approx(2451545.0, abs=0.001)

    def test_aware_utc(self):
        dt = datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        jd = datetime_to_jd(dt)
        assert jd == pytest.approx(2451545.0, abs=0.001)
