"""Tests against the official Swiss Ephemeris API response schema and LMT formula."""
import json
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bot"))

import astro  # noqa: E402
import birthtime  # noqa: E402
import chartwheel  # noqa: E402
import geocoding  # noqa: E402
import bot as botmod  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def load_fixture(name):
    with open(FIXTURES / name, encoding="utf-8") as fh:
        return json.load(fh)


class HouseOccupancyTests(unittest.TestCase):
    """Copied behaviour of swiss-ephemeris-api app/utils/houses.py."""

    def test_equal_houses(self):
        cusps = [i * 30.0 for i in range(12)]
        self.assertEqual(astro.house_for_longitude(15, cusps), 1)
        self.assertEqual(astro.house_for_longitude(30, cusps), 1)
        self.assertEqual(astro.house_for_longitude(31, cusps), 2)
        self.assertEqual(astro.house_for_longitude(0.0, cusps), 12)
        self.assertEqual(astro.house_for_longitude(0.1, cusps), 1)

    def test_wrap_around_aries(self):
        cusps = [350, 20, 50, 80, 110, 140, 170, 200, 230, 260, 290, 320]
        self.assertEqual(astro.house_for_longitude(355, cusps), 1)
        self.assertEqual(astro.house_for_longitude(10, cusps), 1)
        self.assertEqual(astro.house_for_longitude(20, cusps), 1)
        self.assertEqual(astro.house_for_longitude(21, cusps), 2)


class LmtTests(unittest.TestCase):
    def test_einstein_ulm_offset(self):
        offset = birthtime.calculate_lmt_offset(9.9876)
        self.assertAlmostEqual(offset, 9.9876 / 15.0, places=6)

    def test_lmt_is_converted_to_utc(self):
        result = birthtime.resolve_birth_utc("1879-03-14", "11:30", "LMT", 9.9876)
        self.assertTrue(result["is_lmt"])
        self.assertEqual(result["timezone"], "UTC")
        self.assertNotIn("LMT", result["timezone"])
        self.assertTrue(result["datetime"].startswith("1879-03-14T10:50:"))

    def test_pre_1900_uses_lmt(self):
        self.assertTrue(birthtime.should_use_lmt("1879-03-14", "Europe/Berlin"))
        self.assertFalse(birthtime.should_use_lmt("1979-03-14", "Europe/Berlin"))

    def test_iana_passthrough_after_1900(self):
        result = birthtime.resolve_birth_utc("1979-03-14", "11:30", "Europe/Berlin", 9.9876)
        self.assertFalse(result["is_lmt"])
        self.assertEqual(result["timezone"], "Europe/Berlin")
        self.assertEqual(result["datetime"], "1979-03-14T11:30:00")


class ApiSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.chart = load_fixture("einstein_birth_chart.json")
        cls.aspects = load_fixture("einstein_aspects.json")

    def test_house_uses_cusp_not_longitude(self):
        house = self.chart["houses"][0]
        self.assertIn("cusp", house)
        self.assertNotIn("longitude", house)
        formatted = botmod.format_position(house)
        self.assertIn("سرطان", formatted)

    def test_planet_has_name_sun_and_id_sun(self):
        sun = self.chart["positions"][0]
        self.assertEqual(sun["planet"], "SUN")
        self.assertEqual(sun["name"], "Sun")
        self.assertNotIn("house", sun)
        self.assertNotIn("element", sun)

    def test_aspect_uses_aspect_name(self):
        aspect = self.aspects["aspects"][0]
        self.assertIn("aspect_name", aspect)
        self.assertNotIn("aspect", aspect)

    def test_generate_chart_text_does_not_crash(self):
        text = botmod.generate_chart_text(
            self.chart, self.aspects, "آلبرت انیشتین", mode="natal"
        )
        self.assertIn("سیارات اصلی", text)
        self.assertIn("ASC", text)
        self.assertNotIn("خانه ?", text)
        self.assertIn("☌", text)
        self.assertIn("آتش", text)

    def test_wheel_svg_uses_api_fields(self):
        svg = chartwheel.draw_wheel_svg(
            self.chart["positions"],
            self.chart["houses"],
            self.aspects["aspects"],
            self.chart["ascendant"],
        )
        self.assertIsNotNone(svg)
        self.assertIn("<svg", svg)
        self.assertIn("☉", svg)

    def test_elements_from_sign_num(self):
        self.assertEqual(astro.element_for_sign_num(11), "WATER")  # Pisces
        self.assertEqual(astro.element_for_sign_num(0), "FIRE")


class GeocodingTests(unittest.TestCase):
    def test_city_name_is_not_coordinates(self):
        self.assertFalse(geocoding.looks_like_coordinates("Tehran, Iran"))
        self.assertFalse(geocoding.looks_like_coordinates("تهران"))

    def test_numeric_pair_is_coordinates(self):
        self.assertTrue(geocoding.looks_like_coordinates("35.69,51.39"))
        lat, lon = geocoding.parse_coordinates("35.69,51.39")
        self.assertAlmostEqual(lat, 35.69)
        self.assertAlmostEqual(lon, 51.39)

    def test_invalid_coordinates(self):
        with self.assertRaises(geocoding.LocationError):
            geocoding.parse_coordinates("1,2,3")
        with self.assertRaises(geocoding.LocationError):
            geocoding.parse_coordinates("99.0,0")


class ProgressionTests(unittest.TestCase):
    def test_secondary_progression_one_day_per_year(self):
        self.assertEqual(astro.progressed_instant("1879-03-14", 50), "1879-05-03")

    def test_solar_return_first_order_days(self):
        # If the guess Sun is 1° behind natal, add about 1 day.
        days = astro.solar_return_adjust_days(100.0, 99.0)
        self.assertAlmostEqual(days, 1.0 / astro.MEAN_SOLAR_SPEED, places=4)


if __name__ == "__main__":
    unittest.main()
