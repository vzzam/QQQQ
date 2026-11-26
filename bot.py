import logging
import re
import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import Application, ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from keep_alive import keep_alive

# ==========================================
# 🔴 الإعدادات الأساسية
# ==========================================
TOKEN = os.getenv("BOT_TOKEN")
KOFI_URL = "https://ko-fi.com/vzzam"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

X_URL = "https://x.com/qtr_703?s=21"
CREDIT = f'<a href="{X_URL}">@qtr_703</a>'

# ==========================================
# 📊 نظام الإحصائيات
# ==========================================
STATS_FILE = "stats.json"

def load_stats():
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"users": [], "checks": 0}

def save_stats(stats):
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f)

# ==========================================
# 📂 قاعدة البيانات المرجعية (محدثة نوفمبر 2026)
# ==========================================
PS5_DB = {
    # CFI-10 Japanese (2020)
    "S01-13552": "1.02", "S01-1355": "1.02",
    "S01-02720": "2.00", "S01-0272": "2.00",
    "S01-03764": "2.30", "S01-0376": "2.30",
    "S01-1517": "3.20",

    # CFI-10 UK/EU (2020)
    "S01-1270": "1.00", "S01-1272": "1.00",
    "S01-1362": "1.02", "S01-1466": "1.02", "S01-206": "1.02",
    "S01-207": "1.02", "S01-2195": "1.02", "S01-2245": "1.02",
    "S01-2853": "2.00", "S01-2877": "2.00", "S01-3392": "2.00", "S01-3466": "2.00",
    "S01-4435": "2.50", "S01-4498": "2.50",
    "S01-4574": "2.70", "S01-4832": "2.70",
    "S01-5031": "3.00", "S01-5291": "3.00", "S01-530": "3.00",

    # CFI-10 Spain + Australia
    "F10701": "1.00", "F10801": "1.02", "F10901": "1.02",
    "F10B01": "1.02", "F101B01": "2.00", "F11301": "2.50", "F225": "3.20",

    # USA (AJ = CFI-10, AK = CFI-11)
    "AJ13501": "1.00", "AJ13542": "1.00", "AJ13575": "1.00",
    "AJ13571": "1.00", "AJ13610": "1.00", "AJ13619": "1.00",
    "AJ13628": "1.01", "AJ13644": "1.01", "AJ13707": "1.01",
    "AJ13735": "1.02", "AJ1379": "1.02", "AJ1387": "1.02",
    "AJ14144": "1.02", "AJ14181": "1.02", "AJ1446": "1.02",
    "AJ14480": "1.02", "AJ1456": "1.02", "AJ1457": "1.02", "AJ1466": "1.02",
    "AJ1489": "2.00", "AJ1491": "2.00", "AJ1498": "2.00",
    "AJ1501": "2.00", "AJ15078": "2.00", "AJ1514": "2.00",
    "AJ1539": "2.00", "AJ1541": "2.00", "AJ1578": "2.00", "AJ1588": "2.00",
    "AJ1594": "2.30", "AJ1599": "2.30", "AJ1610": "2.30",
    "AJ1617": "2.30", "AJ1639": "2.30", "AJ1644": "2.30", "AJ1646": "2.30",
    "AJ1675": "2.50", "AJ1683": "2.50",
    "AJ1690": "2.70", "AJ17115": "2.70", "AJ1733": "3.00",
    "AK396": "3.20", "AK418": "3.21", "AK4292": "4.03", "AK39908": "4.03",
    "AK3679": "4.50", "AK368": "4.50", "AK436": "5.02", "AK9145": "5.10",

    # CFI-11 (2021)
    "S01-X214": "2.50/3.00/3.10", "S01-X215": "3.00/3.10", "S01-X216": "3.00/3.10/3.20",
    "S01-X217": "3.20/3.21", "S01-X218": "3.21", "S01-X219": "3.20/3.21/4.00",
    "S01-X21A": "3.20/4.00/4.02/4.03", "S01-X21B": "4.03/4.50", "S01-X21C": "4.50",

    # CFI-11 (2022)
    "S01-X221": "4.50", "S01-X222": "4.50", "S01-X223": "4.50/4.51/5.00",
    "S01-X224": "5.00/5.02", "S01-X225": "5.02/5.10", "S01-X226": "5.10",
    "S01-X227": "5.10/5.50", "S01-X228": "5.50", "S01-X229": "5.50/6.00",
    "S01-X22A": "6.00/6.02", "S01-X22B": "6.02", "S01-X22C": "6.02",

    # CFI-12 (2022)
    "S01-X325": "5.10", "S01-X326": "5.10", "S01-X327": "5.10/5.50",
    "S01-X328": "5.50", "S01-X329": "5.50/6.00", "S01-X32A": "5.50/6.00",
    "S01-X32B": "6.02", "S01-X32C": "6.02",

    # CFI-12 (2023)
    "S01-X331": "6.02/6.50", "S01-X332": "6.02/6.50", "S01-X333": "6.50/7.00",
    "S01-X334": "7.00/7.20", "S01-X335": "7.00/7.20", "S01-X336": "7.20/7.40",
    "S01-X337": "7.40/7.60", "S01-X338": "7.60/7.61", "S01-X339": "7.61/8.00",
    "S01-X33A": "8.00/8.20", "S01-X33B": "8.20/8.20.02", "S01-X33C": "8.20.02/8.40",

    # CFI-20 Slim (2023)
    "S01-X434": "7.00", "S01-X435": "7.00/7.20", "S01-X436": "7.20/7.40",
    "S01-X437": "7.40/7.60", "S01-X438": "7.60/7.61", "S01-X439": "7.61/8.00",
    "S01-X43A": "7.61/8.00/8.20", "S01-X43B": "8.20/8.20.02", "S01-X43C": "8.20.02/8.40",

    # CFI-20 Slim (2024)
    "S01-X441": "8.40/8.60", "S01-X442": "8.60", "S01-X443": "8.60/9.00",
    "S01-X444": "9.00", "S01-X445": "9.00/9.20", "S01-X446": "9.20",
    "S01-X447": "9.40/9.60", "S01-X448": "9.40/9.60", "S01-X449": "9.60/10.00/10.01",
    "S01-X44A": "9.60/10.01/10.20", "S01-X44B": "10.20", "S01-X44C": "10.20/10.40",

    # CFI-20 Slim (2025)
    "S01-X451": "10.20/10.40", "S01-X452": "10.40/10.60", "S01-X453": "10.40/10.60",
    "S01-X454": "10.60/11.00", "S01-X455": "11.00/11.20", "S01-X456": "11.20",
    "S01-X457": "11.20/11.40", "S01-X458": "11.40/11.60", "S01-X459": "11.60",
    "S01-X45A": "11.60/12.00",

    # CFI-21 Slim (2025)
    "S01-X556": "11.20", "S01-X557": "11.20/11.40", "S01-X558": "11.40/11.60",
    "S01-X559": "11.60", "S01-X55A": "11.60/12.00", "S01-X55B": "12.02/12.20",
    "S01-X55C": "12.20/12.40",

    # CFI-21 Slim (2026)
    "S01-X561": "12.40/12.60", "S01-X562": "12.60/12.70", "S01-X563": "12.70/13.00",
    "S01-X564": "13.00/13.20", "S01-X565": "13.20", "S01-X566": "13.20",
    "S01-X567": "13.42/13.60", "S01-X568": "13.60", "S01-X569": "13.60/14.00",
    "S01-X56A": "14.10/14.20",

    # CFI-70 Pro (2024)
    "S01-X145": "9.05", "S01-X146": "9.05/9.40", "S01-X147": "9.40/9.60",
    "S01-X148": "9.60", "S01-X149": "9.60/10.00/10.01", "S01-X14A": "9.60/10.00/10.01/10.20",
    "S01-X14B": "10.01/10.20", "S01-X14C": "10.20/10.40",

    # CFI-70 Pro (2025)
    "S01-X151": "10.40", "S01-X152": "10.40/10.60", "S01-X153": "10.40/10.60",
    "S01-X154": "10.60/11.00", "S01-X155": "11.00/11.20", "S01-X156": "11.20",
    "S01-X157": "11.20/11.40", "S01-X158": "11.40/11.60", "S01-X159": "11.60",
    "S01-X15A": "11.60/12.00",

    # CFI-71 Pro (2025)
    "S01-X256": "11.20", "S01-X257": "11.20/11.40", "S01-X258": "11.40/11.60",
    "S01-X259": "11.60", "S01-X25A": "11.60/12.00", "S01-X25B": "12.00/12.02",
    "S01-X25C": "12.02/12.20",

    # CFI-71 Pro (2026)
    "S01-X261": "12.40/12.60", "S01-X262": "12.40/12.60/12.70", "S01-X263": "12.60/12.70/13.00",
    "S01-X264": "13.00/13.20", "S01-X265": "13.20", "S01-X266": "13.20/13.40",
    "S01-X267": "13.42/13.60", "S01-X268": "13.60", "S01-X269": "13.60/14.00",
    "S01-X26A": "14.10/14.20", "S01-X26B": "14.20/14.22"
}

