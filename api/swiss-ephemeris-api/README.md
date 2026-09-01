# Swiss Ephemeris API

**License**: [AGPL-3.0-or-later](LICENSE) — Source code is always public and matches the running server.

REST API for Swiss Ephemeris astronomical calculations. Built with Python 3.12+, FastAPI, and [pysweph](https://github.com/sailorfe/pysweph).

> This project uses Swiss Ephemeris by [Astrodienst AG](https://www.astro.com/swisseph/swephinfo_e.htm).
> Swiss Ephemeris is free for non-commercial use. For commercial use,
> a license must be obtained from Astrodienst AG.

**Source**: https://github.com/devtrongle/swiss-ephemeris-api

---

## Features

| Category | Coverage |
|---|---|
| Planets | Sun–Pluto, Chiron, Ceres, Pallas, Juno, Vesta, Earth |
| Lunar Nodes | True/Mean North & South Node |
| Lilith | True/Mean Black Moon (apogee of Moon's orbit) |
| Special Points | Part of Fortune, Vertex, Anti-Vertex |
| Fixed Stars | 36 fixed stars |
| Houses | Placidus, Koch, Whole Sign, Equal, Porphyrius, Regiomontanus, Campanus, Alcabitius, Morinus (+6 more) |
| Sidereal | 11 ayanamsa systems (Lahiri, Krishnamurti, Raman, etc.) |
| Eclipses | Solar & Lunar (past and future) |
| Lunar Phase | Phase name, illumination %, elongation, lunar age |
| Aspects | Major & minor aspects between planets |

---

## Quick Start

### 1. Download ephemeris files

The API requires Swiss Ephemeris data files. Download from GitHub (aloistr mirror):

```bash
# Required — Sun–Pluto (Jupiter–Pluto, DE431, 1301–1701 AD)
curl -o ephe/sepl_18.se1 https://raw.githubusercontent.com/aloistr/swisseph/master/ephe/sepl_18.se1

# Required — Moon ephemeris
curl -o ephe/semo_18.se1 https://raw.githubusercontent.com/aloistr/swisseph/master/ephe/semo_18.se1

# Required — asteroid bundle (Ceres, Pallas, Juno, Vesta + many more)
curl -o ephe/seas_18.se1 https://raw.githubusercontent.com/aloistr/swisseph/master/ephe/seas_18.se1

# Required — fixed star catalog (36 major fixed stars)
curl -o ephe/sefstars.txt https://raw.githubusercontent.com/aloistr/swisseph/master/ephe/sefstars.txt
```

> **Why these four files?**
> `sepl_18.se1` covers Sun through Pluto (Jupiter–Pluto precision, DE431 ephemeris).
> `semo_18.se1` covers the Moon.
> `seas_18.se1` covers Ceres, Pallas, Juno, Vesta and other numbered asteroids.
> `sefstars.txt` covers 36 fixed stars.
>
> Without these files, `/health` returns 503.
>
> **Note**: File extension is `.se1` (not `.se`). The older `.se` format is deprecated.

**Chiron** (asteroid 2060) requires a separate file:

```bash
mkdir -p ephe/ast2
curl -o ephe/ast2/se02060.se1 https://ephe.scryr.io/ephe/ast2/se02060.se1
```

This covers ~3000 BCE to ~3000 CE.

**Extended time range** (before 1301 or after 1701) — the Dropbox archive
may expire; check [astro.com swedownload](https://www.astro.com/swisseph/swedownload_e.htm)
for the latest link. Individual long-range files are also on [ephe.scryr.io](https://ephe.scryr.io/ephe/).

### 2. Install dependencies

```bash
pip install -e .
```

### 3. Run

```bash
EPHE_PATH=$(pwd)/ephe uvicorn app.main:app --reload
```

Or with an `.env` file:

```bash
cp .env.example .env
# edit .env if needed
uvicorn app.main:app --reload
```

### 4. Verify

```bash
curl http://localhost:8000/health
# → {"status": "ok", "ephe_path": "./ephe", "source": "..."}

curl -X POST http://localhost:8000/api/v1/planets \
  -H "Content-Type: application/json" \
  -d '{
    "datetime": "1990-01-15T12:00:00",
    "timezone": "Asia/Ho_Chi_Minh",
    "latitude": 21.0285,
    "longitude": 105.8542
  }'
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Project info & AGPL notice |
| GET | `/health` | Health check |
| POST | `/api/v1/planets` | Planet positions (16 bodies) |
| POST | `/api/v1/houses` | House cusps & ASC/MC |
| POST | `/api/v1/birth-chart` | Planets + houses combined |
| POST | `/api/v1/fixed-stars` | 36 fixed star positions |
| GET | `/api/v1/eclipses` | Solar & lunar eclipses |
| POST | `/api/v1/lunar-phase` | Phase, illumination, lunar age |
| POST | `/api/v1/lunar-nodes` | North/South nodes + Lilith |
| POST | `/api/v1/special-points` | Part of Fortune, Vertex, Anti-Vertex |
| POST | `/api/v1/aspects` | Astrological aspects between planets |

Full documentation: [docs/API.md](docs/API.md)

---

## Docker

```bash
docker compose up --build
```

The Dockerfile automatically downloads the ephemeris files from the GitHub mirror.

---

## Configuration

| Variable | Default | Description |
|---|---|---|
| `EPHE_PATH` | `./ephe` | Path to directory containing `.se1` files |
| `HOST` | `0.0.0.0` | Bind host |
| `PORT` | `8000` | Bind port |
| `LOG_LEVEL` | `INFO` | Log level: `DEBUG`, `INFO`, `WARNING` |
| `CORS_ORIGINS` | `*` | CORS allowed origins (comma-separated) |

---

## License

This program is free software: you can redistribute it and/or modify it under
the terms of the **GNU Affero General Public License** (AGPL) version 3 or later.

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE. See the GNU AGPL for more details.

You should have received a copy of the GNU AGPL along with this program.
If not, see <https://www.gnu.org/licenses/>.

**Note**: Swiss Ephemeris data files (`.se1` files and `sefstars.txt`) have their
own license from Astrodienst AG. They are free for non-commercial use.
For commercial use, contact Astrodienst AG.
