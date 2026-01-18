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
# Thay Token mới của bạn vào đây
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

# ========== CÔNG CỤ HỖ TRỢ ==========

def spintax_process(text):
    while '{' in text:
        start = text.rfind('{')
        end = text.find('}', start)
        if end == -1: break
        content = text[start + 1:end]
        chosen = random.choice(content.split('|'))
        text = text[:start] + chosen + text[end + 1:]
    return text

# ========== CORE ĐĂNG BÀI (FB) ==========

def post_to_group_v10(cookie, group_id, content, proxy):
    session = requests.Session(impersonate="chrome110") 
    if proxy: session.proxies = {'http': proxy, 'https': proxy}
    
    headers = {
        'authority': 'mbasic.facebook.com',
        'cookie': cookie,
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    session.headers.update(headers)

    try:
        res_view = session.get(f"https://mbasic.facebook.com/groups/{group_id}", timeout=20)
        fb_dtsg = re.search(r'name="fb_dtsg" value="([^"]+)"', res_view.text)
        jazoest = re.search(r'name="jazoest" value="([^"]+)"', res_view.text)
        if not fb_dtsg: return False, "Cookie die"

        post_data = {
            "fb_dtsg": fb_dtsg.group(1),
            "jazoest": jazoest.group(1),
            "xhpc_message_text": spintax_process(content) + "\n" + "".join(random.choices(string.ascii_letters, k=3)),
            "xhpc_targetid": group_id,
        }
        res_post = session.post(f"https://mbasic.facebook.com/a/home.php?refid=7", data=post_data, timeout=25)
        return (True, "Thành công") if res_post.status_code in (200, 302) else (False, "Lỗi đăng")
    except Exception as e:
        return False, str(e)

# ========== XỬ LÝ MENU VÀ NHẬP LIỆU ==========

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("🔑 Nhập Cookie FB", "📋 Danh sách Group", "➕ Thêm Group", "🛡️ Nhập Proxy", "📝 Bắt đầu Đăng bài", "🛑 Dừng bot", "🗑️ Xóa Group")
    return markup

@bot.message_handler(commands=['start'])
def welcome(message):
    bot.send_message(message.chat.id, "🤖 <b>Chào mừng bạn!</b>\nHãy sử dụng các nút bên dưới để cấu hình Bot.", reply_markup=main_menu())

# 1. Nhập Cookie
@bot.message_handler(func=lambda m: m.text == "🔑 Nhập Cookie FB")
def ask_cookie(message):
    msg = bot.send_message(message.chat.id, "🍪 Hãy dán Cookie Facebook của bạn vào đây:")
    bot.register_next_step_handler(msg, save_cookie)

def save_cookie(message):
    user = get_user(message.from_user.id)
    user["fb_cookie"] = message.text
    bot.send_message(message.chat.id, "✅ Đã lưu Cookie thành công!")

# 2. Thêm Group
@bot.message_handler(func=lambda m: m.text == "➕ Thêm Group")
def ask_group(message):
    msg = bot.send_message(message.chat.id, "🆔 Nhập ID Group (Mỗi ID một dòng hoặc cách nhau bởi dấu phẩy):")
    bot.register_next_step_handler(msg, save_group)

def save_group(message):
    user = get_user(message.from_user.id)
    ids = re.findall(r'\d+', message.text)
    user["groups"].extend(ids)
    user["groups"] = list(set(user["groups"])) # Xóa trùng
    bot.send_message(message.chat.id, f"✅ Đã thêm {len(ids)} ID Group!")

# 3. Xem danh sách Group
@bot.message_handler(func=lambda m: m.text == "📋 Danh sách Group")
def list_groups(message):
    user = get_user(message.from_user.id)
    if not user["groups"]:
        bot.send_message(message.chat.id, "⚠️ Danh sách đang trống.")
    else:
        txt = "📋 <b>Danh sách ID Group của bạn:</b>\n\n" + "\n".join(user["groups"])
        bot.send_message(message.chat.id, txt)

# 4. Bắt đầu đăng bài
@bot.message_handler(func=lambda m: m.text == "📝 Bắt đầu Đăng bài")
def start_post_step(message):
    user = get_user(message.from_user.id)
    if not user["fb_cookie"] or not user["groups"]:
        bot.send_message(message.chat.id, "❌ Lỗi: Thiếu Cookie hoặc Group!")
        return
    msg = bot.send_message(message.chat.id, "✍️ Nhập nội dung bài đăng:")
    bot.register_next_step_handler(msg, do_auto_post)

def do_auto_post(message):
    content = message.text
    Thread(target=run_post_logic, args=(message, content)).start()

def run_post_logic(message, content):
    user = get_user(message.from_user.id)
    user["is_running"] = True
    bot.send_message(message.chat.id, "🚀 Bắt đầu tiến trình đăng bài...")
    
    for gid in user["groups"]:
        if not user["is_running"]: break
        ok, res = post_to_group_v10(user["fb_cookie"], gid, content, None)
        bot.send_message(message.chat.id, f"{'✅' if ok else '❌'} Group {gid}: {res}")
        time.sleep(random.randint(60, 120)) # Nghỉ ngắn để test, bạn có thể chỉnh lại 2700

    user["is_running"] = False
    bot.send_message(message.chat.id, "🏁 Hoàn tất chiến dịch.")

@bot.message_handler(func=lambda m: m.text == "🛑 Dừng bot")
def stop_process(message):
    get_user(message.from_user.id)["is_running"] = False
    bot.send_message(message.chat.id, "🛑 Lệnh dừng đã được gửi.")

# ========== KHỞI CHẠY ==========
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    Thread(target=lambda: app.run(host="0.0.0.0", port=port)).start()
    
    while True:
        try:
            bot.remove_webhook()
            bot.polling(none_stop=True)
        except: time.sleep(5)