# ==========================================
# 🛠️ الدوال المساعدة
# ==========================================
def get_exploits(v):
    kernels = []
    if 3.00 <= v <= 4.51:
        kernels.append("IPV6")
    if 1.00 <= v <= 7.61:
        kernels.append("UMTX")
    if (2.00 <= v <= 2.70) or (4.00 <= v <= 10.01):
        kernels.append("Lapse")
    if 4.00 <= v <= 12.00:
        kernels.append("NetControl")
    if 10.20 <= v <= 12.70:
        kernels.append("Kqueueex")
    if 8.00 <= v <= 13.60:
        kernels.append("RELAPSE")
    if 14.00 <= v <= 14.10:
        kernels.append("PROLAPSE ⏳")

    lines = []
    if not kernels:
        lines.append("│ 🧠 Kernel : None ❌")
    elif len(kernels) <= 2:
        lines.append(f"│ 🧠 Kernel : {', '.join(kernels)}")
    else:
        lines.append("│ 🧠 Kernel :")
        for i in range(0, len(kernels), 2):
            lines.append(f"│ • {', '.join(kernels[i:i+2])}")

    if 1.00 <= v <= 13.60:
        lines.append("│ 🌐 WebKit : ✅")
    if 3.00 <= v <= 13.60:
        lines.append("│ 💿 BD-JB  : ✅")
    if 2.00 <= v <= 14.22:
        lines.append("│ 🎮 mast1c : ✅")
    if 2.00 <= v <= 14.22:
        lines.append("│ 🐍 Lua    : ✅")
    if 2.00 <= v <= 13.60:
        lines.append("│ 🧩 Yarpe  : ✅")
    elif 14.00 <= v <= 14.22:
        lines.append("│ 🧩 Yarpe  : ❓")
    if 4.00 <= v <= 13.60:
        lines.append("│ ☕ Y2JB   : ✅")
    elif 14.00 <= v <= 14.22:
        lines.append("│ ☕ Y2JB   : ❓")
    if 4.00 <= v <= 12.40:
        lines.append("│ 📺 Netflix: ✅")

    etahen = "✅" if 2.00 <= v <= 13.60 else "❌"
    kstuff = "✅" if 1.00 <= v <= 13.60 else "❌"
    hv     = "✅" if 1.00 <= v <= 14.10 else "❌"
    linux  = "✅" if 3.00 <= v <= 13.60 else "❌"

    lines.append("├─────────────┤")
    lines.append("│ ⚙️ Features :")
    lines.append(f"│ • EtaHEN : {etahen}")
    lines.append(f"│ • Kstuff : {kstuff}")
    lines.append(f"│ • HV     : {hv}")
    lines.append(f"│ • Linux  : {linux}")

    return "\n".join(lines)

