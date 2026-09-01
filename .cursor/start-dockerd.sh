#!/usr/bin/env bash
#
# Idempotently start the Docker daemon inside the Cloud Agent VM.
#
# There is no systemd/init in the Cloud Agent VM, so dockerd is launched
# directly as a background process. Re-running this script is a no-op when the
# daemon is already responsive.
set -euo pipefail

log() { printf '\033[1;33m[dockerd]\033[0m %s\n' "$*"; }

# Same-bridge container-to-container traffic is silently dropped in this nested
# environment when bridged packets are pushed through the host nftables FORWARD
# chain. Disabling bridge netfilter lets containers on the compose network
# (e.g. nginx -> ephemeris-api) talk to each other at layer 2.
if [ -w /proc/sys/net/bridge/bridge-nf-call-iptables ]; then
    sudo sysctl -q -w net.bridge.bridge-nf-call-iptables=0 || true
    sudo sysctl -q -w net.bridge.bridge-nf-call-ip6tables=0 || true
fi

if sudo docker info >/dev/null 2>&1; then
    log "Docker daemon already running."
    exit 0
fi

log "Starting dockerd..."
sudo mkdir -p /var/log
sudo bash -c 'nohup dockerd >/var/log/dockerd.log 2>&1 &'

# Wait (up to ~30s) for the daemon socket to become responsive.
for _ in $(seq 1 30); do
    if sudo docker info >/dev/null 2>&1; then
        log "Docker daemon is ready."
        exit 0
    fi
    sleep 1
done

log "ERROR: Docker daemon did not become ready in time."
sudo tail -n 40 /var/log/dockerd.log || true
exit 1
