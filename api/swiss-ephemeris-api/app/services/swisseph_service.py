import swisseph as swe


# Maps AyanamsaEnum value names to swisseph sidereal constant names
# Only constants that exist in pysweph 2.10.3.6 are included.
_AYANAMSA_MAP = {
    "TROPICAL": None,          # no sidereal flag = tropical
    "LAHIRI": swe.SIDM_LAHIRI,
    "KRISHNAMURTI": swe.SIDM_KRISHNAMURTI,
    "DE_LUCE": swe.SIDM_DELUCE,
    "RAMAN": swe.SIDM_RAMAN,
    "USHA_SHASTHRA": swe.SIDM_USHASHASHI,   # SIDM_USHASHASHI (4)
    "YUKTESHWAR": swe.SIDM_YUKTESHWAR,
    "SURYASIDDHANTA": swe.SIDM_SURYASIDDHANTA,
    "GALCENT_0SAG": swe.SIDM_GALCENT_0SAG,
    "SS_CITRA": swe.SIDM_SS_CITRA,
    "SS_REVATI": swe.SIDM_SS_REVATI,
}


def get_ayanamsa_constant(name: str) -> int | None:
    """Return swe sidereal constant for a given ayanamsa name, or None for tropical."""
    return _AYANAMSA_MAP.get(name.upper().strip())


def is_retrograde(planet: int, speed_long: float) -> bool:
    """
    Return True if the planet is retrograde.
    All planets from Mercury outward can be retrograde when speed_long < 0.
    Moon is NEVER retrograde in the geocentric swisseph model.
    """
    if planet < swe.MERCURY:
        return False
    return speed_long < 0


def get_ayanamsa_value(jd_ut: float, ayanamsa: int | None) -> float:
    """
    Get current ayanamsa precession value in degrees.
    Works for both tropical (returns 0) and sidereal modes.
    FLG_SWIEPH must be used for consistency with planet calculations.
    """
    if ayanamsa is None:
        return 0.0
    try:
        return swe.get_ayanamsa_ex(jd_ut, swe.FLG_SWIEPH)[1]
    except Exception:
        return 0.0
