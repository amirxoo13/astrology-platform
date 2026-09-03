"""
Multi-mode Astrology Telegram Bot.

Natal, transit, secondary progression, and solar return are computed from the
Swiss Ephemeris API. Synastry and composite use two natal charts plus the
algorithms in astro.py (same aspect/house rules as the API).
"""
import asyncio
import logging
import os
import time
from datetime import datetime, timezone, timedelta, date
from io import BytesIO

import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)
from telegram.error import TelegramError

import state
import geocoding
import birthtime
import astro
import chartwheel

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
PLACEHOLDER_TOKENS = frozenset({"", "PLACEHOLDER_NO_TOKEN", "***:***"})

API_BASE_URL = os.getenv("API_BASE_URL", "http://ephemeris-api:8000")

SIGN_NAMES = {
    "Aries": "♈ حمل",
    "Taurus": "♉ ثور",
    "Gemini": "♊ جوزا",
    "Cancer": "♋ سرطان",
    "Leo": "♌ اسد",
    "Virgo": "♍ سنبله",
    "Libra": "♎ میزان",
    "Scorpio": "♏ عقرب",
    "Sagittarius": "♐ قوس",
    "Capricorn": "♑ جدی",
    "Aquarius": "♒ دلو",
    "Pisces": "♓ حوت",
}

PLANET_SYMBOLS = {
    "Sun": "☉",
    "Moon": "☽",
    "Mercury": "☿",
    "Venus": "♀",
    "Mars": "♂",
    "Jupiter": "♃",
    "Saturn": "♄",
    "Uranus": "♅",
    "Neptune": "♆",
    "Pluto": "♇",
}

ELEMENT_LABELS = {
    "FIRE": "🔥 آتش",
    "EARTH": "🌍 زمین",
    "AIR": "💨 هوا",
    "WATER": "💧 آب",
}

ASPECT_GLYPHS = {
    "CONJUNCTION": "☌",
    "OPPOSITION": "☍",
    "TRINE": "△",
    "SQUARE": "□",
    "SEXTILE": "⚹",
}

MODE_TITLES = {
    "natal": "ناتال",
    "transit": "ترانزیت",
    "synastry": "سیناستری",
    "composite": "کامپوزیت",
    "solar_return": "سولار ریترن",
    "progressed": "پروگرس",
}

ANGLE_HOUSES = ((1, "ASC"), (4, "IC"), (7, "DSC"), (10, "MC"))


def _require_bot_token():
    if not BOT_TOKEN or BOT_TOKEN in PLACEHOLDER_TOKENS:
        logger.error(
            "BOT_TOKEN is missing or a placeholder; the bot will idle instead of crash-looping."
        )
        while True:
            time.sleep(3600)
    return BOT_TOKEN


async def call_api(endpoint, data, method="POST"):
    """Call the Swiss Ephemeris API. POST by default (all calculation routes)."""
    url = f"{API_BASE_URL}{endpoint}"
    logger.info("Calling API: %s", url)
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            if method == "GET":
                response = await client.get(url, params=data)
            else:
                response = await client.post(url, json=data)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error("API returned error for %s: %s body=%s", url, e, getattr(e.response, "text", ""))
    except httpx.RequestError as e:
        logger.error("API call to %s failed: %s", url, e)
    except ValueError as e:
        logger.error("API response from %s was not valid JSON: %s", url, e)
    return None


def format_position(pos):
    """Format a planet or house-cusp dict using official API fields."""
    sign = pos.get("sign", "")
    sign_name = SIGN_NAMES.get(sign, sign)
    if pos.get("degree_in_sign") is not None:
        degree = int(pos["degree_in_sign"])
        minute = int(pos.get("degree_minute") or 0)
        second = int(pos.get("degree_second") or 0)
        if not minute and not second:
            frac = float(pos["degree_in_sign"]) - degree
            minute = int(frac * 60)
            second = int((frac * 60 % 1) * 60)
    else:
        lon = astro.ecliptic_longitude(pos)
        degree = int(lon % 30)
        minute = int((lon % 1) * 60)
        second = int(((lon % 1) * 60 % 1) * 60)
    retro = " ℞" if pos.get("retrograde", False) else ""
    return f"{degree}°{minute:02d}'{second:02d}\" {sign_name}{retro}"


