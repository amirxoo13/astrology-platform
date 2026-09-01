import pytest
import swisseph as swe
import os


def _find_ephe_path() -> str:
    candidates = [
        os.environ.get("EPHE_PATH", ""),
        os.path.join(os.path.dirname(__file__), "..", "ephe"),
        "./ephe",
        "/Users/tronglb/Task/Velora-Workspace/swiss-ephemeris-api/ephe",
    ]
    for p in candidates:
        if p and (os.path.isdir(p) or os.path.isfile(os.path.join(p, "sepl_18.se1"))):
            return p
    return "./ephe"


# Set ephe path at module load time — before TestClient imports app.
# This is critical: the app's lifespan calls swe.set_ephe_path() using
# settings.ephe_path (default "./ephe"). The CWD during pytest IS the repo root,
# so "./ephe" works if set BEFORE TestClient triggers the import.
_ephe_path = _find_ephe_path()
swe.set_ephe_path(_ephe_path)


@pytest.fixture(scope="session")
def ephe_path() -> str:
    return _ephe_path


@pytest.fixture
def swiss_core(ephe_path: str):
    """Instantiate SwissEphemerisCore with a valid ephe path."""
    from app.core.swisseph_core import SwissEphemerisCore
    return SwissEphemerisCore(ephe_path=ephe_path)
