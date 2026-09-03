"""
Astrological calculation utilities.
Cross-aspects, composite charts, progressions, and solar returns.
"""
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# 10 classical planets for main chart calculations
MAIN_PLANETS = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 
                'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto']

# Aspect types and orbs
ASPECT_TYPES = {
    'CONJUNCTION': {'angle': 0, 'orb': 8},
    'OPPOSITION': {'angle': 180, 'orb': 8},
    'TRINE': {'angle': 120, 'orb': 8},
    'SQUARE': {'angle': 90, 'orb': 8},
    'SEXTILE': {'angle': 60, 'orb': 6},
}


def normalize_angle(angle):
    """Normalize angle to 0-360 range."""
    while angle < 0:
        angle += 360
    while angle >= 360:
        angle -= 360
    return angle


def calculate_aspect_orb(lon1, lon2, target_angle):
    """
    Calculate orb for aspect between two longitudes.
    Returns absolute orb in degrees.
    """
    diff = abs(normalize_angle(lon1 - lon2))
    if diff > 180:
        diff = 360 - diff
    
    orb = abs(diff - target_angle)
    if target_angle == 0 and diff > 180:
        orb = 360 - diff
    
    return orb


def cross_aspects(positions1, positions2, max_orb=0.7):
    """
    Calculate aspects between two sets of planetary positions.
    Used for synastry (person1 to person2).
    
    Args:
        positions1: List of planet dicts from chart 1
        positions2: List of planet dicts from chart 2
        max_orb: Maximum orb multiplier (default 0.7 for tighter orbs)
    
    Returns:
        List of aspect dicts with planet1, planet2, aspect, orb, applying
    """
    aspects = []
    
    for p1 in positions1:
        if p1['name'] not in MAIN_PLANETS:
            continue
        
        for p2 in positions2:
            if p2['name'] not in MAIN_PLANETS:
                continue
            
            lon1 = p1['longitude']
            lon2 = p2['longitude']
            
            for aspect_name, aspect_data in ASPECT_TYPES.items():
                target = aspect_data['angle']
                max_orb_degrees = aspect_data['orb'] * max_orb
                
                orb = calculate_aspect_orb(lon1, lon2, target)
                
                if orb <= max_orb_degrees:
                    aspects.append({
                        'planet1': p1['name'],
                        'planet2': p2['name'],
                        'aspect': aspect_name,
                        'orb': orb,
                        'applying': False  # Would need velocity data
                    })
    
    # Sort by orb
    aspects.sort(key=lambda x: x['orb'])
    return aspects


def composite_midpoints(positions1, positions2):
    """
    Calculate composite chart midpoints between two natal charts.
    Returns list of composite planet positions.
    """
    composite = []
    
    for p1 in positions1:
        if p1['name'] not in MAIN_PLANETS:
            continue
        
        # Find matching planet in chart 2
        p2 = next((p for p in positions2 if p['name'] == p1['name']), None)
        if not p2:
            continue
        
        lon1 = p1['longitude']
        lon2 = p2['longitude']
        
        # Calculate midpoint (shortest arc)
        diff = normalize_angle(lon2 - lon1)
        if diff > 180:
            midpoint = normalize_angle(lon1 - (360 - diff) / 2)
        else:
            midpoint = normalize_angle(lon1 + diff / 2)
        
        composite.append({
            'name': p1['name'],
            'longitude': midpoint,
            'sign': get_sign_from_longitude(midpoint)
        })
    
    return composite


def equal_houses_from_asc(asc_longitude):
    """
    Calculate equal house cusps from Ascendant.
    Returns list of 12 house cusps (30° each).
    """
    houses = []
    for i in range(12):
        cusp_lon = normalize_angle(asc_longitude + (i * 30))
        houses.append({
            'house': i + 1,
            'cusp_longitude': cusp_lon,
            'sign': get_sign_from_longitude(cusp_lon)
        })
    return houses


def progressed_instant(birth_date_str, progress_years):
    """
    Calculate progressed date using secondary progression (1 day = 1 year).
    
    Args:
        birth_date_str: Birth date in YYYY-MM-DD format
        progress_years: Years to progress (can be fractional)
    
    Returns:
        Progressed date string in YYYY-MM-DD format
    """
    birth = datetime.strptime(birth_date_str, '%Y-%m-%d')
    progressed = birth + timedelta(days=progress_years)
    return progressed.strftime('%Y-%m-%d')


def solar_return_guess(birth_date_str, target_year):
    """
    Estimate solar return date (when Sun returns to natal position).
    This is a rough guess; actual calculation needs ephemeris.
    
    Args:
        birth_date_str: Birth date in YYYY-MM-DD format
        target_year: Year for solar return
    
    Returns:
        Estimated date string in YYYY-MM-DD format
    """
    birth = datetime.strptime(birth_date_str, '%Y-%m-%d')
    # Solar return is approximately on birth date in target year
    # (can vary by ~1 day due to leap years and Earth's orbit)
    return f"{target_year}-{birth.month:02d}-{birth.day:02d}"


def refine_return(api_positions, natal_sun_lon, base_date_str):
    """
    Refine solar return date by checking if Sun position matches natal.
    
    Args:
        api_positions: Positions from API for base_date
        natal_sun_lon: Natal Sun longitude
        base_date_str: Base date to refine
    
    Returns:
        True if close enough (within 1°), False otherwise
    """
    sun = next((p for p in api_positions if p['name'] == 'Sun'), None)
    if not sun:
        return False
    
    sun_lon = sun['longitude']
    diff = abs(normalize_angle(sun_lon - natal_sun_lon))
    if diff > 180:
        diff = 360 - diff
    
    return diff < 1.0  # Within 1 degree


def get_sign_from_longitude(longitude):
    """Get zodiac sign from longitude (0-360)."""
    signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
             'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
    index = int(longitude / 30) % 12
    return signs[index]