def generate_chart_text(chart_data, aspects_data, user_name, mode="natal"):
    """Text summary from official birth-chart + aspects payloads."""
    positions = chart_data.get("positions", [])
    houses = chart_data.get("houses", [])
    aspects = aspects_data.get("aspects", []) if aspects_data else []
    cusps = astro.house_cusps(houses)

    title = MODE_TITLES.get(mode, "چارت")
    text = f"🌟 *چارت {title} {user_name}* 🌟\n\n"

    text += "🪐 *سیارات اصلی:*\n"
    for planet in positions:
        if not astro.is_main_planet(planet):
            continue
        name = astro.planet_display_name(planet)
        symbol = PLANET_SYMBOLS.get(name, "•")
        pos = format_position(planet)
        house_num = planet.get("house")
        if house_num in (None, "?"):
            house_num = astro.house_for_longitude(astro.ecliptic_longitude(planet), cusps)
        house_label = house_num if house_num is not None else "?"
        text += f"{symbol} {name}: {pos} (خانه {house_label})\n"

    if houses:
        text += "\n🏠 *خانه‌های اصلی:*\n"
        for num, name in ANGLE_HOUSES:
            if num <= len(houses):
                house = houses[num - 1]
                text += f"{name}: {format_position(house)}\n"

    if aspects:
        text += "\n✨ *جنبه‌های کلیدی:*\n"
        ranked = sorted(aspects, key=astro.true_aspect_orb)[:10]
        for aspect in ranked:
            p1 = astro.planet_display_name(aspect.get("planet1", ""))
            p2 = astro.planet_display_name(aspect.get("planet2", ""))
            atype = aspect.get("aspect_name") or aspect.get("aspect", "")
            glyph = ASPECT_GLYPHS.get(atype, "•")
            orb = astro.true_aspect_orb(aspect)
            orb_deg = int(orb)
            orb_min = int((orb % 1) * 60)
            text += f"{p1} {glyph} {p2} ({orb_deg}°{orb_min:02d}')\n"

    text += "\n🔥 *توزیع عناصر:*\n"
    counts = {"FIRE": 0, "EARTH": 0, "AIR": 0, "WATER": 0}
    for planet in positions:
        if not astro.is_main_planet(planet):
            continue
        sign_num = planet.get("sign_num")
        if sign_num is None and planet.get("sign") in astro.ZODIAC_SIGNS:
            sign_num = astro.ZODIAC_SIGNS.index(planet["sign"])
        element = astro.element_for_sign_num(sign_num) if sign_num is not None else None
        if element in counts:
            counts[element] += 1
    total = sum(counts.values())
    for elem, count in counts.items():
        percentage = (count / total * 100) if total else 0
        text += f"{ELEMENT_LABELS[elem]}: {count} ({percentage:.1f}%)\n"

    return text


def welcome_text(user_first_name):
    return (
        f"سلام {user_first_name}! 👋\n\n"
        "به بات استرولوژی حرفه‌ای خوش آمدید 🌟\n\n"
        "محاسبات از Swiss Ephemeris است:\n"
        "• چارت ناتال 🎯\n"
        "• ترانزیت (الان نسبت به ناتال) 🔄\n"
        "• سیناستری و کامپوزیت 💑\n"
        "• سولار ریترن و پروگرس ثانویه ☀️\n\n"
        "چه کاری می‌خواهید انجام دهید؟"
    )


def welcome_keyboard():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🎯 چارت ناتال", callback_data="mode_natal")],
            [InlineKeyboardButton("🔄 ترانزیت", callback_data="mode_transit")],
            [InlineKeyboardButton("💑 سیناستری", callback_data="mode_synastry")],
            [InlineKeyboardButton("🌐 کامپوزیت", callback_data="mode_composite")],
            [InlineKeyboardButton("☀️ سولار ریترن", callback_data="mode_solar_return")],
            [InlineKeyboardButton("📈 پروگرس", callback_data="mode_progressed")],
            [InlineKeyboardButton("⚙️ تنظیمات", callback_data="settings")],
        ]
    )


