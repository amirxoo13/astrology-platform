---
name: astrology-platform-resources
description: Persian astrology research directory covering Swiss Ephemeris, libraries, APIs, and chart requirements
---

# Astrology Platform Resources

این skill منابع و راهنماهای فنی برای توسعه پلتفرم استرولوژی را فراهم می‌کند.

## Swiss Ephemeris

### Core Library
- **Swiss Ephemeris** (AGPL): https://www.astro.com/swisseph/
- دقیق‌ترین کتابخانه محاسبات نجومی (JPL ephemeris base)
- پوشش: 13000 BC تا 17000 AD
- سیارات کلاسیک، Chiron، asteroids (Ceres, Pallas, Juno, Vesta)
- 15 سیستم خانه: Placidus, Koch, Equal, Whole Sign, Campanus, Regiomontanus, etc.
- Tropical و Sidereal zodiac
- **مجوز**: AGPL-3.0 (استفاده شبکه‌ای نیاز به انتشار کد دارد)

### Python Wrappers
- **pyswisseph**: https://github.com/astrorigin/pyswisseph
  - Wrapper رسمی C برای Python
  - نصب: `pip install pyswisseph`
  
- **swiss-ephemeris-api** (REST API): https://github.com/devtrongle/swiss-ephemeris-api
  - FastAPI wrapper روی pyswisseph
  - Endpoints: `/api/v1/birth-chart`, `/api/v1/aspects`, `/api/v1/transits`
  - استفاده در این پروژه: commit 8a03d63f1ca04224aa55817fcf0c4d4248328d8b

## Python Astrology Libraries

### Kerykeion
- https://github.com/g-battaglia/kerykeion
- کتابخانه high-level برای چارت‌های ناتال، synastry، transit
- SVG chart wheel generation
- Swiss Ephemeris backend
- نصب: `pip install kerykeion`

### Astrologer
- https://github.com/hoishing/astrologer
- Modern Python API برای محاسبات
- Type hints و async support
- Swiss Ephemeris wrapper

### Astropy
- https://www.astropy.org/
- نجوم علمی، coordinate systems, time scales
- برای محاسبات دقیق مکانی و زمانی

## SaaS Astrology APIs

### Astro-Seek API
- https://www.astro-seek.com/
- Free tier محدود
- Natal charts, transits, progressions

### Astrolog API
- https://www.astrolog.org/
- Open source astrology software
- Windows/Linux/Mac

## Vedic (Jyotish) Astrology

### Swiss Ephemeris Sidereal
- پشتیبانی کامل از zodiac های sidereal
- Lahiri ayanamsa (پیش‌فرض Vedic)
- Krishnamurti, Raman ayanamsas

### PyJyotish
- کتابخانه Vedic astrology
- Vimshottari Dasha, divisional charts (D1-D60)

## Chinese Astrology

### Four Pillars (BaZi) Libraries
- **pyBaZi**: https://github.com/0xflotus/pybazi
- محاسبه Heavenly Stems و Earthly Branches
- Ten Gods, Hidden Stems

### Lunar Calendar
- **LunarCalendar**: https://github.com/wolfhong/LunarCalendar
- تبدیل Gregorian ↔ Lunar

## Human Design

### BodyGraph Chart
- ترکیب I-Ching, Kabbalah, Chakras, Astrology
- محاسبه Personality (birth) و Design (88° قبل از تولد)
- 64 gates, 36 channels, 9 centers
- Swiss Ephemeris برای planetary activations

## Chart Visualization

### SVG Libraries
- **CairoSVG**: https://cairosvg.org/ - SVG to PNG/PDF
- **svgwrite**: https://svgwrite.readthedocs.io/ - Python SVG generation
- **matplotlib**: برای chart wheels با polar coordinates

### Cairo
- **pycairo**: Python bindings برای cairo graphics
- نصب: `pip install pycairo`
- fonts: DejaVu Sans (Unicode astrology glyphs)

### Chart Wheel Requirements
- ASC در 9 o'clock (East)
- Counterclockwise house numbering
- Aspect lines: conjunction, opposition, trine, square, sextile
- Color coding: elements (Fire/Earth/Air/Water), modalities
- Stellium detection و decollide text

## Geocoding & Timezone

### GeoNames
- **API**: http://api.geonames.org/
- رایگان با ثبت نام (username)
- City search, coordinates, timezone
- **در این پروژه**: `GEONAMES_USER` env var

### Nominatim (OpenStreetMap)
- https://nominatim.openstreetmap.org/
- رایگان، بدون API key
- **geopy**: `pip install geopy`

### TimezoneFinder
- https://github.com/jannikmi/timezonefinder
- Offline timezone resolution از coordinates
- نصب: `pip install timezonefinder`

### IANA Timezone Database
- https://www.iana.org/time-zones
- Standard timezone names (مثال: `Asia/Tehran`)
- **pytz**: `pip install pytz` (deprecated, استفاده از zoneinfo در Python 3.9+)

## Local Mean Time (LMT)

### تعریف
- زمان محلی قبل از استانداردسازی (قبل از 1880-1920)
- محاسبه: `UTC offset = longitude / 15`
- مثال: Einstein (Ulm, Germany lon=9.9876): offset ≈ +0.666 hours

### استفاده
- برای تاریخ‌های قدیمی (< 1900 معمولاً)
- بات از LMT پشتیبانی می‌کند: `birthtime.resolve_birth_utc()`

## Chart Calculation Checklist

### Natal Chart
1. Birth datetime (YYYY-MM-DD HH:MM)
2. Birth location (lat/lon)
3. Timezone یا LMT
4. House system (Placidus پیش‌فرض)
5. Zodiac (Tropical پیش‌فرض)
6. Planetary positions (10 classical + optionally Chiron, asteroids, nodes)
7. House cusps (12)
8. Aspects (major 5: ☌☍△□⚹)

### Synastry
1. دو natal chart کامل
2. Cross-aspects بین planets شخص1 و شخص2
3. Orb tighter (معمولاً 0.7× natal orbs)

### Composite
1. Midpoint هر planet بین دو chart
2. Midpoint ASC (از دو ASC)
3. Equal houses از composite ASC

### Transit
1. Natal chart (ثابت)
2. Current planetary positions
3. Aspects بین transiting planets و natal planets

### Solar Return
1. Natal Sun longitude
2. تاریخی که Sun به همان longitude برمی‌گردد (سالانه)
3. Location فعلی (نه birth location)

### Progressed (Secondary)
1. Natal chart
2. Progress rate: 1 day = 1 year
3. Progressed date = birth + N days (برای N سال)

## License Notes

### Swiss Ephemeris: AGPL-3.0
- ✅ استفاده شخصی/تحقیقاتی: آزاد
- ⚠️ استفاده شبکه‌ای (web app, bot): باید کد منبع منتشر شود
- ⚠️ استفاده تجاری: نیاز به مجوز جداگانه از Astrodienst یا رعایت AGPL

### این پروژه
- مجوز: **AGPL-3.0**
- تمام کدها open source
- استفاده تجاری مجاز با رعایت AGPL (انتشار کد)

## مراجع بیشتر

- **Astrodienst**: https://www.astro.com/ (Swiss Ephemeris maintainer)
- **Astrology API comparison**: https://rapidapi.com/collection/astrology-apis
- **Chart calculation algorithms**: "The American Ephemeris" by Neil F. Michelsen
- **Persian astrology forums**: http://www.astro.ir/

---

**نکته**: این skill فقط منبع اطلاعاتی است و باید در `.cursor/skills/` قرار گیرد، نه در runtime code.
