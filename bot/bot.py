#!/usr/bin/env python3
"""
Astrology Telegram Bot - Production Version
Professional natal chart generator with Swiss Ephemeris
"""
import asyncio
import logging
import os

import httpx
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.error import TelegramError

try:
    from timezonefinder import TimezoneFinder
except ImportError:  # pragma: no cover - optional dependency guard
    TimezoneFinder = None

try:
    from geopy.geocoders import Nominatim
    from geopy.exc import GeopyError
except ImportError:  # pragma: no cover - optional dependency guard
    Nominatim = None
    GeopyError = Exception

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN', '***:***')
API_BASE_URL = os.getenv('API_BASE_URL', 'http://ephemeris-api:8000')

# User state management
user_states = {}

# Restart-flow guidance shown whenever we can't trust the in-memory state
RESTART_MESSAGE = (
    "⚠️ اطلاعات جلسه شما یافت نشد یا منقضی شده است.\n"
    "لطفاً دوباره با /start شروع کنید."
)

_timezone_finder = TimezoneFinder() if TimezoneFinder else None
_geolocator = Nominatim(user_agent="astrology-platform-bot") if Nominatim else None

# Zodiac signs in Persian with symbols
SIGN_NAMES = {
    'Aries': '♈ حمل', 'Taurus': '♉ ثور', 'Gemini': '♊ جوزا',
    'Cancer': '♋ سرطان', 'Leo': '♌ اسد', 'Virgo': '♍ سنبله',
    'Libra': '♎ میزان', 'Scorpio': '♏ عقرب', 'Sagittarius': '♐ قوس',
    'Capricorn': '♑ جدی', 'Aquarius': '♒ دلو', 'Pisces': '♓ حوت'
}

PLANET_SYMBOLS = {
    'Sun': '☉', 'Moon': '☽', 'Mercury': '☿', 'Venus': '♀',
    'Mars': '♂', 'Jupiter': '♃', 'Saturn': '♄', 'Uranus': '♅',
    'Neptune': '♆', 'Pluto': '♇', 'Chiron': '⚷', 'Ceres': '●',
    'Pallas': '●', 'Juno': '●', 'Vesta': '●'
}

def format_position(pos):
    """Format planet position to readable string"""
    lon = pos['longitude']
    sign = pos['sign']
    degree = int(lon % 30)
    minute = int((lon % 1) * 60)
    second = int(((lon % 1) * 60 % 1) * 60)
    sign_name = SIGN_NAMES.get(sign, sign)
    
    # Retrograde indicator
    retro = " ℞" if pos.get('retrograde', False) else ""
    
    return f"{degree}°{minute:02d}'{second:02d}\" {sign_name}{retro}"

async def call_api(endpoint, data):
    """Call Swiss Ephemeris API asynchronously (non-blocking for the bot's event loop)"""
    url = f"{API_BASE_URL}{endpoint}"
    logger.info(f"Calling API: {url}")
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, json=data)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"API returned an error status for {url}: {e}")
    except httpx.RequestError as e:
        logger.error(f"API call to {url} failed: {e}")
    except ValueError as e:
        logger.error(f"API response from {url} was not valid JSON: {e}")
    return None


class LocationError(ValueError):
    """Raised when the user-provided location/coordinates cannot be resolved."""


def looks_like_coordinates(text):
    """Heuristic to decide whether input should be parsed as 'lat,lon'.

    Treats the input as coordinates only if it contains at least one digit
    and no letters (of any script), so city names like "Tehran, Iran" or
    "تهران" are routed to geocoding while numeric-only input (including
    malformed cases like "1,2,3") is routed to coordinate parsing/validation.
    """
    stripped = text.strip()
    if not stripped:
        return False
    has_letter = any(ch.isalpha() for ch in stripped)
    has_digit = any(ch.isdigit() for ch in stripped)
    return has_digit and not has_letter


