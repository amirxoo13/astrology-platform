#!/bin/bash
set -euo pipefail

# Let's Encrypt certificate setup for astrology platform
# Usage: sudo bash scripts/init-letsencrypt.sh yourdomain.com your@email.com

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <domain> <email>"
    echo "Example: $0 astrology.example.com admin@example.com"
    exit 1
fi

DOMAIN="$1"
EMAIL="$2"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "🔒 Setting up Let's Encrypt for $DOMAIN"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

# Create certbot directories
mkdir -p certbot/conf
mkdir -p certbot/www

# Request certificate using webroot
echo "📝 Requesting certificate from Let's Encrypt..."
docker compose run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email \
    -d "$DOMAIN"

if [ $? -ne 0 ]; then
    echo "❌ Certificate request failed"
    exit 1
fi

echo "✅ Certificate obtained successfully"
echo ""

# Uncomment HTTPS block in nginx.conf
echo "🔧 Enabling HTTPS in nginx.conf..."
sed -i "s/# server {/server {/g" nginx.conf
sed -i "s/#     /    /g" nginx.conf
sed -i "s/# }/}/g" nginx.conf
sed -i "s/DOMAIN_PLACEHOLDER/$DOMAIN/g" nginx.conf

echo "✅ nginx.conf updated"
echo ""

# Reload nginx
echo "🔄 Reloading nginx..."
docker compose exec web-server nginx -s reload

if [ $? -eq 0 ]; then
    echo "✅ Nginx reloaded successfully"
    echo ""
    echo "════════════════════════════════════════"
    echo "✅ HTTPS setup complete!"
    echo "════════════════════════════════════════"
    echo ""
    echo "🌐 Your site is now available at:"
    echo "   https://$DOMAIN:8443"
    echo ""
    echo "🔄 Certificate will auto-renew via certbot service"
else
    echo "⚠️  Nginx reload failed - check configuration"
    exit 1
fi
