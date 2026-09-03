"""
Multi-mode Astrology Telegram Bot
Modes: natal, transit, synastry, composite, solar_return, progressed
"""
import asyncio
import logging
import os
from datetime import datetime

import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.error import TelegramError

# Local imports
import state
import geocoding
import birthtime
import astro
import chartwheel

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration - NO default BOT_TOKEN
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required")

API_BASE_URL = os.getenv('API_BASE_URL', 'http://ephemeris-api:8000')

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
    'Neptune': '♆', 'Pluto': '♇'
}


async def call_api(endpoint, data):
    """Call Swiss Ephemeris API asynchronously"""
    url = f"{API_BASE_URL}{endpoint}"
    logger.info(f"Calling API: {url}")
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, json=data)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"API returned error for {url}: {e}")
    except httpx.RequestError as e:
        logger.error(f"API call to {url} failed: {e}")
    except ValueError as e:
        logger.error(f"API response from {url} was not valid JSON: {e}")
    return None


def format_position(pos):
    """Format planet position to readable string"""
    lon = pos['longitude']
    sign = pos.get('sign', '')
    degree = int(lon % 30)
    minute = int((lon % 1) * 60)
    second = int(((lon % 1) * 60 % 1) * 60)
    sign_name = SIGN_NAMES.get(sign, sign)
    
    retro = " ℞" if pos.get('retrograde', False) else ""
    return f"{degree}°{minute:02d}'{second:02d}\" {sign_name}{retro}"


def generate_chart_text(chart_data, aspects_data, user_name, mode='natal'):
    """Generate professional text summary of chart"""
    positions = chart_data.get('positions', [])
    houses = chart_data.get('houses', [])
    aspects = aspects_data.get('aspects', [])
    
    mode_title = {
        'natal': 'ناتال',
        'transit': 'ترانزیت',
        'synastry': 'سیناستری',
        'composite': 'کامپوزیت',
        'solar_return': 'سولار ریترن',
        'progressed': 'پروگرس'
    }.get(mode, 'چارت')
    
    text = f"🌟 *چارت {mode_title} {user_name}* 🌟\n\n"
    
    # Planets section
    text += "🪐 *سیارات اصلی:*\n"
    for planet in positions[:10]:  # 10 classical planets
        name = planet.get('name', '')
        if name not in astro.MAIN_PLANETS:
            continue
        symbol = PLANET_SYMBOLS.get(name, '•')
        pos = format_position(planet)
        house_num = planet.get('house', '?')
        text += f"{symbol} {name}: {pos} (خانه {house_num})\n"
    
    # Houses section
    if houses:
        text += "\n🏠 *خانه‌های اصلی:*\n"
        angle_houses = [(1, 'ASC'), (4, 'IC'), (7, 'DSC'), (10, 'MC')]
        for num, name in angle_houses:
            if num <= len(houses):
                house = houses[num - 1]
                pos = format_position(house)
                text += f"{name}: {pos}\n"
    
    # Aspects section
    if aspects:
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
    
    return text


def welcome_text(user_first_name):
    return (
        f"سلام {user_first_name}! 👋\n\n"
        "به بات استرولوژی حرفه‌ای خوش آمدید 🌟\n\n"
        "این بات از Swiss Ephemeris استفاده می‌کند و چندین حالت دارد:\n"
        "• چارت ناتال 🎯\n"
        "• ترانزیت و پروگرس 🔄\n"
        "• سیناستری و کامپوزیت 💑\n"
        "• سولار ریترن ☀️\n\n"
        "چه کاری می‌خواهید انجام دهید؟"
    )


