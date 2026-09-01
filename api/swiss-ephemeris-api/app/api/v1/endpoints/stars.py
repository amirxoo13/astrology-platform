import asyncio
import swisseph as swe

from fastapi import APIRouter, HTTPException

from app.schemas.stars import FixedStarRequest, FixedStarResponse, FixedStarPosition
from app.services.zodiac import degree_to_sign
from app.services.fixed_stars import FIXED_STAR_NAMES
from app.utils.datetime_utils import parse_iso_with_tz


router = APIRouter()


@router.post("/fixed-stars", response_model=FixedStarResponse)
async def get_fixed_stars(req: FixedStarRequest) -> FixedStarResponse:
    """Calculate positions for one or more fixed stars."""
    star_names = req.stars if req.stars else FIXED_STAR_NAMES
    for star in star_names:
        if star not in FIXED_STAR_NAMES:
            raise HTTPException(
                status_code=422,
                detail=f"Unknown star: '{star}'. Valid: {FIXED_STAR_NAMES}",
            )

    try:
        jd_ut = parse_iso_with_tz(req.datetime, req.timezone)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Invalid datetime/timezone: {e}")

    def _calc_stars() -> list[FixedStarPosition]:
        # Cache magnitudes per star (fixstar_mag is a simple catalog lookup, no datetime needed)
        _mag_cache: dict[str, float | None] = {}

        positions = []
        for star in star_names:
            if star not in _mag_cache:
                mag_raw = swe.fixstar_mag(star)
                _mag_cache[star] = round(float(mag_raw[0]), 3) if mag_raw and mag_raw[0] != "" else None
            result = swe.fixstar(star, jd_ut, swe.FLG_SWIEPH)
            lon = result[0][0]
            lat = result[0][1]
            sign, sign_num, deg_in_sign, *_ = degree_to_sign(lon)
            positions.append(FixedStarPosition(
                star=star,
                longitude=round(lon, 6),
                latitude=round(lat, 6),
                sign=sign,
                sign_num=sign_num,
                degree_in_sign=round(deg_in_sign, 6),
                magnitude=_mag_cache[star],
            ))
        return positions

    positions = await asyncio.to_thread(_calc_stars)

    return FixedStarResponse(
        request=req,
        julian_day_ut=round(jd_ut, 9),
        positions=positions,
    )