def analyze(text):
    text = text.upper().replace(" ", "").strip()

    if re.match(r'^S01[A-Z0-9]{4,}', text):
        text = "S01-" + text[3:]

    match = re.search(
        r'(S01-[A-Z][A-Z0-9]{3}|S01-\d{3,5}|AJ\d{4,5}|AK\d{3,5}|F10[0-9A-Z]{3,4}|F11301|F225)',
        text
    )
    if not match:
        return None

    full_ser = match.group(1)

    origins = {
        'F': "China 🇨🇳",
        'E': "China 🇨🇳",
        'K': "Japan 🇯🇵",
        'M': "Malaysia 🇲🇾",
        'G': "Global 🌐",
        'V': "Global 🌐"
    }
    m_map = {
        '1': 'January', '2': 'February', '3': 'March', '4': 'April',
        '5': 'May', '6': 'June', '7': 'July', '8': 'August',
        '9': 'September', 'A': 'October', 'B': 'November', 'C': 'December'
    }

    ref_key = full_ser
    if full_ser.startswith("S01-") and len(full_ser) == 8 and full_ser[4].isalpha():
        char = full_ser[4]
        origin = origins.get(char, "Unknown")
        ref_key = full_ser[:4] + "X" + full_ser[5:]
        year_char = full_ser[-2]
        month_char = full_ser[-1]
        production_year = f"202{year_char}" if year_char.isdigit() else "Unknown"
        production_month = m_map.get(month_char, "Unknown")
        production_date = f"{production_month} {production_year}"
    elif full_ser.startswith("S01-"):
        jp_prefixes = ("S01-1355", "S01-0272", "S01-0376", "S01-1517")
        origin = "Japan 🇯🇵" if full_ser.startswith(jp_prefixes) else "UK / EU 🇪🇺"
        production_date = "2020"
    elif full_ser.startswith("AJ"):
        origin = "USA 🇺🇸"
        production_date = "2020–2021"
    elif full_ser.startswith("AK"):
        origin = "USA 🇺🇸"
        production_date = "2021–2022"
    elif full_ser.startswith("F"):
        origin = "Spain / Australia 🇪🇸🇦🇺"
        production_date = "2020–2021"
    else:
        origin = "Unknown"
        production_date = "Unknown"

    found_fw = PS5_DB.get(ref_key) or PS5_DB.get(full_ser)
    if not found_fw:
        for k in sorted(PS5_DB.keys(), key=len, reverse=True):
            if ref_key.startswith(k) or full_ser.startswith(k):
                found_fw = PS5_DB[k]
                break

    if not found_fw:
        return "ERR"

    try:
        min_v = float(re.findall(r'(\d+\.\d+)', str(found_fw).split('/')[0])[0])
    except Exception:
        min_v = 99.99

    model = "Fat (CFI-10)"
    if full_ser.startswith("AJ") or full_ser.startswith("F"):
        model = "Fat (CFI-10)"
    elif full_ser.startswith("AK"):
        model = "Fat (CFI-11)"
    elif ref_key.startswith("S01-X") and len(ref_key) == 8:
        code = ref_key[5]
        year_digit = ref_key[6]
        if code == "1":
            model = "Pro (CFI-70)"
        elif code == "2":
            model = "Pro (CFI-71)" if year_digit in ("5", "6") else "Fat (CFI-11)"
        elif code == "3":
            model = "Fat (CFI-12)"
        elif code == "4":
            model = "Slim (CFI-20)"
        elif code == "5":
            model = "Slim (CFI-21)"

    is_supported = min_v <= 13.60
    is_pending = 14.00 <= min_v <= 14.10

    if is_supported:
        fw_icon = "✅"
        status_text = "SUPPORT ✅"
    elif is_pending:
        fw_icon = "⏳"
        status_text = "PENDING ⏳ (PROLAPSE)"
    else:
        fw_icon = "❌"
        status_text = "UNSUPPORTED ❌"

    return (
        f"<b>𝐏𝐒𝟓𝐀𝐙 𝐉𝐀𝐈𝐋𝐁𝐑𝐄𝐀𝐊 𝐂𝐇𝐄𝐂𝐊𝐄𝐑 🎮</b>\n\n"
        f"𝐒𝐞𝐫𝐢𝐚𝐥 📦:\n<code>{full_ser}</code>\n"
        f"𝐅𝐢𝐫𝐦𝐰𝐚𝐫𝐞 🔢:\n{found_fw} {fw_icon}\n"
        f"𝐌𝐨𝐝𝐞𝐥 🎮 :\n{model}\n"
        f"𝐌𝐚𝐝𝐞 𝐢𝐧 🏳️ :\n{origin}\n"
        f"𝐃𝐚𝐭𝐞 𝐨𝐟 𝐩𝐫𝐨𝐝𝐮𝐜𝐭𝐢𝐨𝐧 📅 :\n{production_date}\n"
        f"𝐒𝐭𝐚𝐭𝐮𝐬 📊:\n{status_text}\n\n"
        f"𝐄𝐱𝐩𝐥𝐨𝐢𝐭 𝐀𝐯𝐚𝐢𝐥𝐚𝐛𝐢𝐥𝐢𝐭𝐲 🔓:\n╭─────────────╮\n{get_exploits(min_v)}\n╰─────────────╯\n\n"
        f"BY: AZZAM\n\nThank You {CREDIT}"
    )

