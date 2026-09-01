from pydantic import BaseModel, Field
from app.schemas.common import BaseResponse, HouseSystemEnum
from app.schemas.planets import PlanetPosition
from app.schemas.houses import HouseData


class BirthChartRequest(BaseModel):
    datetime: str = Field(..., description="ISO 8601 datetime string")
    timezone: str = Field(..., description="IANA timezone name")
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    house_system: HouseSystemEnum = Field(
        default=HouseSystemEnum.PLACIDUS,
        description="House system. Default: P (Placidus)",
    )
    ayanamsa: str = Field(
        default="TROPICAL",
        description="Ayanamsa for sidereal mode",
    )
    include_planets: bool = Field(
        default=True,
        description="Whether to include planet positions. Default: True",
    )


class BirthChartResponse(BaseResponse):
    request: BirthChartRequest
    julian_day_ut: float
    ascendant: float
    medium_coeli: float
    ayanamsa_name: str
    ayanamsa_value: float
    positions: list[PlanetPosition]
    houses: list[HouseData]
