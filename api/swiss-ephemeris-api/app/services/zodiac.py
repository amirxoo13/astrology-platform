ZODIAC_SIGNS = [
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
]
ZODIAC_ELEMENTS = [
    "FIRE",    # Aries, Leo, Sagittarius
    "EARTH",   # Taurus, Virgo, Capricorn
    "AIR",     # Gemini, Libra, Aquarius
    "WATER",   # Cancer, Scorpio, Pisces
]
_ELEMENT_MAP = {
    0: "FIRE",   # Aries
    1: "EARTH",  # Taurus
    2: "AIR",    # Gemini
    3: "WATER",  # Cancer
    4: "FIRE",   # Leo
    5: "EARTH",  # Virgo
    6: "AIR",    # Libra
    7: "WATER",  # Scorpio
    8: "FIRE",   # Sagittarius
    9: "EARTH",  # Capricorn
    10: "AIR",   # Aquarius
    11: "WATER", # Pisces
}


def degree_to_sign(longitude: float) -> tuple[str, int, float, int, int]:
    """
    Convert ecliptic longitude (0-360) to zodiac sign information.
    Returns (sign_name, sign_num 0-11, degree_in_sign 0-29.999, minute, second).
    """
    normalized = longitude % 360
    sign_num = int(normalized // 30)
    degree_in_sign = normalized - sign_num * 30
    minute = int((degree_in_sign % 1) * 60)
    second = int((((degree_in_sign % 1) * 60) % 1) * 60)
    return ZODIAC_SIGNS[sign_num], sign_num, round(degree_in_sign, 6), minute, second


def get_element(sign_num: int) -> str:
    """Return the element for a given sign number (0=Aries ... 11=Pisces)."""
    return _ELEMENT_MAP[sign_num]
