import asyncio
import swisseph as swe

from fastapi import APIRouter, HTTPException

from app.schemas.lunar_phase import (
    LunarPhaseRequest,
    LunarPhaseResponse,
    LunarPhaseData,
)
from app.services.lunar_phase import phase_angle_to_name, calculate_lunar_age_days
from app.utils.datetime_utils import parse_iso_with_tz


router = APIRouter()


@router.post("/lunar-phase", response_model=LunarPhaseResponse)
async def get_lunar_phase(req: LunarPhaseRequest) -> LunarPhaseResponse:
    """Calculate lunar phase, illumination, elongation, and age at a given datetime."""
    try:
        jd_ut = parse_iso_with_tz(req.datetime, req.timezone)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Invalid datetime/timezone: {e}")

    def _calc() -> LunarPhaseData:
        # pysweph uses pheno_ut(MOON) instead of lun_phase
        # attr[0] = phase_angle (0-360, 0=new moon, 180=full moon)
        # attr[1] = illumination fraction (0-1)
        # attr[2] = elongation (degrees, angular distance Sun-Moon)
        attrs = swe.pheno_ut(jd_ut, swe.MOON, swe.FLG_SWIEPH)
        phase_angle = attrs[0]
        illumination = attrs[1] * 100.0  # fraction → percentage
        elongation = attrs[2]
        phase_name = phase_angle_to_name(phase_angle)
        age_days = calculate_lunar_age_days(phase_angle)
        return LunarPhaseData(
            phase=phase_name,
            phase_angle=round(phase_angle, 6),
            illumination=round(illumination, 4),
            elongation=round(elongation, 6),
            age_days=round(age_days, 4),
        )

    phase = await asyncio.to_thread(_calc)

    return LunarPhaseResponse(
        request=req,
        julian_day_ut=round(jd_ut, 9),
        phase=phase,
    )
