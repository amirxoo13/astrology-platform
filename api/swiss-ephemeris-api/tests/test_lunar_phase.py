"""
Unit tests for app.services.lunar_phase — phase_angle_to_name and calculate_lunar_age_days.
No swisseph dependency required.
"""
import pytest
from app.services.lunar_phase import phase_angle_to_name, calculate_lunar_age_days


class TestPhaseAngleToName:
    def test_new_moon(self):
        assert phase_angle_to_name(0) == "NEW"

    def test_waxing_crescent(self):
        assert phase_angle_to_name(45) == "WAXING_CRESCENT"

    def test_first_quarter(self):
        assert phase_angle_to_name(90) == "FIRST_QUARTER"

    def test_waxing_gibbous(self):
        assert phase_angle_to_name(135) == "WAXING_GIBBOUS"

    def test_full_moon(self):
        assert phase_angle_to_name(180) == "FULL"

    def test_waning_gibbous(self):
        assert phase_angle_to_name(225) == "WANING_GIBBOUS"

    def test_last_quarter(self):
        assert phase_angle_to_name(270) == "LAST_QUARTER"

    def test_waning_crescent(self):
        assert phase_angle_to_name(315) == "WANING_CRESCENT"

    def test_wraps_around(self):
        assert phase_angle_to_name(360) == "NEW"
        assert phase_angle_to_name(720) == "NEW"

    def test_phase_angles_near_boundaries(self):
        assert phase_angle_to_name(1) == "NEW"
        assert phase_angle_to_name(44) == "NEW"
        assert phase_angle_to_name(45) == "WAXING_CRESCENT"
        assert phase_angle_to_name(89) == "WAXING_CRESCENT"
        assert phase_angle_to_name(90) == "FIRST_QUARTER"
        assert phase_angle_to_name(91) == "FIRST_QUARTER"  # 91 in [90,135) = FIRST_QUARTER


class TestLunarAgeDays:
    MEAN_CYCLE = 29.530588853

    def test_new_moon_age_zero(self):
        assert calculate_lunar_age_days(0) == pytest.approx(0.0, abs=0.001)

    def test_full_moon_age_half_cycle(self):
        age = calculate_lunar_age_days(180)
        expected = (180 / 360) * self.MEAN_CYCLE
        assert age == pytest.approx(expected, abs=0.001)

    def test_age_positive(self):
        assert calculate_lunar_age_days(90) > 0
        assert calculate_lunar_age_days(270) > 0

    def test_within_mean_cycle(self):
        age = calculate_lunar_age_days(360)
        assert age == pytest.approx(self.MEAN_CYCLE, abs=0.001)
