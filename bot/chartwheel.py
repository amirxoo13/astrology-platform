"""
SVG chart wheel generation with Cairo backend.
ASC at 9 o'clock (East), aspect lines, stellium handling.
"""
import math
import logging
from io import BytesIO

logger = logging.getLogger(__name__)

# Try Cairo imports
try:
    import cairo
    from cairosvg import svg2png
    CAIRO_AVAILABLE = True
except ImportError:
    CAIRO_AVAILABLE = False
    logger.warning("Cairo/CairoSVG not available, chart wheels disabled")

# Dark theme colors
BG_COLOR = '#0a0e1a'
RING_COLOR = '#1e293b'
TEXT_COLOR = '#e2e8f0'
SIGN_COLORS = {
    'Aries': '#ff4444', 'Taurus': '#44ff44', 'Gemini': '#ffff44',
    'Cancer': '#4444ff', 'Leo': '#ff8844', 'Virgo': '#88ff44',
    'Libra': '#44ffff', 'Scorpio': '#ff44ff', 'Sagittarius': '#ff4488',
    'Capricorn': '#44ff88', 'Aquarius': '#8844ff', 'Pisces': '#88ffff'
}

ASPECT_COLORS = {
    'CONJUNCTION': '#fbbf24',
    'OPPOSITION': '#ef4444',
    'TRINE': '#10b981',
    'SQUARE': '#f59e0b',
    'SEXTILE': '#3b82f6'
}

# Planet symbols (Unicode + DejaVu fallback)
PLANET_GLYPHS = {
    'Sun': '☉', 'Moon': '☽', 'Mercury': '☿', 'Venus': '♀',
    'Mars': '♂', 'Jupiter': '♃', 'Saturn': '♄',
    'Uranus': '♅', 'Neptune': '♆', 'Pluto': '♇'
}

# Zodiac symbols
SIGN_GLYPHS = {
    'Aries': '♈', 'Taurus': '♉', 'Gemini': '♊',
    'Cancer': '♋', 'Leo': '♌', 'Virgo': '♍',
    'Libra': '♎', 'Scorpio': '♏', 'Sagittarius': '♐',
    'Capricorn': '♑', 'Aquarius': '♒', 'Pisces': '♓'
}


def normalize_angle(angle):
    """Normalize angle to 0-360."""
    while angle < 0:
        angle += 360
    while angle >= 360:
        angle -= 360
    return angle


def asc_to_rotation(asc_lon):
    """
    Calculate rotation to place ASC at 9 o'clock (East).
    In standard astrology wheel, ASC is at 9 o'clock = 180° in drawing coords.
    Drawing coords: 0° is right (3 o'clock), 90° is down, 180° is left.
    Chart coords: 0° Aries starts at ASC, increases counterclockwise.
    """
    return normalize_angle(180 - asc_lon)


def chart_to_drawing_angle(chart_lon, asc_lon):
    """
    Convert chart longitude to drawing angle (0° = right, counterclockwise).
    """
    rotation = asc_to_rotation(asc_lon)
    return normalize_angle(rotation + chart_lon)


def detect_stellium(positions, orb=10):
    """
    Detect stelliums (3+ planets within orb).
    Returns list of lists of planet indices.
    """
    stelliums = []
    used = set()
    
    for i, p1 in enumerate(positions):
        if i in used:
            continue
        
        cluster = [i]
        lon1 = p1['longitude']
        
        for j, p2 in enumerate(positions):
            if j <= i or j in used:
                continue
            
            lon2 = p2['longitude']
            diff = abs(normalize_angle(lon1 - lon2))
            if diff > 180:
                diff = 360 - diff
            
            if diff <= orb:
                cluster.append(j)
        
        if len(cluster) >= 3:
            stelliums.append(cluster)
            used.update(cluster)
    
    return stelliums


def decollide_positions(positions, asc_lon, stelliums, min_sep=8):
    """
    Adjust planet display positions to avoid overlap in stelliums.
    Returns list of adjusted longitudes for display.
    """
    adjusted = [p['longitude'] for p in positions]
    
    for cluster in stelliums:
        if len(cluster) < 2:
            continue
        
        # Calculate cluster center
        lons = [positions[i]['longitude'] for i in cluster]
        center = sum(lons) / len(lons)
        
        # Spread planets around center
        spread = (len(cluster) - 1) * min_sep / 2
        for idx, i in enumerate(cluster):
            offset = (idx - len(cluster) / 2 + 0.5) * min_sep
            adjusted[i] = normalize_angle(center + offset)
    
    return adjusted