def parse_coordinates(text):
    """Parse a 'lat,lon' string into validated floats.

    Raises LocationError on malformed input (wrong number of components,
    non-numeric values, or out-of-range latitude/longitude).
    """
    parts = [p.strip() for p in text.split(',')]
    if len(parts) != 2:
        raise LocationError(
            "فرمت مختصات اشتباه است. لطفاً به شکل lat,lon وارد کنید (مثال: 35.69,51.39)"
        )

    try:
        lat = float(parts[0])
        lon = float(parts[1])
    except ValueError:
        raise LocationError(
            "مختصات باید عدد باشند. لطفاً به شکل lat,lon وارد کنید (مثال: 35.69,51.39)"
        )

    if not (-90 <= lat <= 90):
        raise LocationError("عرض جغرافیایی (latitude) باید بین 90- و 90 باشد.")
    if not (-180 <= lon <= 180):
        raise LocationError("طول جغرافیایی (longitude) باید بین 180- و 180 باشد.")

    return lat, lon


def geocode_city(name):
    """Resolve a city/place name to (latitude, longitude) using Nominatim.

    Returns None if geocoding is unavailable or the place cannot be found.
    This is a blocking network call and must be run in a thread when called
    from async code.
    """
    if _geolocator is None:
        logger.error("Geocoding is unavailable: geopy is not installed")
        return None
    try:
        location = _geolocator.geocode(name, timeout=10)
    except GeopyError as e:
        logger.error(f"Geocoding failed for '{name}': {e}")
        return None
    if location is None:
        return None
    return location.latitude, location.longitude


def resolve_timezone(lat, lon):
    """Resolve the IANA timezone name for the given coordinates, defaulting to UTC."""
    if _timezone_finder is None:
        logger.error("Timezone lookup unavailable: timezonefinder is not installed")
        return 'UTC'
    try:
        tz_name = _timezone_finder.timezone_at(lat=lat, lng=lon)
    except Exception as e:
        logger.error(f"Timezone lookup failed for ({lat}, {lon}): {e}")
        return 'UTC'
    return tz_name or 'UTC'

def generate_chart_text(chart_data, aspects_data, user_name):
    """Generate professional text summary of chart"""
    positions = chart_data.get('positions', [])
    houses = chart_data.get('houses', [])
    aspects = aspects_data.get('aspects', [])
    
    text = f"🌟 *چارت ناتال {user_name}* 🌟\n\n"
    
    # Planets section
    text += "🪐 *سیارات:*\n"
    for planet in positions[:10]:  # Top 10 planets
        name = planet.get('name', '')
        symbol = PLANET_SYMBOLS.get(name, '•')
        pos = format_position(planet)
        house_num = planet.get('house', '?')
        text += f"{symbol} {name}: {pos} (خانه {house_num})\n"
    
    text += "\n🏠 *خانه‌های اصلی:*\n"
    angle_houses = [(1, 'ASC'), (4, 'IC'), (7, 'DSC'), (10, 'MC')]
    for num, name in angle_houses:
        if num <= len(houses):
            house = houses[num - 1]
            pos = format_position(house)
            text += f"{name}: {pos}\n"
    
    # Aspects section
    text += "\n✨ *جنبه‌های کلیدی:*\n"
    aspect_types = {
        'CONJUNCTION': '☌', 'OPPOSITION': '☍', 'TRINE': '△',
        'SQUARE': '□', 'SEXTILE': '⚹'
    }
    for aspect in aspects[:10]:  # Top 10 aspects
        p1 = aspect.get('planet1', '')
        p2 = aspect.get('planet2', '')
        atype = aspect.get('aspect', '')
        symbol = aspect_types.get(atype, '•')
        orb = aspect.get('orb', 0)
        orb_deg = int(orb)
        orb_min = int((orb % 1) * 60)
        text += f"{p1} {symbol} {p2} ({orb_deg}°{orb_min:02d}')\n"
    
    # Element distribution
    text += "\n🔥 *توزیع عناصر:*\n"
    elements = {'Fire': '🔥 آتش', 'Earth': '🌍 زمین', 'Air': '💨 هوا', 'Water': '💧 آب'}
    element_counts = {'Fire': 0, 'Earth': 0, 'Air': 0, 'Water': 0}
    
    for planet in positions:
        element = planet.get('element')
        if element in element_counts:
            element_counts[element] += 1
    
    total = sum(element_counts.values())
    for elem, count in element_counts.items():
        percentage = (count / total * 100) if total > 0 else 0
        text += f"{elements.get(elem, elem)}: {count} ({percentage:.1f}%)\n"
    
    return text

