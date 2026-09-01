from enum import Enum
from pydantic import BaseModel, Field

from app.schemas.common import BaseResponse


class AspectNameEnum(str, Enum):
    CONJUNCTION = "CONJUNCTION"
    OPPOSITION = "OPPOSITION"
    TRINE = "TRINE"
    SQUARE = "SQUARE"
    SEXTILE = "SEXTILE"
    SEMI_SEXTILE = "SEMI_SEXTILE"
    SEMI_SQUARE = "SEMI_SQUARE"
    SESQUIQUADRATE = "SESQUIQUADRATE"
    QUINTILE = "QUINTILE"
    BIQUINTILE = "BIQUINTILE"
    TREdecILE = "TREDEGILE"


# Standard major aspects: conjunction through sextile only
_STANDARD_MAJOR = ["CONJUNCTION", "OPPOSITION", "TRINE", "SQUARE", "SEXTILE"]
_ALL_ASPECTS = [
    "CONJUNCTION", "OPPOSITION", "TRINE", "SQUARE", "SEXTILE",
    "SEMI_SEXTILE", "SEMI_SQUARE", "SESQUIQUADRATE",
    "QUINTILE", "BIQUINTILE", "TREDEGILE",
]


class AspectOrb(str, Enum):
    CONJUNCTION = "CONJUNCTION"
    OPPOSITION = "OPPOSITION"
    TRINE = "TRINE"
    SQUARE = "SQUARE"
    SEXTILE = "SEXTILE"
    SEMI_SEXTILE = "SEMI_SEXTILE"
    SEMI_SQUARE = "SEMI_SQUARE"
    SESQUIQUADRATE = "SESQUIQUADRATE"
    QUINTILE = "QUINTILE"
    BIQUINTILE = "BIQUINTILE"
    TREDEGILE = "TREDEGILE"


_ASPECT_DEGREES: dict[str, float] = {
    "CONJUNCTION": 0.0,
    "OPPOSITION": 180.0,
    "TRINE": 120.0,
    "SQUARE": 90.0,
    "SEXTILE": 60.0,
    "SEMI_SEXTILE": 30.0,
    "SEMI_SQUARE": 45.0,
    "SESQUIQUADRATE": 135.0,
    "QUINTILE": 72.0,
    "BIQUINTILE": 144.0,
    "TREDEGILE": 108.0,
}

# Default orb widths per aspect type (degrees)
_DEFAULT_ORBS: dict[str, float] = {
    "CONJUNCTION": 10.0,
    "OPPOSITION": 10.0,
    "TRINE": 8.0,
    "SQUARE": 8.0,
    "SEXTILE": 6.0,
    "SEMI_SEXTILE": 4.0,
    "SEMI_SQUARE": 4.0,
    "SESQUIQUADRATE": 4.0,
    "QUINTILE": 4.0,
    "BIQUINTILE": 4.0,
    "TREDEGILE": 3.0,
}


def aspect_ideal_degree(name: str) -> float:
    return _ASPECT_DEGREES[name]


def default_orb(name: str) -> float:
    return _DEFAULT_ORBS.get(name, 4.0)


def normalize_angle(angle: float) -> float:
    """Normalize angle to 0–360 range."""
    return angle % 360.0


def angular_distance(a: float, b: float) -> float:
    """Shortest angular distance between two longitudes (0–180)."""
    diff = abs(normalize_angle(a) - normalize_angle(b))
    return min(diff, 360.0 - diff)


class AspectsRequest(BaseModel):
    datetime: str = Field(..., description="ISO 8601 datetime string")
    timezone: str = Field(..., description="IANA timezone name")
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    planets: list[str] = Field(
        default_factory=lambda: ["SUN", "MOON", "MERCURY", "VENUS", "MARS",
                                "JUPITER", "SATURN", "URANUS", "NEPTUNE", "PLUTO",
                                "CERES", "PALLAS", "JUNO", "VESTA"],
        description="List of planet names to check for aspects. Default: all except Earth.",
    )
    include_minor: bool = Field(
        default=False,
        description="Include minor aspects (semi-sextile, semi-square, sesquiquadrate, quintile, biquintile, tredegile). Default: False.",
    )


class AspectData(BaseModel):
    planet1: str = Field(..., description="First planet")
    planet2: str = Field(..., description="Second planet")
    aspect_name: str = Field(..., description="Aspect type (e.g. CONJUNCTION, TRINE)")
    orb: float = Field(..., description="Orb in degrees (positive = within orb, negative = exact)")
    exactness: float = Field(
        ...,
        description="How close to exact (degrees away from exact angle)",
    )
    planet1_longitude: float = Field(..., description="Longitude of planet 1")
    planet2_longitude: float = Field(..., description="Longitude of planet 2")


class AspectsResponse(BaseResponse):
    request: AspectsRequest
    julian_day_ut: float
    aspects: list[AspectData] = Field(default_factory=list)
