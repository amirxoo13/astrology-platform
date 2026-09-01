# 🌟 پلتفرم استرولوژی حرفه‌ای

پلتفرم کامل استرولوژی با Swiss Ephemeris، بات تلگرام، و وب سرور

## ویژگی‌ها

- ✅ **Swiss Ephemeris API** - محاسبات نجومی دقیق
- ✅ **بات تلگرام** - ساخت چارت از طریق تلگرام
- ✅ **وب سرور** - نمایش چارت‌های حرفه‌ای
- ✅ **Docker Compose** - deployment آسان
- ✅ **پورت‌های مجزا** - هیچ تداخلی با پورت 443 (3x UI) ندارد

## پورت‌های استفاده شده

- **8080** - وب سرور (Nginx)؛ نمایش چارت‌ها و پروکسی مسیر `/api/` به سمت API
- **8000 (داخلی)** - Swiss Ephemeris API؛ فقط داخل شبکه Docker در دسترس است و به‌صورت عمومی publish نشده (باید از طریق پروکسی Nginx در `/api/` استفاده شود)
- **پورت 443 دست نخورده** - 3x UI بدون تغییر

## نصب و راه‌اندازی

### پیش‌نیازها

```bash
# در سرور اجرا کنید:
sudo apt update
sudo apt install -y docker.io docker-compose-plugin git curl
sudo systemctl start docker
sudo systemctl enable docker
```

### نصب سریع

```bash
# 1. دانلود پکیج
cd /opt
sudo git clone https://github.com/amirxoo13/astrology-platform.git
cd astrology-platform

# 2. اجرای setup خودکار
sudo bash setup.sh

# 3. بررسی وضعیت
sudo docker compose ps
```

### دسترسی

جایگزین `<YOUR_SERVER_IP>` را با آدرس IP یا دامنه سرور خودتان کنید:

- **وب سرور**: `http://<YOUR_SERVER_IP>:8080`
- **API** (از طریق پروکسی Nginx): `http://<YOUR_SERVER_IP>:8080/api/`
- **بات تلگرام**: `@your_bot_username` (نام کاربری بات خودتان را در BotFather تنظیم کنید و به‌جای این مقدار قرار دهید)

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

## امنیت

- API مستقیماً روی هاست publish نشده و فقط از طریق شبکه Docker یا پروکسی Nginx (که rate-limit و timeout دارد) در دسترس است؛ توجه داشته باشید پورت 8080 وب‌سرور همچنان به‌صورت عمومی منتشر می‌شود، بنابراین ایزوله‌سازی شبکه به‌تنهایی جایگزین نیاز به سخت‌سازی سرویس‌های در معرض دید (Nginx، فایروال، به‌روزرسانی‌ها) نیست.
- Environment variables برای secrets (فایل `.env`، هرگز commit نشود)
- Read-only volumes برای داده‌های ephemeris
- Container ها به‌صورت non-root اجرا می‌شوند (به‌جز پروسه‌ی master کوتاه‌مدت nginx برای bind کردن پورت 80 با capability محدود `NET_BIND_SERVICE`)

## عیب‌یابی

### بات تلگرام کار نمی‌کند
```bash
sudo docker compose logs telegram-bot
```

### API پاسخ نمی‌دهد
```bash
# از طریق پروکسی Nginx (همان مسیری که صفحه وب و کاربران خارجی استفاده می‌کنند):
curl http://localhost:8080/api/health
sudo docker compose logs ephemeris-api
```

### وب سرور باز نمی‌شود
```bash
sudo ufw status
sudo ufw allow 8080/tcp
sudo docker compose logs web-server
```
