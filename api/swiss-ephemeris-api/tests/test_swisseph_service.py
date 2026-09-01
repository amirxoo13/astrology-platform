from app.services.swisseph_service import get_ayanamsa_constant, is_retrograde
import swisseph as swe


class TestAyanamsaMap:
    def test_tropical_returns_none(self):
        assert get_ayanamsa_constant("TROPICAL") is None

    def test_lahiri_returns_constant(self):
        const = get_ayanamsa_constant("LAHIRI")
        assert const == swe.SIDM_LAHIRI

    def test_case_insensitive(self):
        assert get_ayanamsa_constant("lahiri") == swe.SIDM_LAHIRI
        assert get_ayanamsa_constant("Lahiri") == swe.SIDM_LAHIRI

    def test_unknown_returns_none(self):
        assert get_ayanamsa_constant("UNKNOWN") is None

    def test_all_supported_ayanamsas(self):
        names = ["TROPICAL", "LAHIRI", "KRISHNAMURTI", "DE_LUCE", "RAMAN"]
        for name in names:
            result = get_ayanamsa_constant(name)
            assert result is not None or name == "TROPICAL"


class TestRetrograde:
    def test_sun_never_retrograde(self):
        # Sun cannot be retrograde
        assert is_retrograde(swe.SUN, 1.0) is False
        assert is_retrograde(swe.SUN, -1.0) is False

    def test_moon_never_retrograde(self):
        # Moon is never retrograde in geocentric model
        assert is_retrograde(swe.MOON, 1.0) is False
        assert is_retrograde(swe.MOON, -0.5) is False

    def test_mercury_retrograde_when_speed_negative(self):
        assert is_retrograde(swe.MERCURY, 0.5) is False
        assert is_retrograde(swe.MERCURY, -0.5) is True

    def test_mars_retrograde_when_speed_negative(self):
        assert is_retrograde(swe.MARS, 0.5) is False
        assert is_retrograde(swe.MARS, -0.3) is True

    def test_superior_planets_retrograde(self):
        # Jupiter, Saturn, Uranus, Neptune, Pluto
        assert is_retrograde(swe.JUPITER, -0.1) is True
        assert is_retrograde(swe.SATURN, 0.2) is False
        assert is_retrograde(swe.URANUS, -0.05) is True
        assert is_retrograde(swe.NEPTUNE, 0.03) is False
        assert is_retrograde(swe.PLUTO, -0.01) is True
