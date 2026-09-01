#!/bin/bash
set -euo pipefail

# Resolve the directory this script lives in, so all relative paths below
# work regardless of the directory the script is invoked from.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🌟 نصب پلتفرم استرولوژی حرفه‌ای..."
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Tracks whether any health/verification step failed, so we never print a
# false "installation complete" message after a real failure.
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
    apt install -y docker.io docker-compose
    systemctl start docker
    systemctl enable docker
else
    echo -e "${GREEN}✅ Docker نصب است${NC}"
fi

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}📦 نصب Docker Compose...${NC}"
    apt install -y docker-compose
else
    echo -e "${GREEN}✅ Docker Compose نصب است${NC}"
fi

# Create directories
echo -e "${YELLOW}📁 ایجاد ساختار فایل‌ها...${NC}"
mkdir -p ephe web

# Download ephemeris files if not exist
if [ ! -f "ephe/sepl_18.se1" ]; then
    echo -e "${YELLOW}📥 دانلود فایل‌های Ephemeris...${NC}"
    cd ephe
    curl --fail -L -O https://github.com/aloistr/swisseph/raw/master/ephe/sepl_18.se1
    curl --fail -L -O https://github.com/aloistr/swisseph/raw/master/ephe/semo_18.se1
    curl --fail -L -O https://github.com/aloistr/swisseph/raw/master/ephe/seas_18.se1
    curl --fail -L -O https://github.com/aloistr/swisseph/raw/master/ephe/sefstars.txt
    cd "$SCRIPT_DIR"
    echo -e "${GREEN}✅ فایل‌های Ephemeris دانلود شد${NC}"
else
    echo -e "${GREEN}✅ فایل‌های Ephemeris موجود است${NC}"
fi

# Setup web files (they already live in this repository's own web/ directory,
# right next to this script; verify they're present rather than copying from
# an unrelated path).
echo -e "${YELLOW}🌐 تنظیم فایل‌های وب...${NC}"
if [ -f "web/index.html" ]; then
    echo -e "${GREEN}✅ فایل‌های وب موجود است${NC}"
else
    echo -e "${RED}❌ فایل‌های وب یافت نشدند (web/index.html)${NC}"
    HEALTH_OK=false
fi

# Configure firewall
echo -e "${YELLOW}🔥 تنظیم فایروال...${NC}"
if command -v ufw &> /dev/null; then
    # Only the Nginx web server port is exposed publicly. The raw ephemeris
    # API (port 8000) is intentionally NOT opened; it should only be reached
    # from other containers, or from the outside via the Nginx /api/ proxy.
    ufw allow 8080/tcp
    echo -e "${GREEN}✅ پورت 8080 باز شد${NC}"
    echo -e "${YELLOW}⚠️  توجه: پورت 8000 (API خام) عمداً باز نشد؛ از طریق Nginx در دسترس است${NC}"
    echo -e "${YELLOW}⚠️  توجه: پورت 443 دست نخورده (3x UI)${NC}"
else
    echo -e "${YELLOW}⚠️  ufw نصب نیست، فایروال را دستی تنظیم کنید${NC}"
fi

# Build and start
echo -e "${YELLOW}🚀 ساخت و اجرای containers...${NC}"
docker-compose down 2>/dev/null || true
if ! docker-compose up -d --build; then
    echo -e "${RED}❌ راه‌اندازی containers ناموفق بود${NC}"
    exit 1
fi

# Wait for services
echo -e "${YELLOW}⏳ انتظار برای راه‌اندازی سرویس‌ها...${NC}"
sleep 10

# Health check
echo -e "${YELLOW}🔍 بررسی سلامت سرویس‌ها...${NC}"

# Check API
if curl -s http://localhost:8000/health | grep -q "ok"; then
    echo -e "${GREEN}✅ Swiss Ephemeris API فعال است${NC}"
else
    echo -e "${RED}❌ Swiss Ephemeris API مشکل دارد${NC}"
    docker-compose logs ephemeris-api
    HEALTH_OK=false
fi

# Check web server
if curl -s http://localhost:8080 | grep -q "astrology"; then
    echo -e "${GREEN}✅ وب سرور فعال است${NC}"
else
    echo -e "${RED}❌ وب سرور مشکل دارد${NC}"
    docker-compose logs web-server
    HEALTH_OK=false
fi

# Check bot
if docker-compose ps telegram-bot | grep -q "Up"; then
    echo -e "${GREEN}✅ بات تلگرام فعال است${NC}"
else
    echo -e "${RED}❌ بات تلگرام مشکل دارد${NC}"
    docker-compose logs telegram-bot
    HEALTH_OK=false
fi

echo ""
if [ "$HEALTH_OK" = true ]; then
    echo -e "${GREEN}═══════════════════════════════════════════════${NC}"
    echo -e "${GREEN}✅ نصب کامل شد!${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════${NC}"
    echo ""
    echo -e "🌐 وب سرور: ${YELLOW}http://$(hostname -I | awk '{print $1}'):8080${NC}"
    echo -e "🤖 بات تلگرام: از طریق تلگرام تست کنید"
    echo ""
    echo -e "${YELLOW}دستورات مدیریت:${NC}"
    echo "  sudo docker-compose logs -f    # مشاهده لاگ‌ها"
    echo "  sudo docker-compose restart    # ریستارت"
    echo "  sudo docker-compose down       # توقف"
    echo ""
    echo -e "${GREEN}پورت 443 (3x UI) دست نخورده است ✓${NC}"
else
    echo -e "${RED}═══════════════════════════════════════════════${NC}"
    echo -e "${RED}❌ نصب با خطا مواجه شد؛ لطفاً لاگ‌های بالا را بررسی کنید.${NC}"
    echo -e "${RED}═══════════════════════════════════════════════${NC}"
    exit 1
fi
