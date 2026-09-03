# 🌟 پلتفرم استرولوژی حرفه‌ای

پلتفرم کامل استرولوژی با Swiss Ephemeris، بات تلگرام چند حالته، و وب API

## ویژگی‌ها

- ✅ **Swiss Ephemeris API** (با پچ‌های api/patches/) - محاسبات نجومی دقیق
- ✅ **بات تلگرام چند حالته** - ناتال، ترانزیت، سیناستری، کامپوزیت، سولار ریترن، پروگرس
- ✅ **Redis session cache** - ذخیره موقت جلسات کاربران
- ✅ **GeoNames / Nominatim geocoding** - تشخیص مکان با انتخاب چند نتیجه
- ✅ **SVG chart wheels** - چرخ چارت با aspect lines و stellium handling
- ✅ **LMT support** - Local Mean Time از طول جغرافیایی
- ✅ **وب سرور Nginx** - پروکسی /api/ و HTTPS اختیاری
- ✅ **Docker Compose** - deployment آسان

## پورت‌های استفاده شده

- **8080** - وب سرور (HTTP)
- **8443** - وب سرور (HTTPS اختیاری، بعد از اجرای scripts/init-letsencrypt.sh)
- **پورت‌های داخلی** - ephemeris-api:8000 و redis:6379 فقط در شبکه astrology-net

## آزمون سریع با آلبرت انیشتین

| فیلد | مقدار |
|------|-------|
| نام | Albert Einstein |
| تاریخ | 1879-03-14 |
| زمان | 11:30 |
| مکان | Ulm, Germany (48.4011,9.9876) |
| منطقه زمانی | LMT (محاسبه خودکار از طول جغرافیایی) |

بات از LMT (Local Mean Time) پشتیبانی می‌کند زمانی که تاریخ از معرفی منطقه زمانی استاندارد قدیمی‌تر باشد.

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
    "timezone": "LMT",
    "latitude": 48.4011,
    "longitude": 9.9876
  }'

# Aspects
curl -X POST http://localhost:8080/api/v1/aspects \
  -H "Content-Type: application/json" \
  -d '{
    "datetime": "1879-03-14T11:30:00",
    "timezone": "LMT",
    "latitude": 48.4011,
    "longitude": 9.9876
  }'
```

## api/patches/

دو پچ برای swiss-ephemeris-api اعمال می‌شود:

1. **0001-fix-asteroid-planet-ids.patch** - Chiron, Ceres, Pallas, Juno, Vesta از `getattr(swe, name)` استفاده می‌کنند نه شناسه‌های 1-4
2. **0002-robust-house-cusp-indexing.patch** - تشخیص طول raw_cusps 13 یا 12 برای جلوگیری از IndexError

این پچ‌ها در زمان build در api/Dockerfile اعمال می‌شوند.

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
sudo docker compose logs web-server
```

## مجوز

این پروژه تحت مجوز **GNU Affero General Public License v3.0 (AGPL-3.0)** منتشر شده است.

Swiss Ephemeris نیز تحت AGPL است - هر استفاده تجاری یا شبکه‌ای نیاز به انتشار کد دارد.
