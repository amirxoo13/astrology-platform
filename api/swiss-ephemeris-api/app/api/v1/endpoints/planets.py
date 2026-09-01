import asyncio
import swisseph as swe

from fastapi import APIRouter, HTTPException

from app.schemas.planets import (
    PlanetRequest,
    PlanetResponse,
    PlanetPosition,
    ALL_PLANETS,
)
from app.services.zodiac import degree_to_sign
from app.services.swisseph_service import is_retrograde, get_ayanamsa_constant, get_ayanamsa_value
from app.utils.datetime_utils import parse_iso_with_tz
from app.utils.geo import validate_lat_lon
from app.core.swisseph_core import PlanetResult
from app.deps import get_swiss_core


# Planet name -> swe constant
_PLANET_MAP: dict[str, int] = {
    "SUN": swe.SUN,
    "MOON": swe.MOON,
    "MERCURY": swe.MERCURY,
    "VENUS": swe.VENUS,
    "MARS": swe.MARS,
    "JUPITER": swe.JUPITER,
    "SATURN": swe.SATURN,
    "URANUS": swe.URANUS,
    "NEPTUNE": swe.NEPTUNE,
    "PLUTO": swe.PLUTO,
    "CHIRON": swe.CHIRON,
    "CERES": swe.CERES,
    "PALLAS": swe.PALLAS,
    "JUNO": swe.JUNO,
    "VESTA": swe.VESTA,
    "EARTH": swe.EARTH,
}

_PLANET_DISPLAY: dict[str, str] = {
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


def _build_position(planet_name: str, result: PlanetResult) -> PlanetPosition:
    """Build PlanetPosition from swisseph PlanetResult."""
    longitude = result.longitude
    speed = result.speed_long
    sign, sign_num, deg_in_sign, minute, second = degree_to_sign(longitude)

    return PlanetPosition(
        planet=planet_name,
        name=_PLANET_DISPLAY.get(planet_name, planet_name),
        longitude=round(longitude, 6),
        latitude=round(result.latitude, 6),
        distance=round(result.distance, 8),
        sign=sign,
        sign_num=sign_num,
        degree_in_sign=round(deg_in_sign, 6),
        degree_minute=minute,
        degree_second=second,
        speed=round(speed, 6),
        retrograde=is_retrograde(_PLANET_MAP[planet_name], speed),
    )


router = APIRouter()


@router.post("/planets", response_model=PlanetResponse)
async def get_planets(req: PlanetRequest) -> PlanetResponse:
    """Calculate ecliptic positions for one or more planets."""
    validate_lat_lon(req.latitude, req.longitude)

    requested = req.planets if req.planets else ALL_PLANETS
    invalid = [p for p in requested if p not in _PLANET_MAP]
    if invalid:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown planet(s): {invalid}. Valid: {list(_PLANET_MAP.keys())}",
        )

    try:
        jd_ut = parse_iso_with_tz(req.datetime, req.timezone)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Invalid datetime/timezone: {e}")

    ayanamsa_const = get_ayanamsa_constant(req.ayanamsa)

    core = get_swiss_core()

    def _calc_all() -> list[PlanetPosition]:
        return [
            _build_position(
                planet_name,
                core.calc_planet(
                    _PLANET_MAP[planet_name],
                    jd_ut,
                    sidereal_ayanamsa=ayanamsa_const,
                ),
            )
            for planet_name in requested
        ]

    def _houses_asc_mc() -> tuple[float, float]:
        h = core.houses(jd_ut, req.latitude, req.longitude, req.house_system.value)
        return h.ascmc[0], h.ascmc[1]

    positions, (ascendant, medium_coeli) = await asyncio.gather(
        asyncio.to_thread(_calc_all),
        asyncio.to_thread(_houses_asc_mc),
    )

    ayanamsa_value = await asyncio.to_thread(get_ayanamsa_value, jd_ut, ayanamsa_const)

    return PlanetResponse(
        request=req,
        julian_day_ut=round(jd_ut, 9),
        ascendant=round(ascendant, 6),
        medium_coeli=round(medium_coeli, 6),
        ayanamsa_name=req.ayanamsa,
        ayanamsa_value=round(ayanamsa_value, 6),
        positions=list(positions),
    )
