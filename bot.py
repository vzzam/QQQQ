import logging
import os
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from keep_alive import keep_alive

# ==========================================
# 🔴 التوكين الخاص بك
# ==========================================
TOKEN = "7976756950:AAGs4odFu9fABU0nYNUnuCUJyB4QIdINgS4"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ==========================================
# 📂 قاعدة البيانات المحدثة (2020 - 2026)
# ==========================================
PS5_DB = {
    # Japanese & Early Fat Models
    "S01-1355": "1.02", "S01-0272": "2.00", "S01-0376": "2.30", "S01-1517": "3.20",
    "F1070": "1.00", "F1080": "1.02", "F1090": "1.02", "F10B0": "1.02", "F101B": "2.00", "F1130": "2.50", "F225": "3.20",
    "AJ135": "1.00", "AJ148": "2.00", "AJ159": "2.30", "AJ167": "2.50", "AJ173": "3.00",
    "AK396": "3.20", "AK429": "4.03", "AK367": "4.50", "AK436": "5.02", "AK914": "5.10",
    # Fat CFI-11 (2021-2022)
    "S01-X214": "2.50/3.00/3.10", "S01-X217": "3.20/3.21", "S01-X21A": "3.20/4.03", "S01-X21C": "4.50",
    "S01-X221": "4.50", "S01-X223": "4.50/5.00", "S01-X226": "5.10", "S01-X228": "5.50", "S01-X22A": "6.00/6.02",
    # Fat CFI-12 (2022-2023)
    "S01-X325": "5.10", "S01-X328": "5.50", "S01-X32B": "6.02",
    "S01-X331": "6.02/6.50", "S01-X334": "7.00/7.20", "S01-X337": "7.40/7.60", "S01-X339": "7.61/8.00",
    # Slim CFI-20 (2023-2025)
    "S01-X434": "7.00", "S01-X435": "7.00/7.20", "S01-X439": "7.61/8.00", "S01-X441": "8.40/8.60",
    "S01-X445": "9.00/9.20", "S01-X449": "9.60/10.01", "S01-X44A": "9.60/10.20", "S01-X451": "10.40",
    "S01-X457": "11.20/11.40", "S01-X45A": "11.60/12.00",
    # Slim CFI-21 (2025-2026)
    "S01-X556": "11.20", "S01-X558": "11.40/11.60", "S01-X55B": "12.02/12.20",
    # Pro Models (CFI-70/71)
    "S01-X145": "9.05", "S01-X149": "9.60/10.01", "S01-X151": "10.40", "S01-X157": "11.20/11.40",
    "S01-X256": "11.20", "S01-X25C": "12.02"
}

# ==========================================
# 🛠️ Helper Functions
# ==========================================

def get_exploit_checklist(v):
    ex = {"Webkit": "❌", "BD-JB": "❌", "mast1c0re": "❌", "Lua": "❌", "Y2JB": "❌", "Netflix": "❌"}
    if 1.00 <= v <= 1.14: ex.update({"Webkit": "✅"})
    elif 2.00 <= v <= 2.70: ex.update({"Webkit": "✅", "mast1c0re": "✅", "Lua": "✅"})
    elif 3.00 <= v <= 3.20: ex.update({"Webkit": "✅", "BD-JB": "✅", "mast1c0re": "✅", "Lua": "✅"})
    elif 4.00 <= v <= 5.50: ex.update({"Webkit": "✅", "BD-JB": "✅", "mast1c0re": "✅", "Lua": "✅", "Y2JB": "✅", "Netflix": "✅"})
    elif 6.00 <= v <= 7.61: ex.update({"BD-JB": "✅", "mast1c0re": "✅", "Lua": "✅", "Y2JB": "✅", "Netflix": "✅"})
    elif 8.00 <= v <= 12.00: ex.update({"BD-JB": "🔒 (Private)", "mast1c0re": "❗️", "Lua": "✅", "Y2JB": "✅", "Netflix": "✅"})
    elif v >= 12.02: ex.update({"mast1c0re": "❗️", "Lua": "✅", "Y2JB": "✅", "Netflix": "✅"})
    return ex

def get_console_model_and_date(serial_normalized):
    if "S01-X" not in serial_normalized: return "Fat (CFI-10)", "Unknown"
    try:
        suffix = serial_normalized.split("S01-X")[1]
        digit_model, digit_year, digit_month = suffix[0], suffix[1], suffix[2]
        models = {'1': "Pro (CFI-70)", '2': "Fat (CFI-11)" if digit_year in ['1','2'] else "Pro (CFI-71)", 
                  '3': "Fat (CFI-12)", '4': "Slim (CFI-20)", '5': "Slim (CFI-21)"}
        year_map = {'0':'2020', '1':'2021', '2':'2022', '3':'2023', '4':'2024', '5':'2025', '6':'2026'}
        month_map = {'1':'January', '2':'February', '3':'March', '4':'April', '5':'May', '6':'June', 
                     '7':'July', '8':'August', '9':'September', 'A':'October', 'B':'November', 'C':'December'}
        return models.get(digit_model, "Fat (CFI-10)"), f"{month_map.get(digit_month, 'Unknown')} {year_map.get(digit_year, 'Unknown')}"
    except: return "Fat (CFI-10)", "Unknown"

def get_factory_location(user_serial):
    if "-" in user_serial:
        code = user_serial.split("-")[1][0]
        regs = {'F': "China 🇨🇳", 'E': "Saudi Arabia 🇸🇦", 'G': "China 🇨🇳", 'M': "Malaysia 🇲🇾", 'K': "Japan 🇯🇵"}
        return regs.get(code, "China 🇨🇳")
    return None

