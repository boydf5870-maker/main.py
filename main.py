import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import time
import requests
import threading
import json
import os
import html
import re
import sys
from flask import Flask

# ===========================
# কনফিগারেশন
# ===========================
BOT_TOKEN = '8464862852:AAHX8twoWhcQGO_IiXNr8fEhKheOmJHbf2A'
TARGET_GROUP_ID = '-1002651075380'

DEV_LINK = "https://t.me/MUSTAFIZUR_OWNER2"
CHANNEL_LINK = "https://t.me/TECH_BD_BY_MUSTAFIZUR"

# গ্লোবাল ভেরিয়েবল
CURRENT_COOKIE = ""
CURRENT_UA = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36"

bot = telebot.TeleBot(BOT_TOKEN)
processed_ids = []

# ===========================
# RENDER KEEP-ALIVE SERVER
# ===========================
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Bot is Running on Render!"

def run_web_server():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# ===========================
# টেলিগ্রাম হ্যান্ডলার
# ===========================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🤖 **IVASMS CLEANER BOT (Render Edition)**\n\nকুকি দিন: `/cookie ...`", parse_mode='Markdown')

@bot.message_handler(commands=['cookie'])
def update_cookie(message):
    global CURRENT_COOKIE
    try:
        if len(message.text.split()) < 2:
            bot.reply_to(message, "❌ কুকি মিসিং!")
            return
        
        raw_cookie = message.text.split(" ", 1)[1].strip()
        if "Cookie:" in raw_cookie:
            raw_cookie = raw_cookie.replace("Cookie:", "").strip()
            
        CURRENT_COOKIE = raw_cookie
        bot.reply_to(message, "✅ **Cookie Updated!** Scanning Started...", parse_mode='Markdown')
        print(f"\n[Telegram] New Cookie Received.")
    except: pass

@bot.message_handler(commands=['ua'])
def update_ua(message):
    global CURRENT_UA
    if len(message.text.split()) > 1:
        CURRENT_UA = message.text.split(" ", 1)[1].strip()
        bot.reply_to(message, "✅ **User-Agent Updated!**")

# ===========================
# স্ক্যানার লুপ
# ===========================

def scanner_loop():
    print("✅ Scanner waiting for cookie...")
    base_url = "https://www.ivasms.com/portal/sms/test/sms"
    targets = ['WhatsApp', 'Telegram']
    
    while True:
        if not CURRENT_COOKIE:
            time.sleep(5)
            continue

        for target_name in targets:
            try:
                params = {
                    'draw': '1',
                    'columns[0][data]': 'range', 'columns[0][orderable]': 'false',
                    'columns[1][data]': 'termination.test_number', 'columns[1][searchable]': 'false', 'columns[1][orderable]': 'false',
                    'columns[2][data]': 'originator', 'columns[2][orderable]': 'false',
                    'columns[3][data]': 'messagedata', 'columns[3][orderable]': 'false',
                    'columns[4][data]': 'senttime', 'columns[4][searchable]': 'false', 'columns[4][orderable]': 'false',
                    'order[0][column]': '0', 'order[0][dir]': 'asc',
                    'start': '0', 'length': '25',
                    '_': int(time.time() * 1000)
                }

                if target_name == 'WhatsApp':
                    params['app'] = 'WhatsApp'
                    params['search[value]'] = ''
                elif target_name == 'Telegram':
                    params['search[value]'] = 'Telegram'

                headers = {
                    'User-Agent': CURRENT_UA,
                    'Cookie': CURRENT_COOKIE,
                    'Referer': 'https://www.ivasms.com/portal/live/test_sms',
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'application/json, text/javascript, */*; q=0.01'
                }

                response = requests.get(base_url, headers=headers, params=params, timeout=15)

                if response.status_code == 200:
                    try:
                        data = response.json()
                        sms_list = data.get('data', [])
                        
                        if sms_list:
                            for sms in sms_list:
                                raw_msg = sms.get('messagedata', '')
                                clean_msg = html.unescape(raw_msg)
                                if not clean_msg or len(clean_msg) < 2: continue

                                country = sms.get('range', 'Unknown')
                                termination_data = sms.get('termination')
                                if isinstance(termination_data, dict):
                                    raw_number_html = termination_data.get('test_number', 'Unknown')
                                else:
                                    raw_number_html = sms.get('test_number', 'Unknown')
                                
                                number = re.sub(r'<[^>]+>', '', str(raw_number_html)).strip()
                                unique_id = hash(f"{number}|{clean_msg}")

                                is_match = False
                                if target_name == 'WhatsApp':
                                    if "whatsapp" in clean_msg.lower() or "code" in clean_msg.lower(): is_match = True
                                elif target_name == 'Telegram':
                                    if re.search(r'\d+', clean_msg) or "code" in clean_msg.lower(): is_match = True

                                if is_match and unique_id not in processed_ids:
                                    print(f"\n🔥 MATCH [{target_name}]: {number}")
                                    final_text = (
                                        f"🔥 **IVSMS ACTIVE RANGE ({target_name}) 🟢**\n"
                                        f"━━━━━━━━━━━━━━━━\n"
                                        f"🌍 **Country:** `{country}`\n"
                                        f"📱 **Number:** `{number}`\n"
                                        f"📩 **Message:**\n`{clean_msg}`\n"
                                        f"━━━━━━━━━━━━━━━━━━━"
                                    )
                                    markup = InlineKeyboardMarkup()
                                    markup.add(InlineKeyboardButton("👨‍💻 Developer", url=DEV_LINK),
                                               InlineKeyboardButton("📢 Main Channel", url=CHANNEL_LINK))
                                    try:
                                        bot.send_message(TARGET_GROUP_ID, final_text, parse_mode='Markdown', reply_markup=markup)
                                    except: pass
                                    
                                    processed_ids.append(unique_id)
                                    if len(processed_ids) > 500: processed_ids.pop(0)
                    except json.JSONDecodeError:
                        time.sleep(5)
                elif response.status_code == 403:
                    print("\n❌ Cookie Expired.")
                    time.sleep(20)
            except Exception as e:
                time.sleep(2)
            time.sleep(1)
        time.sleep(2)

if __name__ == "__main__":
    web_thread = threading.Thread(target=run_web_server)
    web_thread.daemon = True
    web_thread.start()
    
    print("========================================")
    print("   IVASMS SCANNER (RENDER READY)")
    print("========================================")
    
    scan_thread = threading.Thread(target=scanner_loop)
    scan_thread.daemon = True
    scan_thread.start()
    
    bot.infinity_polling()