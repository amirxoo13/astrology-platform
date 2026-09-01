# Swiss Ephemeris Data Files

This directory is where the Swiss Ephemeris `.se1` data files should be placed.
The API will not function without these files — `/health` will return 503.

> **Important**: The file extension is `.se1`, not `.se`.
> The older `.se` format has been deprecated. Use only `.se1` files.

## Required Files

All four files are required for full functionality:


| File          | Covers                                        | Download                                                                             |
| ------------- | --------------------------------------------- | ------------------------------------------------------------------------------------ |
| `sepl_18.se1` | Sun–Pluto (Jupiter–Pluto, DE431)              | [GitHub](https://raw.githubusercontent.com/aloistr/swisseph/master/ephe/sepl_18.se1) |
| `semo_18.se1` | Moon                                          | [GitHub](https://raw.githubusercontent.com/aloistr/swisseph/master/ephe/semo_18.se1) |
| `seas_18.se1` | Asteroid bundle (Ceres, Pallas, Juno, Vesta…) | [GitHub](https://raw.githubusercontent.com/aloistr/swisseph/master/ephe/seas_18.se1) |


Quick download script:

```bash
curl -o ephe/sepl_18.se1 https://raw.githubusercontent.com/aloistr/swisseph/master/ephe/sepl_18.se1
curl -o ephe/semo_18.se1 https://raw.githubusercontent.com/aloistr/swisseph/master/ephe/semo_18.se1
curl -o ephe/seas_18.se1 https://raw.githubusercontent.com/aloistr/swisseph/master/ephe/seas_18.se1
curl -o ephe/sefstars.txt https://raw.githubusercontent.com/aloistr/swisseph/master/ephe/sefstars.txt
```

## Extended Time Range (Optional)

The standard files above cover **1301–1701 AD**. For historical or future calculations
outside this range, the full archive (~2.4 GB, covers **13201 BC–17191 AD**) is available
via the Astro.com Dropbox link (may expire):

> ⚠️ **The Dropbox share link (`swedownload_e.htm`) may expire.** If it no longer works,
> individual long-range files can be downloaded from [ephe.scryr.io](https://ephe.scryr.io/ephe/).
> Asteroid files in `long_ast/` folders cover 3000 BCE–2999 CE.

If the Dropbox link works:

```bash
curl -L "https://www.dropbox.com/scl/fo/y3naz62gy6f6qfrhquu7u/h?rlkey=ejltdhb262zglm7eo6yfj2940&dl=1" -o ephe/swe_unix.tar.gz
tar -xzf ephe/swe_unix.tar.gz -C ephe/
```

## Asteroid Files

Asteroid files are organized in `ast{N}/` subdirectories where `N = asteroid_number // 1000`.

**Ceres, Pallas, Juno, Vesta** are included in `seas_18.se1` (main asteroid bundle) — no separate files needed.

| Subdirectory | Covers | Notable asteroids |
|---|---|---|
| `ast0/` | Asteroids 0–999 | (covered by `seas_18.se1`) |
| `ast2/` | Asteroids 2000–2999 | `se02060.se1` (Chiron, 6000-year range) |

Download Chiron from the Astro.com mirror:

```bash
mkdir -p ephe/ast2
curl -o ephe/ast2/se02060.se1 https://ephe.scryr.io/ephe/ast2/se02060.se1
```

> **Note**: The Astro.com Dropbox archive (swedownload_e.htm) also contains these files,
> but the link may expire. The scryr.io mirror is a reliable alternative.
> For any numbered asteroid not listed here, see [swedownload_e.htm](https://www.astro.com/swisseph/swedownload_e.htm)
> for the full folder structure.

## Licensing

The `.se1` data files are distributed by **Astrodienst AG** under their own license:

> Swiss Ephemeris is free for **non-commercial use**. For commercial use,
> a license must be obtained from Astrodienst AG.
> See: [https://www.astro.com/swisseph/swephinfo_e.htm](https://www.astro.com/swisseph/swephinfo_e.htm)

The API source code itself is released under **AGPL-3.0-or-later**.