def draw_wheel_svg(positions, houses, aspects, asc_lon, width=800):
    """
    Generate SVG chart wheel.
    
    Args:
        positions: Planet positions from API
        houses: House cusps from API
        aspects: Aspect list
        asc_lon: Ascendant longitude
        width: Image width in pixels
    
    Returns:
        SVG string
    """
    if not CAIRO_AVAILABLE:
        return None
    
    height = width
    center_x = width / 2
    center_y = height / 2
    
    # Radii
    outer_r = width * 0.45
    sign_r = width * 0.38
    planet_r = width * 0.30
    inner_r = width * 0.15
    
    # SVG header
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">\n'
    
    # Background
    svg += f'<rect width="{width}" height="{height}" fill="{BG_COLOR}"/>\n'
    
    # Outer circle
    svg += f'<circle cx="{center_x}" cy="{center_y}" r="{outer_r}" fill="none" stroke="{RING_COLOR}" stroke-width="2"/>\n'
    
    # Sign ring
    svg += f'<circle cx="{center_x}" cy="{center_y}" r="{sign_r}" fill="none" stroke="{RING_COLOR}" stroke-width="2"/>\n'
    
    # Planet ring
    svg += f'<circle cx="{center_x}" cy="{center_y}" r="{planet_r}" fill="none" stroke="{RING_COLOR}" stroke-width="1"/>\n'
    
    # Inner circle
    svg += f'<circle cx="{center_x}" cy="{center_y}" r="{inner_r}" fill="none" stroke="{RING_COLOR}" stroke-width="2"/>\n'
    
    # Draw house cusps
    for house in houses[:12]:
        cusp_lon = house['cusp_longitude']
        angle_deg = chart_to_drawing_angle(cusp_lon, asc_lon)
        angle_rad = math.radians(angle_deg)
        
        x1 = center_x + inner_r * math.cos(angle_rad)
        y1 = center_y + inner_r * math.sin(angle_rad)
        x2 = center_x + planet_r * math.cos(angle_rad)
        y2 = center_y + planet_r * math.sin(angle_rad)
        
        svg += f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{RING_COLOR}" stroke-width="1"/>\n'
    
    # Draw zodiac signs
    signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
             'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
    
    for i, sign in enumerate(signs):
        sign_lon = i * 30 + 15  # Middle of sign
        angle_deg = chart_to_drawing_angle(sign_lon, asc_lon)
        angle_rad = math.radians(angle_deg)
        
        r_text = (sign_r + outer_r) / 2
        x = center_x + r_text * math.cos(angle_rad)
        y = center_y + r_text * math.sin(angle_rad)
        
        glyph = SIGN_GLYPHS.get(sign, sign[0])
        color = SIGN_COLORS.get(sign, TEXT_COLOR)
        
        svg += f'<text x="{x}" y="{y}" fill="{color}" font-size="20" text-anchor="middle" dominant-baseline="middle" font-family="DejaVu Sans">{glyph}</text>\n'
    
    # Detect stelliums and adjust positions
    stelliums = detect_stellium(positions)
    adjusted_lons = decollide_positions(positions, asc_lon, stelliums)
    
    # Draw aspect lines
    for aspect in aspects[:30]:  # Limit to avoid clutter
        p1_name = aspect['planet1']
        p2_name = aspect['planet2']
        
        p1_idx = next((i for i, p in enumerate(positions) if p['name'] == p1_name), None)
        p2_idx = next((i for i, p in enumerate(positions) if p['name'] == p2_name), None)
        
        if p1_idx is None or p2_idx is None:
            continue
        
        lon1 = adjusted_lons[p1_idx]
        lon2 = adjusted_lons[p2_idx]
        
        angle1_deg = chart_to_drawing_angle(lon1, asc_lon)
        angle2_deg = chart_to_drawing_angle(lon2, asc_lon)
        
        angle1_rad = math.radians(angle1_deg)
        angle2_rad = math.radians(angle2_deg)
        
        x1 = center_x + inner_r * math.cos(angle1_rad)
        y1 = center_y + inner_r * math.sin(angle1_rad)
        x2 = center_x + inner_r * math.cos(angle2_rad)
        y2 = center_y + inner_r * math.sin(angle2_rad)
        
        color = ASPECT_COLORS.get(aspect['aspect'], TEXT_COLOR)
        opacity = max(0.3, 1.0 - aspect['orb'] / 8.0)
        
        svg += f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="1" opacity="{opacity}"/>\n'
    
    # Draw planets
    for i, planet in enumerate(positions[:10]):  # Main 10 planets
        display_lon = adjusted_lons[i]
        angle_deg = chart_to_drawing_angle(display_lon, asc_lon)
        angle_rad = math.radians(angle_deg)
        
        r_planet = (planet_r + sign_r) / 2
        x = center_x + r_planet * math.cos(angle_rad)
        y = center_y + r_planet * math.sin(angle_rad)
        
        glyph = PLANET_GLYPHS.get(planet['name'], planet['name'][0])
        
        svg += f'<text x="{x}" y="{y}" fill="{TEXT_COLOR}" font-size="18" text-anchor="middle" dominant-baseline="middle" font-family="DejaVu Sans">{glyph}</text>\n'
    
    svg += '</svg>'
    return svg


def generate_chart_wheel_png(positions, houses, aspects, asc_lon, width=800):
    """
    Generate PNG chart wheel from SVG.
    Returns PNG bytes or None if Cairo unavailable.
    """
    svg = draw_wheel_svg(positions, houses, aspects, asc_lon, width)
    if svg is None:
        return None
    
    try:
        png_bytes = svg2png(bytestring=svg.encode('utf-8'))
        return png_bytes
    except Exception as e:
        logger.error(f"PNG generation failed: {e}")
        return None
