"""
Geocoding utilities with GeoNames and Nominatim support.
timezonefinder stays in bot for offline timezone resolution.
"""
import logging
import os

logger = logging.getLogger(__name__)

# Configuration
GEOCODER = os.getenv('GEOCODER', 'geonames')  # 'geonames' or 'nominatim'
GEONAMES_USER = os.getenv('GEONAMES_USER', '')

# Try GeoNames
try:
    import requests
    GEONAMES_AVAILABLE = True
except ImportError:
    GEONAMES_AVAILABLE = False

# Try Nominatim
try:
    from geopy.geocoders import Nominatim
    from geopy.exc import GeopyError
    NOMINATIM_AVAILABLE = True
except ImportError:
    Nominatim = None
    GeopyError = Exception
    NOMINATIM_AVAILABLE = False

# Try timezonefinder
try:
    from timezonefinder import TimezoneFinder
    _timezone_finder = TimezoneFinder()
except ImportError:
    _timezone_finder = None

# Initialize geocoders
_nominatim = Nominatim(user_agent="astrology-platform-bot") if NOMINATIM_AVAILABLE else None


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
    parts = [p.strip() for p in text.split(',')]
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
    """
    Resolve city/place name using GeoNames API.
    Returns list of (name, lat, lon, country) tuples for disambiguation.
    """
    if not GEONAMES_AVAILABLE:
        logger.error("GeoNames unavailable: requests not installed")
        return []
    
    if not GEONAMES_USER:
        logger.error("GeoNames username not configured")
        return []
    
    try:
        url = "http://api.geonames.org/searchJSON"
        params = {
            'q': name,
            'maxRows': max_results,
            'username': GEONAMES_USER,
            'featureClass': 'P',  # Populated places
            'orderby': 'relevance'
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for place in data.get('geonames', []):
            results.append({
                'name': place.get('name', ''),
                'country': place.get('countryName', ''),
                'admin1': place.get('adminName1', ''),
                'lat': float(place.get('lat', 0)),
                'lon': float(place.get('lng', 0)),
                'population': place.get('population', 0)
            })
        
        return results
        
    except Exception as e:
        logger.error(f"GeoNames search failed for '{name}': {e}")
        return []


def geocode_nominatim(name):
    """
    Resolve city/place name using Nominatim.
    Returns single (lat, lon) or None.
    """
    if not NOMINATIM_AVAILABLE or _nominatim is None:
        logger.error("Nominatim unavailable: geopy not installed")
        return None
    
    try:
        location = _nominatim.geocode(name, timeout=10)
    except GeopyError as e:
        logger.error(f"Nominatim geocoding failed for '{name}': {e}")
        return None
    
    if location is None:
        return None
    
    return location.latitude, location.longitude


def geocode_city(name):
    """
    Main geocoding function.
    Returns list of results for GeoNames, or single result for Nominatim.
    """
    if GEOCODER == 'geonames':
        return geocode_geonames(name)
    else:
        result = geocode_nominatim(name)
        if result:
            lat, lon = result
            return [{'name': name, 'country': '', 'admin1': '', 'lat': lat, 'lon': lon, 'population': 0}]
        return []


def resolve_timezone(lat, lon):
    """Resolve the IANA timezone name for the given coordinates, defaulting to UTC."""
    if _timezone_finder is None:
        logger.error("Timezone lookup unavailable: timezonefinder is not installed")
        return 'UTC'
    
    try:
        tz_name = _timezone_finder.timezone_at(lat=lat, lng=lon)
    except Exception as e:
        logger.error(f"Timezone lookup failed for ({lat}, {lon}): {e}")
        return 'UTC'
    
    return tz_name or 'UTC'
