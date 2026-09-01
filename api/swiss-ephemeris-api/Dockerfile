FROM python:3.12-slim

WORKDIR /app

# Download required Swiss Ephemeris data files from the official GitHub source.
# File extension is .se1 (the older .se format is deprecated).
# - sepl_18.se1  : planets Jupiter–Pluto (DE431, 1301–1701)
# - semo_18.se1  : Moon / lunar ephemeris
# - seas_18.se1  : fixed star catalog (30 major stars used by this API)
# These three files are sufficient for all API endpoints.
# For extended time ranges (13201 BC–17191 AD) or asteroid files,
# see the Dropbox archive: https://www.astro.com/swisseph/swedownload_e.htm
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        build-essential \
        python3-dev \
        libffi-dev \
    && curl -sLo /tmp/sepl_18.se1 https://raw.githubusercontent.com/aloistr/swisseph/master/ephe/sepl_18.se1 \
    && curl -sLo /tmp/semo_18.se1 https://raw.githubusercontent.com/aloistr/swisseph/master/ephe/semo_18.se1 \
    && curl -sLo /tmp/seas_18.se1 https://raw.githubusercontent.com/aloistr/swisseph/master/ephe/seas_18.se1 \
    && mkdir -p /app/ephe \
    && mv /tmp/sepl_18.se1 /tmp/semo_18.se1 /tmp/seas_18.se1 /app/ephe/ \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY app ./app
COPY pyproject.toml ./
RUN pip install --no-cache-dir .

EXPOSE 8000

ENV EPHE_PATH=/app/ephe
ENV HOST=0.0.0.0
ENV PORT=8000
ENV CORS_ORIGINS=*

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
