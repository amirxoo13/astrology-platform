"""
Birth time validation, parsing, and Local Mean Time (LMT) handling.

The Swiss Ephemeris API only accepts IANA timezone names (see
app/utils/datetime_utils.py). Passing timezone="LMT" returns HTTP 422.

LMT offset is the standard geographic formula used before civil time zones:

    UTC offset (hours) = longitude_east / 15

When the caller asks for LMT, this module converts the civil clock time to
UTC and returns timezone="UTC" so the API can parse it.
"""
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Civil time zones were adopted country-by-country ~1880–1920. Astrology
# software uses birth-place LMT for dates before 1900 (see project skill).
LMT_YEAR_THRESHOLD = 1900


class BirthTimeError(ValueError):
    """Raised when birth date or time input is invalid."""


def validate_date(date_str):
    """
    Validate date string in YYYY-MM-DD format.
    Returns the validated date string.
    Raises BirthTimeError if invalid.
    """
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return date_str
    except ValueError:
        raise BirthTimeError(
            "❌ فرمت تاریخ اشتباه است.\n"
            "لطفاً از فرمت YYYY-MM-DD استفاده کنید.\n"
            "مثال: 1879-03-14"
        )


def validate_time(time_str):
    """
    Validate time string in HH:MM format.
    Returns the validated time string.
    Raises BirthTimeError if invalid.
    """
    try:
        datetime.strptime(time_str, "%H:%M")
        return time_str
    except ValueError:
        raise BirthTimeError(
            "❌ فرمت زمان اشتباه است.\n"
            "لطفاً از فرمت HH:MM استفاده کنید.\n"
            "مثال: 11:30"
        )


def format_datetime_for_api(date_str, time_str):
    """ISO datetime string: YYYY-MM-DDTHH:MM:00"""
    return f"{date_str}T{time_str}:00"


def calculate_lmt_offset(longitude):
    """Local Mean Time offset from Greenwich, in hours (longitude / 15)."""
    return float(longitude) / 15.0


def should_use_lmt(date_str, timezone_name=None):
    """True when birth-place LMT should be used instead of an IANA zone."""
    if timezone_name and str(timezone_name).upper() == "LMT":
        return True
    try:
        year = datetime.strptime(date_str, "%Y-%m-%d").year
    except ValueError:
        return False
    return year < LMT_YEAR_THRESHOLD


def resolve_birth_utc(date_str, time_str, timezone_name, longitude):
    """
    Build the datetime/timezone pair the Swiss Ephemeris API accepts.

    Returns dict with:
        - datetime: ISO string for API
        - timezone: IANA name (never "LMT")
        - utc_offset_hours: LMT offset when LMT was applied
        - is_lmt: whether LMT conversion was used
    """
    if should_use_lmt(date_str, timezone_name):
        offset_hours = calculate_lmt_offset(longitude)
        local = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        utc = local - timedelta(hours=offset_hours)
        logger.info(
            "Using LMT: offset %.4f hours from longitude %s -> %s UTC",
            offset_hours,
            longitude,
            utc.isoformat(timespec="seconds"),
        )
        return {
            "datetime": utc.strftime("%Y-%m-%dT%H:%M:%S"),
            "timezone": "UTC",
            "utc_offset_hours": offset_hours,
            "is_lmt": True,
            "dst_fold": 0,
            "dst_gap": False,
        }

    tz_name = timezone_name or "UTC"
    logger.info("Using timezone: %s", tz_name)
    return {
        "datetime": format_datetime_for_api(date_str, time_str),
        "timezone": tz_name,
        "utc_offset_hours": 0,
        "is_lmt": False,
        "dst_fold": 0,
        "dst_gap": False,
    }
