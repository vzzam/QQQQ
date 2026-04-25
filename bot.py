import logging
import os
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from keep_alive import keep_alive

# ==========================================
# 🔴 إعدادات التوكن الآمنة
# ==========================================
# قم بوضع التوكن في متغيرات البيئة في منصة الاستضافة باسم BOT_TOKEN
TOKEN = os.environ.get("BOT_TOKEN")

if not TOKEN:
    # للتشغيل المحلي فقط، ضع التوكن هنا (للتجربة وليس للإنتاج)
    # تذكر تغييره من BotFather لأنك نشرته!
    TOKEN = "PUT_YOUR_NEW_TOKEN_HERE" 

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ==========================================
# 📂 قاعدة البيانات (تم اختصارها هنا لتوفير المساحة، استخدم قاعدتك الكاملة)
# ==========================================
PS5_DB = {
    "S01-1355": "1.02", "S01-0272": "2.00", 
    # ... أضف باقي قاعدتك هنا ...
    "S01-X25C": "12.02"
}

# ==========================================
# 🛠️ Helper Functions
# ==========================================

def get_exploit_checklist(v):
    ex = {"Webkit": "❌", "BD-JB": "❌", "mast1c0re": "❌", "Lua": "❌", "Y2JB": "❌", "Netflix": "❌"}
    if 1.00 <= v <= 1.14:
        ex.update({"Webkit": "✅", "BD-JB": "❌", "mast1c0re": "❌", "Lua": "❌", "Y2JB": "❌", "Netflix": "❌"})
    elif 2.00 <= v <= 2.70:
        ex.update({"Webkit": "✅", "BD-JB": "❌", "mast1c0re": "✅", "Lua": "✅", "Y2JB": "❌", "Netflix": "❌"})
    elif 3.00 <= v <= 3.20:
        ex.update({"Webkit": "✅", "BD-JB": "✅", "mast1c0re": "✅", "Lua": "✅", "Y2JB": "❌", "Netflix": "❌"})
    elif 4.00 <= v <= 4.51:
        ex.update({"Webkit": "✅", "BD-JB": "✅", "mast1c0re": "✅", "Lua": "✅", "Y2JB": "✅", "Netflix": "✅"})
    elif 5.00 <= v <= 5.50:
        ex.update({"Webkit": "✅", "BD-JB": "✅", "mast1c0re": "✅", "Lua": "✅", "Y2JB": "✅", "Netflix": "✅"})
    elif 6.00 <= v <= 7.61:
        ex.update({"Webkit": "❌", "BD-JB": "✅", "mast1c0re": "✅", "Lua": "✅", "Y2JB": "✅", "Netflix": "✅"})
    elif 8.00 <= v <= 10.01:
        ex.update({"Webkit": "❌", "BD-JB": "🔒 (Private)", "mast1c0re": "❗️", "Lua": "✅", "Y2JB": "✅", "Netflix": "✅"})
    elif 10.20 <= v <= 12.00:
        ex.update({"Webkit": "❌", "BD-JB": "🔒 (Private)", "mast1c0re": "❗️", "Lua": "✅", "Y2JB": "✅", "Netflix": "✅"})
    elif v >= 12.02:
        ex.update({"Webkit": "❌", "BD-JB": "❌", "mast1c0re": "❗️", "Lua": "✅", "Y2JB": "✅", "Netflix": "✅"})
    return ex

def get_console_model_and_date(serial_normalized):
    if "S01-X" not in serial_normalized: return "Fat (CFI-10)", "Unknown"
    try:
        suffix = serial_normalized.split("S01-X")[1]
        if len(suffix) < 3: return "Unknown", "Unknown"
        digit_model, digit_year, digit_month = suffix[0], suffix[1], suffix[2]
        model_name = "Unknown"
        if digit_model == '2': model_name = "Fat (CFI-11)" if digit_year in ['1', '2'] else "Pro (CFI-71)"
        elif digit_model == '3': model_name = "Fat (CFI-12)"
        elif digit_model == '4': model_name = "Slim (CFI-20)"
        elif digit_model == '5': model_name = "Slim (CFI-21)"
        elif digit_model == '1': model_name = "Pro (CFI-70)"
        else: model_name = "Fat (CFI-10)"
        year_map = {'0':'2020', '1':'2021', '2':'2022', '3':'2023', '4':'2024', '5':'2025'}
        month_map = {'1':'January', '2':'February', '3':'March', '4':'April', '5':'May', '6':'June', '7':'July', '8':'August', '9':'September', 'A':'October', 'B':'November', 'C':'December'}
        prod_date = f"{month_map.get(digit_month, 'Unknown')} {year_map.get(digit_year, 'Unknown')}"
        return model_name, prod_date
    except: return "Fat (CFI-10)", "Unknown"

