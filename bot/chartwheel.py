"""
SVG natal-wheel drawing. ASC is placed at 9 o'clock (east).

PNG conversion uses CairoSVG when installed. SVG generation itself is
plain-string drawing and does not require pycairo.
"""
import math
import logging

logger = logging.getLogger(__name__)

try:
    from cairosvg import svg2png
    CAIROSVG_AVAILABLE = True
except ImportError:
    CAIROSVG_AVAILABLE = False
    logger.warning("CairoSVG not available, chart wheel PNG disabled")

import astro

BG_COLOR = "#0a0e1a"
RING_COLOR = "#1e293b"
TEXT_COLOR = "#e2e8f0"
SIGN_COLORS = {
    "Aries": "#ff4444",
    "Taurus": "#44ff44",
    "Gemini": "#ffff44",
    "Cancer": "#4444ff",
    "Leo": "#ff8844",
    "Virgo": "#88ff44",
    "Libra": "#44ffff",
    "Scorpio": "#ff44ff",
    "Sagittarius": "#ff4488",
    "Capricorn": "#44ff88",
    "Aquarius": "#8844ff",
    "Pisces": "#88ffff",
}

ASPECT_COLORS = {
    "CONJUNCTION": "#fbbf24",
    "OPPOSITION": "#ef4444",
    "TRINE": "#10b981",
    "SQUARE": "#f59e0b",
    "SEXTILE": "#3b82f6",
}

PLANET_GLYPHS = {
    "Sun": "☉",
    "Moon": "☽",
    "Mercury": "☿",
    "Venus": "♀",
    "Mars": "♂",
    "Jupiter": "♃",
    "Saturn": "♄",
    "Uranus": "♅",
    "Neptune": "♆",
    "Pluto": "♇",
}

SIGN_GLYPHS = {
    "Aries": "♈",
    "Taurus": "♉",
    "Gemini": "♊",
    "Cancer": "♋",
    "Leo": "♌",
    "Virgo": "♍",
    "Libra": "♎",
    "Scorpio": "♏",
    "Sagittarius": "♐",
    "Capricorn": "♑",
    "Aquarius": "♒",
    "Pisces": "♓",
}


def normalize_angle(angle):
    return angle % 360.0


def asc_to_rotation(asc_lon):
    """Rotation that places ASC at 9 o'clock (180° in SVG coords)."""
    return normalize_angle(180 - asc_lon)


def chart_to_drawing_angle(chart_lon, asc_lon):
    rotation = asc_to_rotation(asc_lon)
    return normalize_angle(rotation + chart_lon)


def _main_positions(positions):
    return [p for p in positions if astro.is_main_planet(p)]


def detect_stellium(positions, orb=10):
    """Clusters of 3+ planets within orb. Returns lists of indices."""
    stelliums = []
    used = set()

    for i, p1 in enumerate(positions):
        if i in used:
            continue
        cluster = [i]
        lon1 = astro.ecliptic_longitude(p1)
        for j, p2 in enumerate(positions):
            if j <= i or j in used:
                continue
            lon2 = astro.ecliptic_longitude(p2)
            if astro.angular_distance(lon1, lon2) <= orb:
                cluster.append(j)
        if len(cluster) >= 3:
            stelliums.append(cluster)
            used.update(cluster)
    return stelliums


def decollide_positions(positions, stelliums, min_sep=8):
    """Spread overlapping glyphs around a stellium centre."""
    adjusted = [astro.ecliptic_longitude(p) for p in positions]
    for cluster in stelliums:
        if len(cluster) < 2:
            continue
        lons = [astro.ecliptic_longitude(positions[i]) for i in cluster]
        center = sum(lons) / len(lons)
        for idx, i in enumerate(cluster):
            offset = (idx - len(cluster) / 2 + 0.5) * min_sep
            adjusted[i] = normalize_angle(center + offset)
    return adjusted


def _house_cusp_longitude(house):
    if house.get("cusp") is not None:
        return float(house["cusp"])
    if house.get("longitude") is not None:
        return float(house["longitude"])
    raise KeyError("house is missing cusp")


def _aspect_name(aspect):
    return aspect.get("aspect_name") or aspect.get("aspect") or ""


