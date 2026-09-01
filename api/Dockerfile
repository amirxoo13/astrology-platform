FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Clone Swiss Ephemeris API
RUN git clone https://github.com/devtrongle/swiss-ephemeris-api.git /app

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Download ephemeris files
RUN mkdir -p /app/ephe && \
    curl -L -o /app/ephe/sepl_18.se1 https://github.com/aloistr/swisseph/raw/master/ephe/sepl_18.se1 && \
    curl -L -o /app/ephe/semo_18.se1 https://github.com/aloistr/swisseph/raw/master/ephe/semo_18.se1 && \
    curl -L -o /app/ephe/seas_18.se1 https://github.com/aloistr/swisseph/raw/master/ephe/seas_18.se1 && \
    curl -L -o /app/ephe/sefstars.txt https://github.com/aloistr/swisseph/raw/master/ephe/sefstars.txt

# Expose port
EXPOSE 8000

# Start server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
