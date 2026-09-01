# 🌟 پلتفرم استرولوژی حرفه‌ای

پلتفرم کامل استرولوژی با Swiss Ephemeris، بات تلگرام، و وب سرور

## ویژگی‌ها

- ✅ **Swiss Ephemeris API** - محاسبات نجومی دقیق
- ✅ **بات تلگرام** - ساخت چارت از طریق تلگرام
- ✅ **وب سرور** - نمایش چارت‌های حرفه‌ای
- ✅ **Docker Compose** - deployment آسان
- ✅ **پورت‌های مجزا** - هیچ تداخلی با پورت 443 (3x UI) ندارد

## پورت‌های استفاده شده

- **8000** - Swiss Ephemeris API (فقط داخلی؛ از طریق شبکه Docker، بدون انتشار به هاست)
- **8080** - وب سرور نمایش چارت‌ها (شامل proxy برای API در مسیر /api/)
- **پورت 443 دست نخورده** - 3x UI بدون تغییر

## نصب و راه‌اندازی

### پیش‌نیازها

```bash
# در سرور اجرا کنید:
sudo apt update
sudo apt install -y docker.io docker-compose git curl
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
sudo docker-compose ps
```

### دسترسی

- **وب سرور**: http://155.103.71.163:8080
- **API**: http://155.103.71.163:8080/api/ (پورت 8000 خام منتشر نشده و فقط داخل شبکه Docker در دسترس است)
- **بات تلگرام**: @YourBotName (از طریق تلگرام)

## دستورات مدیریت

```bash
# مشاهده لاگ‌ها
sudo docker-compose logs -f

# توقف سرویس‌ها
sudo docker-compose down

# ریستارت سرویس‌ها
sudo docker-compose restart

# به‌روزرسانی
sudo docker-compose down
sudo docker-compose up -d --build
```

## امنیت

- هیچ تداخلی با 3x UI (پورت 443)
- شبکه Docker ایزوله
- Environment variables برای secrets
- Read-only volumes برای data

## عیب‌یابی

### بات تلگرام کار نمی‌کند
```bash
sudo docker-compose logs telegram-bot
```

### API پاسخ نمی‌دهد
```bash
curl http://localhost:8080/api/health
sudo docker-compose logs ephemeris-api
```

### وب سرور باز نمی‌شود
```bash
sudo ufw status
sudo ufw allow 8080/tcp
sudo docker-compose logs web-server
```