def draw_wheel_svg(positions, houses, aspects, asc_lon, width=800):
    """Return an SVG natal wheel string."""
    positions = _main_positions(positions)
    if not positions or not houses:
        return None

    height = width
    center_x = width / 2
    center_y = height / 2

    outer_r = width * 0.45
    sign_r = width * 0.38
    planet_r = width * 0.30
    inner_r = width * 0.15

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">\n'
    )
    svg += f'<rect width="{width}" height="{height}" fill="{BG_COLOR}"/>\n'
    svg += f'<circle cx="{center_x}" cy="{center_y}" r="{outer_r}" fill="none" stroke="{RING_COLOR}" stroke-width="2"/>\n'
    svg += f'<circle cx="{center_x}" cy="{center_y}" r="{sign_r}" fill="none" stroke="{RING_COLOR}" stroke-width="2"/>\n'
    svg += f'<circle cx="{center_x}" cy="{center_y}" r="{planet_r}" fill="none" stroke="{RING_COLOR}" stroke-width="1"/>\n'
    svg += f'<circle cx="{center_x}" cy="{center_y}" r="{inner_r}" fill="none" stroke="{RING_COLOR}" stroke-width="2"/>\n'

    for house in houses[:12]:
        try:
            cusp_lon = _house_cusp_longitude(house)
        except (KeyError, TypeError, ValueError):
            continue
        angle_rad = math.radians(chart_to_drawing_angle(cusp_lon, asc_lon))
        x1 = center_x + inner_r * math.cos(angle_rad)
        y1 = center_y + inner_r * math.sin(angle_rad)
        x2 = center_x + planet_r * math.cos(angle_rad)
        y2 = center_y + planet_r * math.sin(angle_rad)
        svg += f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{RING_COLOR}" stroke-width="1"/>\n'

    for i, sign in enumerate(astro.ZODIAC_SIGNS):
        sign_lon = i * 30 + 15
        angle_rad = math.radians(chart_to_drawing_angle(sign_lon, asc_lon))
        r_text = (sign_r + outer_r) / 2
        x = center_x + r_text * math.cos(angle_rad)
        y = center_y + r_text * math.sin(angle_rad)
        glyph = SIGN_GLYPHS.get(sign, sign[0])
        color = SIGN_COLORS.get(sign, TEXT_COLOR)
        svg += (
            f'<text x="{x}" y="{y}" fill="{color}" font-size="20" text-anchor="middle" '
            f'dominant-baseline="middle" font-family="DejaVu Sans">{glyph}</text>\n'
        )

    stelliums = detect_stellium(positions)
    adjusted_lons = decollide_positions(positions, stelliums)
    index_by_id = {astro.planet_id(p): i for i, p in enumerate(positions)}

    for aspect in aspects[:30]:
        p1_idx = index_by_id.get(astro.planet_id(aspect.get("planet1", "")))
        p2_idx = index_by_id.get(astro.planet_id(aspect.get("planet2", "")))
        if p1_idx is None or p2_idx is None:
            continue
        angle1_rad = math.radians(chart_to_drawing_angle(adjusted_lons[p1_idx], asc_lon))
        angle2_rad = math.radians(chart_to_drawing_angle(adjusted_lons[p2_idx], asc_lon))
        x1 = center_x + inner_r * math.cos(angle1_rad)
        y1 = center_y + inner_r * math.sin(angle1_rad)
        x2 = center_x + inner_r * math.cos(angle2_rad)
        y2 = center_y + inner_r * math.sin(angle2_rad)
        name = _aspect_name(aspect)
        color = ASPECT_COLORS.get(name, TEXT_COLOR)
        orb = astro.true_aspect_orb(aspect)
        opacity = max(0.3, 1.0 - orb / 8.0)
        svg += (
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" '
            f'stroke-width="1" opacity="{opacity}"/>\n'
        )

    for i, planet in enumerate(positions):
        angle_rad = math.radians(chart_to_drawing_angle(adjusted_lons[i], asc_lon))
        r_planet = (planet_r + sign_r) / 2
        x = center_x + r_planet * math.cos(angle_rad)
        y = center_y + r_planet * math.sin(angle_rad)
        display = astro.planet_display_name(planet)
        glyph = PLANET_GLYPHS.get(display, display[:1] or "•")
        svg += (
            f'<text x="{x}" y="{y}" fill="{TEXT_COLOR}" font-size="18" text-anchor="middle" '
            f'dominant-baseline="middle" font-family="DejaVu Sans">{glyph}</text>\n'
        )

    svg += "</svg>"
    return svg


def generate_chart_wheel_png(positions, houses, aspects, asc_lon, width=800):
    """PNG bytes, or None if CairoSVG is missing or rendering fails."""
    svg = draw_wheel_svg(positions, houses, aspects, asc_lon, width)
    if svg is None or not CAIROSVG_AVAILABLE:
        return None
    try:
        return svg2png(bytestring=svg.encode("utf-8"))
    except Exception as e:
        logger.error("PNG generation failed: %s", e)
        return None
