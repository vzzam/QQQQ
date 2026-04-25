import logging
import os
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from keep_alive import keep_alive

# ==========================================
# 🔴 التوكين الجديد الخاص بك
# ==========================================
TOKEN = "7976756950:AAGs4odFu9fABU0nYNUnuCUJyB4QIdINgS4"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ==========================================
# 📂 قاعدة البيانات المحدثة (أبريل 2026)
# ==========================================
PS5_DB = {
    # الموديلات القديمة (Fat)
    "S01-1355": "1.02", "S01-0272": "2.00", "S01-0376": "2.30", "S01-1517": "3.20",
    "F1070": "1.00", "F1080": "1.02", "F1090": "1.02", "F10B0": "1.02", "F101B": "2.00", "F1130": "2.50", "F225": "3.20",
    "AJ135": "1.00", "AJ136": "1.00", "AJ137": "1.02", "AJ141": "1.02", "AJ144": "1.02", "AJ145": "1.02", "AJ146": "1.02",
    "AJ148": "2.00", "AJ149": "2.00", "AJ150": "2.00", "AJ151": "2.00", "AJ153": "2.00", "AJ154": "2.00", "AJ157": "2.00",
    "AJ158": "2.00", "AJ159": "2.30", "AJ161": "2.30", "AJ163": "2.30", "AJ164": "2.30", "AJ167": "2.50", "AJ168": "2.50",
    "AJ169": "2.70", "AJ171": "2.70", "AJ173": "3.00", "AK396": "3.20", "AK418": "3.21", "AK429": "4.03", "AK399": "4.03", 
    "AK367": "4.50", "AK368": "4.50", "AK436": "5.02", "AK914": "5.10",
    
    # سلسلة S01-X (Slim / Pro / Fat Newer)
    "S01-X214": "2.50/3.00/3.10", "S01-X215": "3.00/3.10", "S01-X216": "3.00/3.10/3.20",
    "S01-X217": "3.20/3.21", "S01-X218": "3.21", "S01-X219": "3.20/3.21/4.00",
    "S01-X21A": "3.20/4.00/4.02/4.03", "S01-X21B": "4.03/4.50", "S01-X21C": "4.50",
    "S01-X223": "4.50/4.51/5.00", "S01-X224": "5.00/5.02", "S01-X225": "5.02/5.10", 
    "S01-X227": "5.10/5.50", "S01-X229": "5.50/6.00", "S01-X22A": "6.00/6.02",
    "S01-X327": "5.10/5.50", "S01-X329": "5.50/6.00", "S01-X331": "6.02/6.50",
    "S01-X333": "6.50/7.00", "S01-X334": "7.00/7.20", "S01-X336": "7.20/7.40",
    "S01-X337": "7.40/7.60", "S01-X339": "7.61/8.00", "S01-X33A": "8.00/8.20",
    "S01-X435": "7.00/7.20", "S01-X437": "7.40/7.60", "S01-X439": "7.61/8.00",
    "S01-X441": "8.40/8.60", "S01-X443": "8.60/9.00", "S01-X445": "9.00/9.20",
    "S01-X447": "9.40/9.60", "S01-X449": "9.60/10.01", "S01-X44A": "9.60/10.20",
    "S01-X451": "10.40", "S01-X454": "10.60/11.00", "S01-X457": "11.20/11.40",
    "S01-X45A": "11.60/12.00", "S01-X45C": "12.02",
    
    # PS5 Pro (CFI-70/71) & Slim (CFI-21)
    "S01-X145": "9.05", "S01-X149": "9.60/10.01", "S01-X14A": "9.60/10.20",
    "S01-X151": "10.40", "S01-X154": "10.60/11.00", "S01-X157": "11.20/11.40",
    "S01-X15A": "11.60/12.00", "S01-X557": "11.20/11.40", "S01-X55A": "11.60/12.00",
    "S01-X55C": "12.02",
    
    # تحديثات 2026
    "S01-X461": "13.00/13.20", "S01-X161": "13.00/13.20", "S01-X561": "13.00/13.20"
}

