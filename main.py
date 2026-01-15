import telebot
from telebot import types
import requests
import os
import time
import re
from flask import Flask
from threading import Thread

# ========== CẤU HÌNH ==========
BOT_TOKEN = os.environ.get("BOT_TOKEN") or "6556057870:AAFPx3CJpAcGt-MfKRoAo00SlAEQ26XSS-s"
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
app = Flask(__name__)

user_data = {}

def get_user(uid):
    if uid not in user_data:
        user_data[uid] = {"fb_cookie": "", "groups": []}
    return user_data[uid]

# Hàm mới: Tự động tìm ID từ Link chữ
def find_id_from_url(url):
    try:
        # Sử dụng tool lookup-id ngầm qua API
        response = requests.post("https://lookup-id.com/", data={'fburl': url, 'check': 'Lookup'}, timeout=10)
        match = re.search(r'id="code".*?>(\d+)<', response.text)
        if match:
            return match.group(1)
    except:
        pass
    return None

@app.route('/')
def home():
    return "Bot is running!"

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "🤖 <b>FB Auto Tool v4.0</b>\nĐã hỗ trợ tự động tìm ID từ link chữ!", reply_markup=main_menu())

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("🔑 Nhập Cookie FB", "📋 Danh sách Group", "➕ Thêm Group", "📝 Đăng bài")
    return markup

@bot.message_handler(func=lambda m: m.text == "🔑 Nhập Cookie FB")
def request_cookie(message):
    msg = bot.send_message(message.chat.id, "📌 Dán Cookie Facebook của bạn:")
    bot.register_next_step_handler(msg, save_cookie)

def save_cookie(message):
    user = get_user(message.from_user.id)
    user["fb_cookie"] = message.text.strip()
    bot.send_message(message.chat.id, "✅ Đã lưu Cookie!", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "➕ Thêm Group")
def add_group(message):
    msg = bot.send_message(message.chat.id, "📌 Dán Link Group (Hỗ trợ cả link có tên như <i>hiendzgm</i>):")
    bot.register_next_step_handler(msg, save_group)

def save_group(message):
    user = get_user(message.from_user.id)
    items = re.split(r'[,\n ]+', message.text.strip())
    bot.send_message(message.chat.id, "⏳ Đang quét ID, vui lòng đợi giây lát...")
    
    added_count = 0
    for item in items:
        if not item: continue
        if item.isdigit():
            if item not in user["groups"]:
                user["groups"].append(item)
                added_count += 1
        else:
            # Nếu là link, thử tìm ID ngầm
            found_id = find_id_from_url(item)
            if found_id and found_id not in user["groups"]:
                user["groups"].append(found_id)
                added_count += 1

    bot.send_message(message.chat.id, f"✅ Thành công! Đã thêm {added_count} Group ID vào danh sách.", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "📋 Danh sách Group")
def list_groups(message):
    user = get_user(message.from_user.id)
    if not user["groups"]:
        bot.send_message(message.chat.id, "❌ Trống.")
        return
    bot.send_message(message.chat.id, "📋 <b>ID hiện có:</b>\n" + "\n".join(user["groups"]))

@bot.message_handler(func=lambda m: m.text == "📝 Đăng bài")
def request_post(message):
    msg = bot.send_message(message.chat.id, "✍️ Nhập nội dung bài đăng:")
    bot.register_next_step_handler(msg, execute_post)

def execute_post(message):
    user = get_user(message.from_user.id)
    content = message.text
    success = 0
    for gid in user["groups"]:
        try:
            # Logic đăng bài mbasic
            headers = {'cookie': user["fb_cookie"], 'user-agent': 'Mozilla/5.0 (iPhone; CPU OS 14_0)'}
            requests.post(f"https://mbasic.facebook.com/a/home.php?refid=7", headers=headers, data={'status': content})
            time.sleep(20)
            success += 1
        except: pass
    bot.send_message(message.chat.id, f"🏁 Đã đăng xong {success} nhóm!")

if __name__ == "__main__":
    Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))).start()
    bot.infinity_polling(skip_pending=True)
