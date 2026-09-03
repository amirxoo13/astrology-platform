"""
Birth time validation, parsing, and LMT (Local Mean Time) handling.
"""
from datetime import datetime, timezone, timedelta
import logging

logger = logging.getLogger(__name__)


class BirthTimeError(ValueError):
    """Raised when birth date or time input is invalid."""


def validate_date(date_str):
    """
    Validate date string in YYYY-MM-DD format.
    Returns the validated date string.
    Raises BirthTimeError if invalid.
    """
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
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
        datetime.strptime(time_str, '%H:%M')
        return time_str
    except ValueError:
        raise BirthTimeError(
            "❌ فرمت زمان اشتباه است.\n"
            "لطفاً از فرمت HH:MM استفاده کنید.\n"
            "مثال: 11:30"
        )


def format_datetime_for_api(date_str, time_str):
    """
    Format date and time for API consumption.
    Returns ISO datetime string: YYYY-MM-DDTHH:MM:00
    """
    return f"{date_str}T{time_str}:00"


def calculate_lmt_offset(longitude):
    """
    Calculate Local Mean Time offset from longitude.
    LMT offset = longitude / 15 degrees per hour.
    Returns offset in hours (float).
    """
    return longitude / 15.0


def resolve_birth_utc(date_str, time_str, timezone_name, longitude):
    """
    Resolve birth datetime to UTC, handling LMT (Local Mean Time).
    
    When timezone_name is 'LMT', calculates offset from longitude.
    Otherwise uses the provided timezone.
    
    Returns dict with:
        - datetime: ISO string for API
        - timezone: resolved timezone name
        - utc_offset_hours: offset in hours
        - is_lmt: whether LMT was used
        - dst_fold: 0 or 1 (for DST ambiguity)
        - dst_gap: True if time falls in DST gap
    """
    result = {
        'datetime': format_datetime_for_api(date_str, time_str),
        'timezone': timezone_name,
        'utc_offset_hours': 0,
        'is_lmt': False,
        'dst_fold': 0,
        'dst_gap': False
    }
    
    if timezone_name.upper() == 'LMT':
        # Local Mean Time from longitude
        offset_hours = calculate_lmt_offset(longitude)
        result['timezone'] = 'LMT'
        result['utc_offset_hours'] = offset_hours
        result['is_lmt'] = True
        logger.info(f"Using LMT: offset {offset_hours:.4f} hours from longitude {longitude}")
    else:
        # Standard timezone
        # Note: DST fold/gap detection would require pytz or zoneinfo
        # For now, just pass through the timezone name
        result['timezone'] = timezone_name
        logger.info(f"Using timezone: {timezone_name}")
    
    return result
