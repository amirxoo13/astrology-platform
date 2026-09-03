#!/usr/bin/env bash
#
# Cloud Agent start phase for the astrology platform.
#
# Runs on every boot. Reconciles per-boot runtime state and then returns:
#   * Start the Docker daemon (idempotent).
#   * Materialise the bot's .env from the injected BOT_TOKEN secret.
#   * Ensure the Swiss Ephemeris data files exist (guard for snapshot drift).
#   * Bring the docker-compose stack up in the background.
#
# Long-running log tailing lives in the `terminals` section of
# environment.json, not here.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_DIR}"

log() { printf '\033[1;33m[start]\033[0m %s\n' "$*"; }

# --- 1. Docker daemon --------------------------------------------------------
"${SCRIPT_DIR}/start-dockerd.sh"

# --- 2. Bot environment file -------------------------------------------------
# docker-compose reads BOT_TOKEN for the telegram-bot service from .env. The
# real value is injected as the BOT_TOKEN secret; without it the API and web
# services still run and the bot simply cannot authenticate with Telegram.
if [ -n "${BOT_TOKEN:-}" ]; then
    log "Writing .env from injected BOT_TOKEN secret."
    BOT_TOKEN_VALUE="${BOT_TOKEN}"
else
    log "BOT_TOKEN not set; writing placeholder (telegram-bot will idle without authenticating)."
    BOT_TOKEN_VALUE="PLACEHOLDER_NO_TOKEN"
fi
GEOCODER_VALUE="${GEOCODER:-nominatim}"
GEONAMES_VALUE="${GEONAMES_USER:-}"
if [ -n "${GEONAMES_VALUE}" ] && [ -z "${GEOCODER:-}" ]; then
    GEOCODER_VALUE="geonames"
fi
umask 077
{
    printf 'BOT_TOKEN=%s\n' "${BOT_TOKEN_VALUE}"
    printf 'API_BASE_URL=http://ephemeris-api:8000\n'
    printf 'REDIS_URL=redis://redis:6379/0\n'
    printf 'SESSION_TTL_SECONDS=1800\n'
    printf 'GEOCODER=%s\n' "${GEOCODER_VALUE}"
    printf 'GEONAMES_USER=%s\n' "${GEONAMES_VALUE}"
} > .env
umask 022

mkdir -p certbot/conf certbot/www

# --- 3. Swiss Ephemeris data guard -------------------------------------------
mkdir -p ephe
sudo chown -R "$(id -u):$(id -g)" ephe
EPHE_BASE="https://github.com/aloistr/swisseph/raw/master/ephe"
for f in sepl_18.se1 semo_18.se1 seas_18.se1 sefstars.txt; do
    if [ ! -s "ephe/${f}" ]; then
        log "Downloading missing ephe/${f}"
        curl --fail -sL -o "ephe/${f}" "${EPHE_BASE}/${f}"
    fi
done

# --- 4. Bring the stack up ---------------------------------------------------
log "Starting docker-compose stack..."
sudo docker compose up -d

log "Services:"
sudo docker compose ps
log "Start phase complete. Web UI on port 8080, API proxied at /api/."
