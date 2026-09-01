import swisseph as swe
from datetime import datetime

from fastapi import APIRouter, HTTPException

from app.schemas.eclipses import EclipseRequest, EclipseResponse, EclipseData
from app.services.eclipses import find_eclipses_in_range


router = APIRouter()


@router.get("/eclipses", response_model=EclipseResponse)
async def get_eclipses(
    start_date: str = "2020-01-01",
    end_date: str = "2030-01-01",
    type: str = "SOLAR",
    latitude: float | None = None,
    longitude: float | None = None,
) -> EclipseResponse:
    """Find all eclipses of the given type within a date range."""
    if type not in ("SOLAR", "LUNAR"):
        raise HTTPException(status_code=422, detail="type must be SOLAR or LUNAR")

    try:
        dt_start = datetime.fromisoformat(start_date)
        dt_end = datetime.fromisoformat(end_date)
        jd_start = swe.julday(dt_start.year, dt_start.month, dt_start.day, 0.0, swe.GREG_CAL)
        jd_end = swe.julday(dt_end.year, dt_end.month, dt_end.day, 0.0, swe.GREG_CAL)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Invalid date format: {e}")

    req = EclipseRequest(
        start_date=start_date,
        end_date=end_date,
        type=type,
        latitude=latitude,
        longitude=longitude,
    )

    raw_eclipses = find_eclipses_in_range(jd_start, jd_end, type, latitude, longitude)
    eclipses = [EclipseData(**e) for e in raw_eclipses]

    return EclipseResponse(request=req, eclipses=eclipses)
