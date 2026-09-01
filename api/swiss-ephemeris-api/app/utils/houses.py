def house_for_longitude(longitude: float, cusps: list[float]) -> int | None:
    """
    Return the house number (1-12) that contains the given ecliptic longitude.
    Correctly handles wrap-around at 0° Aries (e.g., cusp in Pisces, planet in Aries).
    """
    for i in range(12):
        lo = cusps[i]
        hi = cusps[(i + 1) % 12]
        if lo < hi:
            in_house = lo < longitude <= hi
        else:
            # Wrap-around: house spans 0° Aries
            in_house = longitude > lo or longitude <= hi
        if in_house:
            return i + 1
    return None
