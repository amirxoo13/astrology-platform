FROM python:3.12.14-slim AS builder

WORKDIR /app

# Install build-time dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    patch \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Clone Swiss Ephemeris API at the pinned commit
ARG SWISS_EPHEMERIS_API_COMMIT=8a03d63f1ca04224aa55817fcf0c4d4248328d8b
RUN git clone https://github.com/devtrongle/swiss-ephemeris-api.git /app \
    && cd /app \
    && git checkout ${SWISS_EPHEMERIS_API_COMMIT}

# Apply local patches against that commit (must apply with `git apply`)
COPY patches/*.patch /tmp/patches/
RUN cd /app && git apply --verbose /tmp/patches/*.patch

RUN pip install --no-cache-dir --prefix=/install -e .

# Download the four Swiss Ephemeris files required by the API README
RUN mkdir -p /app/ephe && \
    curl --fail -L -o /app/ephe/sepl_18.se1 https://github.com/aloistr/swisseph/raw/master/ephe/sepl_18.se1 && \
    curl --fail -L -o /app/ephe/semo_18.se1 https://github.com/aloistr/swisseph/raw/master/ephe/semo_18.se1 && \
    curl --fail -L -o /app/ephe/seas_18.se1 https://github.com/aloistr/swisseph/raw/master/ephe/seas_18.se1 && \
    curl --fail -L -o /app/ephe/sefstars.txt https://github.com/aloistr/swisseph/raw/master/ephe/sefstars.txt

FROM python:3.12.14-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local
COPY --from=builder /app /app

ENV EPHE_PATH=/app/ephe

RUN useradd --create-home --uid 1000 --shell /usr/sbin/nologin apiuser \
    && chown -R apiuser:apiuser /app
USER apiuser

EXPOSE 8000

# Healthcheck uses stdlib only — python:slim does not ship curl
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