def cancel_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("❌ لغو", callback_data="cancel")]])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    try:
        await update.message.reply_text(
            welcome_text(user.first_name),
            reply_markup=welcome_keyboard(),
        )
    except TelegramError as e:
        logger.error("Failed to send welcome message: %s", e)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except TelegramError as e:
        logger.error("Failed to acknowledge callback query: %s", e)

    user_id = query.from_user.id
    data = query.data

    try:
        if data.startswith("mode_"):
            await start_chart_flow(query, context, data.replace("mode_", ""))
        elif data == "settings":
            await show_settings(query, context)
        elif data == "settings_noop":
            await query.edit_message_text(
                "در حال حاضر فقط Placidus و Tropical از طریق API استفاده می‌شوند.",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🔙 بازگشت", callback_data="settings")]]
                ),
            )
        elif data == "confirm_create":
            await generate_and_send_chart(query, context)
        elif data == "cancel":
            state.delete_state(user_id)
            await query.edit_message_text("❌ عملیات لغو شد.\n\nبرای شروع مجدد /start را بزنید.")
        elif data == "start":
            state.delete_state(user_id)
            await query.edit_message_text(
                welcome_text(query.from_user.first_name),
                reply_markup=welcome_keyboard(),
            )
        elif data.startswith("pick_location_"):
            await handle_location_pick(query, context)
        elif data == "time_unknown":
            await handle_time_unknown(query, context)
    except TelegramError as e:
        logger.error("Telegram API error while handling '%s': %s", data, e)


async def start_chart_flow(query, context, mode):
    user_id = query.from_user.id
    s = state.init_state(user_id)
    s["mode"] = mode
    s["step"] = "name"
    s["person_index"] = 1
    state.set_state(user_id, s)

    extra = ""
    if mode in astro.MODES_NEEDING_SECOND_PERSON:
        extra = "\n(نفر اول)"
    elif mode == "transit":
        extra = "\n(ترانزیت نسبت به لحظهٔ فعلی محاسبه می‌شود)"
    elif mode == "progressed":
        extra = "\n(پروگرس ثانویه: یک روز = یک سال، تا امروز)"
    elif mode == "solar_return":
        extra = "\n(بازگشت خورشید برای سال جاری)"

    await query.edit_message_text(
        f"🌟 ساخت چارت {MODE_TITLES.get(mode, mode)}{extra}\n\n"
        "لطفاً نام شخص را وارد کنید:\n"
        "(مثال: آلبرت انیشتین)",
        reply_markup=cancel_keyboard(),
    )


def _apply_location(s, loc):
    lat = loc["lat"]
    lon = loc["lon"]
    country = loc.get("country") or ""
    name = loc.get("name") or ""
    s["data"]["latitude"] = lat
    s["data"]["longitude"] = lon
    s["data"]["location_name"] = f"{name}, {country}".strip(", ")
    date_str = s["data"].get("date")
    if birthtime.should_use_lmt(date_str or "1900-01-01"):
        s["data"]["timezone"] = "LMT"
    else:
        s["data"]["timezone"] = geocoding.resolve_timezone(lat, lon)


async def _after_location(message_or_query, user_id, s):
    """Either start person 2, or show confirmation."""
    mode = s.get("mode", "natal")
    if mode in astro.MODES_NEEDING_SECOND_PERSON and s.get("person_index", 1) == 1:
        s["person1"] = dict(s["data"])
        s["data"] = {}
        s["person_index"] = 2
        s["step"] = "name"
        state.set_state(user_id, s)
        text = (
            "✅ نفر اول ثبت شد.\n\n"
            "💑 نفر دوم:\n"
            "لطفاً نام را وارد کنید:"
        )
        if hasattr(message_or_query, "edit_message_text"):
            await message_or_query.edit_message_text(text, reply_markup=cancel_keyboard())
        else:
            await message_or_query.reply_text(text, reply_markup=cancel_keyboard())
        return

    s["step"] = "confirm"
    state.set_state(user_id, s)
    await show_confirmation(message_or_query, s)


