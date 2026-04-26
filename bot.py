import logging
import re
import asyncio
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from keep_alive import keep_alive

# ==========================================
# 🔴 إعدادات البوت
# ==========================================
TOKEN = "7976756950:AAGs4odFu9fABU0nYNUnuCUJyB4QIdINgS4"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ==========================================
# 📂 قاعدة البيانات
# ==========================================
PS5_DB = {
    # CFI-10/11 (Fat)
    "S01-1355": "1.02", "S01-0272": "2.00", "S01-0376": "2.30", "S01-1517": "3.20",
    "F1070": "1.00", "F1080": "1.02", "F1090": "1.02", "F10B0": "1.02", "F1130": "2.50", "F225": "3.20",
    "AJ135": "1.00", "AJ148": "2.00", "AJ159": "2.30", "AJ173": "3.00",
    "AK396": "3.20", "AK429": "4.03", "AK367": "4.50", "AK914": "5.10",
    "S01-1270": "1.00", "S01-2853": "2.00", "S01-5031": "3.00",
    
    # CFI-11/12/20 (S01-X Pattern)
    "S01-X214": "2.50/3.10", "S01-X215": "3.00/3.10", "S01-X216": "3.00/3.20",
    "S01-X217": "3.20/3.21", "S01-X218": "3.21", "S01-X219": "3.20/4.00",
    "S01-X21A": "3.20/4.03", "S01-X21B": "4.03/4.50", "S01-X21C": "4.50",
    "S01-X221": "4.50", "S01-X222": "4.50", "S01-X223": "4.50/5.00",
    "S01-X224": "5.00/5.02", "S01-X225": "5.02/5.10", "S01-X226": "5.10",
    "S01-X227": "5.10/5.50", "S01-X228": "5.50", "S01-X229": "5.50/6.00",
    "S01-X22A": "6.00/6.02", "S01-X22B": "6.02", "S01-X22C": "6.02",
    
    # S01-X32 Series
    "S01-X325": "5.10", "S01-X326": "5.10", "S01-X327": "5.10/5.50",
    "S01-X328": "5.50", "S01-X329": "5.50/6.00", "S01-X32A": "5.50/6.00",
    "S01-X32B": "6.02", "S01-X32C": "6.02",
    
    # S01-X33 Series
    "S01-X331": "6.02/6.50", "S01-X332": "6.02/6.50", "S01-X333": "6.50/7.00",
    "S01-X334": "7.00/7.20", "S01-X335": "7.00/7.20", "S01-X336": "7.20/7.40",
    "S01-X337": "7.40/7.60", "S01-X338": "7.60/7.61", "S01-X339": "7.61/8.00",
    "S01-X33A": "8.00/8.20", "S01-X33B": "8.20/8.20.02", "S01-X33C": "8.20.02/8.40",

    # CFI-20 (Slim)
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

    # CFI-21 (Slim Refresh)
    "S01-X556": "11.20", "S01-X557": "11.20/11.40", "S01-X558": "11.40/11.60",
    "S01-X559": "11.60", "S01-X55A": "11.60/12.00", "S01-X55B": "12.02/12.20",
    "S01-X55C": "12.02/12.20",

    # CFI-70 (Pro)
    "S01-X145": "9.05", "S01-X146": "9.05/9.40", "S01-X147": "9.40/9.60",
    "S01-X148": "9.60", "S01-X149": "9.60/10.01", "S01-X14A": "9.60/10.20",
    "S01-X14B": "10.01/10.20", "S01-X14C": "10.20/10.40",
    "S01-X151": "10.40", "S01-X152": "10.40/10.60", "S01-X153": "10.40/10.60",
    "S01-X154": "10.60/11.00", "S01-X155": "11.00/11.20", "S01-X156": "11.20",
    "S01-X157": "11.20/11.40", "S01-X158": "11.40/11.60", "S01-X159": "11.60",
    "S01-X15A": "11.60/12.00",

    # CFI-71 (Pro Refresh)
    "S01-X256": "11.20", "S01-X257": "11.20/11.40", "S01-X258": "11.40/11.60",
    "S01-X259": "11.60", "S01-X25A": "11.60/12.00", "S01-X25B": "12.00/12.02",
    "S01-X25C": "12.02/12.20"
}

def get_supported_exploits(v):
    exploits = {
        "🧬 UMTX": "✅" if v <= 7.61 else "❌",
        "⏳ Lapse": "✅" if v <= 10.01 else "❌",
        "🌐 Webkit": "✅" if v <= 5.50 else "❌",
        "💿 BD-JB": "✅" if v <= 7.61 else "🔒 (Private)" if v <= 10.01 else "❌",
        "🎮 mast1c": "✅" if v <= 13.20 else "❌",
        "🐍 Lua": "✅" if v <= 13.20 else "❌",
        "☕ Y2JB": "✅" if v <= 13.20 else "❌",
        "📺 Netflix": "✅" if v <= 12.40 else "❌"
    }
    return {k: v for k, v in exploits.items() if v != "❌"}

