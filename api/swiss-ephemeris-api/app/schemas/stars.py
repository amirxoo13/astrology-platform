from pydantic import BaseModel, Field
from app.schemas.common import BaseResponse


class FixedStarPosition(BaseModel):
    star: str
    longitude: float
    latitude: float
    sign: str
    sign_num: int
    degree_in_sign: float
    magnitude: float | None = None


class FixedStarRequest(BaseModel):
    datetime: str = Field(..., description="ISO 8601 datetime string")
    timezone: str = Field(..., description="IANA timezone name")
    stars: list[str] | None = Field(
        default=None,
        description="List of star names (e.g. Sirius, Polaris). If null, returns all 30 stars.",
    )


class FixedStarResponse(BaseResponse):
    request: FixedStarRequest
    julian_day_ut: float
    positions: list[FixedStarPosition]
