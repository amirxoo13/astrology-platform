import asyncio
import swisseph as swe

from fastapi import APIRouter, HTTPException

from app.schemas.nodes import (
    SpecialPointsRequest,
    SpecialPointsResponse,
    SpecialPointPosition,
    SpecialPointType,
)
from app.services.zodiac import degree_to_sign
from app.services.swisseph_service import get_ayanamsa_constant, get_ayanamsa_value
from app.utils.datetime_utils import parse_iso_with_tz
from app.utils.geo import validate_lat_lon
from app.utils.houses import house_for_longitude
from app.deps import get_swiss_core


router = APIRouter()


def _part_of_fortune(sun_lon: float, moon_lon: float, asc_lon: float) -> float:
    """
    Calculate the Part of Fortune.
    Diurnal (day birth):  PF = ASC + Moon - Sun
    Nocturnal (night birth): PF = ASC + Sun - Moon
    We use the diurnal formula (most common in modern astrology).
    Returns longitude 0-360.
    """
    return (asc_lon + moon_lon - sun_lon) % 360.0


def _anti_vertex(vertex_lon: float) -> float:
    """Return the Anti-Vertex (180° opposite the Vertex)."""
    return (vertex_lon + 180.0) % 360.0


@router.post("/special-points", response_model=SpecialPointsResponse)
async def get_special_points(req: SpecialPointsRequest) -> SpecialPointsResponse:
    """
    Calculate Part of Fortune, Vertex, and Anti-Vertex.

    - Vertex: via swe.calc_ut(VERTEX)
    - Anti-Vertex: Vertex + 180°
    - Part of Fortune: ASC + Moon − Sun (diurnal formula)
    """
    validate_lat_lon(req.latitude, req.longitude)

    requested_points = req.points if req.points else [
        SpecialPointType.PART_OF_FORTUNE,
        SpecialPointType.VERTEX,
        SpecialPointType.ANTI_VERTEX,
    ]
    invalid = [p for p in requested_points if p not in (
        SpecialPointType.PART_OF_FORTUNE,
        SpecialPointType.VERTEX,
        SpecialPointType.ANTI_VERTEX,
    )]
    if invalid:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown point(s): {invalid}. Valid: PART_OF_FORTUNE, VERTEX, ANTI_VERTEX",
        )

    try:
        jd_ut = parse_iso_with_tz(req.datetime, req.timezone)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Invalid datetime/timezone: {e}")

    ayanamsa_const = get_ayanamsa_constant(req.ayanamsa)
    core = get_swiss_core()

    def _calc() -> SpecialPointsResponse:
        # Houses
        h = core.houses(jd_ut, req.latitude, req.longitude, req.house_system.value)
        ascendant = h.ascmc[0]
        medium_coeli = h.ascmc[1]
        cusps = h.cusps

        # Sun, Moon, and Vertex via core (sidereal-aware)
        sun_result = core.calc_planet(
            swe.SUN, jd_ut, sidereal_ayanamsa=ayanamsa_const,
        )
        moon_result = core.calc_planet(
            swe.MOON, jd_ut, sidereal_ayanamsa=ayanamsa_const,
        )
        vertex_result = core.calc_special(
            swe.VERTEX, jd_ut, sidereal_ayanamsa=ayanamsa_const,
        )

        sun_lon = sun_result.longitude
        moon_lon = moon_result.longitude
        vertex_lon = vertex_result.longitude
        anti_vertex_lon = _anti_vertex(vertex_lon)

        positions = []
        for point in requested_points:
            if point == SpecialPointType.VERTEX:
                lon = vertex_lon
            elif point == SpecialPointType.ANTI_VERTEX:
                lon = anti_vertex_lon
            elif point == SpecialPointType.PART_OF_FORTUNE:
                lon = _part_of_fortune(sun_lon, moon_lon, ascendant)
            else:
                continue

            sign, sign_num, deg, _, _ = degree_to_sign(lon)
            house = house_for_longitude(lon, cusps)
            positions.append(SpecialPointPosition(
                point_type=point,
                longitude=round(lon, 6),
                sign=sign,
                sign_num=sign_num,
                degree_in_sign=round(deg, 6),
                house=house,
            ))

        ayanamsa_val = get_ayanamsa_value(jd_ut, ayanamsa_const)

        return SpecialPointsResponse(
            request=req,
            julian_day_ut=round(jd_ut, 9),
            ascendant=round(ascendant, 6),
            medium_coeli=round(medium_coeli, 6),
            ayanamsa_value=round(ayanamsa_val, 6),
            positions=positions,
        )

    return await asyncio.to_thread(_calc)
