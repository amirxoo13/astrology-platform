PHASE_NAMES = [
    "NEW",
    "WAXING_CRESCENT",
    "FIRST_QUARTER",
    "WAXING_GIBBOUS",
    "FULL",
    "WANING_GIBBOUS",
    "LAST_QUARTER",
    "WANING_CRESCENT",
]
SYZIGY_THRESHOLD = 90.0  # degrees — near 0, 90, 180, 270 = syzygy events


def phase_angle_to_name(phase_angle: float) -> str:
    """
    Map phase angle (0-360) to phase name.
    phase_angle 0-44   = NEW (New Moon)
    phase_angle 45-89   = WAXING_CRESCENT
    phase_angle 90-134  = FIRST_QUARTER
    phase_angle 135-179 = WAXING_GIBBOUS
    phase_angle 180-224 = FULL (Full Moon)
    phase_angle 225-269 = WANING_GIBBOUS
    phase_angle 270-314 = LAST_QUARTER
    phase_angle 315-359 = WANING_CRESCENT
    phase_angle 360     = NEW (New Moon again)
    """
    normalized = phase_angle % 360
    index = int(normalized / 45.0) % 8
    return PHASE_NAMES[index]


def calculate_lunar_age_days(phase_angle: float) -> float:
    """
    Convert phase_angle (0-360) to approximate lunar age in days.
    Mean lunar cycle ≈ 29.530588 days.
    """
    return (phase_angle / 360.0) * 29.530588853
