"""
Astrological helpers used by the Telegram bot.

House occupancy and element mapping are copied from the pinned Swiss
Ephemeris API (commit 8a03d63):

- app/utils/houses.py :: house_for_longitude
- app/services/zodiac.py :: ZODIAC_SIGNS / _ELEMENT_MAP
- app/schemas/aspects.py :: _ASPECT_DEGREES
"""
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Display names as returned in PlanetPosition.name
MAIN_PLANETS = (
    "Sun",
    "Moon",
    "Mercury",
    "Venus",
    "Mars",
    "Jupiter",
    "Saturn",
    "Uranus",
    "Neptune",
    "Pluto",
)

# PlanetPosition.planet / AspectData.planet1 identifiers
MAIN_PLANET_IDS = (
    "SUN",
    "MOON",
    "MERCURY",
    "VENUS",
    "MARS",
    "JUPITER",
    "SATURN",
    "URANUS",
    "NEPTUNE",
    "PLUTO",
)

PLANET_ID_TO_NAME = {
    "SUN": "Sun",
    "MOON": "Moon",
    "MERCURY": "Mercury",
    "VENUS": "Venus",
    "MARS": "Mars",
    "JUPITER": "Jupiter",
    "SATURN": "Saturn",
    "URANUS": "Uranus",
    "NEPTUNE": "Neptune",
    "PLUTO": "Pluto",
    "CHIRON": "Chiron",
    "CERES": "Ceres",
    "PALLAS": "Pallas",
    "JUNO": "Juno",
    "VESTA": "Vesta",
    "EARTH": "Earth",
}

PLANET_NAME_TO_ID = {name: pid for pid, name in PLANET_ID_TO_NAME.items()}

# app/services/zodiac.py
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

# sign_num -> element, from app/services/zodiac.py
ELEMENT_MAP = {
    0: "FIRE",
    1: "EARTH",
    2: "AIR",
    3: "WATER",
    4: "FIRE",
    5: "EARTH",
    6: "AIR",
    7: "WATER",
    8: "FIRE",
    9: "EARTH",
    10: "AIR",
    11: "WATER",
}

# app/schemas/aspects.py
ASPECT_DEGREES = {
    "CONJUNCTION": 0.0,
    "OPPOSITION": 180.0,
    "TRINE": 120.0,
    "SQUARE": 90.0,
    "SEXTILE": 60.0,
}

# Default natal orbs from app/schemas/aspects.py _DEFAULT_ORBS
DEFAULT_ORBS = {
    "CONJUNCTION": 10.0,
    "OPPOSITION": 10.0,
    "TRINE": 8.0,
    "SQUARE": 8.0,
    "SEXTILE": 6.0,
}

# Mean tropical year used for secondary progression and solar-return
# first-order correction (IAU tropical year).
TROPICAL_YEAR_DAYS = 365.24219
MEAN_SOLAR_SPEED = 360.0 / TROPICAL_YEAR_DAYS

MODES_NEEDING_SECOND_PERSON = frozenset({"synastry", "composite"})


def planet_id(pos_or_name):
    """Return the API planet identifier (SUN, MOON, ...)."""
    if isinstance(pos_or_name, dict):
        if pos_or_name.get("planet"):
            return str(pos_or_name["planet"]).upper()
        name = pos_or_name.get("name", "")
        return PLANET_NAME_TO_ID.get(name, str(name).upper())
    text = str(pos_or_name)
    return PLANET_NAME_TO_ID.get(text, text.upper())


def planet_display_name(pos_or_name):
    """Return the API display name (Sun, Moon, ...)."""
    if isinstance(pos_or_name, dict):
        if pos_or_name.get("name"):
            return pos_or_name["name"]
        return PLANET_ID_TO_NAME.get(str(pos_or_name.get("planet", "")).upper(), "")
    text = str(pos_or_name)
    return PLANET_ID_TO_NAME.get(text.upper(), text)


def is_main_planet(pos_or_name):
    """True if the body is one of the ten classical planets."""
    return planet_id(pos_or_name) in MAIN_PLANET_IDS


