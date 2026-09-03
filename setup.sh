#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🌟 نصب پلتفرم استرولوژی حرفه‌ای..."
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

HEALTH_OK=true

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ این اسکریپت را با sudo اجرا کنید${NC}"
    exit 1
fi

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}📦 نصب Docker...${NC}"
    apt update
    apt install -y docker.io
    systemctl start docker
    systemctl enable docker
else
    echo -e "${GREEN}✅ Docker نصب است${NC}"
fi

# Check Docker Compose v2
if ! docker compose version &> /dev/null; then
    echo -e "${YELLOW}📦 نصب Docker Compose v2...${NC}"
    apt install -y docker-compose-v2
else
    echo -e "${GREEN}✅ Docker Compose v2 نصب است${NC}"
fi

# Validate .env
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ فایل .env یافت نشد. لطفاً از .env.example کپی کنید${NC}"
    exit 1
fi

source .env || true

if [ -z "${BOT_TOKEN:-}" ]; then
    echo -e "${RED}❌ BOT_TOKEN در .env خالی است${NC}"
    exit 1
fi

if [ -z "${GEONAMES_USER:-}" ]; then
    echo -e "${YELLOW}⚠️  GEONAMES_USER خالی است — geocoding از Nominatim استفاده می‌کند${NC}"
fi

# Configure firewall
echo -e "${YELLOW}🔥 تنظیم فایروال...${NC}"
if command -v ufw &> /dev/null; then
    ufw allow 8080/tcp
    echo -e "${GREEN}✅ پورت 8080 باز شد${NC}"
else
    echo -e "${YELLOW}⚠️  ufw نصب نیست، فایروال را دستی تنظیم کنید${NC}"
fi

# Build and start
echo -e "${YELLOW}🚀 ساخت و اجرای containers...${NC}"
docker compose down 2>/dev/null || true
if ! docker compose up -d --build; then
    echo -e "${RED}❌ راه‌اندازی containers ناموفق بود${NC}"
    exit 1
fi

# Wait for services
echo -e "${YELLOW}⏳ انتظار برای راه‌اندازی سرویس‌ها...${NC}"
sleep 15

# Health checks
echo -e "${YELLOW}🔍 بررسی سلامت سرویس‌ها...${NC}"

# Check API via Nginx
if curl -sf http://localhost:8080/api/health | grep -q "ok"; then
    echo -e "${GREEN}✅ Swiss Ephemeris API فعال است (via /api/health)${NC}"
else
    echo -e "${RED}❌ Swiss Ephemeris API مشکل دارد${NC}"
    docker compose logs ephemeris-api
    HEALTH_OK=false
fi

# Check Redis
if docker compose exec -T redis redis-cli ping | grep -q "PONG"; then
    echo -e "${GREEN}✅ Redis فعال است${NC}"
else
    echo -e "${RED}❌ Redis مشکل دارد${NC}"
    docker compose logs redis
    HEALTH_OK=false
fi

# Check web server
if curl -sf http://localhost:8080 | grep -qiE 'astrology|استرولوژی|Ephemeris'; then
    echo -e "${GREEN}✅ وب سرور فعال است${NC}"
else
    echo -e "${RED}❌ وب سرور مشکل دارد${NC}"
    docker compose logs web-server
    HEALTH_OK=false
fi

# Check bot
if docker compose ps telegram-bot | grep -q "Up"; then
    echo -e "${GREEN}✅ بات تلگرام فعال است${NC}"
else
    echo -e "${RED}❌ بات تلگرام مشکل دارد${NC}"
    docker compose logs telegram-bot
    HEALTH_OK=false
fi

echo ""
if [ "$HEALTH_OK" = true ]; then
    echo -e "${GREEN}═══════════════════════════════════════════════${NC}"
    echo -e "${GREEN}✅ نصب کامل شد!${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════${NC}"
    echo ""
    echo -e "🌐 وب API: ${YELLOW}http://$(hostname -I | awk '{print $1}'):8080/api/health${NC}"
    echo -e "🤖 بات تلگرام: از طریق تلگرام تست کنید"
    echo ""
    echo -e "${YELLOW}دستورات مدیریت:${NC}"
    echo "  sudo docker compose logs -f    # مشاهده لاگ‌ها"
    echo "  sudo docker compose restart    # ریستارت"
    echo "  sudo docker compose down       # توقف"
    echo ""
    echo -e "🔒 برای فعال‌سازی HTTPS: ${YELLOW}sudo bash scripts/init-letsencrypt.sh yourdomain.com your@email.com${NC}"
else
    echo -e "${RED}═══════════════════════════════════════════════${NC}"
    echo -e "${RED}❌ نصب با خطا مواجه شد؛ لطفاً لاگ‌های بالا را بررسی کنید.${NC}"
    echo -e "${RED}═══════════════════════════════════════════════${NC}"
    exit 1
fi
