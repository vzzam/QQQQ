import logging
import re
import asyncio
import os
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from keep_alive import keep_alive

# ==========================================
# 🔴 الإعدادات الأساسية
# ==========================================
TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

X_URL = "https://x.com/qtr_703?s=21"
CREDIT = f'<a href="{X_URL}">@qtr_703</a>'

# ==========================================
# 📂 قاعدة البيانات المرجعية
# ==========================================
PS5_DB = {
    "S01-1355": "1.02", "S01-0272": "2.00", "S01-0376": "2.30", "S01-1517": "3.20",
    "S01-1270": "1.00", "S01-2853": "2.00", "S01-5031": "3.00",
    "S01-X214": "2.50/3.10", "S01-X215": "3.00/3.10", "S01-X216": "3.00/3.20",
    "S01-X217": "3.20/3.21", "S01-X218": "3.21", "S01-X219": "3.20/4.00",
    "S01-X21A": "3.20/4.03", "S01-X21B": "4.03/4.50", "S01-X21C": "4.50",
    "S01-X221": "4.50", "S01-X222": "4.50", "S01-X223": "4.50/5.00",
    "S01-X224": "5.00/5.02", "S01-X225": "5.02/5.10", "S01-X226": "5.10",
    "S01-X227": "5.10/5.50", "S01-X228": "5.50", "S01-X229": "5.50/6.00",
    "S01-X22A": "6.00/6.02", "S01-X22B": "6.02", "S01-X22C": "6.02",
    "S01-X325": "5.10", "S01-X326": "5.10", "S01-X327": "5.10/5.50",
    "S01-X328": "5.50", "S01-X329": "5.50/6.00", "S01-X32A": "5.50/6.00",
    "S01-X32B": "6.02", "S01-X32C": "6.02",
    "S01-X331": "6.02/6.50", "S01-X332": "6.02/6.50", "S01-X333": "6.50/7.00",
    "S01-X334": "7.00/7.20", "S01-X335": "7.00/7.20", "S01-X336": "7.20/7.40",
    "S01-X337": "7.40/7.60", "S01-X338": "7.60/7.61", "S01-X339": "7.61/8.00",
    "S01-X33A": "8.00/8.20", "S01-X33B": "8.20/8.20.02", "S01-X33C": "8.20.02/8.40",
    "S01-X434": "7.00", "S01-X435": "7.00/7.20", "S01-X436": "7.20/7.40",
    "S01-X437": "7.40/7.60", "S01-X438": "7.60/7.61", "S01-X439": "7.61/8.00",
    "S01-X43A": "7.61/8.20", "S01-X43B": "8.20", "S01-X43C": "8.20/8.40",
    "S01-X441": "8.40/8.60", "S01-X442": "8.60", "S01-X443": "8.60/9.00",
    "S01-X444": "9.00", "S01-X445": "9.00/9.20", "S01-X446": "9.20",
    "S01-X447": "9.40/9.60", "S01-X448": "9.40/9.60", "S01-X449": "9.60/10.01",
    "S01-X44A": "10.01/10.20", "S01-X44B": "10.20", "S01-X44C": "10.20/10.40",
    "S01-X451": "10.40", "S01-X452": "10.40/10.60", "S01-X453": "10.40/10.60",
    "S01-X454": "10.60/11.00", "S01-X455": "11.00/11.20", "S01-X456": "11.20",
    "S01-X457": "11.20/11.40", "S01-X458": "11.40/11.60", "S01-X459": "11.60",
    "S01-X45A": "11.60/12.00",
    "S01-X556": "11.20", "S01-X557": "11.20/11.40", "S01-X558": "11.40/11.60",
    "S01-X559": "11.60", "S01-X55A": "11.60/12.00", "S01-X55B": "12.02/12.20",
    "S01-X55C": "12.02/12.20",
    "S01-X145": "9.05", "S01-X146": "9.05/9.40", "S01-X147": "9.40/9.60",
    "S01-X148": "9.60", "S01-X149": "9.60/10.01", "S01-X14A": "9.60/10.20",
    "S01-X14B": "10.01/10.20", "S01-X14C": "10.20/10.40",
    "S01-X151": "10.40", "S01-X152": "10.40/10.60", "S01-X153": "10.40/10.60",
    "S01-X154": "10.60/11.00", "S01-X155": "11.00/11.20", "S01-X156": "11.20",
    "S01-X157": "11.20/11.40", "S01-X158": "11.40/11.60", "S01-X159": "11.60",
    "S01-X15A": "11.60/12.00",
    "S01-X256": "11.20", "S01-X257": "11.20/11.40", "S01-X258": "11.40/11.60",
    "S01-X259": "11.60", "S01-X25A": "11.60/12.00", "S01-X25B": "12.00/12.02",
    "S01-X25C": "12.02/12.20"
}