def welcome_text(user_first_name):
    return (
        f"سلام {user_first_name}! 👋\n\n"
        "به بات استرولوژی حرفه‌ای خوش آمدید 🌟\n\n"
        "این بات با استفاده از Swiss Ephemeris دقیق‌ترین محاسبات نجومی را ارائه می‌دهد.\n\n"
        "چه کاری می‌خواهید انجام دهید؟"
    )


def welcome_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌟 ساخت چارت ناتال", callback_data="create_chart")],
        [InlineKeyboardButton("📚 راهنما", callback_data="help")],
        [InlineKeyboardButton("⚙️ تنظیمات", callback_data="settings")]
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message"""
    user = update.effective_user
    try:
        await update.message.reply_text(
            welcome_text(user.first_name),
            reply_markup=welcome_keyboard()
        )
    except TelegramError as e:
        logger.error(f"Failed to send welcome message: {e}")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    try:
        await query.answer()
    except TelegramError as e:
        logger.error(f"Failed to acknowledge callback query: {e}")

    user_id = query.from_user.id

    try:
        if query.data == "create_chart":
            await create_chart_flow(query, context)
        elif query.data == "help":
            await show_help(query, context)
        elif query.data == "settings":
            await show_settings(query, context)
        elif query.data == "confirm_create":
            await generate_and_send_chart(query, context)
        elif query.data == "cancel":
            user_states.pop(user_id, None)
            await query.edit_message_text("❌ عملیات لغو شد.\n\nبرای شروع مجدد /start را بزنید.")
        elif query.data == "start":
            user_states.pop(user_id, None)
            await query.edit_message_text(
                welcome_text(query.from_user.first_name),
                reply_markup=welcome_keyboard()
            )
        elif query.data == "set_house_placidus":
            await query.edit_message_text(
                "✅ سیستم خانه Placidus انتخاب شد (تنها گزینه فعلی).",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🔙 بازگشت به تنظیمات", callback_data="settings")]]
                )
            )
        elif query.data == "set_zodiac_tropical":
            await query.edit_message_text(
                "✅ زودیاک Tropical انتخاب شد (تنها گزینه فعلی).",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🔙 بازگشت به تنظیمات", callback_data="settings")]]
                )
            )
        elif query.data == "time_unknown":
            state = user_states.get(user_id)
            if state is None or 'data' not in state:
                await query.edit_message_text(RESTART_MESSAGE)
                return
            state['data']['time'] = "12:00"
            state['step'] = 'city'

            await query.edit_message_text(
                "⏰ زمان: 12:00 (پیش‌فرض)\n\n"
                "📍 نام شهر یا مختصات جغرافیایی را وارد کنید:\n"
                "(مثال: Tehran, Iran یا 35.69,51.39)"
            )
    except TelegramError as e:
        logger.error(f"Telegram API error while handling '{query.data}': {e}")

async def create_chart_flow(query, context):
    """Start chart creation flow"""
    user_id = query.from_user.id
    
    # Initialize user state
    user_states[user_id] = {
        'step': 'name',
        'data': {}
    }
    
    keyboard = [[InlineKeyboardButton("❌ لغو", callback_data="cancel")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🌟 ساخت چارت ناتال\n\n"
        "لطفاً نام شخص را وارد کنید:\n"
        "(مثال: آلبرت انیشتین)",
        reply_markup=reply_markup
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages based on user state"""
    user_id = update.effective_user.id
    text = update.message.text
    
    if user_id not in user_states:
        await update.message.reply_text(
            "برای ساخت چارت، لطفاً /start را بزنید."
        )
        return
    
    state = user_states[user_id]
    if 'data' not in state:
        user_states.pop(user_id, None)
        await update.message.reply_text(RESTART_MESSAGE)
        return

    step = state.get('step')

    try:
        if step == 'name':
            state['data']['name'] = text
            state['step'] = 'date'
            
            await update.message.reply_text(
                f"✅ نام: {text}\n\n"
                "📅 تاریخ تولد را وارد کنید:\n"
                "فرمت: YYYY-MM-DD\n"
                "(مثال: 1879-03-14)"
            )
        
        elif step == 'date':
            try:
                datetime.strptime(text, '%Y-%m-%d')
                state['data']['date'] = text
                state['step'] = 'time'
                
                keyboard = [
                    [InlineKeyboardButton("⏰ زمان دقیق نمی‌دانم", callback_data="time_unknown")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    f"✅ تاریخ: {text}\n\n"
                    "⏰ ساعت تولد را وارد کنید:\n"
                    "فرمت: HH:MM (24 ساعته)\n"
                    "(مثال: 11:30)",
                    reply_markup=reply_markup
                )
            except ValueError:
                await update.message.reply_text(
                    "❌ فرمت تاریخ اشتباه است.\n"
                    "لطفاً از فرمت YYYY-MM-DD استفاده کنید.\n"
                    "مثال: 1879-03-14"
                )
        
        elif step == 'time':
            try:
                datetime.strptime(text, '%H:%M')
                state['data']['time'] = text
                state['step'] = 'city'
                
                await update.message.reply_text(
                    f"✅ زمان: {text}\n\n"
                    "📍 نام شهر یا مختصات جغرافیایی را وارد کنید:\n"
                    "(مثال: Tehran, Iran یا 35.69,51.39)"
                )
            except ValueError:
                await update.message.reply_text(
                    "❌ فرمت زمان اشتباه است.\n"
                    "لطفاً از فرمت HH:MM استفاده کنید.\n"
                    "مثال: 11:30"
                )
        
        elif step == 'city':
            text_stripped = text.strip()

            try:
                if looks_like_coordinates(text_stripped):
                    lat, lon = parse_coordinates(text_stripped)
                    location_name = f"{lat}, {lon}"
                else:
                    coords = await asyncio.to_thread(geocode_city, text_stripped)
                    if coords is None:
                        await update.message.reply_text(
                            "❌ نام شهر یافت نشد.\n"
                            "لطفاً نام شهر معتبر (مثال: Tehran, Iran) یا مختصات دقیق (lat,lon) وارد کنید."
                        )
                        return
                    lat, lon = coords
                    location_name = text_stripped
            except LocationError as e:
                await update.message.reply_text(f"❌ {e}")
                return

            # Geocoding runs in a separate thread and may take a while; guard
            # against the user cancelling/restarting the flow while it was
            # in flight, which would otherwise resurrect a stale session.
            if user_states.get(user_id) is not state:
                return

            state['data']['latitude'] = lat
            state['data']['longitude'] = lon
            state['data']['location_name'] = location_name
            state['data']['timezone'] = resolve_timezone(lat, lon)

            state['step'] = 'confirm'
            
            # Show confirmation
            data = state['data']
            keyboard = [
                [
                    InlineKeyboardButton("✅ تایید و ساخت چارت", callback_data="confirm_create"),
                    InlineKeyboardButton("❌ لغو", callback_data="cancel")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "📋 اطلاعات چارت:\n\n"
                f"👤 نام: {data.get('name', 'N/A')}\n"
                f"📅 تاریخ: {data.get('date', 'N/A')}\n"
                f"⏰ زمان: {data.get('time', 'Unknown')}\n"
                f"📍 مکان: {data.get('location_name', 'N/A')}\n"
                f"🕒 منطقه زمانی: {data.get('timezone', 'UTC')}\n\n"
                "آیا این اطلاعات درست است؟",
                reply_markup=reply_markup
            )
    except TelegramError as e:
        logger.error(f"Telegram API error while handling step '{step}': {e}")

async def generate_and_send_chart(query, context):
    """Generate chart and send to user"""
    user_id = query.from_user.id
    state = user_states.get(user_id)
    data = state.get('data') if state else None

    if not data or 'date' not in data or 'time' not in data:
        try:
            await query.edit_message_text(RESTART_MESSAGE)
        except TelegramError as e:
            logger.error(f"Failed to notify user about missing session state: {e}")
        user_states.pop(user_id, None)
        return

    try:
        await query.edit_message_text("⏳ در حال محاسبه چارت...")
    except TelegramError as e:
        logger.error(f"Failed to update progress message: {e}")

    # Prepare API request
    birth_data = {
        'datetime': f"{data['date']}T{data['time']}:00",
        'timezone': data.get('timezone', 'UTC'),
        'latitude': data.get('latitude', 35.69),
        'longitude': data.get('longitude', 51.39)
    }
    
    # Call API
    chart_data = await call_api('/api/v1/birth-chart', birth_data)
    aspects_data = await call_api('/api/v1/aspects', birth_data)
    
    if not chart_data or not aspects_data:
        try:
            await query.edit_message_text(
                "❌ خطا در محاسبه چارت.\n"
                "لطفاً بعداً دوباره تلاش کنید."
            )
        except TelegramError as e:
            logger.error(f"Failed to notify user about chart calculation error: {e}")
        user_states.pop(user_id, None)
        return
    
    # Generate text summary
    try:
        chart_text = generate_chart_text(chart_data, aspects_data, data.get('name', 'شخص'))
    except (KeyError, TypeError, ValueError) as e:
        logger.error(f"Failed to parse ephemeris API response: {e}")
        try:
            await query.edit_message_text(
                "❌ پاسخ سرویس محاسبات نامعتبر بود.\n"
                "لطفاً بعداً دوباره تلاش کنید."
            )
        except TelegramError as te:
            logger.error(f"Failed to notify user about response parsing error: {te}")
        user_states.pop(user_id, None)
        return

    # Send chart
    try:
        await query.edit_message_text(chart_text, parse_mode='Markdown')
    except TelegramError as e:
        logger.error(f"Failed to send chart result: {e}")
    
    # Clean up
    user_states.pop(user_id, None)

async def show_help(query, context):
    """Show help message"""
    await query.edit_message_text(
        "📚 راهنمای استفاده\n\n"
        "این بات به شما کمک می‌کند چارت ناتال حرفه‌ای بسازید.\n\n"
        "🌟 ویژگی‌ها:\n"
        "• محاسبات دقیق با Swiss Ephemeris\n"
        "• 15 سیاره و سیارک\n"
        "• 12 خانه (Placidus و 14 سیستم دیگر)\n"
        "• تحلیل جنبه‌ها\n"
        "• توزیع عناصر\n"
        "• سیارات حاکم\n\n"
        "📝 برای شروع، /start را بزنید.\n\n"
        "💡 نکات:\n"
        "• تاریخ را به فرمت YYYY-MM-DD وارد کنید\n"
        "• زمان را به فرمت HH:MM وارد کنید\n"
        "• می‌توانید نام شهر یا مختصات (lat,lon) را وارد کنید"
    )

async def show_settings(query, context):
    """Show settings menu"""
    keyboard = [
        [InlineKeyboardButton("🏠 سیستم خانه: Placidus", callback_data="set_house_placidus")],
        [InlineKeyboardButton("🌍 زودیاک: Tropical", callback_data="set_zodiac_tropical")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "⚙️ تنظیمات\n\n"
        "تنظیمات فعلی:\n"
        "• سیستم خانه: Placidus\n"
        "• زودیاک: Tropical\n\n"
        "برای تغییر، روی گزینه‌ها کلیک کنید:",
        reply_markup=reply_markup
    )

def main():
    """Start the bot"""
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Start polling
    logger.info("🚀 Starting Astrology Bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
