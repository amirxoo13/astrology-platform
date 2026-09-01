import asyncio

from fastapi import APIRouter, HTTPException

from app.schemas.houses import HouseRequest, HouseResponse, HouseData
from app.services.zodiac import degree_to_sign, get_element
from app.services.swisseph_service import get_ayanamsa_constant, get_ayanamsa_value
from app.utils.datetime_utils import parse_iso_with_tz
from app.utils.geo import validate_lat_lon
from app.deps import get_swiss_core


router = APIRouter()


@router.post("/houses", response_model=HouseResponse)
async def get_houses(req: HouseRequest) -> HouseResponse:
    """Calculate house cusps and ASC/MC."""
    validate_lat_lon(req.latitude, req.longitude)

    try:
        jd_ut = parse_iso_with_tz(req.datetime, req.timezone)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Invalid datetime/timezone: {e}")

    ayanamsa_const = get_ayanamsa_constant(req.ayanamsa)

    core = get_swiss_core()

    def _calc() -> tuple[list[HouseData], float, float, float]:
        result = core.houses(jd_ut, req.latitude, req.longitude, req.house_system.value)
        ascendant = result.ascmc[0]
        medium_coeli = result.ascmc[1]
        ayanamsa_val = get_ayanamsa_value(jd_ut, ayanamsa_const)

        houses = []
        for i, cusp in enumerate(result.cusps, start=1):
            sign, sign_num, deg_in_sign, minute, second = degree_to_sign(cusp)
            houses.append(HouseData(
                house=i,
                cusp=round(cusp, 6),
                sign=sign,
                sign_num=sign_num,
                degree_in_sign=round(deg_in_sign, 6),
                element=get_element(sign_num),
            ))
        return houses, ascendant, medium_coeli, ayanamsa_val

    houses, ascendant, medium_coeli, ayanamsa_value = await asyncio.to_thread(_calc)

    return HouseResponse(
        request=req,
        julian_day_ut=round(jd_ut, 9),
        ascendant=round(ascendant, 6),
        medium_coeli=round(medium_coeli, 6),
        ayanamsa_value=round(ayanamsa_value, 6),
        houses=houses,
    )