# ==========================================
# 🛠️ الدوال المساعدة
# ==========================================
def get_exploits(v):
    exploits = {
        "⏳ Lapse": "✅" if v <= 10.01 else "❌",
        "💿 BD-JB": "✅" if v <= 7.61 else "🔒 (Private)" if v <= 10.01 else "❌",
        "🎮 mast1c": "✅" if v <= 13.20 else "❌",
        "🐍 Lua": "✅" if v <= 13.20 else "❌",
        "☕ Y2JB": "✅" if v <= 13.20 else "❌",
        "📺 Netflix": "✅" if v <= 12.40 else "❌"
    }
    return "\n".join([f"│ {k} : {val}" for k, val in exploits.items() if val != "❌"])

def analyze(text):
    text = text.upper().replace(" ", "").strip()
    # استخراج أول 8 رموز (S01-XXXX) للتعامل معها كمرجع صارم
    match = re.search(r'(S0[A-Z0-9-]{5,6})', text)
    if not match: return None
    
    full_ser = match.group(1)
    
    # 1. تحديد الدولة بناءً على الحرف الرابع
    origin = "Unknown"
    char = full_ser[4] if len(full_ser) > 4 else ""
    origins = {'F': "China 🇨🇳", 'E': "China 🇨🇳", 'K': "Japan 🇯🇵", 'M': "Malaysia 🇲🇾", 'G': "Global 🌐"}
    origin = origins.get(char, "Unknown")

    # 2. تحويل السيريال لمفتاح مرجعي (استبدال حرف الدولة بـ X)
    ref_key = full_ser
    if char.isalpha():
        ref_key = full_ser[:4] + "X" + full_ser[5:]

    # 3. البحث في قاعدة البيانات عن الفيرموير
    found_fw = None
    for k in sorted(PS5_DB.keys(), key=len, reverse=True):
        if ref_key.startswith(k) or full_ser.startswith(k):
            found_fw = PS5_DB[k]
            break
    
    if not found_fw: return "ERR"

    try:
        min_v = float(re.findall(r'(\d+\.\d+)', str(found_fw).split('/')[0])[0])
    except: min_v = 99.99

    # 4. تحديد الموديل بناءً على الرموز المرجعية
    model = "Fat"
    if "X4" in ref_key or "X3" in ref_key: model = "Slim (CFI-20)"
    elif "X5" in ref_key: model = "Slim (CFI-21)"
    elif "X1" in ref_key: model = "Pro (CFI-70)"
    elif "X2" in ref_key:
        model = "Pro (CFI-71)" if "X25" in ref_key else "Fat/Pro"

    # 5. تحديد تاريخ الإنتاج (القبل الأخير سنة، الأخير شهر)
    m_map = {'1':'January','2':'February','3':'March','4':'April','5':'May','6':'June','7':'July','8':'August','9':'September','A':'October','B':'November','C':'December'}
    
    year_char = full_ser[-2] if len(full_ser) >= 2 else ""
    production_year = f"202{year_char}" if year_char.isdigit() else "Unknown"
    
    month_char = full_ser[-1] if len(full_ser) >= 1 else ""
    production_month = m_map.get(month_char, "Unknown")

    return (
        f"<b> Councilor 𝐏𝐒𝟓𝐀𝐙 𝐉𝐀𝐈𝐋𝐁𝐑𝐄𝐀𝐊 𝐂𝐇𝐄𝐂𝐊𝐄𝐑 🎮</b>\n\n"
        f"𝐒𝐞𝐫𝐢𝐚𝐥 📦:\n<code>{full_ser}</code>\n"
        f"𝐅𝐢𝐫𝐦𝐰𝐚𝐫𝐞 🔢:\n{found_fw} {'✅' if min_v <= 11.00 else '❌'}\n"
        f"𝐌𝐨𝐝𝐞𝐥 🎮 :\n{model}\n"
        f"𝐌𝐚𝐝𝐞 𝐢𝐧 🏳️ :\n{origin}\n"
        f"𝐃𝐚𝐭𝐞 𝐨𝐟 𝐩𝐫𝐨𝐝𝐮𝐜𝐭𝐢𝐨𝐧 📅 :\n{production_month} {production_year}\n"
        f"𝐒𝐭𝐚𝐭𝐮𝐬 📊:\n{'SUPPORT ✅' if min_v <= 11.00 else 'UNSUPPORTED ❌'}\n\n"
        f"𝐄𝐱𝐩𝐥𝐨𝐢𝐭 𝐀𝐯𝐚𝐢𝐥𝐚𝐛𝐢𝐥𝐢𝐭𝐲 🔓:\n╭─────────────╮\n{get_exploits(min_v)}\n╰─────────────╯\n\n"
        f"BY: AZZAM\n\nThank You {CREDIT}"
    )