async def handle_location_pick(query, context):
    user_id = query.from_user.id
    s = state.get_state(user_id)

    if not s or "location_results" not in s:
        await query.edit_message_text(state.RESTART_MESSAGE)
        return

    idx = int(query.data.replace("pick_location_", ""))
    results = s["location_results"]
    if idx >= len(results):
        await query.edit_message_text("❌ انتخاب نامعتبر")
        return

    _apply_location(s, results[idx])
    del s["location_results"]
    await _after_location(query, user_id, s)


async def handle_time_unknown(query, context):
    user_id = query.from_user.id
    s = state.get_state(user_id)

    if not s or "data" not in s:
        await query.edit_message_text(state.RESTART_MESSAGE)
        return

    s["data"]["time"] = "12:00"
    s["step"] = "city"
    state.set_state(user_id, s)

    await query.edit_message_text(
        "⏰ زمان: 12:00 (پیش‌فرض ظهر؛ خانه‌ها تقریبی خواهند بود)\n\n"
        "📍 نام شهر یا مختصات جغرافیایی را وارد کنید:\n"
        "(مثال: Tehran, Iran یا 35.69,51.39)"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    s = state.get_state(user_id)
    if not s:
        await update.message.reply_text("برای ساخت چارت، لطفاً /start را بزنید.")
        return

    if "data" not in s:
        state.delete_state(user_id)
        await update.message.reply_text(state.RESTART_MESSAGE)
        return

    step = s.get("step")

    try:
        if step == "name":
            s["data"]["name"] = text
            s["step"] = "date"
            state.set_state(user_id, s)
            await update.message.reply_text(
                f"✅ نام: {text}\n\n"
                "📅 تاریخ تولد را وارد کنید:\n"
                "فرمت: YYYY-MM-DD\n"
                "(مثال: 1879-03-14)"
            )

        elif step == "date":
            try:
                validated = birthtime.validate_date(text)
                s["data"]["date"] = validated
                s["step"] = "time"
                state.set_state(user_id, s)
                keyboard = [
                    [InlineKeyboardButton("⏰ زمان دقیق نمی‌دانم", callback_data="time_unknown")]
                ]
                await update.message.reply_text(
                    f"✅ تاریخ: {text}\n\n"
                    "⏰ ساعت تولد را وارد کنید:\n"
                    "فرمت: HH:MM (24 ساعته)\n"
                    "(مثال: 11:30)",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                )
            except birthtime.BirthTimeError as e:
                await update.message.reply_text(str(e))

        elif step == "time":
            try:
                validated = birthtime.validate_time(text)
                s["data"]["time"] = validated
                s["step"] = "city"
                state.set_state(user_id, s)
                await update.message.reply_text(
                    f"✅ زمان: {text}\n\n"
                    "📍 نام شهر یا مختصات جغرافیایی را وارد کنید:\n"
                    "(مثال: Tehran, Iran یا 35.69,51.39)"
                )
            except birthtime.BirthTimeError as e:
                await update.message.reply_text(str(e))

        elif step == "city":
            text_stripped = text.strip()
            try:
                if geocoding.looks_like_coordinates(text_stripped):
                    lat, lon = geocoding.parse_coordinates(text_stripped)
                    _apply_location(
                        s,
                        {"name": f"{lat}, {lon}", "country": "", "lat": lat, "lon": lon},
                    )
                    await _after_location(update.message, user_id, s)
                else:
                    results = await asyncio.to_thread(geocoding.geocode_city, text_stripped)
                    if not results:
                        await update.message.reply_text(
                            "❌ نام شهر یافت نشد.\n"
                            "لطفاً نام شهر معتبر (مثال: Tehran, Iran) یا مختصات دقیق (lat,lon) وارد کنید."
                        )
                        return
                    if len(results) == 1:
                        _apply_location(s, results[0])
                        await _after_location(update.message, user_id, s)
                    else:
                        s["location_results"] = results[:5]
                        state.set_state(user_id, s)
                        keyboard = []
                        for i, loc in enumerate(s["location_results"]):
                            label = f"{loc['name']}, {loc.get('admin1', '')}, {loc['country']}"
                            keyboard.append(
                                [InlineKeyboardButton(label, callback_data=f"pick_location_{i}")]
                            )
                        await update.message.reply_text(
                            "📍 چندین مکان یافت شد. لطفاً یکی را انتخاب کنید:",
                            reply_markup=InlineKeyboardMarkup(keyboard),
                        )
            except geocoding.LocationError as e:
                await update.message.reply_text(f"❌ {e}")

    except TelegramError as e:
        logger.error("Telegram API error while handling step '%s': %s", step, e)


def _person_summary(data, heading):
    tz_note = data.get("timezone", "UTC")
    if tz_note == "LMT":
        tz_note = "LMT (تبدیل به UTC از روی طول جغرافیایی)"
    return (
        f"{heading}\n"
        f"👤 نام: {data.get('name', 'N/A')}\n"
        f"📅 تاریخ: {data.get('date', 'N/A')}\n"
        f"⏰ زمان: {data.get('time', 'Unknown')}\n"
        f"📍 مکان: {data.get('location_name', 'N/A')}\n"
        f"🕒 منطقه زمانی: {tz_note}"
    )


async def show_confirmation(message_or_query, s):
    mode = s.get("mode", "natal")
    parts = []
    if s.get("person1"):
        parts.append(_person_summary(s["person1"], "نفر اول:"))
        parts.append(_person_summary(s["data"], "نفر دوم:"))
    else:
        parts.append(_person_summary(s["data"], "📋 اطلاعات چارت:"))

    if mode == "transit":
        parts.append("🔄 ترانزیت نسبت به زمان فعلی (UTC) محاسبه می‌شود.")
    elif mode == "progressed":
        parts.append("📈 پروگرس ثانویه تا امروز (۱ روز = ۱ سال).")
    elif mode == "solar_return":
        parts.append("☀️ سولار ریترن سال جاری در محل تولد.")

    text = "\n\n".join(parts) + "\n\nآیا این اطلاعات درست است؟"
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✅ تایید و ساخت چارت", callback_data="confirm_create"),
                InlineKeyboardButton("❌ لغو", callback_data="cancel"),
            ]
        ]
    )

    if hasattr(message_or_query, "edit_message_text"):
        await message_or_query.edit_message_text(text, reply_markup=keyboard)
    else:
        await message_or_query.reply_text(text, reply_markup=keyboard)


