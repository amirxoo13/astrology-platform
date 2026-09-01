#!/usr/bin/env bash
#
# Cloud Agent install phase for the astrology platform.
#
# Responsibilities (durable, source-derived state that is baked into the
# environment build snapshot):
#   * Install Docker Engine + the Compose plugin and fuse-overlayfs, which are
#     required to build and run the docker-compose stack inside the nested
#     Cloud Agent VM.
#   * Configure the Docker daemon to use the fuse-overlayfs storage driver
#     (the default overlay2 driver is unavailable in this nested environment).
#   * Download the Swiss Ephemeris data files that docker-compose bind-mounts
#     into the API container at ./ephe.
#   * Build the docker-compose images so booting from the snapshot is fast.
#
# The script is idempotent: re-running it skips work that is already done and
# must always terminate (no long-running foreground processes live here).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_DIR}"

log() { printf '\033[1;33m[install]\033[0m %s\n' "$*"; }

# --- 1. Docker Engine + Compose plugin ---------------------------------------
if ! command -v docker >/dev/null 2>&1; then
    log "Installing Docker Engine and the Compose plugin..."
    export DEBIAN_FRONTEND=noninteractive
    sudo apt-get update -qq
    sudo apt-get install -y -qq ca-certificates curl gnupg
    sudo install -m 0755 -d /etc/apt/keyrings
    if [ ! -f /etc/apt/keyrings/docker.gpg ]; then
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
            | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
        sudo chmod a+r /etc/apt/keyrings/docker.gpg
    fi
    # shellcheck disable=SC1091
    . /etc/os-release
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu ${VERSION_CODENAME} stable" \
        | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
    sudo apt-get update -qq
    # --force-confold keeps the fuse3 conffile so the install stays non-interactive.
    sudo apt-get install -y -qq \
        -o Dpkg::Options::=--force-confold -o Dpkg::Options::=--force-confdef \
        docker-ce docker-ce-cli containerd.io docker-buildx-plugin \
        docker-compose-plugin fuse-overlayfs
else
    log "Docker already installed: $(docker --version)"
fi

# Let the ubuntu user run docker without sudo in interactive shells (the
# scripts still use sudo so they work before the group membership is picked up).
sudo groupadd -f docker
sudo usermod -aG docker "$(id -un)" || true

# --- 2. Docker daemon config (nested-VM friendly storage driver) -------------
log "Writing /etc/docker/daemon.json (fuse-overlayfs storage driver)..."
sudo mkdir -p /etc/docker
printf '{\n  "storage-driver": "fuse-overlayfs"\n}\n' | sudo tee /etc/docker/daemon.json >/dev/null

# --- 3. Ensure the daemon is running so we can build images -------------------
"${SCRIPT_DIR}/start-dockerd.sh"

# --- 4. Swiss Ephemeris data files (bind-mounted into the API container) ------
log "Ensuring Swiss Ephemeris data files exist in ./ephe ..."
mkdir -p ephe
# Fix ownership in case Docker previously auto-created ./ephe as root.
sudo chown -R "$(id -u):$(id -g)" ephe
EPHE_BASE="https://github.com/aloistr/swisseph/raw/master/ephe"
for f in sepl_18.se1 semo_18.se1 seas_18.se1 sefstars.txt; do
    if [ ! -s "ephe/${f}" ]; then
        log "Downloading ephe/${f}"
        curl --fail -sL -o "ephe/${f}" "${EPHE_BASE}/${f}"
    fi
done

# --- 5. Build the compose images ---------------------------------------------
log "Building docker-compose images..."
sudo docker compose build
log "Pre-pulling the nginx web image..."
sudo docker compose pull web-server

log "Install phase complete."
