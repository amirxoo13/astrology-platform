# 🌟 پلتفرم استرولوژی حرفه‌ای

پلتفرم کامل استرولوژی با Swiss Ephemeris، بات تلگرام چند حالته، و وب API

## ویژگی‌ها

- ✅ **Swiss Ephemeris API** (با پچ‌های api/patches/) - محاسبات نجومی دقیق
- ✅ **بات تلگرام چند حالته** - ناتال، ترانزیت، سیناستری، کامپوزیت، سولار ریترن، پروگرس
- ✅ **Redis session cache** - ذخیره موقت جلسات کاربران
- ✅ **GeoNames / Nominatim geocoding** - تشخیص مکان با انتخاب چند نتیجه
- ✅ **SVG chart wheels** - چرخ چارت با aspect lines و stellium handling
- ✅ **LMT support** - برای تولد قبل از ۱۹۰۰، زمان محلی با `longitude/15` به UTC تبدیل می‌شود (API مقدار `LMT` را نمی‌پذیرد)
- ✅ **وب سرور Nginx** - پروکسی /api/ و HTTPS اختیاری
- ✅ **Docker Compose** - deployment آسان

## پورت‌های استفاده شده

- **8080** - وب سرور (HTTP) در docker-compose.yml پیش‌فرض
- **8090** - وب سرور روی سرورهایی که پورت 443 از قبل توسط برنامه دیگری اشغال شده (`docker-compose.prod.yml`)
- **8443** - وب سرور (HTTPS اختیاری، بعد از اجرای scripts/init-letsencrypt.sh) — روی سرورهایی که 443 آزاد است
- **پورت‌های داخلی** - ephemeris-api:8000 و redis:6379 فقط در شبکه astrology-net

اگر روی سرور برنامه دیگری پورت **443** را گرفته، به آن دست نزنید. این استک نباید 443 را bind کند. از `docker-compose.prod.yml` استفاده کنید تا فقط 8090 منتشر شود و certbot اجرا نشود:

```bash
sudo docker compose -f docker-compose.prod.yml up -d --build
```

## آزمون سریع با آلبرت انیشتین

| فیلد | مقدار |
|------|-------|
| نام | Albert Einstein |
| تاریخ | 1879-03-14 |
| زمان | 11:30 |
| مکان | Ulm, Germany (48.4011,9.9876) |
| منطقه زمانی | LMT محل تولد (برای تاریخ‌های قبل از ۱۹۰۰) که بات آن را به UTC تبدیل می‌کند |

Swiss Ephemeris API فقط نام IANA می‌پذیرد (`timezone: "LMT"` برابر HTTP 422 است). برای تولدهای قبل از ۱۹۰۰ بات زمان محلی را با فرمول `UTC offset = longitude / 15` به UTC تبدیل می‌کند و `timezone=UTC` می‌فرستد. برای تاریخ‌های جدیدتر از IANA (مثلاً `Europe/Berlin`) استفاده می‌شود.

## نصب و راه‌اندازی

### پیش‌نیازها

```bash
# در سرور اجرا کنید:
sudo apt update
sudo apt install -y docker.io docker-compose-v2 git curl
sudo systemctl start docker
sudo systemctl enable docker
```

### نصب سریع

```bash
# 1. دانلود پکیج
cd /opt
sudo git clone https://github.com/amirxoo13/astrology-platform.git
cd astrology-platform

# 2. تنظیم محیط
sudo cp .env.example .env
sudo nano .env  # BOT_TOKEN و GEONAMES_USER را پر کنید

# 3. اجرای setup خودکار
sudo bash setup.sh

# 4. بررسی وضعیت
sudo docker compose ps
```

### تنظیمات HTTPS (اختیاری)

برای فعال‌سازی HTTPS روی پورت 8443:

```bash
sudo bash scripts/init-letsencrypt.sh yourdomain.com your@email.com
```

این اسکریپت گواهی Let's Encrypt دریافت می‌کند، بلوک HTTPS در nginx.conf را فعال می‌کند، و nginx را reload می‌کند.

### دسترسی

- **وب API (HTTP)**: http://your-server:8080/api/health
- **وب API (HTTPS)**: https://your-server:8443/api/health (بعد از init-letsencrypt)
- **بات تلگرام**: @YourBotName (از طریق تلگرام)

## دستورات مدیریت

```bash
# مشاهده لاگ‌ها
sudo docker compose logs -f

# توقف سرویس‌ها
sudo docker compose down

# ریستارت سرویس‌ها
sudo docker compose restart

# به‌روزرسانی
sudo docker compose down
sudo docker compose up -d --build
```

## استفاده از API

API از طریق Nginx در `/api/` در دسترس است:

```bash
# Health check
curl http://localhost:8080/api/health

# Birth chart
curl -X POST http://localhost:8080/api/v1/birth-chart \
  -H "Content-Type: application/json" \
  -d '{
    "datetime": "1879-03-14T11:30:00",
    "timezone": "Europe/Berlin",
    "latitude": 48.4011,
    "longitude": 9.9876
  }'

# Aspects
curl -X POST http://localhost:8080/api/v1/aspects \
  -H "Content-Type: application/json" \
  -d '{
    "datetime": "1879-03-14T11:30:00",
    "timezone": "Europe/Berlin",
    "latitude": 48.4011,
    "longitude": 9.9876
  }'
```

## api/patches/

یک پچ روی swiss-ephemeris-api در commit پین‌شده `8a03d63` اعمال می‌شود:

**`0001-fix-aspects-asteroid-planet-ids.patch`** — در `app/api/v1/endpoints/aspects.py` شناسه‌های سیارک اشتباه بود (`CERES=1` که همان `swe.MOON` است). پچ همان نگاشت `swe.SUN` / `swe.CERES` / … موجود در `app/api/v1/endpoints/planets.py` را کپی می‌کند.

ایندکس خانه‌ها در `app/core/swisseph_core.py` از قبل `raw_cusps[1:13]` است و پچ جدا نمی‌خواهد.

## امنیت

- فقط پورت 8080 (HTTP) و 8443 (HTTPS) عمومی هستند
- ephemeris-api و redis فقط در شبکه داخلی docker قابل دسترسی
- شبکه Docker ایزوله (astrology-net)
- Environment variables برای secrets
- Redis LRU cache بدون persistence (حافظه 128MB)

## عیب‌یابی

### بات تلگرام کار نمی‌کند
```bash
sudo docker compose logs telegram-bot
# بررسی کنید که BOT_TOKEN در .env صحیح است
```

### API پاسخ نمی‌دهد
```bash
curl http://localhost:8080/api/health
sudo docker compose logs ephemeris-api
```

### Redis
```bash
sudo docker compose exec redis redis-cli ping
sudo docker compose logs redis
```

### وب سرور باز نمی‌شود
```bash
sudo ufw status
sudo ufw allow 8080/tcp
# اگر از docker-compose.prod.yml استفاده می‌کنید:
sudo ufw allow 8090/tcp
sudo docker compose logs web-server
```

## مجوز

این پروژه تحت مجوز **GNU Affero General Public License v3.0 (AGPL-3.0)** منتشر شده است.

Swiss Ephemeris نیز تحت AGPL است - هر استفاده تجاری یا شبکه‌ای نیاز به انتشار کد دارد.