def _api_payload(data):
    if "latitude" not in data or "longitude" not in data:
        raise KeyError("latitude/longitude")
    birth_info = birthtime.resolve_birth_utc(
        data["date"],
        data["time"],
        data.get("timezone", "UTC"),
        data["longitude"],
    )
    return {
        "datetime": birth_info["datetime"],
        "timezone": birth_info["timezone"],
        "latitude": data["latitude"],
        "longitude": data["longitude"],
        "house_system": "P",
        "ayanamsa": "TROPICAL",
    }, birth_info


async def _sun_longitude(payload):
    planets = await call_api(
        "/api/v1/planets",
        {
            "datetime": payload["datetime"],
            "timezone": payload["timezone"],
            "latitude": payload["latitude"],
            "longitude": payload["longitude"],
            "planets": ["SUN"],
        },
    )
    if not planets:
        return None
    for pos in planets.get("positions", []):
        if astro.planet_id(pos) == "SUN":
            return astro.ecliptic_longitude(pos)
    return None


async def _build_mode_charts(mode, data, person1=None):
    """Return (chart_data, aspects_data, wheel_positions, wheel_houses, wheel_aspects, asc_lon)."""
    natal_payload, _ = _api_payload(data)

    if mode == "synastry":
        p1_payload, _ = _api_payload(person1)
        p2_payload = natal_payload
        c1 = await call_api("/api/v1/birth-chart", p1_payload)
        c2 = await call_api("/api/v1/birth-chart", p2_payload)
        if not c1 or not c2:
            return None
        aspects = {"aspects": astro.cross_aspects(c1["positions"], c2["positions"], max_orb=0.7)}
        return c1, aspects, c1.get("positions", []), c1.get("houses", []), aspects["aspects"], c1.get("ascendant", 0)

    if mode == "composite":
        p1_payload, _ = _api_payload(person1)
        p2_payload = natal_payload
        c1 = await call_api("/api/v1/birth-chart", p1_payload)
        c2 = await call_api("/api/v1/birth-chart", p2_payload)
        if not c1 or not c2:
            return None
        midpoints = astro.composite_midpoints(c1["positions"], c2["positions"])
        composite_asc = astro.shortest_arc_midpoint(c1["ascendant"], c2["ascendant"])
        houses = astro.equal_houses_from_asc(composite_asc)
        chart = {
            "positions": midpoints,
            "houses": houses,
            "ascendant": composite_asc,
            "medium_coeli": astro.normalize_angle(composite_asc + 270),
        }
        aspects = {"aspects": astro.find_aspects(midpoints)}
        return chart, aspects, midpoints, houses, aspects["aspects"], composite_asc

    if mode == "transit":
        natal = await call_api("/api/v1/birth-chart", natal_payload)
        now = datetime.now(timezone.utc)
        transit_payload = {
            "datetime": now.strftime("%Y-%m-%dT%H:%M:%S"),
            "timezone": "UTC",
            "latitude": natal_payload["latitude"],
            "longitude": natal_payload["longitude"],
            "house_system": "P",
            "ayanamsa": "TROPICAL",
        }
        transit = await call_api("/api/v1/birth-chart", transit_payload)
        if not natal or not transit:
            return None
        aspects = {"aspects": astro.cross_aspects(natal["positions"], transit["positions"], max_orb=1.0)}
        return transit, aspects, transit.get("positions", []), natal.get("houses", []), aspects["aspects"], natal.get("ascendant", 0)

    if mode == "progressed":
        birth = datetime.strptime(data["date"], "%Y-%m-%d").date()
        years = (date.today() - birth).days / astro.TROPICAL_YEAR_DAYS
        prog_date = astro.progressed_instant(data["date"], years)
        prog_payload = dict(natal_payload)
        # Keep the natal clock time; only the calendar day is progressed.
        natal_time = data["time"]
        if natal_payload["timezone"] == "UTC" and "T" in natal_payload["datetime"]:
            prog_payload["datetime"] = f"{prog_date}T{natal_payload['datetime'].split('T', 1)[1]}"
        else:
            prog_payload["datetime"] = f"{prog_date}T{natal_time}:00"
        chart = await call_api("/api/v1/birth-chart", prog_payload)
        aspects = await call_api("/api/v1/aspects", prog_payload)
        if not chart or not aspects:
            return None
        return chart, aspects, chart.get("positions", []), chart.get("houses", []), aspects.get("aspects", []), chart.get("ascendant", 0)

    if mode == "solar_return":
        natal = await call_api("/api/v1/birth-chart", natal_payload)
        if not natal:
            return None
        natal_sun = None
        for pos in natal.get("positions", []):
            if astro.planet_id(pos) == "SUN":
                natal_sun = astro.ecliptic_longitude(pos)
                break
        if natal_sun is None:
            return None
        target_year = datetime.now(timezone.utc).year
        guess_date = astro.solar_return_guess(data["date"], target_year)
        guess_payload = dict(natal_payload)
        if natal_payload["timezone"] == "UTC" and "T" in natal_payload["datetime"]:
            guess_payload["datetime"] = f"{guess_date}T{natal_payload['datetime'].split('T', 1)[1]}"
        else:
            guess_payload["datetime"] = f"{guess_date}T{data['time']}:00"
        sun_on_guess = await _sun_longitude(guess_payload)
        if sun_on_guess is None:
            return None
        delta_days = astro.solar_return_adjust_days(natal_sun, sun_on_guess)
        guess_dt = datetime.strptime(guess_payload["datetime"], "%Y-%m-%dT%H:%M:%S")
        sr_dt = guess_dt + timedelta(days=delta_days)
        sr_payload = dict(guess_payload)
        sr_payload["datetime"] = sr_dt.strftime("%Y-%m-%dT%H:%M:%S")
        chart = await call_api("/api/v1/birth-chart", sr_payload)
        aspects = await call_api("/api/v1/aspects", sr_payload)
        if not chart or not aspects:
            return None
        return chart, aspects, chart.get("positions", []), chart.get("houses", []), aspects.get("aspects", []), chart.get("ascendant", 0)

    # natal
    chart = await call_api("/api/v1/birth-chart", natal_payload)
    aspects = await call_api("/api/v1/aspects", natal_payload)
    if not chart or not aspects:
        return None
    return chart, aspects, chart.get("positions", []), chart.get("houses", []), aspects.get("aspects", []), chart.get("ascendant", 0)


