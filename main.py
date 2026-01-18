import telebot
from telebot import types
from curl_cffi import requests
import os
import time
import re
import random
import string
from flask import Flask
from threading import Thread

# ========== CẤU HÌNH HỆ THỐNG ==========
# LƯU Ý: Bạn nên vào BotFather lấy Token MỚI vì token cũ đã bị lộ
BOT_TOKEN = "6556057870:AAFPx3CJpAcGt-MfKRoAo00SlAEQ26XSS-s"
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
app = Flask(__name__)

user_data = {}

def get_user(uid):
    if uid not in user_data:
        user_data[uid] = {"fb_cookie": "", "groups": [], "proxies": [], "is_running": False}
    return user_data[uid]

@app.route('/')
def home():
    return "Ultra Stealth System v10.0 is Active!"

# ========== CÔNG CỤ BYPASS NĂNG CAO ==========

def spintax_process(text):
    while '{' in text:
        start = text.rfind('{')
        end = text.find('}', start)
        if end == -1: break
        content = text[start + 1:end]
        chosen = random.choice(content.split('|'))
        text = text[:start] + chosen + text[end + 1:]
    return text

def get_random_ua():
    versions = ["120", "121", "122", "123", "130", "132"]
    ua_list = [
        f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.choice(versions)}.0.0.0 Safari/537.36",
        f"Mozilla/5.0 (iPhone; CPU iPhone OS {random.randint(15, 17)}_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{random.randint(15, 17)}.0 Mobile/15E148 Safari/604.1"
    ]
    return random.choice(ua_list)

# ========== CORE ĐĂNG BÀI ==========

def post_to_group_v10(cookie, group_id, content, proxy):
    session = requests.Session(impersonate="chrome110") 
    if proxy:
        session.proxies = {'http': proxy, 'https': proxy}

    ua = get_random_ua()
    headers = {
        'authority': 'mbasic.facebook.com',
        'cookie': cookie,
        'user-agent': ua,
        'referer': f'https://mbasic.facebook.com/groups/{group_id}'
    }
    session.headers.update(headers)

    try:
        res_view = session.get(f"https://mbasic.facebook.com/groups/{group_id}", timeout=20)
        if "checkpoint" in res_view.url: return False, "Checkpoint"
        
        fb_dtsg = re.search(r'name="fb_dtsg" value="([^"]+)"', res_view.text)
        jazoest = re.search(r'name="jazoest" value="([^"]+)"', res_view.text)
        if not fb_dtsg: return False, "Cookie die"

        final_content = spintax_process(content) + f"\n\n. . ." + "".join(random.choices(string.ascii_letters, k=3)) 

        post_data = {
            "fb_dtsg": fb_dtsg.group(1),
            "jazoest": jazoest.group(1),
            "xhpc_message_text": final_content,
            "xhpc_targetid": group_id,
        }
        
        res_post = session.post(f"https://mbasic.facebook.com/a/home.php?refid=7", data=post_data, timeout=25)
        return (True, "Thành công") if res_post.status_code in (200, 302) else (False, f"Lỗi {res_post.status_code}")
    except Exception as e:
        return False, str(e)

# ========== MENU VÀ ĐIỀU KHIỂN ==========

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("🔑 Nhập Cookie FB", "📋 Danh sách Group", "➕ Thêm Group", "🛡️ Nhập Proxy", "📝 Bắt đầu Đăng bài", "🛑 Dừng bot")
    return markup

@bot.message_handler(commands=['start'])
def welcome(message):
    bot.send_message(message.chat.id, "🤖 <b>Bot đã online!</b>", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "📝 Bắt đầu Đăng bài")
def request_post(message):
    user = get_user(message.from_user.id)
    if not user["fb_cookie"] or not user["groups"]:
        bot.send_message(message.chat.id, "❌ Thiếu dữ liệu!")
        return
    msg = bot.send_message(message.chat.id, "✍️ Nhập nội dung:")
    bot.register_next_step_handler(msg, trigger_auto_post)

def trigger_auto_post(message):
    Thread(target=start_auto_post, args=(message, message.text)).start()

def start_auto_post(message, content):
    user = get_user(message.from_user.id)
    if user["is_running"]: return
    user["is_running"] = True
    bot.send_message(message.chat.id, "🚀 Bắt đầu chạy...")
    
    success = 0
    for gid in user["groups"]:
        if not user["is_running"]: break
        proxy = random.choice(user["proxies"]) if user["proxies"] else None
        ok, result = post_to_group_v10(user["fb_cookie"], gid, content, proxy)
        bot.send_message(message.chat.id, f"{'✅' if ok else '❌'} Group {gid}: {result}")
        if ok: success += 1
        
        # Nghỉ an toàn (Có thể bấm Dừng bot ngay)
        delay = random.randint(2700, 5400)
        for _ in range(delay):
            if not user["is_running"]: break
            time.sleep(1)

    user["is_running"] = False
    bot.send_message(message.chat.id, f"🏁 Hoàn tất. Thành công: {success}")

@bot.message_handler(func=lambda m: m.text == "🛑 Dừng bot")
def stop_bot(message):
    get_user(message.from_user.id)["is_running"] = False
    bot.send_message(message.chat.id, "🛑 Đang dừng...")

# ========== KHỞI CHẠY (FIXED FOR RENDER) ==========
if __name__ == "__main__":
    # 1. Chạy Web Server để Render không tắt
    port = int(os.environ.get("PORT", 10000))
    server = Thread(target=lambda: app.run(host="0.0.0.0", port=port))
    server.daemon = True
    server.start()

    # 2. Chạy Bot với cơ chế tự kết nối lại
    print(f"Bot khởi động trên Port {port}")
    while True:
        try:
            bot.remove_webhook() # Quan trọng để nhận tin nhắn
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            print(f"Lỗi: {e}")
            time.sleep(5)