def welcome_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎯 چارت ناتال", callback_data="mode_natal")],
        [InlineKeyboardButton("🔄 ترانزیت", callback_data="mode_transit")],
        [InlineKeyboardButton("💑 سیناستری", callback_data="mode_synastry")],
        [InlineKeyboardButton("🌐 کامپوزیت", callback_data="mode_composite")],
        [InlineKeyboardButton("☀️ سولار ریترن", callback_data="mode_solar_return")],
        [InlineKeyboardButton("📈 پروگرس", callback_data="mode_progressed")],
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
    data = query.data

    try:
        if data.startswith("mode_"):
            mode = data.replace("mode_", "")
            await start_chart_flow(query, context, mode)
        elif data == "settings":
            await show_settings(query, context)
        elif data == "confirm_create":
            await generate_and_send_chart(query, context)
        elif data == "cancel":
            state.delete_state(user_id)
            await query.edit_message_text("❌ عملیات لغو شد.\n\nبرای شروع مجدد /start را بزنید.")
        elif data == "start":
            state.delete_state(user_id)
            await query.edit_message_text(
                welcome_text(query.from_user.first_name),
                reply_markup=welcome_keyboard()
            )
        elif data.startswith("pick_location_"):
            await handle_location_pick(query, context)
        elif data == "time_unknown":
            await handle_time_unknown(query, context)
    except TelegramError as e:
        logger.error(f"Telegram API error while handling '{data}': {e}")


async def start_chart_flow(query, context, mode):
    """Start chart creation flow with selected mode"""
    user_id = query.from_user.id
    
    s = state.init_state(user_id)
    s['mode'] = mode
    s['step'] = 'name'
    state.set_state(user_id, s)
    
    mode_names = {
        'natal': 'ناتال',
        'transit': 'ترانزیت',
        'synastry': 'سیناستری',
        'composite': 'کامپوزیت',
        'solar_return': 'سولار ریترن',
        'progressed': 'پروگرس'
    }
    
    await query.edit_message_text(
        f"🌟 ساخت چارت {mode_names.get(mode, mode)}\n\n"
        "لطفاً نام شخص را وارد کنید:\n"
        "(مثال: آلبرت انیشتین)",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ لغو", callback_data="cancel")]])
    )


async def handle_location_pick(query, context):
    """Handle location disambiguation pick"""
    user_id = query.from_user.id
    s = state.get_state(user_id)
    
    if not s or 'location_results' not in s:
        await query.edit_message_text(state.RESTART_MESSAGE)
        return
    
    # Extract index from callback data
    idx = int(query.data.replace("pick_location_", ""))
    results = s['location_results']
    
    if idx >= len(results):
        await query.edit_message_text("❌ انتخاب نامعتبر")
        return
    
    loc = results[idx]
    s['data']['latitude'] = loc['lat']
    s['data']['longitude'] = loc['lon']
    s['data']['location_name'] = f"{loc['name']}, {loc['country']}"
    s['data']['timezone'] = geocoding.resolve_timezone(loc['lat'], loc['lon'])
    s['step'] = 'confirm'
    del s['location_results']
    state.set_state(user_id, s)
    
    await show_confirmation(query, s['data'])


