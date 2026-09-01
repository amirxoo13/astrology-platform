import swisseph as swe
from datetime import datetime, timezone
from dateutil import parser as dtparser
import zoneinfo


TIMEZONE_ALIASES = {
    # Historical IANA links are not always available in minimal runtime images.
    "Asia/Saigon": "Asia/Ho_Chi_Minh",
    "Europe/Kiev": "Europe/Kyiv",
}


def get_timezone(tz_name: str) -> zoneinfo.ZoneInfo:
    """Return a ZoneInfo, accepting common historical IANA aliases."""
    canonical_name = TIMEZONE_ALIASES.get(tz_name, tz_name)
    try:
        return zoneinfo.ZoneInfo(canonical_name)
    except Exception:
        raise ValueError(f"Invalid timezone: {tz_name!r}") from None


def datetime_to_jd(dt_utc: datetime) -> float:
    """
    Convert a timezone-aware (or naive UTC) datetime to Julian Day (UT).
    - Naive datetime is treated as UTC.
    - Aware datetime is converted to UTC first.
    """
    if dt_utc.tzinfo is None:
        dt_utc = dt_utc.replace(tzinfo=timezone.utc)
    else:
        dt_utc = dt_utc.astimezone(timezone.utc)

    return swe.julday(
        dt_utc.year,
        dt_utc.month,
        dt_utc.day,
        dt_utc.hour + dt_utc.minute / 60.0 + dt_utc.second / 3600.0,
        swe.GREG_CAL,
    )


def parse_iso_with_tz(datetime_str: str, tz_name: str) -> float:
    """
    Parse an ISO 8601 datetime string in the given IANA timezone,
    then return Julian Day (UT).
    Raises ValueError if the timezone is invalid.
    """
    dt_naive = dtparser.parse(datetime_str)
    tz = get_timezone(tz_name)
    dt_aware = dt_naive.replace(tzinfo=tz)
    return datetime_to_jd(dt_aware)


def jd_to_iso(jd_ut: float) -> str:
    """Convert Julian Day (UT) to ISO 8601 datetime string in UTC."""
    year, month, day, hour = swe.revjul(jd_ut, swe.GREG_CAL)
    hour_int = int(hour)
    minute_int = int((hour - hour_int) * 60)
    second_int = int((((hour - hour_int) * 60) - minute_int) * 60)
    dt_utc = datetime(year, month, day, hour_int, minute_int, second_int, tzinfo=timezone.utc)
    return dt_utc.isoformat().replace("+00:00", "Z")