def get_factory_location(user_serial):
    if "-" in user_serial:
        try:
            code = user_serial.split("-")[1][0]
            if code in ['F', 'E', 'G']: return "China 🇨🇳"
            if code == 'M': return "Malaysia 🇲🇾"
            if code == 'K': return "Japan 🇯🇵"
        except: return None
    return None

def format_version_status(version_str):
    versions = str(version_str).split('/')
    formatted_list = []
    min_v = 99.99
    has_supported, has_unsupported = False, False
    for v_raw in versions:
        v_clean = v_raw.strip().split(' ')[0]
        try:
            val = float(v_clean)
            if val < min_v: min_v = val
            if val <= 10.01: 
                formatted_list.append(f"{v_clean} ✅") 
                has_supported = True
            else:
                formatted_list.append(f"{v_clean} ❌") 
                has_unsupported = True
        except: formatted_list.append(f"{v_raw} ❓")
    
    state = "SUPPORT ✅" if has_supported and not has_unsupported else "UNSUPPORTED ❌" if has_unsupported and not has_supported else "CHANCE ⚠️"
    return " / ".join(formatted_list), min_v, state

def process_serial_check(user_text):
    user_text = user_text.upper().strip()
    found_v = None
    search_key = f"S01-X{user_text.split('-')[1][1:]}" if user_text.startswith("S01-") and len(user_text)>=8 else user_text
    
    sorted_keys = sorted(PS5_DB.keys(), key=len, reverse=True)
    for k in sorted_keys:
        if search_key.startswith(k): found_v = PS5_DB[k]; break
    if not found_v:
        for k in sorted_keys:
            if user_text.startswith(k): found_v = PS5_DB[k]; break
            
    if not found_v:
        return None

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
    
    # تم تصحيح الخطأ البرمجي هنا
    res += "By: <a href='https://x.com/vaz3m?s=21'>@vAz3m</a>\n"
    res += "Thank You <a href='https://x.com/qtr_703?s=21'>@qtr_703</a>"
    
    return res

