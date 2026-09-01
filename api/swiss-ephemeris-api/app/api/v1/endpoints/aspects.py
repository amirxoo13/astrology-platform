import asyncio
import logging

from fastapi import APIRouter, HTTPException

from app.schemas.aspects import (
    AspectsRequest,
    AspectsResponse,
    AspectData,
    _ALL_ASPECTS,
    _STANDARD_MAJOR,
    angular_distance,
    aspect_ideal_degree,
    default_orb,
)
from app.schemas.planets import ALL_PLANETS
from app.utils.datetime_utils import parse_iso_with_tz
from app.utils.geo import validate_lat_lon
from app.deps import get_swiss_core
from app.core.logging_config import app_logger as log


router = APIRouter()


def _find_aspects(positions: dict[str, float], include_minor: bool) -> list[AspectData]:
    """Compute all aspects between planets in the positions dict (name → longitude)."""
    aspect_names = _ALL_ASPECTS if include_minor else _STANDARD_MAJOR
    results: list[AspectData] = []
    planets = list(positions.keys())

    for i, p1 in enumerate(planets):
        for p2 in planets[i + 1:]:
            lon1 = positions[p1]
            lon2 = positions[p2]
            dist = angular_distance(lon1, lon2)

            for aspect_name in aspect_names:
                ideal = aspect_ideal_degree(aspect_name)
                orb = default_orb(aspect_name)
                diff = abs(dist - ideal)

                if diff <= orb:
                    exactness = round(orb - diff, 4)
                    actual_orb = round(orb - diff, 4)
                    results.append(AspectData(
                        planet1=p1,
                        planet2=p2,
                        aspect_name=aspect_name,
                        orb=actual_orb,
                        exactness=exactness,
                        planet1_longitude=round(lon1, 6),
                        planet2_longitude=round(lon2, 6),
                    ))

    results.sort(key=lambda a: (-a.orb))
    return results


@router.post("/aspects", response_model=AspectsResponse)
async def get_aspects(req: AspectsRequest) -> AspectsResponse:
    """Calculate astrological aspects between planets."""
    log.info("aspects_request", planets=req.planets, include_minor=req.include_minor)

    validate_lat_lon(req.latitude, req.longitude)

    invalid = [p for p in req.planets if p not in ALL_PLANETS]
    if invalid:
        log.warning("aspects_unknown_planets", unknown=invalid)
        raise HTTPException(
            status_code=422,
            detail=f"Unknown planet(s): {invalid}. Valid: {ALL_PLANETS}",
        )

    try:
        jd_ut = parse_iso_with_tz(req.datetime, req.timezone)
    except Exception as e:
        log.warning("aspects_datetime_error", error=str(e))
        raise HTTPException(status_code=422, detail=f"Invalid datetime/timezone: {e}")

    core = get_swiss_core()

    def _calc_positions() -> dict[str, float]:
        positions: dict[str, float] = {}
        for planet_name in req.planets:
            try:
                result = core.calc_planet(
                    _PLANET_MAP[planet_name], jd_ut, sidereal_ayanamsa=None
                )
                positions[planet_name] = result.longitude
            except Exception as e:
                log.error("aspects_planet_calc_error", planet=planet_name, error=str(e))
                raise
        return positions

    try:
        positions = await asyncio.to_thread(_calc_positions)
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Swiss Ephemeris failed while calculating planet positions.",
        )

    aspects = _find_aspects(positions, req.include_minor)
    log.info(
        "aspects_result",
        planets_count=len(positions),
        aspects_count=len(aspects),
    )

    return AspectsResponse(
        request=req,
        julian_day_ut=round(jd_ut, 9),
        aspects=aspects,
    )


# Planet name -> swe constant (same as in planets.py, copied here to avoid circular imports)
_PLANET_MAP: dict[str, int] = {
    "SUN": 0, "MOON": 1, "MERCURY": 2, "VENUS": 3, "MARS": 4,
    "JUPITER": 5, "SATURN": 6, "URANUS": 7, "NEPTUNE": 8, "PLUTO": 9,
    "CHIRON": 15, "CERES": 1, "PALLAS": 2, "JUNO": 3, "VESTA": 4,
}
