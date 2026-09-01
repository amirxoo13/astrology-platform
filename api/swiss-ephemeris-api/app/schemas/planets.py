from pydantic import BaseModel, Field
from enum import Enum
from app.schemas.common import BaseResponse, HouseSystemEnum


class PlanetEnum(str, Enum):
    SUN = "SUN"
    MOON = "MOON"
    MERCURY = "MERCURY"
    VENUS = "VENUS"
    MARS = "MARS"
    JUPITER = "JUPITER"
    SATURN = "SATURN"
    URANUS = "URANUS"
    NEPTUNE = "NEPTUNE"
    PLUTO = "PLUTO"
    CHIRON = "CHIRON"
    CERES = "CERES"
    PALLAS = "PALLAS"
    JUNO = "JUNO"
    VESTA = "VESTA"
    EARTH = "EARTH"


ALL_PLANETS = [
    "SUN", "MOON", "MERCURY", "VENUS", "MARS",
    "JUPITER", "SATURN", "URANUS", "NEPTUNE", "PLUTO",
    "CHIRON", "CERES", "PALLAS", "JUNO", "VESTA",
]


class PlanetPosition(BaseModel):
    planet: str
    name: str
    longitude: float = Field(..., description="Ecliptic longitude in degrees (0-360)")
    latitude: float = Field(..., description="Ecliptic latitude in degrees")
    distance: float = Field(..., description="Distance in AU")
    sign: str = Field(..., description="Zodiac sign name, e.g. ARIES, TAURUS")
    sign_num: int = Field(..., ge=0, le=11, description="Sign number 0=Aries .. 11=Pisces")
    degree_in_sign: float = Field(..., ge=0, lt=30, description="Degrees within sign (0-29.999)")
    degree_minute: int = Field(..., ge=0, le=59, description="Minute of arc")
    degree_second: int = Field(..., ge=0, le=59, description="Second of arc")
    speed: float = Field(..., description="Daily speed in degrees/day")
    retrograde: bool = Field(..., description="True if planet is retrograde")


class PlanetRequest(BaseModel):
    datetime: str = Field(..., description="ISO 8601 datetime string")
    timezone: str = Field(..., description="IANA timezone name")
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    planets: list[str] = Field(
        default_factory=lambda: ALL_PLANETS,
        description=f"List of planet names. Default: all. Options: {ALL_PLANETS}",
    )
    ayanamsa: str = Field(
        default="TROPICAL",
        description="Ayanamsa (sidereal mode). Default: TROPICAL. Options: TROPICAL, LAHIRI, KRISHNAMURTI, etc.",
    )
    house_system: HouseSystemEnum = Field(
        default=HouseSystemEnum.PLACIDUS,
        description="House system for ascendant/MC calculation. Default: P (Placidus)",
    )


class PlanetResponse(BaseResponse):
    request: PlanetRequest
    julian_day_ut: float = Field(..., description="Julian Day (UT)")
    ascendant: float = Field(..., description="Ascendant longitude in degrees")
    medium_coeli: float = Field(..., description="Medium Coeli (Midheaven) longitude in degrees")
    ayanamsa_name: str
    ayanamsa_value: float = Field(..., description="Current ayanamsa precession value in degrees")
    positions: list[PlanetPosition]