async def delete_msg_job(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    try:
        await context.bot.delete_message(chat_id=job.chat_id, message_id=job.data)
    except Exception as e:
        print(f"Failed to delete message: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_type = update.message.chat.type
    is_group = chat_type in ['group', 'supergroup']

    if is_group:
        if '/start' in update.message.text: return 
        
    if context.args:
        serial_to_check = " ".join(context.args)
        result_text = process_serial_check(serial_to_check)
        if result_text:
            sent_msg = await update.message.reply_text(result_text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
            if is_group:
                context.job_queue.run_once(delete_msg_job, 1800, chat_id=sent_msg.chat_id, data=sent_msg.message_id)
            return
        else:
             if not is_group:
                 await update.message.reply_text("⚠️ Serial not found")
             return

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
    
    if is_group:
        context.job_queue.run_once(delete_msg_job, 1800, chat_id=sent_msg.chat_id, data=sent_msg.message_id)

async def analyze_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw_text = update.message.text.upper().strip()
    chat_type = update.message.chat.type
    is_group = chat_type in ['group', 'supergroup']
    
    bot_username = context.bot.username.upper() if context.bot.username else ""

    if is_group:
        clean_text = raw_text.replace(f"@{bot_username}", "").strip()
        potential_serial = False
        if clean_text.startswith(("S01-", "AJ", "F", "AK")) and len(clean_text) > 4:
            potential_serial = True
        
        if potential_serial:
            result_text = process_serial_check(clean_text)
            if result_text:
                sent_msg = await update.message.reply_text(result_text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
                context.job_queue.run_once(delete_msg_job, 1800, chat_id=sent_msg.chat_id, data=sent_msg.message_id)
            return

        if f"@{bot_username}" in raw_text:
            welcome_msg = (
                "𝐏𝐒𝟓𝐀𝐙 𝐉𝐀𝐈𝐋𝐁𝐑𝐄𝐀𝐊 𝐂𝐇𝐄𝐂𝐊𝐄𝐑 🎮\n\n"
                "📥 <b>Send the Serial Number found on the bottom of the box.</b>\n"
                "<b>ارسل السيريال نمبر الموجود أسفل كرتون الجهاز.</b>\n\n"
                "📝 <b>Examples / أمثلة:</b>\n"
                "<code>S01-X44A</code> | <code>S01-E44A</code>\n"
                "<code>S01-F148</code> (Pro) | <code>S01-M44A</code>\n"
                "<code>S01-G44A</code> (Fat)\n\n"
                "Thank You <a href='https://x.com/qtr_703?s=21'>@qtr_703</a>"
            )
            sent_msg = await update.message.reply_text(welcome_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
            context.job_queue.run_once(delete_msg_job, 1800, chat_id=sent_msg.chat_id, data=sent_msg.message_id)
            return
    else:
        user_text = raw_text
        result_text = process_serial_check(user_text)
        
        if result_text:
            await update.message.reply_text(result_text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
        else:
            await update.message.reply_text("⚠️ Serial not found")

if __name__ == '__main__':
    keep_alive()
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler(['start', 'check'], start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), analyze_message))
    
    app.run_polling()
    "S01-X227": "5.10/5.50", "S01-X228": "5.50", "S01-X229": "5.50/6.00",
    "S01-X22A": "6.00/6.02", "S01-X22B": "6.02", "S01-X22C": "6.02",
    "S01-X324": "NO RECORD", "S01-X325": "5.10", "S01-X326": "5.10",
    "S01-X327": "5.10/5.50", "S01-X328": "5.50", "S01-X329": "5.50/6.00",
    "S01-X32A": "5.50/6.00", "S01-X32B": "6.02", "S01-X32C": "6.02",
    "S01-X331": "6.02/6.50", "S01-X332": "6.02/6.50", "S01-X333": "6.50/7.00",
    "S01-X334": "7.00/7.20", "S01-X335": "7.00/7.20", "S01-X336": "7.20/7.40",
    "S01-X337": "7.40/7.60", "S01-X338": "7.60/7.61", 
    "S01-X339": "7.61/8.00", "S01-X33A": "8.00/8.20", "S01-X33B": "8.20/8.20.02", "S01-X33C": "8.20.02/8.40",
    "S01-X434": "7.00", "S01-X435": "7.00/7.20", "S01-X436": "7.20/7.40",
    "S01-X437": "7.40/7.60", "S01-X438": "7.60/7.61", "S01-X439": "7.61/8.00",
    "S01-X43A": "7.61/8.00/8.20", "S01-X43B": "8.20/8.20.02", "S01-X43C": "8.20.02/8.40",
    "S01-X441": "8.40/8.60", "S01-X442": "8.60", "S01-X443": "8.60/9.00",
    "S01-X444": "9.00", "S01-X445": "9.00/9.20", "S01-X446": "9.20",
    "S01-X447": "9.40/9.60", "S01-X448": "9.40/9.60",
    "S01-X449": "9.60/10.00/10.01", "S01-X44A": "9.60/10.01/10.20",
    "S01-X44B": "10.20", "S01-X44C": "10.20/10.40",
    "S01-X451": "10.40", "S01-X452": "10.40/10.60", "S01-X453": "10.40/10.60",
    "S01-X454": "10.60/11.00", "S01-X455": "11.00/11.20", "S01-X456": "11.20",
    "S01-X457": "11.20/11.40", "S01-X458": "11.40/11.60", "S01-X459": "11.60",
    "S01-X45A": "11.60/12.00",
    "S01-X556": "11.20", "S01-X557": "11.20/11.40", "S01-X558": "11.40/11.60",
    "S01-X559": "11.60", "S01-X55A": "11.60/12.00", "S01-X55B": "12.00/12.02",
    "S01-X55C": "12.02",
    "S01-X145": "9.05", "S01-X146": "9.05/9.40", "S01-X147": "9.40/9.60",
    "S01-X148": "9.60", "S01-X149": "9.60/10.00/10.01",
    "S01-X14A": "9.60/10.00/10.01/10.20", "S01-X14B": "10.01/10.20", "S01-X14C": "10.20/10.40",
    "S01-X151": "10.40", "S01-X152": "10.40/10.60", "S01-X153": "10.40/10.60",
    "S01-X154": "10.60/11.00", "S01-X155": "11.00/11.20", "S01-X156": "11.20",
    "S01-X157": "11.20/11.40", "S01-X158": "11.40/11.60", "S01-X159": "11.60",
    "S01-X15A": "11.60/12.00",
    "S01-X256": "11.20", "S01-X257": "11.20/11.40", "S01-X258": "11.40/11.60",
    "S01-X259": "11.60", "S01-X25A": "11.60/12.00", "S01-X25B": "12.00/12.02",
    "S01-X25C": "12.02"
}

# ==========================================
# 🛠️ Helper Functions
# ==========================================

def get_exploit_checklist(v):
    ex = {"Webkit": "❌", "BD-JB": "❌", "mast1c0re": "❌", "Lua": "❌", "Y2JB": "❌", "Netflix": "❌"}
    if 1.00 <= v <= 1.14:
        ex.update({"Webkit": "✅", "BD-JB": "❌", "mast1c0re": "❌", "Lua": "❌", "Y2JB": "❌", "Netflix": "❌"})
    elif 2.00 <= v <= 2.70:
        ex.update({"Webkit": "✅", "BD-JB": "❌", "mast1c0re": "✅", "Lua": "✅", "Y2JB": "❌", "Netflix": "❌"})
    elif 3.00 <= v <= 3.20:
        ex.update({"Webkit": "✅", "BD-JB": "✅", "mast1c0re": "✅", "Lua": "✅", "Y2JB": "❌", "Netflix": "❌"})
    elif 4.00 <= v <= 4.51:
        ex.update({"Webkit": "✅", "BD-JB": "✅", "mast1c0re": "✅", "Lua": "✅", "Y2JB": "✅", "Netflix": "✅"})
    elif 5.00 <= v <= 5.50:
        ex.update({"Webkit": "✅", "BD-JB": "✅", "mast1c0re": "✅", "Lua": "✅", "Y2JB": "✅", "Netflix": "✅"})
    elif 6.00 <= v <= 7.61:
        ex.update({"Webkit": "❌", "BD-JB": "✅", "mast1c0re": "✅", "Lua": "✅", "Y2JB": "✅", "Netflix": "✅"})
    elif 8.00 <= v <= 10.01:
        ex.update({"Webkit": "❌", "BD-JB": "🔒 (Private)", "mast1c0re": "❗️", "Lua": "✅", "Y2JB": "✅", "Netflix": "✅"})
    elif 10.20 <= v <= 12.00:
        ex.update({"Webkit": "❌", "BD-JB": "🔒 (Private)", "mast1c0re": "❗️", "Lua": "✅", "Y2JB": "✅", "Netflix": "✅"})
    elif v >= 12.02:
        ex.update({"Webkit": "❌", "BD-JB": "❌", "mast1c0re": "❗️", "Lua": "✅", "Y2JB": "✅", "Netflix": "✅"})
    return ex

def get_console_model_and_date(serial_normalized):
    if "S01-X" not in serial_normalized: return "Fat (CFI-10)", "Unknown"
    try:
        suffix = serial_normalized.split("S01-X")[1]
        if len(suffix) < 3: return "Unknown", "Unknown"
        digit_model, digit_year, digit_month = suffix[0], suffix[1], suffix[2]
        model_name = "Unknown"
        if digit_model == '2': model_name = "Fat (CFI-11)" if digit_year in ['1', '2'] else "Pro (CFI-71)"
        elif digit_model == '3': model_name = "Fat (CFI-12)"
        elif digit_model == '4': model_name = "Slim (CFI-20)"
        elif digit_model == '5': model_name = "Slim (CFI-21)"
        elif digit_model == '1': model_name = "Pro (CFI-70)"
        else: model_name = "Fat (CFI-10)"
        year_map = {'0':'2020', '1':'2021', '2':'2022', '3':'2023', '4':'2024', '5':'2025'}
        month_map = {'1':'January', '2':'February', '3':'March', '4':'April', '5':'May', '6':'June', '7':'July', '8':'August', '9':'September', 'A':'October', 'B':'November', 'C':'December'}
        prod_date = f"{month_map.get(digit_month, 'Unknown')} {year_map.get(digit_year, 'Unknown')}"
        return model_name, prod_date
    except: return "Fat (CFI-10)", "Unknown"

def get_factory_location(user_serial):
    if "-" in user_serial:
        try:
            code = user_serial.split("-")[1][0]
            if code in ['F', 'E', 'G']: return "China 🇨🇳"
            if code == 'M': return "Malaysia 🇲🇾"
            if code == 'K': return "Japan 🇯🇵"
        except: return None
    return None

def format_version_status(version_str):
    versions = str(version_str).split('/')
    formatted_list = []
    min_v = 99.99
    has_supported, has_unsupported = False, False
    for v_raw in versions:
        v_clean = v_raw.strip().split(' ')[0]
        try:
            val = float(v_clean)
            if val < min_v: min_v = val
            if val <= 10.01: 
                formatted_list.append(f"{v_clean} ✅") 
                has_supported = True
            else:
                formatted_list.append(f"{v_clean} ❌") 
                has_unsupported = True
        except: formatted_list.append(f"{v_raw} ❓")
    
    state = "SUPPORT ✅" if has_supported and not has_unsupported else "UNSUPPORTED ❌" if has_unsupported and not has_supported else "CHANCE ⚠️"
    return " / ".join(formatted_list), min_v, state

# دالة الفحص (الرد الكامل)
def process_serial_check(user_text):
    user_text = user_text.upper().strip()
    found_v = None
    search_key = f"S01-X{user_text.split('-')[1][1:]}" if user_text.startswith("S01-") and len(user_text)>=8 else user_text
    
    sorted_keys = sorted(PS5_DB.keys(), key=len, reverse=True)
    for k in sorted_keys:
        if search_key.startswith(k): found_v = PS5_DB[k]; break
    if not found_v:
        for k in sorted_keys:
            if user_text.startswith(k): found_v = PS5_DB[k]; break
            
    if not found_v:
        return None

    f_ver, min_v, state = format_version_status(found_v)
    ex = get_exploit_checklist(min_v)
    mod, date = get_console_model_and_date(search_key)
    loc = get_factory_location(user_text)

    # الرد الكامل (دائماً)
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
    
    </a>\nThank You <a href='https://x.com/qtr_703?s=21'>@qtr_703</a>"
    return res

# 👇👇 دالة الحذف التلقائي 👇👇
async def delete_msg_job(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    try:
        await context.bot.delete_message(chat_id=job.chat_id, message_id=job.data)
    except Exception as e:
        print(f"Failed to delete message: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_type = update.message.chat.type
    is_group = chat_type in ['group', 'supergroup']

    if is_group:
        if '/start' in update.message.text: return 
        
    if context.args:
        serial_to_check = " ".join(context.args)
        result_text = process_serial_check(serial_to_check)
        if result_text:
            sent_msg = await update.message.reply_text(result_text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
            # ⏳ جدولة الحذف بعد 30 دقيقة (1800 ثانية) إذا كان في مجموعة
            if is_group:
                context.job_queue.run_once(delete_msg_job, 1800, chat_id=sent_msg.chat_id, data=sent_msg.message_id)
            return
        else:
             if not is_group:
                 await update.message.reply_text("⚠️ Serial not found")
             return

    # رسالة الترحيب الأصلية
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
    
    # ⏳ جدولة الحذف بعد 30 دقيقة (1800 ثانية) إذا كان في مجموعة
    if is_group:
        context.job_queue.run_once(delete_msg_job, 1800, chat_id=sent_msg.chat_id, data=sent_msg.message_id)

async def analyze_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw_text = update.message.text.upper().strip()
    chat_type = update.message.chat.type
    is_group = chat_type in ['group', 'supergroup']
    
    bot_username = context.bot.username.upper() if context.bot.username else ""

    if is_group:
        clean_text = raw_text.replace(f"@{bot_username}", "").strip()
        potential_serial = False
        if clean_text.startswith(("S01-", "AJ", "F", "AK")) and len(clean_text) > 4:
            potential_serial = True
        
        if potential_serial:
            result_text = process_serial_check(clean_text)
            if result_text:
                sent_msg = await update.message.reply_text(result_text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
                # ⏳ جدولة الحذف بعد 30 دقيقة (1800 ثانية)
                context.job_queue.run_once(delete_msg_job, 1800, chat_id=sent_msg.chat_id, data=sent_msg.message_id)
            return

        if f"@{bot_username}" in raw_text:
            welcome_msg = (
                "𝐏𝐒𝟓𝐀𝐙 𝐉𝐀𝐈𝐋𝐁𝐑𝐄𝐀𝐊 𝐂𝐇𝐄𝐂𝐊𝐄𝐑 🎮\n\n"
                "📥 <b>Send the Serial Number found on the bottom of the box.</b>\n"
                "<b>ارسل السيريال نمبر الموجود أسفل كرتون الجهاز.</b>\n\n"
                "📝 <b>Examples / أمثلة:</b>\n"
                "<code>S01-X44A</code> | <code>S01-E44A</code>\n"
                "<code>S01-F148</code> (Pro) | <code>S01-M44A</code>\n"
                "<code>S01-G44A</code> (Fat)\n\n"
                "Thank You <a href='https://x.com/qtr_703?s=21'>@qtr_703</a>"
            )
            sent_msg = await update.message.reply_text(welcome_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
            # ⏳ جدولة الحذف بعد 30 دقيقة (1800 ثانية)
            context.job_queue.run_once(delete_msg_job, 1800, chat_id=sent_msg.chat_id, data=sent_msg.message_id)
            return
    else:
        # خاص
        user_text = raw_text
        result_text = process_serial_check(user_text)
        
        if result_text:
            await update.message.reply_text(result_text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
        else:
            await update.message.reply_text("⚠️ Serial not found")

if __name__ == '__main__':
    keep_alive()
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler(['start', 'check'], start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), analyze_message))
    
    app.run_polling()
