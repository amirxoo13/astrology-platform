FROM python:3.12.14-slim AS builder

WORKDIR /app

# Build deps only needed in the builder stage
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Vendored Swiss Ephemeris API source, pinned to commit
# 8a03d63f1ca04224aa55817fcf0c4d4248328d8b of
# https://github.com/uselflabs/Swiss-Ephemeris-API
# (formerly devtrongle/swiss-ephemeris-api). Vendoring avoids fragile
# build-time git clones and keeps the exact schema the bot is written against.
COPY swiss-ephemeris-api/ /app/

# Install Python dependencies into an isolated prefix so only the
# resulting site-packages need to be copied into the final image
RUN pip install --no-cache-dir --prefix=/install -e .

# Ensure required Swiss Ephemeris data files exist. Prefer files already
# present in the vendored tree; otherwise fetch the same official set the
# upstream Dockerfile downloads from aloistr/swisseph.
RUN mkdir -p /app/ephe \
    && if [ ! -f /app/ephe/sepl_18.se1 ] || [ ! -f /app/ephe/semo_18.se1 ] || [ ! -f /app/ephe/seas_18.se1 ]; then \
         apt-get update && apt-get install -y --no-install-recommends curl \
         && curl -fsSL -o /app/ephe/sepl_18.se1 https://raw.githubusercontent.com/aloistr/swisseph/master/ephe/sepl_18.se1 \
         && curl -fsSL -o /app/ephe/semo_18.se1 https://raw.githubusercontent.com/aloistr/swisseph/master/ephe/semo_18.se1 \
         && curl -fsSL -o /app/ephe/seas_18.se1 https://raw.githubusercontent.com/aloistr/swisseph/master/ephe/seas_18.se1 \
         && apt-get purge -y curl && apt-get autoremove -y \
         && rm -rf /var/lib/apt/lists/* ; \
       fi \
    && test -f /app/ephe/sepl_18.se1 \
    && test -f /app/ephe/semo_18.se1 \
    && test -f /app/ephe/seas_18.se1

FROM python:3.12.14-slim

WORKDIR /app

# Copy only the installed Python packages and application/ephemeris data,
# leaving build-time tooling out of the final runtime image
COPY --from=builder /install /usr/local
COPY --from=builder /app /app

ENV EPHE_PATH=/app/ephe

# Run as a non-root user
RUN useradd --create-home --uid 1000 --shell /usr/sbin/nologin apiuser \
    && chown -R apiuser:apiuser /app
USER apiuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