def ecliptic_longitude(pos):
    """Longitude from a planet position or a house cusp dict."""
    if pos.get("longitude") is not None:
        return float(pos["longitude"])
    if pos.get("cusp") is not None:
        return float(pos["cusp"])
    raise KeyError("position is missing longitude/cusp")


def house_cusps(houses):
    """Extract 12 cusp longitudes from an API houses list."""
    cusps = []
    for house in houses[:12]:
        if house.get("cusp") is not None:
            cusps.append(float(house["cusp"]))
        elif house.get("longitude") is not None:
            cusps.append(float(house["longitude"]))
    return cusps


def house_for_longitude(longitude, cusps):
    """
    Return the house number (1-12) that contains the given ecliptic longitude.

    Copied from swiss-ephemeris-api app/utils/houses.py (commit 8a03d63).
    """
    if not cusps or len(cusps) < 12:
        return None
    for i in range(12):
        lo = cusps[i]
        hi = cusps[(i + 1) % 12]
        if lo < hi:
            in_house = lo < longitude <= hi
        else:
            in_house = longitude > lo or longitude <= hi
        if in_house:
            return i + 1
    return None


def element_for_sign_num(sign_num):
    """Return FIRE/EARTH/AIR/WATER for a 0-11 sign number."""
    return ELEMENT_MAP.get(int(sign_num))


def get_sign_from_longitude(longitude):
    """Get tropical zodiac sign from longitude (0-360)."""
    index = int((longitude % 360) / 30) % 12
    return ZODIAC_SIGNS[index]


def normalize_angle(angle):
    """Normalize angle to 0-360 range."""
    return angle % 360.0


def angular_distance(a, b):
    """Shortest angular distance between two longitudes (0-180)."""
    diff = abs(normalize_angle(a) - normalize_angle(b))
    return min(diff, 360.0 - diff)


def calculate_aspect_orb(lon1, lon2, target_angle):
    """Absolute orb in degrees from the named aspect angle."""
    return abs(angular_distance(lon1, lon2) - target_angle)


def true_aspect_orb(aspect):
    """
    Degrees from exact, using planet longitudes when the API provides them.

    The upstream AspectData.orb field is remaining orb-allowance
    (orb_width - diff), not the astrologer's 'orb from exact'.
    """
    name = aspect.get("aspect_name") or aspect.get("aspect")
    lon1 = aspect.get("planet1_longitude")
    lon2 = aspect.get("planet2_longitude")
    if name in ASPECT_DEGREES and lon1 is not None and lon2 is not None:
        return calculate_aspect_orb(float(lon1), float(lon2), ASPECT_DEGREES[name])
    return float(aspect.get("orb") or 0)


def find_aspects(positions, max_orb_scale=1.0):
    """
    Major aspects between positions, matching app/api/v1/endpoints/aspects.py.

    Args:
        positions: PlanetPosition-like dicts with longitude and name/planet.
        max_orb_scale: Multiply default orbs (0.7 is typical for synastry).
    """
    bodies = [p for p in positions if is_main_planet(p)]
    results = []
    for i, p1 in enumerate(bodies):
        for p2 in bodies[i + 1 :]:
            lon1 = ecliptic_longitude(p1)
            lon2 = ecliptic_longitude(p2)
            dist = angular_distance(lon1, lon2)
            for aspect_name, ideal in ASPECT_DEGREES.items():
                max_orb = DEFAULT_ORBS[aspect_name] * max_orb_scale
                diff = abs(dist - ideal)
                if diff <= max_orb:
                    results.append(
                        {
                            "planet1": planet_id(p1),
                            "planet2": planet_id(p2),
                            "aspect_name": aspect_name,
                            "orb": round(max_orb - diff, 4),
                            "exactness": round(max_orb - diff, 4),
                            "planet1_longitude": round(lon1, 6),
                            "planet2_longitude": round(lon2, 6),
                        }
                    )
    results.sort(key=lambda a: true_aspect_orb(a))
    return results


