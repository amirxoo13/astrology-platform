FROM python:3.12.14-slim

WORKDIR /app

# Install system dependencies for Cairo/SVG rendering
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2 \
    fonts-dejavu-core \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Copy bot files
COPY bot.py birthtime.py geocoding.py state.py astro.py chartwheel.py requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run as non-root user
RUN useradd --create-home --uid 1000 --shell /usr/sbin/nologin botuser \
    && chown -R botuser:botuser /app
USER botuser

# Start bot
CMD ["python", "bot.py"]
