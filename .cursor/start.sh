#!/usr/bin/env bash
#
# Cloud Agent start phase for the astrology platform.
#
# Runs on every boot. Reconciles per-boot runtime state and then returns:
#   * Start the Docker daemon (idempotent).
#   * Materialise the bot's .env from the injected BOT_TOKEN secret.
#   * Bring the docker-compose stack up in the background.
#   * Attach telegram-bot to the default docker bridge so it can reach
#     api.telegram.org in the nested Cloud Agent VM.
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
    log "BOT_TOKEN not set; writing placeholder (telegram-bot will not authenticate)."
    BOT_TOKEN_VALUE="PLACEHOLDER_NO_TOKEN"
fi
umask 077
printf 'BOT_TOKEN=%s\nAPI_BASE_URL=http://ephemeris-api:8000\n' "${BOT_TOKEN_VALUE}" > .env
umask 022

# --- 3. Bring the stack up ---------------------------------------------------
# Ephemeris data is baked into the API image at build time (api/Dockerfile);
# no host-side ./ephe bind-mount is used.
log "Starting docker-compose stack..."
sudo docker compose up -d

# --- 4. Give the telegram-bot outbound internet access -----------------------
# In the nested Cloud Agent VM only the *default* docker bridge can reach the
# public internet; custom compose bridges cannot egress. The telegram-bot is
# the only service that needs outbound access (to api.telegram.org). Attach it
# to the default bridge and make that bridge its default gateway (--gw-priority)
# so it egresses via docker0 while still resolving `ephemeris-api` over
# astrology-net. Idempotent: skips if already attached.
attach_bot_egress() {
    local cid
    cid="$(sudo docker compose ps -q telegram-bot 2>/dev/null || true)"
    if [ -z "${cid}" ]; then
        log "telegram-bot container not found; skipping egress attach."
        return 0
    fi
    if sudo docker inspect -f '{{json .NetworkSettings.Networks}}' "${cid}" 2>/dev/null | grep -q '"bridge"'; then
        log "telegram-bot already attached to the default bridge."
        return 0
    fi
    log "Attaching telegram-bot to the default bridge for outbound internet..."
    sudo docker network connect --gw-priority 100 bridge "${cid}" 2>/dev/null || true
    # Restart so the bot re-runs its Telegram connection now that it has egress.
    sudo docker restart "${cid}" >/dev/null 2>&1 || true
}
attach_bot_egress

log "Services:"
sudo docker compose ps
log "Start phase complete. Web UI on port 8080, API proxied at /api/."