def cross_aspects(positions1, positions2, max_orb=0.7):
    """
    Aspects between two charts (synastry / transits).

    max_orb is a multiplier on the natal default orbs (0.7 = tighter).
    """
    aspects = []
    bodies1 = [p for p in positions1 if is_main_planet(p)]
    bodies2 = [p for p in positions2 if is_main_planet(p)]
    for p1 in bodies1:
        lon1 = ecliptic_longitude(p1)
        for p2 in bodies2:
            lon2 = ecliptic_longitude(p2)
            dist = angular_distance(lon1, lon2)
            for aspect_name, ideal in ASPECT_DEGREES.items():
                max_orb_degrees = DEFAULT_ORBS[aspect_name] * max_orb
                diff = abs(dist - ideal)
                if diff <= max_orb_degrees:
                    aspects.append(
                        {
                            "planet1": planet_id(p1),
                            "planet2": planet_id(p2),
                            "aspect_name": aspect_name,
                            "orb": round(max_orb_degrees - diff, 4),
                            "exactness": round(max_orb_degrees - diff, 4),
                            "planet1_longitude": round(lon1, 6),
                            "planet2_longitude": round(lon2, 6),
                        }
                    )
    aspects.sort(key=lambda a: true_aspect_orb(a))
    return aspects


def composite_midpoints(positions1, positions2):
    """
    Composite chart midpoints (shortest-arc) between matching planets.
    """
    composite = []
    index2 = {planet_id(p): p for p in positions2}
    for p1 in positions1:
        if not is_main_planet(p1):
            continue
        p2 = index2.get(planet_id(p1))
        if not p2:
            continue
        lon1 = ecliptic_longitude(p1)
        lon2 = ecliptic_longitude(p2)
        diff = normalize_angle(lon2 - lon1)
        if diff > 180:
            midpoint = normalize_angle(lon1 - (360 - diff) / 2)
        else:
            midpoint = normalize_angle(lon1 + diff / 2)
        sign = get_sign_from_longitude(midpoint)
        sign_num = ZODIAC_SIGNS.index(sign)
        composite.append(
            {
                "planet": planet_id(p1),
                "name": planet_display_name(p1),
                "longitude": midpoint,
                "sign": sign,
                "sign_num": sign_num,
            }
        )
    return composite


def equal_houses_from_asc(asc_longitude):
    """
    Equal houses from the Ascendant (Swiss Ephemeris house system 'E').
    Cusps use the API HouseData field name `cusp`.
    """
    houses = []
    for i in range(12):
        cusp_lon = normalize_angle(asc_longitude + (i * 30))
        sign = get_sign_from_longitude(cusp_lon)
        sign_num = ZODIAC_SIGNS.index(sign)
        houses.append(
            {
                "house": i + 1,
                "cusp": cusp_lon,
                "sign": sign,
                "sign_num": sign_num,
                "element": element_for_sign_num(sign_num),
            }
        )
    return houses


def shortest_arc_midpoint(lon1, lon2):
    """Midpoint along the shorter arc between two longitudes."""
    diff = normalize_angle(lon2 - lon1)
    if diff > 180:
        return normalize_angle(lon1 - (360 - diff) / 2)
    return normalize_angle(lon1 + diff / 2)


def progressed_instant(birth_date_str, progress_years):
    """
    Secondary progression: 1 day after birth = 1 year of life.
    """
    birth = datetime.strptime(birth_date_str, "%Y-%m-%d")
    progressed = birth + timedelta(days=progress_years)
    return progressed.strftime("%Y-%m-%d")


def solar_return_guess(birth_date_str, target_year):
    """Birthday in the target year; used as the first solar-return guess."""
    birth = datetime.strptime(birth_date_str, "%Y-%m-%d")
    return f"{target_year}-{birth.month:02d}-{birth.day:02d}"


def solar_return_adjust_days(natal_sun_lon, sun_lon_on_guess):
    """
    First-order solar-return correction in days.

    Sun moves about MEAN_SOLAR_SPEED degrees per day. The signed shortest
    arc from the guess Sun to the natal Sun, divided by that speed, is the
    time offset to apply to the guess datetime.
    """
    diff = ((natal_sun_lon - sun_lon_on_guess + 180.0) % 360.0) - 180.0
    return diff / MEAN_SOLAR_SPEED
