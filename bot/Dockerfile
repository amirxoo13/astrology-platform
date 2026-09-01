FROM python:3.12-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir \
    python-telegram-bot \
    requests

# Copy bot code
COPY bot.py /app/bot.py

# Run bot
CMD ["python", "bot.py"]
