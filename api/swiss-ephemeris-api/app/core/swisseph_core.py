import swisseph as swe
from dataclasses import dataclass


@dataclass
class PlanetResult:
    longitude: float
    latitude: float
    distance: float
    speed_long: float
    speed_lat: float
    speed_dist: float


@dataclass
class HouseResult:
    cusps: list[float]
    ascmc: list[float]


class SwissEphemerisCore:
    """
    Thin, stateless wrapper around the swisseph C library.
    All swisseph calls are sync/blocking — must be called from a thread
    via asyncio.to_thread(), never directly from an async handler.

    Uses calc_ut (UT mode) throughout for consistency with the datetime_to_jd
    conversion that returns Julian Day UT.

    IMPORTANT: swe.set_ephe_path() uses thread-local storage in the C library.
    It must be called in every thread that performs calculations, not just the
    main thread. _ensure_path() handles this transparently.
    """

    def __init__(self, ephe_path: str) -> None:
        self._ephe_path = ephe_path

    def _ensure_path(self) -> None:
        """Set the ephemeris path in the current thread (cheap C call, safe to repeat)."""
        swe.set_ephe_path(self._ephe_path)

    def calc_planet(
        self,
        planet: int,
        jd_ut: float,
        flags: int = swe.FLG_SWIEPH | swe.FLG_SPEED,
        sidereal_ayanamsa: int | None = None,
    ) -> PlanetResult:
        """
        Calculate planet position using UT (Julian Day UT input).
        If sidereal_ayanamsa is provided, FLG_SIDEREAL | sidereal_ayanamsa | FLG_SPEED is used.
        """
        self._ensure_path()
        if sidereal_ayanamsa is not None:
            actual_flags = swe.FLG_SIDEREAL + sidereal_ayanamsa + swe.FLG_SPEED
        else:
            actual_flags = flags
        result = swe.calc_ut(jd_ut, planet, actual_flags)
        return PlanetResult(
            longitude=result[0][0],
            latitude=result[0][1],
            distance=result[0][2],
            speed_long=result[0][3],
            speed_lat=result[0][4],
            speed_dist=result[0][5],
        )

    def calc_special(
        self,
        planet: int,
        jd_ut: float,
        flags: int = swe.FLG_SWIEPH,
        sidereal_ayanamsa: int | None = None,
    ) -> PlanetResult:
        """
        Calculate special points (TRUE_NODE, MEAN_NODE, VERTEX, etc.)
        that require swe.calc_ut with FLG_SPEED.
        """
        self._ensure_path()
        if sidereal_ayanamsa is not None:
            actual_flags = swe.FLG_SIDEREAL + sidereal_ayanamsa + swe.FLG_SPEED
        else:
            actual_flags = flags + swe.FLG_SPEED
        result = swe.calc_ut(jd_ut, planet, actual_flags)
        return PlanetResult(
            longitude=result[0][0],
            latitude=result[0][1],
            distance=result[0][2],
            speed_long=result[0][3],
            speed_lat=result[0][4],
            speed_dist=result[0][5],
        )

    def calc_lilith(
        self,
        jd_ut: float,
        true: bool = True,
        flags: int = swe.FLG_SWIEPH,
        sidereal_ayanamsa: int | None = None,
    ) -> PlanetResult:
        """
        Calculate Lilith (Black Moon) longitude and speed.
        true=True  -> True Lilith: NODBIT_OSCU | NODBIT_FOPOINT
        true=False -> Mean Lilith: NODBIT_MEAN | NODBIT_FOPOINT
        FLG_SPEED is always included to capture the speed for retrograde detection.
        If sidereal_ayanamsa is provided, sidereal mode is used.
        """
        self._ensure_path()
        if sidereal_ayanamsa is not None:
            actual_flags = swe.FLG_SIDEREAL + sidereal_ayanamsa + swe.FLG_SPEED
        else:
            actual_flags = flags + swe.FLG_SPEED
        nodbit = swe.NODBIT_OSCU | swe.NODBIT_FOPOINT if true else swe.NODBIT_MEAN | swe.NODBIT_FOPOINT
        # nod_aps_ut returns (asc_node, dsc_node, perigee, apogee) — Lilith = apogee at index 3
        result = swe.nod_aps_ut(jd_ut, swe.MOON, nodbit, actual_flags)
        apogee = result[3]
        return PlanetResult(
            longitude=apogee[0],
            latitude=apogee[1],
            distance=apogee[2],
            speed_long=apogee[3],
            speed_lat=apogee[4],
            speed_dist=apogee[5],
        )

    def calc_nodes(
        self,
        jd_ut: float,
        true: bool = True,
        flags: int = swe.FLG_SWIEPH | swe.FLG_SPEED,
        sidereal_ayanamsa: int | None = None,
    ) -> tuple[PlanetResult, PlanetResult]:
        """
        Calculate both Lunar Nodes.
        Returns (north_node, south_node) as PlanetResult tuples.
        North Node = TRUE_NODE or MEAN_NODE.
        South Node = North Node + 180°.
        All speeds are negated for the South Node (it moves opposite).
        """
        self._ensure_path()
        planet = swe.TRUE_NODE if true else swe.MEAN_NODE
        if sidereal_ayanamsa is not None:
            actual_flags = swe.FLG_SIDEREAL + sidereal_ayanamsa + swe.FLG_SPEED
        else:
            actual_flags = flags
        north = swe.calc_ut(jd_ut, planet, actual_flags)
        north_result = PlanetResult(
            longitude=north[0][0],
            latitude=north[0][1],
            distance=north[0][2],
            speed_long=north[0][3],
            speed_lat=north[0][4],
            speed_dist=north[0][5],
        )
        south_result = PlanetResult(
            longitude=(north[0][0] + 180.0) % 360.0,
            latitude=-north[0][1],
            distance=north[0][2],
            speed_long=-north[0][3],
            speed_lat=-north[0][4],
            speed_dist=-north[0][5],
        )
        return north_result, south_result

    def houses(
        self,
        jd_ut: float,
        latitude: float,
        longitude: float,
        hsys: str = "P",
    ) -> HouseResult:
        """Return house cusps and ascendant/MC (ascmc[0]=ASC, ascmc[1]=MC)."""
        self._ensure_path()
        if isinstance(hsys, str):
            hsys = hsys.encode()
        raw_cusps, ascmc = swe.houses(jd_ut, latitude, longitude, hsys)
        # pysweph 2.10.3.4+: cusps[0] is empty; skip it
        cusps = list(raw_cusps[1:13])  # houses 1-12 only
        return HouseResult(cusps=cusps, ascmc=list(ascmc))

    @staticmethod
    def julday(
        year: int, month: int, day: int, hour: float, cal: int = swe.GREG_CAL
    ) -> float:
        return swe.julday(year, month, day, hour, cal)

    @staticmethod
    def revjul(jd_ut: float, cal: int = swe.GREG_CAL) -> tuple[int, int, int, float]:
        return swe.revjul(jd_ut, cal)