# ==========================================
# 🔘 زر الدعم فقط
# ==========================================
def get_support_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💎 Donate", url=KOFI_URL)]
    ])

# ==========================================
# 🚀 المعالجات (Handlers)
# ==========================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "<b>𝐏𝐒𝟓𝐀𝐙 𝐉𝐀𝐈𝐋𝐁𝐑𝐄𝐀𝐊 𝐂𝐇𝐄𝐂𝐊𝐄𝐑 🎮</b>\n\n"
        "📥 Send the Serial Number found on the bottom of the box.\n"
        "ارسل السيريال نمبر الموجود أسفل كرتون الجهاز.\n\n"
        "📝 Examples / أمثلة:\n"
        "<code>S01-E568 (Slim) | S01-F44A (Slim)</code>\n"
        "<code>S01-K268 (Pro)  | S01-F148 (Pro)</code>\n"
        "<code>S01-G338 (Fat)  | AJ1489 (USA)</code>\n\n"
        f"Thank You {CREDIT}"
    )
    await update.message.reply_text(
        msg,
        parse_mode=ParseMode.HTML,
        reply_markup=get_support_kb(),
        disable_web_page_preview=True
    )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.effective_user.username
    if username and username.lower() == "qtr_703":
        stats = load_stats()
        msg = (
            "📊 <b>إحصائيات البوت الحالية:</b>\n\n"
            f"👥 عدد المستخدمين الفريدين: <code>{len(stats['users'])}</code>\n"
            f"🔍 إجمالي عمليات الفحص: <code>{stats['checks']}</code>\n"
            "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
            "🛡️ <i>هذه الإحصائيات تظهر لك أنت فقط.</i>"
        )
        await update.message.reply_text(msg, parse_mode=ParseMode.HTML)

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    raw = update.message.text.upper().strip()

    if not raw.startswith(("S0", "AJ", "AK", "F10", "F113", "F225")):
        return

    user_id = update.effective_user.id
    stats = load_stats()
    if user_id not in stats["users"]:
        stats["users"].append(user_id)
    stats["checks"] += 1
    save_stats(stats)

    res = analyze(raw)

    if res == "ERR":
        text = (
            "<b>𝐏𝐒𝟓𝐀𝐙 𝐉𝐀𝐈𝐋𝐁𝐑𝐄𝐀𝐊 𝐂𝐇𝐄𝐂𝐊𝐄𝐑 🎮</b>\n\n"
            "❌ الرقم التسلسلي غير موجود في المرجع حالياً\n"
            "يرجى التأكد من كتابة الرقم الموجود أسفل كرتون الجهاز بشكل صحيح.\n\n"
            "❌ Serial number not found\n"
            "Please ensure you enter the number from the bottom of the box correctly.\n\n"
            "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
            "BY: AZZAM\n"
            f"Thank You {CREDIT}"
        )
        await update.message.reply_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=get_support_kb(),
            disable_web_page_preview=True
        )
    elif res:
        sent = await update.message.reply_text(
            res,
            parse_mode=ParseMode.HTML,
            reply_markup=get_support_kb(),
            disable_web_page_preview=True
        )
        # if update.effective_chat.type in ["group", "supergroup"]:
        #     context.job_queue.run_once(lambda c: c.bot.delete_message(sent.chat_id, sent.message_id), 3600)

async def post_init(application: Application):
    await application.bot.set_my_short_description(
        "𝐏𝐒𝟓𝐀𝐙 𝐉𝐀𝐈𝐋𝐁𝐑𝐄𝐀𝐊 𝐂𝐇𝐄𝐂𝐊𝐄𝐑 🎮\n"
        "📥 ارسل السيريال نمبر الموجود أسفل كرتون الجهاز."
    )
    await application.bot.set_my_description(
        "𝐏𝐒𝟓𝐀𝐙 𝐉𝐀𝐈𝐋𝐁𝐑𝐄𝐀𝐊 𝐂𝐇𝐄𝐂𝐊𝐄𝐑 🎮\n\n"
        "📥 Send the Serial Number (e.g., S01-F447).\n"
        "ارسل السيريال نمبر الموجود أسفل كرتون الجهاز.\n\n"
        "Thank You @qtr_703"
    )

if __name__ == '__main__':
    if not TOKEN:
        logging.error("BOT_TOKEN is not set! Please add it to your Environment Variables.")
    else:
        keep_alive()
        app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()

        app.add_handler(CommandHandler('start', start))
        app.add_handler(CommandHandler('stats', stats_command))
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle))

        app.run_polling()
