from pydantic import BaseModel, Field
from app.schemas.common import BaseResponse


class EclipseData(BaseModel):
    type: str = Field(..., description="SOLAR or LUNAR")
    date: str = Field(..., description="ISO date of the eclipse")
    julian_day: float
    saros: int | None = None
    magnitude: float | None = None
    visible_from_lat: float | None = None
    visible_from_lon: float | None = None


class EclipseRequest(BaseModel):
    start_date: str = Field(
        default="2020-01-01",
        description="Start date (ISO). Default: 2020-01-01",
    )
    end_date: str = Field(
        default="2030-01-01",
        description="End date (ISO). Default: 2030-01-01",
    )
    type: str = Field(
        default="SOLAR",
        description="Type: SOLAR or LUNAR. Default: SOLAR",
    )
    latitude: float | None = Field(
        default=None,
        ge=-90, le=90,
        description="Observer latitude (optional, for local circumstances)",
    )
    longitude: float | None = Field(
        default=None,
        ge=-180, le=180,
        description="Observer longitude (optional, for local circumstances)",
    )


class EclipseResponse(BaseResponse):
    request: EclipseRequest
    eclipses: list[EclipseData]
