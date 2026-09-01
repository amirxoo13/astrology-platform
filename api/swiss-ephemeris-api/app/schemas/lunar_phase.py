from pydantic import BaseModel, Field
from app.schemas.common import BaseResponse


class LunarPhaseData(BaseModel):
    phase: str = Field(..., description="Phase name: NEW, WAXING_CRESCENT, FIRST_QUARTER, WAXING_GIBBOUS, FULL, WANING_GIBBOUS, LAST_QUARTER, WANING_CRESCENT")
    phase_angle: float = Field(..., description="Phase angle in degrees (0-360)")
    illumination: float = Field(..., ge=0, le=100, description="Illumination percentage (0-100)")
    elongation: float = Field(..., description="Elongation from Sun in degrees")
    age_days: float = Field(..., description="Lunar age in days")


class LunarPhaseRequest(BaseModel):
    datetime: str = Field(..., description="ISO 8601 datetime string")
    timezone: str = Field(..., description="IANA timezone name")


class LunarPhaseResponse(BaseResponse):
    request: LunarPhaseRequest
    julian_day_ut: float
    phase: LunarPhaseData