async def generate_and_send_chart(query, context):
    user_id = query.from_user.id
    s = state.get_state(user_id)
    data = s.get("data") if s else None

    if not data or "date" not in data or "time" not in data:
        await query.edit_message_text(state.RESTART_MESSAGE)
        state.delete_state(user_id)
        return

    if "latitude" not in data or "longitude" not in data:
        await query.edit_message_text(
            "❌ مختصات جغرافیایی موجود نیست. لطفاً دوباره از /start شروع کنید."
        )
        state.delete_state(user_id)
        return

    mode = s.get("mode", "natal")
    if mode in astro.MODES_NEEDING_SECOND_PERSON and not s.get("person1"):
        await query.edit_message_text(state.RESTART_MESSAGE)
        state.delete_state(user_id)
        return

    await query.edit_message_text("⏳ در حال محاسبه چارت...")

    try:
        built = await _build_mode_charts(mode, data, s.get("person1"))
    except (KeyError, ValueError, TypeError) as e:
        logger.error("Failed to prepare chart request: %s", e)
        built = None

    if not built:
        await query.edit_message_text(
            "❌ خطا در محاسبه چارت.\nلطفاً بعداً دوباره تلاش کنید."
        )
        state.delete_state(user_id)
        return

    chart_data, aspects_data, positions, houses, aspects, asc_lon = built

    try:
        chart_text = generate_chart_text(
            chart_data, aspects_data, data.get("name", "شخص"), mode
        )
    except (KeyError, TypeError, ValueError) as e:
        logger.error("Failed to parse ephemeris API response: %s", e)
        await query.edit_message_text(
            "❌ پاسخ سرویس محاسبات نامعتبر بود.\nلطفاً بعداً دوباره تلاش کنید."
        )
        state.delete_state(user_id)
        return

    try:
        await query.edit_message_text(chart_text, parse_mode="Markdown")
    except TelegramError as e:
        logger.error("Markdown send failed, retrying plain text: %s", e)
        try:
            await query.edit_message_text(chart_text)
        except TelegramError as e2:
            logger.error("Failed to send chart result: %s", e2)

    if positions and houses:
        if not asc_lon:
            try:
                asc_lon = astro.ecliptic_longitude(houses[0])
            except (KeyError, TypeError, ValueError, IndexError):
                asc_lon = 0
        png_bytes = chartwheel.generate_chart_wheel_png(positions, houses, aspects, asc_lon)
        if png_bytes:
            try:
                await context.bot.send_photo(
                    chat_id=query.message.chat_id,
                    photo=BytesIO(png_bytes),
                    caption=f"🎯 Chart Wheel - {data.get('name', 'Chart')}",
                )
            except TelegramError as e:
                logger.error("Failed to send chart wheel: %s", e)

    state.delete_state(user_id)


async def show_settings(query, context):
    keyboard = [
        [InlineKeyboardButton("🏠 سیستم خانه: Placidus", callback_data="settings_noop")],
        [InlineKeyboardButton("🌍 زودیاک: Tropical", callback_data="settings_noop")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="start")],
    ]
    await query.edit_message_text(
        "⚙️ تنظیمات\n\n"
        "تنظیمات فعلی (مطابق پیش‌فرض Swiss Ephemeris API):\n"
        "• سیستم خانه: Placidus (`house_system=P`)\n"
        "• زودیاک: Tropical (`ayanamsa=TROPICAL`)\n",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


def main():
    token = _require_bot_token()
    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("Starting astrology bot")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
