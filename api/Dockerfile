FROM python:3.12.14-slim AS builder

WORKDIR /app

# Install build-time only dependencies (not present in the final image)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Clone Swiss Ephemeris API, pinned to a specific commit for reproducible builds
ARG SWISS_EPHEMERIS_API_COMMIT=8a03d63f1ca04224aa55817fcf0c4d4248328d8b
RUN git clone https://github.com/devtrongle/swiss-ephemeris-api.git /app \
    && cd /app \
    && git checkout ${SWISS_EPHEMERIS_API_COMMIT}

# Install Python dependencies into an isolated prefix so only the
# resulting site-packages need to be copied into the final image
RUN pip install --no-cache-dir --prefix=/install -e .

# Download ephemeris files; --fail ensures HTTP error responses (e.g. 404)
# abort the build instead of being silently saved as valid data files
RUN mkdir -p /app/ephe && \
    curl --fail -L -o /app/ephe/sepl_18.se1 https://github.com/aloistr/swisseph/raw/master/ephe/sepl_18.se1 && \
    curl --fail -L -o /app/ephe/semo_18.se1 https://github.com/aloistr/swisseph/raw/master/ephe/semo_18.se1 && \
    curl --fail -L -o /app/ephe/seas_18.se1 https://github.com/aloistr/swisseph/raw/master/ephe/seas_18.se1 && \
    curl --fail -L -o /app/ephe/sefstars.txt https://github.com/aloistr/swisseph/raw/master/ephe/sefstars.txt

FROM python:3.12.14-slim

WORKDIR /app

# Copy only the installed Python packages and application/ephemeris data,
# leaving build-time tools (git, curl) out of the final runtime image
COPY --from=builder /install /usr/local
COPY --from=builder /app /app

# Run as a non-root user
RUN useradd --create-home --uid 1000 --shell /usr/sbin/nologin apiuser \
    && chown -R apiuser:apiuser /app
USER apiuser

# Expose port
EXPOSE 8000

# Start server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
