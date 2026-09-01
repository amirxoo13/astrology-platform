FROM python:3.12.14-slim

WORKDIR /app

# Install dependencies (pinned in requirements.txt)
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot code
COPY bot.py /app/bot.py

# Run as a non-root user
RUN useradd --create-home --uid 1000 --shell /usr/sbin/nologin botuser \
    && chown -R botuser:botuser /app
USER botuser

# Run bot
CMD ["python", "bot.py"]
