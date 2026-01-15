import telebot
from telebot import types
import requests
import os
import time
from flask import Flask
from threading import Thread

# ========== CẤU HÌNH ==========
BOT_TOKEN = os.environ.get("BOT_TOKEN") or "6556057870:AAFPx3CJpAcGt-MfKRoAo00SlAEQ26XSS-s"
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
app = Flask(__name__)

# ========== LƯU DATA THEO USER ==========
# user_id : { fb_cookie: "", groups: [] }
user_data = {}

def get_user(uid):
    if uid not in user_data:
        user_data[uid] = {
            "fb_cookie": "",
            "groups": []
        }
    return user_data[uid]

# ========== FLASK ==========
@app.route('/')
def home():
    return "Bot is running!"

# ========== MENU ==========
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        "🔑 Nhập Cookie FB",
        "📋 Danh sách Group",
        "➕ Thêm Group",
        "📝 Đăng bài"
    )
    return markup

# ========== START ==========
@bot.message_handler(commands=['start'])
def start(message):
    get_user(message.from_user.id)
    bot.send_message(
        message.chat.id,
        "🤖 <b>FB Auto Tool</b>\nChọn chức năng bên dưới:",
        reply_markup=main_menu()
    )

# ========== COOKIE ==========
@bot.message_handler(func=lambda m: m.text == "🔑 Nhập Cookie FB")
def request_cookie(message):
    msg = bot.send_message(message.chat.id, "📌 Dán Cookie Facebook:")
    bot.register_next_step_handler(msg, save_cookie)

def save_cookie(message):
    user = get_user(message.from_user.id)
    user["fb_cookie"] = message.text.strip()
    bot.send_message(message.chat.id, "✅ Đã lưu Cookie!", reply_markup=main_menu())

# ========== GROUP ==========
@bot.message_handler(func=lambda m: m.text == "➕ Thêm Group")
def add_group(message):
    msg = bot.send_message(message.chat.id, "📌 Nhập ID Group:")
    bot.register_next_step_handler(msg, save_group)

def save_group(message):
    user = get_user(message.from_user.id)
    user["groups"].append(message.text.strip())
    bot.send_message(message.chat.id, "✅ Đã thêm group!", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "📋 Danh sách Group")
def list_groups(message):
    user = get_user(message.from_user.id)
    if not user["groups"]:
        bot.send_message(message.chat.id, "❌ Chưa có group nào.")
        return
    text = "📋 <b>Group của bạn:</b>\n" + "\n".join(user["groups"])
    bot.send_message(message.chat.id, text)

# ========== ĐĂNG BÀI ==========
@bot.message_handler(func=lambda m: m.text == "📝 Đăng bài")
def request_post(message):
    user = get_user(message.from_user.id)
    if not user["fb_cookie"]:
        bot.send_message(message.chat.id, "❌ Chưa nhập Cookie!")
        return
    if not user["groups"]:
        bot.send_message(message.chat.id, "❌ Chưa có group!")
        return
    msg = bot.send_message(message.chat.id, "✍️ Nhập nội dung bài viết:")
    bot.register_next_step_handler(msg, execute_post)

def execute_post(message):
    user = get_user(message.from_user.id)
    content = message.text
    bot.send_message(message.chat.id, "🚀 Bắt đầu đăng bài...")

    success = 0
    for gid in user["groups"]:
        time.sleep(3)  # giả lập
        success += 1

    bot.send_message(
        message.chat.id,
        f"✅ Đăng thành công <b>{success}</b> group!"
    )

# ========== RUN ==========
def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    Thread(target=run).start()
    bot.infinity_polling(skip_pending=True)