# ==========================================
# 🛠️ دالة فحص الثغرات (Exploits)
# ==========================================
def get_exploit_checklist(v):
    ex = {"Webkit": "❌", "BD-JB": "❌", "mast1c0re": "❌", "Lua": "❌", "Y2JB": "❌", "Netflix": "❌"}
    if 1.00 <= v <= 1.14: ex.update({"Webkit": "✅"})
    elif 2.00 <= v <= 2.70: ex.update({"Webkit": "✅", "mast1c0re": "✅", "Lua": "✅"})
    elif 3.00 <= v <= 3.20: ex.update({"Webkit": "✅", "BD-JB": "✅", "mast1c0re": "✅", "Lua": "✅"})
    elif 4.00 <= v <= 4.51: ex.update({"Webkit": "✅", "BD-JB": "✅", "mast1c0re": "✅", "Lua": "✅", "Y2JB": "✅", "Netflix": "✅"})
    elif 5.00 <= v <= 5.50: ex.update({"Webkit": "✅", "BD-JB": "✅", "mast1c0re": "✅", "Lua": "✅", "Y2JB": "✅", "Netflix": "✅"})
    elif 6.00 <= v <= 7.61: ex.update({"BD-JB": "✅", "mast1c0re": "✅", "Lua": "✅", "Y2JB": "✅", "Netflix": "✅"})
    elif 8.00 <= v <= 10.01: ex.update({"BD-JB": "🔒 (Private)", "mast1c0re": "❗️", "Lua": "✅", "Y2JB": "✅", "Netflix": "✅"})
    elif v >= 10.20: ex.update({"mast1c0re": "❗️", "Lua": "✅", "Y2JB": "✅", "Netflix": "✅"})
    return ex

# ==========================================
# 🛠️ تحليل الموديل وتاريخ التصنيع
# ==========================================
def get_console_model_and_date(serial_normalized):
    if "S01-X" not in serial_normalized: return "Fat (CFI-10)", "Unknown"
    try:
        suffix = serial_normalized.split("S01-X")[1]
        digit_model, digit_year, digit_month = suffix[0], suffix[1], suffix[2]
        
        model_name = "Unknown"
        if digit_model == '1': model_name = "Pro (CFI-70)"
        elif digit_model == '2': model_name = "Fat (CFI-11)" if digit_year in ['1', '2'] else "Pro (CFI-71)"
        elif digit_model == '3': model_name = "Fat (CFI-12)"
        elif digit_model == '4': model_name = "Slim (CFI-20)"
        elif digit_model == '5': model_name = "Slim (CFI-21)"
        else: model_name = "Fat (CFI-10)"
        
        year_map = {'0':'2020', '1':'2021', '2':'2022', '3':'2023', '4':'2024', '5':'2025', '6':'2026'}
        month_map = {'1':'Jan', '2':'Feb', '3':'Mar', '4':'Apr', '5':'May', '6':'Jun', '7':'Jul', '8':'Aug', '9':'Sep', 'A':'Oct', 'B':'Nov', 'C':'Dec'}
        
        prod_date = f"{month_map.get(digit_month, 'Unknown')} {year_map.get(digit_year, 'Unknown')}"
        return model_name, prod_date
    except: return "Fat (CFI-10)", "Unknown"

