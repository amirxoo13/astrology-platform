import swisseph as swe


# Eclipse type constants
_ECL_SOLAR_ALL = swe.ECL_PARTIAL | swe.ECL_CENTRAL | swe.ECL_NONCENTRAL | swe.ECL_TOTAL | swe.ECL_ANNULAR | swe.ECL_ANNULAR_TOTAL  # = 63
_ECL_LUNAR_ALL = swe.ECL_PENUMBRAL | swe.ECL_PARTIAL | swe.ECL_TOTAL  # = 84


def _jd_to_iso(jd: float) -> str:
    year, month, day, hour = swe.revjul(jd, swe.GREG_CAL)
    hour_int = int(hour)
    minute_int = int((hour - hour_int) * 60)
    second_int = int((((hour - hour_int) * 60) - minute_int) * 60)
    return f"{year:04d}-{month:02d}-{day:02d}T{hour_int:02d}:{minute_int:02d}:{second_int:02d}"


def find_eclipses_in_range(
    jd_start: float,
    jd_end: float,
    eclipse_type: str = "SOLAR",
    latitude: float | None = None,
    longitude: float | None = None,
) -> list[dict]:
    """
    Find all eclipses of the given type between jd_start and jd_end.
    eclipse_type: "SOLAR" or "LUNAR"
    Returns list of dicts with eclipse data.

    Function signatures (pysweph 2.10.3.6):
      - sol_eclipse_when_glob(tjd_start, ifl, ifltype, backward) -> (retflag, tret[10])
      - lun_eclipse_when(tjd_start, ifl, ifltype, backward)         -> (retflag, tret[10])
      - sol_eclipse_when_loc(tjd_start, geopos[3], ifl)            -> (retflag, tret[10], attr[20])
      - lun_eclipse_when_loc(tjd_start, geopos[3], ifl)            -> (retflag, tret[10], attr[20])
    """
    eclipses = []
    jd_current = jd_start
    is_solar = eclipse_type == "SOLAR"

    while True:
        try:
            if is_solar:
                retflag, tret = swe.sol_eclipse_when_glob(
                    jd_current, 0, _ECL_SOLAR_ALL, 0
                )
            else:
                retflag, tret = swe.lun_eclipse_when(
                    jd_current, 0, _ECL_LUNAR_ALL, 0
                )

            jd_next = tret[0]
            if jd_next <= 0 or jd_next > jd_end:
                break

            entry: dict = {
                "type": eclipse_type,
                "date": _jd_to_iso(jd_next),
                "julian_day": jd_next,
                "saros": int(tret[9]) if tret[9] > 0 else None,
            }

            # Local circumstances if location provided
            if latitude is not None and longitude is not None:
                geopos = [latitude, longitude, 0.0]
                if is_solar:
                    ret2, tret2, attr = swe.sol_eclipse_when_loc(
                        jd_next, geopos, 0
                    )
                    if ret2 >= 0:
                        entry["magnitude"] = round(attr[0], 6)
                        entry["saros"] = int(attr[9]) if attr[9] > 0 else None
                        entry["visible_from_lat"] = latitude
                        entry["visible_from_lon"] = longitude
                else:
                    ret2, tret2, attr = swe.lun_eclipse_when_loc(
                        jd_next, geopos, 0
                    )
                    if ret2 >= 0:
                        entry["magnitude"] = round(attr[0], 6)
                        entry["saros"] = int(attr[9]) if attr[9] > 0 else None
                        entry["visible_from_lat"] = latitude
                        entry["visible_from_lon"] = longitude

            eclipses.append(entry)
            jd_current = jd_next + 1

        except Exception:
            break

        if len(eclipses) > 100:
            break

    return eclipses
