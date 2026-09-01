from pydantic import BaseModel, Field
from app.schemas.common import BaseResponse, HouseSystemEnum


class HouseData(BaseModel):
    house: int = Field(..., ge=1, le=12, description="House number (1=Cusp I ... 12=Cusp XII)")
    cusp: float = Field(..., description="House cusp longitude in degrees (0-360)")
    sign: str = Field(..., description="Zodiac sign of the cusp")
    sign_num: int = Field(..., ge=0, le=11)
    degree_in_sign: float = Field(..., ge=0, lt=30)
    element: str = Field(..., description="Element: FIRE, EARTH, AIR, or WATER")


class HouseRequest(BaseModel):
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


class HouseResponse(BaseResponse):
    request: HouseRequest
    julian_day_ut: float
    ascendant: float
    medium_coeli: float
    ayanamsa_value: float
    houses: list[HouseData]
