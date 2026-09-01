import asyncio

from fastapi import APIRouter, HTTPException

from app.schemas.nodes import (
    NodesRequest,
    NodesResponse,
    LunarNodePosition,
    LilithPosition,
    LunarNodeType,
    LilithType,
)
from app.services.zodiac import degree_to_sign
from app.services.swisseph_service import get_ayanamsa_constant, get_ayanamsa_value
from app.utils.datetime_utils import parse_iso_with_tz
from app.utils.geo import validate_lat_lon
from app.utils.houses import house_for_longitude
from app.deps import get_swiss_core


router = APIRouter()


@router.post("/lunar-nodes", response_model=NodesResponse)
async def get_lunar_nodes(req: NodesRequest) -> NodesResponse:
    """
    Calculate North/South Lunar Nodes and Lilith (Black Moon),
    including house placements and sidereal mode support.

    North Node = swe.TRUE_NODE or swe.MEAN_NODE via swe.calc_ut + FLG_SPEED.
    South Node = North Node + 180°.
    Lilith = apogee of Moon's orbit via swe.nod_aps with NODBIT_FOPOINT.
    """
    validate_lat_lon(req.latitude, req.longitude)

    try:
        jd_ut = parse_iso_with_tz(req.datetime, req.timezone)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Invalid datetime/timezone: {e}")

    ayanamsa_const = get_ayanamsa_constant(req.ayanamsa)
    core = get_swiss_core()

    def _calc() -> NodesResponse:
        # Houses
        h = core.houses(jd_ut, req.latitude, req.longitude, req.house_system.value)
        ascendant = h.ascmc[0]
        medium_coeli = h.ascmc[1]
        cusps = h.cusps

        # North and South Nodes via core (sidereal-aware)
        north_result, south_result = core.calc_nodes(
            jd_ut,
            true=(req.node_type == LunarNodeType.TRUE),
            sidereal_ayanamsa=ayanamsa_const,
        )
        north_lon = north_result.longitude
        north_speed = north_result.speed_long
        south_lon = south_result.longitude
        south_speed = south_result.speed_long

        north_sign, north_sign_num, north_deg, north_min, north_sec = degree_to_sign(north_lon)
        south_sign, south_sign_num, south_deg, south_min, south_sec = degree_to_sign(south_lon)

        # Lilith via core (sidereal-aware)
        lilith_result = core.calc_lilith(
            jd_ut,
            true=(req.lilith_type == LilithType.TRUE),
            sidereal_ayanamsa=ayanamsa_const,
        )
        lilith_lon = lilith_result.longitude
        lilith_speed = lilith_result.speed_long
        lilith_sign, lilith_sign_num, lilith_deg, lilith_min, lilith_sec = degree_to_sign(lilith_lon)

        # House placements
        north_house = house_for_longitude(north_lon, cusps)
        south_house = house_for_longitude(south_lon, cusps)
        lilith_house = house_for_longitude(lilith_lon, cusps)

        ayanamsa_val = get_ayanamsa_value(jd_ut, ayanamsa_const)

        north_node = LunarNodePosition(
            node_type=req.node_type,
            north_longitude=round(north_lon, 6),
            south_longitude=round(south_lon, 6),
            north_sign=north_sign,
            north_sign_num=north_sign_num,
            north_degree_in_sign=round(north_deg, 6),
            north_speed=round(north_speed, 6),
            north_retrograde=north_speed < 0,
            south_sign=south_sign,
            south_sign_num=south_sign_num,
            south_degree_in_sign=round(south_deg, 6),
            north_house=north_house,
            south_house=south_house,
        )

        lilith_pos = LilithPosition(
            lilith_type=req.lilith_type,
            longitude=round(lilith_lon, 6),
            sign=lilith_sign,
            sign_num=lilith_sign_num,
            degree_in_sign=round(lilith_deg, 6),
            speed=round(lilith_speed, 6),
            retrograde=lilith_speed < 0,  # Lilith is slow-moving; speed < 0 = retrograde
            house=lilith_house,
        )

        return NodesResponse(
            request=req,
            julian_day_ut=round(jd_ut, 9),
            ascendant=round(ascendant, 6),
            medium_coeli=round(medium_coeli, 6),
            ayanamsa_value=round(ayanamsa_val, 6),
            north_node=north_node,
            lilith=lilith_pos,
        )

    return await asyncio.to_thread(_calc)
