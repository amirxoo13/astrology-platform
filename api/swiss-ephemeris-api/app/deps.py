from app.core.swisseph_core import SwissEphemerisCore
from app.core.config import settings

# Singleton instance — shared across all requests.
# ephe_path is set ONCE in main.py lifespan (swe.set_ephe_path).
# SwissEphemerisCore itself is stateless (no ephe_path call in __init__).
_core: SwissEphemerisCore | None = None


def get_swiss_core() -> SwissEphemerisCore:
    global _core
    if _core is None:
        _core = SwissEphemerisCore(ephe_path=settings.ephe_path)
    return _core


def init_core() -> SwissEphemerisCore:
    """Called once at app startup (lifespan) to eagerly initialize the core."""
    return get_swiss_core()
