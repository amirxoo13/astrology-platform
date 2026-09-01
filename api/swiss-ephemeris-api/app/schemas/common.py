from pydantic import BaseModel, Field
from enum import Enum


class AyanamsaEnum(str, Enum):
    TROPICAL = "TROPICAL"
    LAHIRI = "LAHIRI"
    KRISHNAMURTI = "KRISHNAMURTI"
    DE_LUCE = "DE_LUCE"
    RAMAN = "RAMAN"
    USHA_SHASTHRA = "USHA_SHASTHRA"
    YUKTESHWAR = "YUKTESHWAR"
    SURYASIDDHANTA = "SURYASIDDHANTA"
    GALCENT_0SAG = "GALCENT_0SAG"
    SS_CITRA = "SS_CITRA"
    SS_REVATI = "SS_REVATI"


class HouseSystemEnum(str, Enum):
    # Official codes from Swiss Ephemeris (astro.com swephprg.htm §15):
    # 'P' Placidus, 'K' Koch, 'W' Whole Sign,
    # 'E' or 'A' Equal (cusp 1 = Ascendant),
    # 'N' Equal/1=Aries (cusp 1 = 0° Aries),
    # 'D' Equal/MC (cusp 10 = MC),
    # 'O' Porphyrius, 'R' Regiomontanus, 'C' Campanus,
    # 'B' Alcabitius, 'M' Morinus,
    # 'V' Vehlow equal (Ascendant in middle of house 1),
    # 'G' Gauquelin sectors.
    # Note: Koch ('K') and Gauquelin ('G') cannot be computed beyond polar circle.
    PLACIDUS = "P"
    KOCH = "K"
    WHOLE_SIGN = "W"
    EQUAL = "E"
    PORPHYRIUS = "O"
    REGIOMONTANUS = "R"
    CAMPANUS = "C"
    ALCABITIUS = "B"
    MORINUS = "M"


class DateTimeInput(BaseModel):
    datetime: str = Field(..., description="ISO 8601 datetime string, e.g. 1990-01-15T12:00:00")
    timezone: str = Field(..., description="IANA timezone name, e.g. Asia/Ho_Chi_Minh")


class GeoLocation(BaseModel):
    latitude: float = Field(..., ge=-90, le=90, description="Geographic latitude in degrees")
    longitude: float = Field(..., ge=-180, le=180, description="Geographic longitude in degrees")


class BaseResponse(BaseModel):
    license: str = "AGPL-3.0-or-later"


class ErrorResponse(BaseModel):
    error: str
    detail: str
    code: str
