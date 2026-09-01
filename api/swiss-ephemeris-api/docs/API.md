# Swiss Ephemeris API — API Reference

**Version**: 0.1.0
**License**: [AGPL-3.0-or-later](https://www.gnu.org/licenses/agpl-3.0.html)
**Source**: `https://github.com/devtrongle/Swiss-Ephemeris-API`

This document is the authoritative reference for all public API endpoints.
Base URL: `https://your-host.com` (or `http://localhost:8000` locally)

---

## Table of Contents

1. [Conventions](#1-conventions)
2. [Common Types](#2-common-types)
3. [Endpoints](#3-endpoints)
   - [GET /](#31-get-)
   - [GET /health](#32-get-health)
   - [POST /api/v1/planets](#33-post-apiv1planets)
   - [POST /api/v1/houses](#34-post-apiv1houses)
   - [POST /api/v1/birth-chart](#35-post-apiv1birth-chart)
   - [POST /api/v1/fixed-stars](#36-post-apiv1fixed-stars)
   - [GET /api/v1/eclipses](#37-get-apiv1eclipses)
   - [POST /api/v1/lunar-phase](#38-post-apiv1lunar-phase)
   - [POST /api/v1/lunar-nodes](#39-post-apiv1lunar-nodes)
   - [POST /api/v1/special-points](#310-post-apiv1special-points)
   - [POST /api/v1/aspects](#311-post-apiv1aspects)
4. [Error Format](#4-error-format)

---

## 1. Conventions

| Convention | Value |
|---|---|
| HTTP method | `POST` for all calculation endpoints; `GET` for eclipse search |
| Content-Type | `application/json` |
| Authentication | None (public API) |
| License header | Every response includes `"license": "AGPL-3.0-or-later"` |
| Date format | ISO 8601 strings |
| Coordinate system | Tropical zodiac (0° = Aries spring equinox), geocentric ecliptic coordinates |
| Sidereal mode | Set `ayanamsa` parameter; see [Ayanamsa Values](#ayanamsa-values) |
| Time handling | All input times are converted to Julian Day (UT) internally |
| House systems | Character codes; see [House System Values](#house-system-values) |

### Response Envelope

Every successful response extends `BaseResponse`:

```json
{
  "license": "AGPL-3.0-or-later"
}
```

### Decimal Precision

| Field | Precision |
|---|---|
| Longitude, latitude, speed | 6 decimal places |
| Julian Day | 9 decimal places |
| Distance (AU) | 8 decimal places |
| Illumination (%) | 4 decimal places |

---

## 2. Common Types

### 2.1 Zodiac Signs

| sign_num | sign | Element |
|---|---|---|
| 0 | Aries | FIRE |
| 1 | Taurus | EARTH |
| 2 | Gemini | AIR |
| 3 | Cancer | WATER |
| 4 | Leo | FIRE |
| 5 | Virgo | EARTH |
| 6 | Libra | AIR |
| 7 | Scorpio | WATER |
| 8 | Sagittarius | FIRE |
| 9 | Capricorn | EARTH |
| 10 | Aquarius | AIR |
| 11 | Pisces | WATER |

### 2.2 Planet Identifiers

```
SUN, MOON, MERCURY, VENUS, MARS,
JUPITER, SATURN, URANUS, NEPTUNE, PLUTO,
CHIRON, CERES, PALLAS, JUNO, VESTA, EARTH
```

### 2.3 House System Values

| Value | System |
|---|---|
| `P` | Placidus (default) |
| `K` | Koch |
| `W` | Whole Sign |
| `E` | Equal (cusp 1 = Ascendant) |
| `O` | Porphyrius |
| `R` | Regiomontanus |
| `C` | Campanus |
| `B` | Alcabitius |
| `M` | Morinus |

> Note: `N` (Equal/1=Aries), `D` (Equal/MC), `V` (Vehlow equal), and `G` (Gauquelin sectors) are also supported by Swiss Ephemeris but not exposed via this API. Koch (`K`) and Gauquelin cannot be computed for locations beyond the polar circle.

### 2.4 Ayanamsa Values

| Value | Description |
|---|---|
| `TROPICAL` | Default; no sidereal correction |
| `LAHIRI` | Indian national standard |
| `KRISHNAMURTI` | Krishnamurti–Verghote |
| `DE_LUCE` | De Luce |
| `RAMAN` | Bangalore Raman |
| `USHA_SHASTHRA` | Usha Shastra |
| `YUKTESHWAR` | Yukteshwar |
| `SURYASIDDHANTA` | Suryasiddhanta |
| `GALCENT_0SAG` | Galactic Centre at 0° Sagittarius |
| `SS_CITRA` | Sri Sri Sri Chitraputhra |
| `SS_REVATI` | Sri Sri Sri Revati |

### 2.5 Lunar Node Types

| Value | Description |
|---|---|
| `TRUE` | True (oscillating) North Lunar Node (default) |
| `MEAN` | Mean (average) North Lunar Node |

### 2.6 Lilith Types

| Value | Description |
|---|---|
| `TRUE` | True Lilith — apogee of Moon's orbit (default) |
| `MEAN` | Mean Lilith — mean apogee |

### 2.7 Special Point Types

| Value | Description |
|---|---|
| `PART_OF_FORTUNE` | Part of Fortune (AS + Moon − Sun) |
| `VERTEX` | Vertex — right vertical point |
| `ANTI_VERTEX` | Anti-Vertex — opposite of Vertex |

---

## 3. Endpoints

---

### 3.1 GET /

Root endpoint returning project metadata and AGPL license notice.

**Response**

```json
{
  "name": "swiss-ephemeris-api",
  "version": "0.1.0",
  "license": "AGPL-3.0-or-later",
  "notice": "This project is based on Swiss Ephemeris by Astrodienst AG...",
  "docs": "/docs",
  "redoc": "/redoc"
}
```

---

### 3.2 GET /health

Health check verifying Swiss Ephemeris initialization.

**Response (200 OK)**

```json
{
  "status": "ok",
  "ephe_path": "./ephe",
  "source": "https://github.com/devtrongle/Swiss-Ephemeris-API"
}
```

**Response (503 Service Unavailable)** — if ephemeris files are missing.

---

### 3.3 POST /api/v1/planets

Calculate ecliptic positions for one or more planets.

**Request body**

```json
{
  "datetime": "1990-01-15T12:00:00",
  "timezone": "Asia/Ho_Chi_Minh",
  "latitude": 21.0285,
  "longitude": 105.8542,
  "planets": ["SUN", "MOON", "MERCURY", "VENUS", "MARS"],
  "ayanamsa": "TROPICAL",
  "house_system": "P"
}
```

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `datetime` | string | Yes | — | ISO 8601 datetime string |
| `timezone` | string | Yes | — | IANA timezone name (e.g. `Asia/Ho_Chi_Minh`, `UTC`) |
| `latitude` | number | Yes | — | −90 to 90 degrees |
| `longitude` | number | Yes | — | −180 to 180 degrees |
| `planets` | string[] | No | all 16 | List of planet identifiers |
| `ayanamsa` | string | No | `TROPICAL` | Sidereal ayanamsa |
| `house_system` | string | No | `P` | House system character code |

**Response**

```json
{
  "license": "AGPL-3.0-or-later",
  "request": { ... },
  "julian_day_ut": 2447893.958333,
  "ascendant": 295.423100,
  "medium_coeli": 123.456789,
  "ayanamsa_name": "TROPICAL",
  "ayanamsa_value": 0.0,
  "positions": [
    {
      "planet": "SUN",
      "name": "Sun",
      "longitude": 295.423100,
      "latitude": -0.000123,
      "distance": 0.98345678,
      "sign": "Capricorn",
      "sign_num": 9,
      "degree_in_sign": 25.423100,
      "degree_minute": 25,
      "degree_second": 25,
      "speed": 0.956123,
      "retrograde": false
    }
  ]
}
```

---

### 3.4 POST /api/v1/houses

Calculate house cusps and ascendant/MC.

**Request body**

```json
{
  "datetime": "1990-01-15T12:00:00",
  "timezone": "Asia/Ho_Chi_Minh",
  "latitude": 21.0285,
  "longitude": 105.8542,
  "house_system": "P",
  "ayanamsa": "TROPICAL"
}
```

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `datetime` | string | Yes | — | ISO 8601 datetime string |
| `timezone` | string | Yes | — | IANA timezone name |
| `latitude` | number | Yes | — | −90 to 90 degrees |
| `longitude` | number | Yes | — | −180 to 180 degrees |
| `house_system` | string | No | `P` | House system character |
| `ayanamsa` | string | No | `TROPICAL` | Sidereal ayanamsa |

**Response**

```json
{
  "license": "AGPL-3.0-or-later",
  "request": { ... },
  "julian_day_ut": 2447893.958333,
  "ascendant": 295.423100,
  "medium_coeli": 123.456789,
  "ayanamsa_value": 0.0,
  "houses": [
    {
      "house": 1,
      "cusp": 295.423100,
      "sign": "Capricorn",
      "sign_num": 9,
      "degree_in_sign": 25.423100,
      "element": "EARTH"
    }
  ]
}
```

---

### 3.5 POST /api/v1/birth-chart

Combined planet positions + house cusps + ASC/MC in a single request.

**Request body**

```json
{
  "datetime": "1990-01-15T12:00:00",
  "timezone": "Asia/Ho_Chi_Minh",
  "latitude": 21.0285,
  "longitude": 105.8542,
  "house_system": "P",
  "ayanamsa": "TROPICAL",
  "include_planets": true
}
```

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `datetime` | string | Yes | — | ISO 8601 datetime string |
| `timezone` | string | Yes | — | IANA timezone name |
| `latitude` | number | Yes | — | −90 to 90 degrees |
| `longitude` | number | Yes | — | −180 to 180 degrees |
| `house_system` | string | No | `P` | House system character |
| `ayanamsa` | string | No | `TROPICAL` | Sidereal ayanamsa |
| `include_planets` | boolean | No | `true` | Whether to include planet positions |

**Response**

```json
{
  "license": "AGPL-3.0-or-later",
  "request": { ... },
  "julian_day_ut": 2447893.958333,
  "ascendant": 295.423100,
  "medium_coeli": 123.456789,
  "ayanamsa_name": "TROPICAL",
  "ayanamsa_value": 0.0,
  "positions": [ /* PlanetPosition[] — see /planets */ ],
  "houses": [ /* HouseData[] — see /houses */ ]
}
```

---

### 3.6 POST /api/v1/fixed-stars

Calculate positions for one or more fixed stars.

**Request body**

```json
{
  "datetime": "1990-01-15T12:00:00",
  "timezone": "Asia/Ho_Chi_Minh",
  "stars": ["Sirius", "Regulus", "Antares"]
}
```

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `datetime` | string | Yes | — | ISO 8601 datetime string |
| `timezone` | string | Yes | — | IANA timezone name |
| `stars` | string[] | No | all 30 | Star names |

**Available stars** (30 major fixed stars):

```
Alphard, Alcyone, Aldebaran, Algol, Alhena, Alpheratz,
Altair, Antares, Arcturus, Bellatrix, Betelgeuse, Canopus,
Capella, Deneb, Denebola, Dubhe, Elnath, Fomalhaut,
Hamul, Kaus Australis, Markab, Menkar, Miaplacidus, Mira,
Nunki, Polaris, Pollux, Procyon, Regulus, Rigel, Sadir,
Sirius, Spica, Thuban, Vega
```

**Response**

```json
{
  "license": "AGPL-3.0-or-later",
  "request": { ... },
  "julian_day_ut": 2447893.958333,
  "positions": [
    {
      "star": "Sirius",
      "longitude": 143.527811,
      "latitude": -39.029877,
      "sign": "Leo",
      "sign_num": 4,
      "degree_in_sign": 23.527811,
      "magnitude": -1.46
    }
  ]
}
```

---

### 3.7 GET /api/v1/eclipses

Find all eclipses of a given type within a date range.

**Query parameters**

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `start_date` | string | No | `2020-01-01` | ISO date |
| `end_date` | string | No | `2030-01-01` | ISO date |
| `type` | string | No | `SOLAR` | `SOLAR` or `LUNAR` |
| `latitude` | number | No | — | Observer latitude (for local circumstances) |
| `longitude` | number | No | — | Observer longitude (for local circumstances) |

**Response**

```json
{
  "license": "AGPL-3.0-or-later",
  "request": { ... },
  "eclipses": [
    {
      "type": "SOLAR",
      "date": "2020-12-14",
      "julian_day": 2459200.5,
      "magnitude": 0.97,
      "saros": 142,
      "visible_from_lat": 21.0285,
      "visible_from_lon": 105.8542
    }
  ]
}
```

---

### 3.8 POST /api/v1/lunar-phase

Calculate lunar phase, illumination, elongation, and lunar age.

**Request body**

```json
{
  "datetime": "1990-01-15T12:00:00",
  "timezone": "Asia/Ho_Chi_Minh"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `datetime` | string | Yes | ISO 8601 datetime string |
| `timezone` | string | Yes | IANA timezone name |

**Response**

```json
{
  "license": "AGPL-3.0-or-later",
  "request": { ... },
  "julian_day_ut": 2447893.958333,
  "phase": {
    "phase": "FULL",
    "phase_angle": 180.123456,
    "illumination": 99.8234,
    "elongation": 180.123456,
    "age_days": 14.765294
  }
}
```

**Phase names**: `NEW`, `WAXING_CRESCENT`, `FIRST_QUARTER`, `WAXING_GIBBOUS`, `FULL`, `WANING_GIBBOUS`, `LAST_QUARTER`, `WANING_CRESCENT`

---

### 3.9 POST /api/v1/lunar-nodes

Calculate North/South Lunar Nodes and Lilith (Black Moon), including house placements.

**Request body**

```json
{
  "datetime": "1990-01-15T12:00:00",
  "timezone": "Asia/Ho_Chi_Minh",
  "latitude": 21.0285,
  "longitude": 105.8542,
  "house_system": "P",
  "ayanamsa": "TROPICAL",
  "node_type": "TRUE",
  "lilith_type": "TRUE"
}
```

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `datetime` | string | Yes | — | ISO 8601 datetime string |
| `timezone` | string | Yes | — | IANA timezone name |
| `latitude` | number | Yes | — | −90 to 90 degrees |
| `longitude` | number | Yes | — | −180 to 180 degrees |
| `house_system` | string | No | `P` | House system character |
| `ayanamsa` | string | No | `TROPICAL` | Sidereal ayanamsa |
| `node_type` | string | No | `TRUE` | `TRUE` or `MEAN` |
| `lilith_type` | string | No | `TRUE` | `TRUE` or `MEAN` |

**Response**

```json
{
  "license": "AGPL-3.0-or-later",
  "request": { ... },
  "julian_day_ut": 2447893.958333,
  "ascendant": 295.423100,
  "medium_coeli": 123.456789,
  "ayanamsa_value": 0.0,
  "north_node": {
    "node_type": "TRUE",
    "north_longitude": 82.456123,
    "south_longitude": 262.456123,
    "north_sign": "Leo",
    "north_sign_num": 4,
    "north_degree_in_sign": 22.456123,
    "north_speed": -0.002345,
    "north_retrograde": true,
    "south_sign": "Aquarius",
    "south_sign_num": 10,
    "south_degree_in_sign": 22.456123,
    "north_house": 5,
    "south_house": 11
  },
  "lilith": {
    "lilith_type": "TRUE",
    "longitude": 315.789012,
    "sign": "Pisces",
    "sign_num": 11,
    "degree_in_sign": 15.789012,
    "speed": 0.011234,
    "retrograde": false,
    "house": 12
  }
}
```

---

### 3.10 POST /api/v1/special-points

Calculate Part of Fortune, Vertex, and Anti-Vertex.

**Request body**

```json
{
  "datetime": "1990-01-15T12:00:00",
  "timezone": "Asia/Ho_Chi_Minh",
  "latitude": 21.0285,
  "longitude": 105.8542,
  "house_system": "P",
  "ayanamsa": "TROPICAL",
  "points": ["PART_OF_FORTUNE", "VERTEX", "ANTI_VERTEX"]
}
```

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `datetime` | string | Yes | — | ISO 8601 datetime string |
| `timezone` | string | Yes | — | IANA timezone name |
| `latitude` | number | Yes | — | −90 to 90 degrees |
| `longitude` | number | Yes | — | −180 to 180 degrees |
| `house_system` | string | No | `P` | House system character |
| `ayanamsa` | string | No | `TROPICAL` | Sidereal ayanamsa |
| `points` | string[] | No | all three | List of point types |

**Response**

```json
{
  "license": "AGPL-3.0-or-later",
  "request": { ... },
  "julian_day_ut": 2447893.958333,
  "ascendant": 295.423100,
  "medium_coeli": 123.456789,
  "ayanamsa_value": 0.0,
  "positions": [
    {
      "point_type": "PART_OF_FORTUNE",
      "longitude": 12.345678,
      "sign": "Aries",
      "sign_num": 0,
      "degree_in_sign": 12.345678,
      "house": 1
    },
    {
      "point_type": "VERTEX",
      "longitude": 78.901234,
      "sign": "Cancer",
      "sign_num": 3,
      "degree_in_sign": 18.901234,
      "house": 4
    },
    {
      "point_type": "ANTI_VERTEX",
      "longitude": 258.901234,
      "sign": "Scorpio",
      "sign_num": 7,
      "degree_in_sign": 18.901234,
      "house": 10
    }
  ]
}
```

---

### 3.11 POST /api/v1/aspects

Calculate astrological aspects between planets.

**Request body**

```json
{
  "datetime": "1990-01-15T12:00:00",
  "timezone": "Asia/Ho_Chi_Minh",
  "latitude": 21.0285,
  "longitude": 105.8542,
  "planets": ["SUN", "MOON", "MARS", "VENUS", "JUPITER", "SATURN"],
  "include_minor": false
}
```

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `datetime` | string | Yes | — | ISO 8601 datetime string |
| `timezone` | string | Yes | — | IANA timezone name |
| `latitude` | number | Yes | — | −90 to 90 degrees |
| `longitude` | number | Yes | — | −180 to 180 degrees |
| `planets` | string[] | No | all 14 | Planets to check |
| `include_minor` | boolean | No | `false` | Include minor aspects |

**Major aspects** (always included): CONJUNCTION, OPPOSITION, TRINE, SQUARE, SEXTILE.

**Minor aspects** (when `include_minor=true`): SEMI_SEXTILE, SEMI_SQUARE, SESQUIQUADRATE, QUINTILE, BIQUINTILE, TREDEGILE.

**Response**

```json
{
  "license": "AGPL-3.0-or-later",
  "request": { ... },
  "julian_day_ut": 2447906.708333,
  "aspects": [
    {
      "planet1": "SUN",
      "planet2": "MOON",
      "aspect_name": "TRINE",
      "orb": 6.50,
      "exactness": 1.50,
      "planet1_longitude": 294.781269,
      "planet2_longitude": 193.527811
    }
  ]
}
```

> `orb` is positive when within orb width, decreasing toward 0 at exact. `exactness` = orb_width − diff.

---

## 4. Error Format

All errors return a consistent JSON structure:

```json
{
  "error": "Validation Error",
  "detail": "Unknown planet(s): ['INVALID']. Valid: ['SUN', 'MOON', ...]",
  "code": "VALIDATION_ERROR"
}
```

| HTTP Status | Meaning |
|---|---|
| `200` | Success |
| `422` | Validation error (invalid input) |
| `500` | Internal server error (Swiss Ephemeris failure) |
| `503` | Service unavailable (ephemeris files not found) |

---

## Appendix A: Swiss Ephemeris Acknowledgement

This API uses the Swiss Ephemeris library by [Astrodienst AG](https://www.astro.com/swisseph/).
Swiss Ephemeris is free for non-commercial use. For commercial use,
a license must be obtained from Astrodienst AG.
