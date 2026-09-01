from pydantic import BaseModel, Field
from enum import Enum
from app.schemas.common import BaseResponse, HouseSystemEnum


# ─── Enums ────────────────────────────────────────────────────────────────────

class LunarNodeType(str, Enum):
    """Type of lunar node calculation."""
    TRUE = "TRUE"
    MEAN = "MEAN"


class LilithType(str, Enum):
    """Type of Lilith (Black Moon) calculation."""
    TRUE = "TRUE"   # True Lilith: apogee of Moon's orbit
    MEAN = "MEAN"   # Mean Lilith: mean apogee


class SpecialPointType(str, Enum):
    """Special derived points."""
    PART_OF_FORTUNE = "PART_OF_FORTUNE"
    VERTEX = "VERTEX"
    ANTI_VERTEX = "ANTI_VERTEX"


# ─── Shared input ──────────────────────────────────────────────────────────────

class NodesRequest(BaseModel):
    datetime: str = Field(..., description="ISO 8601 datetime string")
    timezone: str = Field(..., description="IANA timezone name")
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    house_system: HouseSystemEnum = Field(
        default=HouseSystemEnum.PLACIDUS,
        description="House system for planet-in-house placement. Default: P (Placidus)",
    )
    ayanamsa: str = Field(
        default="TROPICAL",
        description="Ayanamsa for sidereal mode",
    )
    node_type: LunarNodeType = Field(
        default=LunarNodeType.TRUE,
        description="TRUE or MEAN lunar node. Default: TRUE",
    )
    lilith_type: LilithType = Field(
        default=LilithType.TRUE,
        description="TRUE or MEAN Lilith. Default: TRUE",
    )


class SpecialPointsRequest(BaseModel):
    datetime: str = Field(..., description="ISO 8601 datetime string")
    timezone: str = Field(..., description="IANA timezone name")
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    house_system: HouseSystemEnum = Field(
        default=HouseSystemEnum.PLACIDUS,
        description="House system for placement. Default: P (Placidus)",
    )
    ayanamsa: str = Field(
        default="TROPICAL",
        description="Ayanamsa for sidereal mode",
    )
    points: list[SpecialPointType] = Field(
        default_factory=lambda: [
            SpecialPointType.PART_OF_FORTUNE,
            SpecialPointType.VERTEX,
            SpecialPointType.ANTI_VERTEX,
        ],
        description="Which points to calculate. Default: all three",
    )


# ─── Position models ─────────────────────────────────────────────────────────

class LunarNodePosition(BaseModel):
    node_type: LunarNodeType
    north_longitude: float = Field(..., description="North (True/Mean) Lunar Node longitude")
    south_longitude: float = Field(..., description="South Lunar Node longitude (180° opposite)")
    north_sign: str
    north_sign_num: int = Field(..., ge=0, le=11)
    north_degree_in_sign: float = Field(..., ge=0, lt=30)
    north_speed: float = Field(..., description="Daily speed in degrees/day")
    north_retrograde: bool = Field(..., description="Always retrograde (negative speed)")
    south_sign: str
    south_sign_num: int = Field(..., ge=0, le=11)
    south_degree_in_sign: float = Field(..., ge=0, lt=30)
    north_house: int | None = Field(None, ge=1, le=12)
    south_house: int | None = Field(None, ge=1, le=12)


class LilithPosition(BaseModel):
    lilith_type: LilithType
    longitude: float
    sign: str
    sign_num: int = Field(..., ge=0, le=11)
    degree_in_sign: float = Field(..., ge=0, lt=30)
    speed: float
    retrograde: bool
    house: int | None = Field(None, ge=1, le=12)


class SpecialPointPosition(BaseModel):
    point_type: SpecialPointType
    longitude: float
    sign: str
    sign_num: int = Field(..., ge=0, le=11)
    degree_in_sign: float = Field(..., ge=0, lt=30)
    house: int | None = Field(None, ge=1, le=12)


# ─── Response models ───────────────────────────────────────────────────────────

class NodesResponse(BaseResponse):
    request: NodesRequest
    julian_day_ut: float
    ascendant: float
    medium_coeli: float
    ayanamsa_value: float
    north_node: LunarNodePosition  # contains both north + south data via north_*/south_* fields
    lilith: LilithPosition


class SpecialPointsResponse(BaseResponse):
    request: SpecialPointsRequest
    julian_day_ut: float
    ascendant: float
    medium_coeli: float
    ayanamsa_value: float
    positions: list[SpecialPointPosition]
