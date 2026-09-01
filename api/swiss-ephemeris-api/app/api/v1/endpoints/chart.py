import asyncio
import swisseph as swe

from fastapi import APIRouter, HTTPException

from app.schemas.chart import BirthChartRequest, BirthChartResponse
from app.schemas.planets import PlanetPosition, ALL_PLANETS
from app.schemas.houses import HouseData
from app.services.zodiac import degree_to_sign, get_element
from app.services.swisseph_service import is_retrograde, get_ayanamsa_constant, get_ayanamsa_value
from app.utils.datetime_utils import parse_iso_with_tz
from app.utils.geo import validate_lat_lon
from app.deps import get_swiss_core


_PLANET_MAP = {
    k.upper(): getattr(swe, k.upper()) for k in
    ["SUN", "MOON", "MERCURY", "VENUS", "MARS", "JUPITER",
     "SATURN", "URANUS", "NEPTUNE", "PLUTO", "CHIRON",
     "CERES", "PALLAS", "JUNO", "VESTA", "EARTH"]
}

_PLANET_DISPLAY = {
    "SUN": "Sun", "MOON": "Moon", "MERCURY": "Mercury",
    "VENUS": "Venus", "MARS": "Mars", "JUPITER": "Jupiter",
    "SATURN": "Saturn", "URANUS": "Uranus", "NEPTUNE": "Neptune",
    "PLUTO": "Pluto", "CHIRON": "Chiron", "CERES": "Ceres",
    "PALLAS": "Pallas", "JUNO": "Juno", "VESTA": "Vesta", "EARTH": "Earth",
}


router = APIRouter()


def _build_position(planet_name: str, result) -> PlanetPosition:
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


@router.post("/birth-chart", response_model=BirthChartResponse)
async def get_birth_chart(req: BirthChartRequest) -> BirthChartResponse:
    """Combined planet positions + house cusps + ASC/MC in one call."""
    validate_lat_lon(req.latitude, req.longitude)

    try:
        jd_ut = parse_iso_with_tz(req.datetime, req.timezone)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Invalid datetime/timezone: {e}")

    ayanamsa_const = get_ayanamsa_constant(req.ayanamsa)

    core = get_swiss_core()

    def _calc_all() -> tuple[list[PlanetPosition], list[HouseData], float, float]:
        # Houses
        h = core.houses(jd_ut, req.latitude, req.longitude, req.house_system.value)
        ascendant = h.ascmc[0]
        medium_coeli = h.ascmc[1]

        houses: list[HouseData] = []
        for i, cusp in enumerate(h.cusps, start=1):
            sign, sign_num, deg_in_sign, minute, second = degree_to_sign(cusp)
            houses.append(HouseData(
                house=i,
                cusp=round(cusp, 6),
                sign=sign,
                sign_num=sign_num,
                degree_in_sign=round(deg_in_sign, 6),
                element=get_element(sign_num),
            ))

        # Planets
        positions = []
        if req.include_planets:
            for planet_name in ALL_PLANETS:
                r = core.calc_planet(
                    _PLANET_MAP[planet_name],
                    jd_ut,
                    sidereal_ayanamsa=ayanamsa_const,
                )
                positions.append(_build_position(planet_name, r))

        return positions, houses, ascendant, medium_coeli

    positions, houses, ascendant, medium_coeli = await asyncio.to_thread(_calc_all)

    ayanamsa_value = await asyncio.to_thread(get_ayanamsa_value, jd_ut, ayanamsa_const)

    return BirthChartResponse(
        request=req,
        julian_day_ut=round(jd_ut, 9),
        ascendant=round(ascendant, 6),
        medium_coeli=round(medium_coeli, 6),
        ayanamsa_name=req.ayanamsa,
        ayanamsa_value=round(ayanamsa_value, 6),
        positions=positions,
        houses=houses,
    )