def format_version_status(version_str):
    versions = str(version_str).split('/')
    formatted_list, min_v, has_supported, has_unsupported = [], 99.99, False, False
    for v_raw in versions:
        v_clean = v_raw.strip().split(' ')[0]
        try:
            val = float(v_clean)
            if val < min_v: min_v = val
            if val <= 10.01: (formatted_list.append(f"{v_clean} ✅"), globals().update(has_supported=True))
            else: (formatted_list.append(f"{v_clean} ❌"), globals().update(has_unsupported=True))
        except: formatted_list.append(f"{v_raw} ❓")
    state = "SUPPORT ✅" if has_supported and not has_unsupported else "UNSUPPORTED ❌" if has_unsupported and not has_supported else "CHANCE ⚠️"
    return " / ".join(formatted_list), min_v, state

def process_serial_check(user_text):
    user_text = user_text.upper().strip()
    search_key = f"S01-X{user_text.split('-')[1][1:]}" if user_text.startswith("S01-") and len(user_text)>=8 else user_text
    found_v = next((PS5_DB[k] for k in sorted(PS5_DB.keys(), key=len, reverse=True) if search_key.startswith(k)), None)
    if not found_v: return None

    f_ver, min_v, state = format_version_status(found_v)
    ex = get_exploit_checklist(min_v)
    mod, date = get_console_model_and_date(search_key)
    loc = get_factory_location(user_text)

    res = f"𝐏𝐒𝟓𝐀𝐙 𝐉𝐀𝐈𝐋𝐁𝐑𝐄𝐀𝐊 𝐂𝐇𝐄𝐂𝐊𝐄𝐑 🎮\n\n"
    res += f"𝐒𝐞𝐫𝐢𝐚𝐥 📦:\n{user_text}\n"
    res += f"𝐅𝐢𝐫𝐦𝐰𝐚𝐫𝐞 🔢:\n{f_ver}\n"
    res += f"𝐌𝐨𝐝𝐞𝐥 🎮 :\n{mod}\n"
    if loc: res += f"𝐌𝐚𝐝𝐞 𝐢𝐧 🏳️ :\n{loc}\n"
    res += f"𝐃𝐚𝐭𝐞 𝐨𝐟 𝐩𝐫𝐨𝐝𝐮𝐜𝐭𝐢𝐨𝐧 📅 :\n{date}\n"
    res += f"𝐒𝐭𝐚𝐭𝐮𝐬 📊:\n{state}\n\n"

    if "UNSUPPORTED" not in state:
        res += "𝐄𝐱𝐩𝐥𝐨𝐢𝐭 𝐀𝐯𝐚𝐢𝐥𝐚𝐛𝐢𝐥𝐢𝐭𝐲 🔓:\n╭─────────────╮\n"
        res += f"│ 🌐 Webkit : {ex['Webkit']}\n│ 💿 BD-JB  : {ex['BD-JB']}\n│ 🎮 mast1c : {ex['mast1c0re']}\n│ 🐍 Lua : {ex['Lua']}\n│ ☕ Y2JB   : {ex['Y2JB']}\n│ 📺 Netflix: {ex['Netflix']}\n╰─────────────╯\n\n"
    
    res += "By:<a href='https://x.com/vaz3m?s=21'>@vAz3m</a>\nThank You <a href='https://x.com/qtr_703?s=21'>@qtr_703</a>"
    return res

# ==========================================
# 🤖 Bot Handlers
# ==========================================

async def delete_msg_job(context: ContextTypes.DEFAULT_TYPE):
    try: await context.bot.delete_message(chat_id=context.job.chat_id, message_id=context.job.data)
    except: pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    is_group = update.message.chat.type in ['group', 'supergroup']
    if is_group and '/start' in update.message.text: return 

    welcome_msg = (
        "𝐏𝐒𝟓𝐀𝐙 𝐉𝐀𝐈𝐋𝐁𝐑𝐄𝐀𝐊 𝐂𝐇𝐄𝐂𝐊𝐄𝐑 🎮\n\n"
        "📥 <b>Send the Serial Number found on the bottom of the box.</b>\n"
        "<b>ارسل السيريال نمبر الموجود أسفل كرتون الجهاز.</b>\n\n"
        "📝 <b>Examples / أمثلة:</b>\n"
        "<code>S01-X44A</code> | <code>S01-E44A</code>\n"
        "<code>S01-F148</code> (Pro) | <code>S01-M44A</code>\n"
        "<code>S01-G44A</code> (Fat)\n\n"
        "By:<a href='https://x.com/vaz3m?s=21'>@vAz3m</a>\n"
        "Thank You <a href='https://x.com/qtr_703?s=21'>@qtr_703</a>"
    )
    sent_msg = await update.message.reply_text(welcome_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    if is_group: context.job_queue.run_once(delete_msg_job, 1800, chat_id=sent_msg.chat_id, data=sent_msg.message_id)

async def analyze_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw_text = update.message.text.upper().strip()
    is_group = update.message.chat.type in ['group', 'supergroup']
    
    # التعامل مع المجموعات (تنظيف المعرف @)
    clean_text = raw_text.split('@')[0].strip() if is_group else raw_text
    
    result_text = process_serial_check(clean_text)
    if result_text:
        sent_msg = await update.message.reply_text(result_text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
        if is_group: context.job_queue.run_once(delete_msg_job, 1800, chat_id=sent_msg.chat_id, data=sent_msg.message_id)
    elif not is_group:
        await update.message.reply_text("⚠️ Serial not found")

if __name__ == '__main__':
    keep_alive()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler(['start', 'check'], start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), analyze_message))
    app.run_polling()