# ==========================================
# 🚀 المعالجات (Handlers)
# ==========================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "<b>Components 𝐏𝐒𝟓𝐀𝐙 𝐉𝐀𝐈𝐋𝐁𝐑𝐄𝐀𝐊 𝐂𝐇𝐄𝐂𝐊𝐄𝐑 🎮</b>\n\n"
        "📥 Send the Serial Number found on the bottom of the box.\n"
        "ارسل السيريال نمبر الموجود أسفل كرتون الجهاز.\n\n"
        "📝 Examples / أمثلة:\n"
        "<code>S01-X44A | S01-E44A</code>\n"
        "<code>S01-F148 (Pro) | S01-M44A</code>\n"
        "<code>S01-G44A (Fat)</code>\n\n"
        f"Thank You {CREDIT}"
    )
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    raw = update.message.text.upper().strip()
    
    # فلترة صارمة: تجاهل أي رسالة لا تبدأ بـ S0
    if not raw.startswith("S0"): return

    res = analyze(raw)
    if res == "ERR":
        text = (
            "<b>🎛️ 𝐏𝐒𝟓𝐀𝐙 𝐉𝐀𝐈𝐋𝐁𝐑𝐄𝐀𝐊 𝐂𝐇𝐄𝐂𝐊𝐄𝐑 🎮</b>\n\n"
            "❌ الرقم التسلسلي غير صحيح\n"
            "يرجى التأكد من كتابة الرقم الموجود أسفل كرتون الجهاز بشكل صحيح.\n\n"
            "❌ Serial number incorrect\n"
            "Please ensure you enter the number from the bottom of the box correctly.\n\n"
            "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
            "BY: AZZAM\n"
            f"Thank You {CREDIT}"
        )
    elif res:
        text = res
    else: return

    sent = await update.message.reply_text(text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    
    if update.effective_chat.type in ["group", "supergroup"]:
        context.job_queue.run_once(lambda c: c.bot.delete_message(sent.chat_id, sent.message_id), 3600)

if __name__ == '__main__':
    keep_alive()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle))
    app.run_polling()