def analyze_serial(raw_text):
    text = raw_text.upper().strip()
    match = re.search(r'([A-Z0-9]{2,3}-?[A-Z0-9]{3,5})', text)
    if not match: return None
    
    serial = match.group(1)
    search_key = serial
    origin = "Unknown"
    
    if serial.startswith("S01-"):
        char = serial[4]
        if char in ['F', 'E']: origin = "China 🇨🇳"
        elif char == 'K': origin = "Japan 🇯🇵"
        elif char == 'M': origin = "Malaysia 🇲🇾"
        elif char == 'G': origin = "Global/Other 🌐"
        if char.isalpha(): search_key = f"S01-X{serial[5:]}"

    found_v = None
    for k in sorted(PS5_DB.keys(), key=len, reverse=True):
        if search_key.startswith(k) or serial.startswith(k):
            found_v = PS5_DB[k]
            break
    
    if not found_v: return None

    v_list = str(found_v).split('/')
    try: 
        clean_v = re.findall(r'(\d+\.\d+)', v_list[0])[0]
        min_v = float(clean_v)
    except: min_v = 99.99

    if "X4" in search_key or "X3" in search_key: model = "Slim (CFI-20)"
    elif "X5" in search_key: model = "Slim (CFI-21)"
    elif "X1" in search_key: model = "Pro (CFI-70)"
    elif "X2" in search_key and len(search_key) > 5 and search_key[5] == '5': model = "Pro (CFI-71)"
    else: model = "Fat (CFI-10/11/12)"

    month_map = {'1':'January','2':'February','3':'March','4':'April','5':'May','6':'June','7':'July','8':'August','9':'September','A':'October','B':'November','C':'December'}
    try:
        month = month_map.get(search_key[-1], "Unknown")
        year = f"202{search_key[-2]}"
    except: month, year = "Unknown", "Unknown"

    supported_ex = get_supported_exploits(min_v)
    ex_text = "\n".join([f"│ {k} : {v}" for k, v in supported_ex.items()])

    return (
        f"<b>𝐏𝐒𝟓𝐀𝐉 𝐉𝐀𝐈𝐋𝐁𝐑𝐄𝐀𝐊 𝐂𝐇𝐄𝐂𝐊𝐄𝐑 🎮</b>\n\n"
        f"𝐒𝐞𝐫𝐢𝐚𝐥 📦:\n<code>{serial}</code>\n"
        f"𝐅𝐢𝐫𝐦𝐰𝐚𝐫𝐞 🔢:\n{found_v} {'✅' if min_v <= 11.00 else '❌'}\n"
        f"𝐌𝐨𝐝𝐞𝐥 🎮 :\n{model}\n"
        f"𝐌𝐚𝐝𝐞 𝐢𝐧 🏳️ :\n{origin}\n"
        f"𝐃𝐚𝐭𝐞 𝐨𝐟 𝐩𝐫𝐨𝐝𝐮𝐜𝐭𝐢𝐨𝐧 📅 :\n{month} {year}\n"
        f"𝐒𝐭𝐚𝐭𝐮𝐬 📊:\n{'SUPPORT ✅' if min_v <= 11.00 else 'UNSUPPORTED ❌'}\n\n"
        f"𝐄𝐱𝐩𝐥𝐨𝐢𝐭 𝐀𝐯𝐚𝐢𝐥𝐚𝐛𝐢𝐥𝐢𝐭𝐲 🔓:\n"
        f"╭─────────────╮\n"
        f"{ex_text}\n"
        f"╰─────────────╯\n\n"
        f"<b>BY: AZZAM</b>\n\n"
        f"Thank You <a href='https://x.com/qtr_703?s=21'>@qtr_703</a>"
    )

# ==========================================
# ⏰ وظيفة الحذف التلقائي
# ==========================================
async def delete_message_job(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    try:
        await context.bot.delete_message(chat_id=job.chat_id, message_id=job.data)
    except Exception as e:
        logging.warning(f"Could not delete message: {e}")

# ==========================================
# 🚀 أوامر البوت
# ==========================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome = (
        "<b>𝐏𝐒𝟓𝐀𝐙 𝐉𝐀𝐈𝐋𝐁𝐑𝐄𝐀𝐊 𝐂𝐇𝐄𝐂𝐊𝐄𝐑 🎮</b>\n\n"
        "📥 Send the Serial Number found on the bottom of the box.\n"
        "ارسل السيريال نمبر الموجود أسفل كرتون الجهاز.\n\n"
        "📝 Examples / أمثلة:\n"
        "<code>S01-X44A</code> | <code>S01-E44A</code>\n"
        "<code>S01-F148 (Pro)</code> | <code>S01-M44A</code>\n"
        "<code>S01-G44A (Fat)</code>\n\n"
        "Thank You @qtr_703"
    )
    await update.message.reply_text(welcome, parse_mode=ParseMode.HTML)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response = analyze_serial(update.message.text)
    
    # تحديد النص المراد إرساله
    if response:
        text_to_send = response
    else:
        text_to_send = (
            "<b>𝐏𝐒𝟓𝐀𝐙 𝐉𝐀𝐈𝐋𝐁𝐑𝐄𝐀𝐊 𝐂𝐇𝐄𝐂𝐊𝐄𝐑 🎮</b>\n\n"
            "❌ <b>الرقم التسلسلي غير صحيح</b>\n"
            "يرجى التأكد من كتابة الرقم الموجود أسفل كرتون الجهاز بشكل صحيح.\n\n"
            "❌ <b>Serial number incorrect</b>\n"
            "Please ensure you enter the number from the bottom of the box correctly.\n\n"
            "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
            "<b>BY: AZZAM</b>\n"
            "Thank You @qtr_703"
        )

    # إرسال الرسالة
    sent_msg = await update.message.reply_text(
        text_to_send, 
        parse_mode=ParseMode.HTML, 
        disable_web_page_preview=True
    )

    # إذا كانت الرسالة في "قروب" أو "سوبر قروب"، جدول الحذف بعد ساعة (3600 ثانية)
    if update.effective_chat.type in ["group", "supergroup"]:
        context.job_queue.run_once(
            delete_message_job, 
            when=3600, 
            data=sent_msg.message_id, 
            chat_id=update.effective_chat.id
        )

if __name__ == '__main__':
    keep_alive()
    # بناء التطبيق مع تفعيل JobQueue
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    app.run_polling()