async def handle_time_unknown(query, context):
    """Handle unknown birth time"""
    user_id = query.from_user.id
    s = state.get_state(user_id)
    
    if not s or 'data' not in s:
        await query.edit_message_text(state.RESTART_MESSAGE)
        return
    
    s['data']['time'] = "12:00"
    s['step'] = 'city'
    state.set_state(user_id, s)
    
    await query.edit_message_text(
        "⏰ زمان: 12:00 (پیش‌فرض)\n\n"
        "📍 نام شهر یا مختصات جغرافیایی را وارد کنید:\n"
        "(مثال: Tehran, Iran یا 35.69,51.39)"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages based on user state"""
    user_id = update.effective_user.id
    text = update.message.text
    
    s = state.get_state(user_id)
    if not s:
        await update.message.reply_text("برای ساخت چارت، لطفاً /start را بزنید.")
        return
    
    if 'data' not in s:
        state.delete_state(user_id)
        await update.message.reply_text(state.RESTART_MESSAGE)
        return

    step = s.get('step')
    
    try:
        if step == 'name':
            s['data']['name'] = text
            s['step'] = 'date'
            state.set_state(user_id, s)
            
            await update.message.reply_text(
                f"✅ نام: {text}\n\n"
                "📅 تاریخ تولد را وارد کنید:\n"
                "فرمت: YYYY-MM-DD\n"
                "(مثال: 1879-03-14)"
            )
        
        elif step == 'date':
            try:
                validated = birthtime.validate_date(text)
                s['data']['date'] = validated
                s['step'] = 'time'
                state.set_state(user_id, s)
                
                keyboard = [[InlineKeyboardButton("⏰ زمان دقیق نمی‌دانم", callback_data="time_unknown")]]
                await update.message.reply_text(
                    f"✅ تاریخ: {text}\n\n"
                    "⏰ ساعت تولد را وارد کنید:\n"
                    "فرمت: HH:MM (24 ساعته)\n"
                    "(مثال: 11:30)",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            except birthtime.BirthTimeError as e:
                await update.message.reply_text(str(e))
        
        elif step == 'time':
            try:
                validated = birthtime.validate_time(text)
                s['data']['time'] = validated
                s['step'] = 'city'
                state.set_state(user_id, s)
                
                await update.message.reply_text(
                    f"✅ زمان: {text}\n\n"
                    "📍 نام شهر یا مختصات جغرافیایی را وارد کنید:\n"
                    "(مثال: Tehran, Iran یا 35.69,51.39)"
                )
            except birthtime.BirthTimeError as e:
                await update.message.reply_text(str(e))
        
        elif step == 'city':
            text_stripped = text.strip()

            try:
                if geocoding.looks_like_coordinates(text_stripped):
                    lat, lon = geocoding.parse_coordinates(text_stripped)
                    s['data']['latitude'] = lat
                    s['data']['longitude'] = lon
                    s['data']['location_name'] = f"{lat}, {lon}"
                    s['data']['timezone'] = geocoding.resolve_timezone(lat, lon)
                    s['step'] = 'confirm'
                    state.set_state(user_id, s)
                    
                    await show_confirmation(update.message, s['data'])
                else:
                    # Geocode with disambiguation
                    results = await asyncio.to_thread(geocoding.geocode_city, text_stripped)
                    
                    if not results:
                        await update.message.reply_text(
                            "❌ نام شهر یافت نشد.\n"
                            "لطفاً نام شهر معتبر (مثال: Tehran, Iran) یا مختصات دقیق (lat,lon) وارد کنید."
                        )
                        return
                    
                    if len(results) == 1:
                        # Single result, use it
                        loc = results[0]
                        s['data']['latitude'] = loc['lat']
                        s['data']['longitude'] = loc['lon']
                        s['data']['location_name'] = f"{loc['name']}, {loc['country']}"
                        s['data']['timezone'] = geocoding.resolve_timezone(loc['lat'], loc['lon'])
                        s['step'] = 'confirm'
                        state.set_state(user_id, s)
                        
                        await show_confirmation(update.message, s['data'])
                    else:
                        # Multiple results, ask user to pick
                        s['location_results'] = results
                        state.set_state(user_id, s)
                        
                        keyboard = []
                        for i, loc in enumerate(results[:5]):  # Limit to 5
                            label = f"{loc['name']}, {loc.get('admin1', '')}, {loc['country']}"
                            keyboard.append([InlineKeyboardButton(label, callback_data=f"pick_location_{i}")])
                        
                        await update.message.reply_text(
                            "📍 چندین مکان یافت شد. لطفاً یکی را انتخاب کنید:",
                            reply_markup=InlineKeyboardMarkup(keyboard)
                        )
                        
            except geocoding.LocationError as e:
                await update.message.reply_text(f"❌ {e}")
                
    except TelegramError as e:
        logger.error(f"Telegram API error while handling step '{step}': {e}")


async def show_confirmation(message_or_query, data):
    """Show confirmation screen"""
    keyboard = [
        [
            InlineKeyboardButton("✅ تایید و ساخت چارت", callback_data="confirm_create"),
            InlineKeyboardButton("❌ لغو", callback_data="cancel")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "📋 اطلاعات چارت:\n\n"
        f"👤 نام: {data.get('name', 'N/A')}\n"
        f"📅 تاریخ: {data.get('date', 'N/A')}\n"
        f"⏰ زمان: {data.get('time', 'Unknown')}\n"
        f"📍 مکان: {data.get('location_name', 'N/A')}\n"
        f"🕒 منطقه زمانی: {data.get('timezone', 'UTC')}\n\n"
        "آیا این اطلاعات درست است؟"
    )
    
    if hasattr(message_or_query, 'edit_message_text'):
        await message_or_query.edit_message_text(text, reply_markup=reply_markup)
    else:
        await message_or_query.reply_text(text, reply_markup=reply_markup)


async def generate_and_send_chart(query, context):
    """Generate chart and send to user"""
    user_id = query.from_user.id
    s = state.get_state(user_id)
    data = s.get('data') if s else None

    if not data or 'date' not in data or 'time' not in data:
        await query.edit_message_text(state.RESTART_MESSAGE)
        state.delete_state(user_id)
        return

    await query.edit_message_text("⏳ در حال محاسبه چارت...")

    # Resolve birth datetime with LMT support
    birth_info = birthtime.resolve_birth_utc(
        data['date'],
        data['time'],
        data.get('timezone', 'UTC'),
        data.get('longitude', 0)
    )

    # Prepare API request
    birth_data = {
        'datetime': birth_info['datetime'],
        'timezone': birth_info['timezone'],
        'latitude': data.get('latitude', 35.69),
        'longitude': data.get('longitude', 51.39)
    }
    
    # Call API
    chart_data = await call_api('/api/v1/birth-chart', birth_data)
    aspects_data = await call_api('/api/v1/aspects', birth_data)
    
    if not chart_data or not aspects_data:
        await query.edit_message_text(
            "❌ خطا در محاسبه چارت.\n"
            "لطفاً بعداً دوباره تلاش کنید."
        )
        state.delete_state(user_id)
        return
    
    # Generate text summary
    mode = s.get('mode', 'natal')
    chart_text = generate_chart_text(chart_data, aspects_data, data.get('name', 'شخص'), mode)
    
    # Send text
    await query.edit_message_text(chart_text, parse_mode='Markdown')
    
    # Generate and send chart wheel
    positions = chart_data.get('positions', [])
    houses = chart_data.get('houses', [])
    aspects = aspects_data.get('aspects', [])
    
    if positions and houses:
        asc = houses[0] if houses else {'cusp_longitude': 0}
        asc_lon = asc.get('cusp_longitude', 0)
        
        png_bytes = chartwheel.generate_chart_wheel_png(positions, houses, aspects, asc_lon)
        if png_bytes:
            try:
                await context.bot.send_photo(
                    chat_id=query.message.chat_id,
                    photo=png_bytes,
                    caption=f"🎯 Chart Wheel - {data.get('name', 'Chart')}"
                )
            except TelegramError as e:
                logger.error(f"Failed to send chart wheel: {e}")
    
    # Clean up
    state.delete_state(user_id)


async def show_settings(query, context):
    """Show settings menu"""
    keyboard = [
        [InlineKeyboardButton("🏠 سیستم خانه: Placidus (فقط)", callback_data="settings_noop")],
        [InlineKeyboardButton("🌍 زودیاک: Tropical (فقط)", callback_data="settings_noop")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "⚙️ تنظیمات\n\n"
        "تنظیمات فعلی:\n"
        "• سیستم خانه: Placidus\n"
        "• زودیاک: Tropical\n\n"
        "(در حال حاضر فقط Placidus و Tropical پشتیبانی می‌شوند)",
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
    logger.info("🚀 Starting Multi-Mode Astrology Bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
