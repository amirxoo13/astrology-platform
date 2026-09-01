---
name: swiss-ephemeris-api
description: Build and maintain the swiss-ephemeris-api project. Use when creating, editing, or auditing files in this repository. Covers FastAPI endpoints, pysweph wrapper (import swisseph as swe), Pydantic schemas, AGPL-3.0 compliance, and Swiss Ephemeris astronomy calculations.
---

# swiss-ephemeris-api Skill

## Quick Reference

| Item | Value |
|---|---|
| License | AGPL-3.0-or-later |
| Python | 3.12+ |
| HTTP framework | FastAPI |
| Ephemeris lib | `pysweph` (community fork) — `import swisseph as swe` |
| Validation | Pydantic v2 |
| Testing | pytest + pytest-asyncio |

## Critical Rules

1. **NEVER call `swisseph` directly in `async def`** — use `asyncio.to_thread()`
2. **`set_ephe_path()` is ONE-TIME at app startup** — process-global, never per-request
3. **AGPL everywhere** — no NPML code, source always public
4. **`GET /` must return AGPL notice + GitHub source URL**
5. **Return Pydantic models, never raw dicts**
6. **`PlanetEnum` values must match `swe.SUN`, `swe.MOON`, etc.**

## Standard Request Format

```json
{
  "datetime": "1990-01-15T12:00:00",
  "timezone": "Asia/Ho_Chi_Minh",
  "latitude": 21.0285,
  "longitude": 105.8542,
  "house_system": "P",
  "ayanamsa": "LAHIRI"
}
```

## Standard Response Format (Planet)

```json
{
  "planet": "SUN",
  "name": "Sun",
  "longitude": 295.42,
  "sign": "CAPRICORN",
  "sign_num": 9,
  "degree_in_sign": 25.42,
  "minute": 25,
  "second": 25,
  "speed": -0.95,
  "retrograde": false
}
```

## Key swisseph Constants

```python
# Planets
swe.SUN=0, swe.MOON=1, swe.MERCURY=2, swe.VENUS=3, swe.MARS=4
swe.JUPITER=5, swe.SATURN=6, swe.URANUS=7, swe.NEPTUNE=8, swe.PLUTO=9
swe.CHIRON=15, swe.CERES=17, swe.PALLAS=18, swe.JUNO=19, swe.VESTA=20, swe.EARTH=14

# Lunar Nodes
swe.TRUE_NODE=11    # North True Node (oscillating)
swe.MEAN_NODE=10    # North Mean Node

# South Node = North Node + 180° (computed manually, no swe constant)
# Anti-Vertex = Vertex + 180° (computed manually, no swe constant)
# Part of Fortune = ASC + Moon - Sun (computed manually, no swe constant)
# swe.TRUE_SOUTH_NODE, swe.MEAN_SOUTH_NODE, swe.TRUE_LILITH, swe.MEAN_LILITH
# do NOT exist in pysweph 2.10.3.6.

# nod_aps_ut / nod_aps return structure:
# (asc_node, dsc_node, perigee, apogee)  ← 4 elements, apogee at index 3
# Use nod_aps_ut (UT) not nod_aps (ET) for consistency.

# Flags (pysweph 2.10.3.6):
swe.FLG_SWIEPH   =   2   # Swiss Ephemeris (NOT 256!)
swe.FLG_SPEED    = 256   # include speed
swe.FLG_SIDEREAL = 65536 # tropical/sidereal toggle

# NODBIT constants:
swe.NODBIT_MEAN      = 1   # mean node
swe.NODBIT_OSCU      = 2   # oscillating (true) node
swe.NODBIT_FOPOINT   = 256 # focl point (apogee/Lilith)
# Combine: NODBIT_OSCU | NODBIT_FOPOINT = 258 (True Lilith)
#          NODBIT_MEAN | NODBIT_FOPOINT = 257 (Mean Lilith)

# Sidereal ayanamsa constants:
swe.SIDM_LAHIRI, swe.SIDM_KRISHNAMURTI, swe.SIDM_DELUCE, swe.SIDM_RAMAN,
swe.SIDM_USHASHASHI, swe.SIDM_YUKTESHWAR, swe.SIDM_SURYASIDDHANTA,
swe.SIDM_GALCENT_0SAG, swe.SIDM_SS_CITRA, swe.SIDM_SS_REVATI

# House systems (char code → pass as string 'P', encode to b'P'):
'P' Placidus, 'K' Koch, 'W' Whole Sign, 'E' Equal, 'O' Porphyrius,
'R' Regiomontanus, 'C' Campanus, 'B' Alcabitius, 'M' Morinus
```

## async/sync Bridge Pattern (Python 3.11+)

```python
import asyncio

# swe is a C extension — NEVER call directly in async def
# Use asyncio.to_thread() (Python 3.11+) instead of run_in_executor
result = await asyncio.to_thread(swe.calc_ut, jd_ut, planet, flags)

# For multiple parallel computations:
results = await asyncio.gather(
    asyncio.to_thread(swe.calc_ut, jd_ut, planet1, flags),
    asyncio.to_thread(swe.calc_ut, jd_ut, planet2, flags),
)
```

```python
# UTC datetime → Julian Day (UT)
jd_ut = await asyncio.to_thread(swe.julday, year, month, day, hour)
# Note: swe.julday expects hour as decimal (0-24)

# Reverse: Julian Day → calendar
year, month, day, hour = await asyncio.to_thread(swe.revjul, jd_ut, swe.GREG_CAL)
```

## Sign Parsing (from degree 0-360)

| degree range | sign | num |
|---|---|---|
| 0-29.99 | Aries | 0 |
| 30-59.99 | Taurus | 1 |
| ... | ... | ... |
| 270-299.99 | Scorpio | 8 |
| 300-329.99 | Sagittarius | 9 |
| 330-359.99 | Capricorn | 10 |

## Retrograde Detection

```python
# All planets from Mercury outward can be retrograde when speed_long < 0
# Moon is NEVER retrograde (geocentric model — speed always positive relative to Earth)
# Sun is NEVER retrograde
is_retrograde = speed_long < 0 if planet >= swe.MERCURY else False
```

## File Order for New Work

1. Check `.cursor/rules/10-swiss-ephemeris-api.mdc` for standards
2. `schemas/common.py` if shared input types needed
3. `schemas/<domain>.py` for request/response models
4. `services/<domain>.py` for business logic
5. `core/swisseph_core.py` if new swisseph call needed
6. `api/v1/endpoints/<domain>.py` for route handler
7. Register route in `api/v1/router.py`
8. Add test in `tests/test_api/test_<domain>.py`

## AGPL Notice Template

Every response metadata should include:

```python
license: str = "AGPL-3.0-or-later"
source_url: str = "https://github.com/YOUR_USERNAME/swiss-ephemeris-api"
```

Root endpoint returns:

```markdown
This project is based on Swiss Ephemeris by Astrodienst and is released
under AGPL-3.0-or-later license. Source code must always be public and
match the code running on this server.
Source: https://github.com/YOUR_USERNAME/swiss-ephemeris-api
```
