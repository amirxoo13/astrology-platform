"""
Geocoding utilities with Nominatim (default) and optional GeoNames.

Nominatim (OpenStreetMap) needs no API key. GeoNames requires GEONAMES_USER.
If GeoNames is selected but unconfigured or empty, Nominatim is used.
"""
import json
import logging
import os
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import urlopen

try:
    from geopy.geocoders import Nominatim
    from geopy.exc import GeopyError
    NOMINATIM_AVAILABLE = True
except ImportError:
    Nominatim = None
    GeopyError = Exception
    NOMINATIM_AVAILABLE = False

try:
    from timezonefinder import TimezoneFinder
    _timezone_finder = TimezoneFinder()
except ImportError:
    _timezone_finder = None

_nominatim = Nominatim(user_agent="astrology-platform-bot") if NOMINATIM_AVAILABLE else None

logger = logging.getLogger(__name__)
GEONAMES_USER = os.getenv("GEONAMES_USER", "")


class LocationError(ValueError):
    """Raised when the user-provided location/coordinates cannot be resolved."""


def looks_like_coordinates(text):
    """Heuristic to decide whether input should be parsed as 'lat,lon'."""
    stripped = text.strip()
    if not stripped:
        return False
    has_letter = any(ch.isalpha() for ch in stripped)
    has_digit = any(ch.isdigit() for ch in stripped)
    return has_digit and not has_letter


def parse_coordinates(text):
    """Parse a 'lat,lon' string into validated floats."""
    parts = [p.strip() for p in text.split(",")]
    if len(parts) != 2:
        raise LocationError(
            "فرمت مختصات اشتباه است. لطفاً به شکل lat,lon وارد کنید (مثال: 35.69,51.39)"
        )

    try:
        lat = float(parts[0])
        lon = float(parts[1])
    except ValueError:
        raise LocationError(
            "مختصات باید عدد باشند. لطفاً به شکل lat,lon وارد کنید (مثال: 35.69,51.39)"
        )

    if not (-90 <= lat <= 90):
        raise LocationError("عرض جغرافیایی (latitude) باید بین 90- و 90 باشد.")
    if not (-180 <= lon <= 180):
        raise LocationError("طول جغرافیایی (longitude) باید بین 180- و 180 باشد.")

    return lat, lon


def geocode_geonames(name, max_results=5):
    """Resolve a place name with the GeoNames searchJSON API."""
    if not GEONAMES_USER:
        logger.error("GeoNames username not configured")
        return []

    try:
        params = urlencode(
            {
                "q": name,
                "maxRows": max_results,
                "username": GEONAMES_USER,
                "featureClass": "P",
                "orderby": "relevance",
            }
        )
        url = f"http://api.geonames.org/searchJSON?{params}"
        with urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))

        results = []
        for place in data.get("geonames", []):
            results.append(
                {
                    "name": place.get("name", ""),
                    "country": place.get("countryName", ""),
                    "admin1": place.get("adminName1", ""),
                    "lat": float(place.get("lat", 0)),
                    "lon": float(place.get("lng", 0)),
                    "population": place.get("population", 0),
                }
            )
        return results
    except (URLError, TimeoutError, ValueError, json.JSONDecodeError) as e:
        logger.error("GeoNames search failed for '%s': %s", name, e)
        return []


def geocode_nominatim(name):
    """Resolve a place name with Nominatim. Returns a one-item list or []."""
    if not NOMINATIM_AVAILABLE or _nominatim is None:
        logger.error("Nominatim unavailable: geopy is not installed")
        return []

    try:
        location = _nominatim.geocode(name, timeout=10, addressdetails=True)
    except GeopyError as e:
        logger.error("Nominatim geocoding failed for '%s': %s", name, e)
        return []

    if location is None:
        return []

    address = location.raw.get("address", {}) if isinstance(location.raw, dict) else {}
    return [
        {
            "name": location.address.split(",")[0] if location.address else name,
            "country": address.get("country", ""),
            "admin1": address.get("state", address.get("county", "")),
            "lat": location.latitude,
            "lon": location.longitude,
            "population": 0,
        }
    ]


def _preferred_geocoder():
    configured = os.getenv("GEOCODER", "nominatim").strip().lower()
    if configured == "geonames" and GEONAMES_USER:
        return "geonames"
    return "nominatim"


def geocode_city(name):
    """
    Main geocoding function. Always returns a list of result dicts.

    GeoNames is only used when GEOCODER=geonames and GEONAMES_USER is set.
    Otherwise Nominatim is used. An empty GeoNames result falls back to Nominatim.
    """
    if _preferred_geocoder() == "geonames":
        results = geocode_geonames(name)
        if results:
            return results
        logger.warning("GeoNames returned no results for '%s'; trying Nominatim", name)

    return geocode_nominatim(name)


def resolve_timezone(lat, lon):
    """IANA timezone for coordinates, or UTC if lookup is unavailable."""
    if _timezone_finder is None:
        logger.error("Timezone lookup unavailable: timezonefinder is not installed")
        return "UTC"

    try:
        tz_name = _timezone_finder.timezone_at(lat=lat, lng=lon)
    except Exception as e:
        logger.error("Timezone lookup failed for (%s, %s): %s", lat, lon, e)
        return "UTC"

    return tz_name or "UTC"