# ==========================================
# 🛠️ معالجة الفحص
# ==========================================
def process_serial_check(user_text):
    user_text = user_text.upper().strip()
    found_v = None
    
    # تحويل حرف المنطقة إلى X للمطابقة
    if user_text.startswith("S01-") and len(user_text) >= 8:
        search_key = f"S01-X{user_text.split('-')[1][1:]}"
    else:
        search_key = user_text
    
    # البحث عن السيريال في قاعدة البيانات
    sorted_keys = sorted(PS5_DB.keys(), key=len, reverse=True)
    for k in sorted_keys:
        if search_key.startswith(k): 
            found_v = PS5_DB[k]
            break
    
    if not found_v: return None

    # تحليل الإصدارات
    versions = str(found_v).split('/')
    formatted_list = []
    min_v = 99.99
    has_ok, has_no = False, False
    
    for v_raw in versions:
        v_clean = v_raw.strip()
        try:
            val = float(v_clean)
            if val < min_v: min_v = val
            if val <= 10.01: 
                formatted_list.append(f"{v_clean} ✅")
                has_ok = True
            else: 
                formatted_list.append(f"{v_clean} ❌")
                has_no = True
        except: formatted_list.append(f"{v_raw} ❓")
    
    state = "SUPPORT ✅" if has_ok and not has_no else "UNSUPPORTED ❌" if has_no and not has_ok else "CHANCE ⚠️"
    ex = get_exploit_checklist(min_v)
    mod, date = get_console_model_and_date(search_key)

    # بناء الرسالة
    res = f"𝐏𝐒𝟓𝐀𝐙 𝐉𝐀𝐈𝐋𝐁𝐑𝐄𝐀𝐊 𝐂𝐇𝐄𝐂𝐊𝐄𝐑 🎮\n\n"
    res += f"𝐒𝐞𝐫𝐢𝐚𝐥 📦: <code>{user_text}</code>\n"
    res += f"𝐅𝐢𝐫𝐦𝐰𝐚𝐫𝐞 🔢: {', '.join(formatted_list)}\n"
    res += f"𝐌𝐨𝐝𝐞𝐥 🎮 : {mod}\n"
    res += f"𝐃𝐚𝐭𝐞 📅 : {date}\n"
    res += f"𝐒𝐭𝐚𝐭𝐮𝐬 📊: <b>{state}</b>\n\n"

    if state != "UNSUPPORTED ❌":
        res += "𝐄𝐱𝐩𝐥𝐨𝐢𝐭 𝐀𝐯𝐚𝐢𝐥𝐚𝐛𝐢𝐥𝐢𝐭𝐲 🔓:\n╭─────────────╮\n"
        res += f"│ 🌐 Webkit : {ex['Webkit']}\n│ 💿 BD-JB  : {ex['BD-JB']}\n│ 🎮 mast1c : {ex['mast1c0re']}\n│ 🐍 Lua : {ex['Lua']}\n│ ☕ Y2JB   : {ex['Y2JB']}\n│ 📺 Netflix: {ex['Netflix']}\n╰─────────────╯\n\n"
    
    res += "Thank You <a href='https://x.com/qtr_703?s=21'>@qtr_703</a>"
    return res

# ==========================================
# 🤖 التعامل مع تليجرام
# ==========================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_msg = (
        "𝐏𝐒𝟓𝐀𝐙 𝐉𝐀𝐈𝐋𝐁𝐑𝐄𝐀𝐊 𝐂𝐇𝐄𝐂𝐊𝐄𝐑 🎮\n\n"
        "📥 <b>ارسل السيريال نمبر الموجود أسفل كرتون الجهاز.</b>\n"
        "📝 <b>أمثلة:</b> <code>S01-X44A</code>, <code>S01-F148</code>\n\n"
        "Thank You <a href='https://x.com/qtr_703?s=21'>@qtr_703</a>"
    )
    await update.message.reply_text(welcome_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

async def analyze_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    res = process_serial_check(update.message.text)
    if res:
        await update.message.reply_text(res, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    elif update.message.chat.type == 'private':
        await update.message.reply_text("⚠️ Serial not found / السيريال غير موجود")

# ==========================================
# 🚀 تشغيل البوت
# ==========================================
if __name__ == '__main__':
    keep_alive() # تشغيل سيرفر Flask
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), analyze_message))
    
    print("Bot is alive and checking...")
    app.run_polling(drop_pending_updates=True)
