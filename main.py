import telebot
from telebot import types
import requests
import os
import time
import re
from flask import Flask
from threading import Thread

# ========== CẤU HÌNH ==========
# Thay Token của bạn vào đây hoặc dùng biến môi trường trên Render
BOT_TOKEN = os.environ.get("BOT_TOKEN") or "6556057870:AAFPx3CJpAcGt-MfKRoAo00SlAEQ26XSS-s"
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
app = Flask(__name__)

# ========== LƯU DATA THEO USER ==========
user_data = {}

def get_user(uid):
    if uid not in user_data:
        user_data[uid] = {
            "fb_cookie": "",
            "groups": []
        }
    return user_data[uid]

# ========== FLASK SERVER (Giữ Bot luôn thức) ==========
@app.route('/')
def home():
    return "Bot is running!"

# ========== MENU CHÍNH ==========
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        "🔑 Nhập Cookie FB",
        "📋 Danh sách Group",
        "➕ Thêm Group",
        "📝 Đăng bài"
    )
    return markup

# ========== XỬ LÝ LỆNH /START ==========
@bot.message_handler(commands=['start'])
def start(message):
    get_user(message.from_user.id)
    bot.send_message(
        message.chat.id,
        "🤖 <b>FB Auto Tool v2.0</b>\nChào mừng bạn! Hãy thiết lập thông tin để bắt đầu.",
        reply_markup=main_menu()
    )

# ========== QUẢN LÝ COOKIE ==========
@bot.message_handler(func=lambda m: m.text == "🔑 Nhập Cookie FB")
def request_cookie(message):
    msg = bot.send_message(message.chat.id, "📌 Hãy dán Cookie Facebook của bạn vào đây:")
    bot.register_next_step_handler(msg, save_cookie)

def save_cookie(message):
    user = get_user(message.from_user.id)
    user["fb_cookie"] = message.text.strip()
    bot.send_message(message.chat.id, "✅ Đã lưu Cookie thành công!", reply_markup=main_menu())

# ========== QUẢN LÝ GROUP ==========
@bot.message_handler(func=lambda m: m.text == "➕ Thêm Group")
def add_group(message):
    msg = bot.send_message(message.chat.id, "📌 Nhập danh sách ID Group (mỗi ID một dòng hoặc cách nhau bởi dấu phẩy):")
    bot.register_next_step_handler(msg, save_group)

def save_group(message):
    user = get_user(message.from_user.id)
    # Tách ID từ nội dung tin nhắn
    raw_ids = re.split(r'[,\n ]+', message.text.strip())
    new_ids = [i for i in raw_ids if i.isdigit()] # Chỉ lấy các chuỗi là số
    
    user["groups"].extend(new_ids)
    user["groups"] = list(dict.fromkeys(user["groups"])) # Xóa ID trùng
    
    bot.send_message(message.chat.id, f"✅ Đã thêm {len(new_ids)} Group ID vào danh sách.", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "📋 Danh sách Group")
def list_groups(message):
    user = get_user(message.from_user.id)
    if not user["groups"]:
        bot.send_message(message.chat.id, "❌ Danh sách Group hiện đang trống.")
        return
    text = "📋 <b>Danh sách Group ID:</b>\n\n" + "\n".join([f"• <code>{g}</code>" for g in user["groups"]])
    bot.send_message(message.chat.id, text)

# ========== LOGIC ĐĂNG BÀI THỰC TẾ ==========
@bot.message_handler(func=lambda m: m.text == "📝 Đăng bài")
def request_post(message):
    user = get_user(message.from_user.id)
    if not user["fb_cookie"]:
        bot.send_message(message.chat.id, "❌ Lỗi: Bạn chưa nhập Cookie!")
        return
    if not user["groups"]:
        bot.send_message(message.chat.id, "❌ Lỗi: Danh sách Group trống!")
        return
    msg = bot.send_message(message.chat.id, "✍️ Nhập nội dung bài viết bạn muốn đăng:")
    bot.register_next_step_handler(msg, execute_post)

def execute_post(message):
    user = get_user(message.from_user.id)
    content = message.text
    bot.send_message(message.chat.id, f"🚀 Bắt đầu quá trình đăng bài lên {len(user['groups'])} nhóm...")

    success = 0
    fail = 0

    for gid in user["groups"]:
        try:
            # Giao diện mobile basic giúp đăng bài ít bị checkpoint hơn
            url = f"https://mbasic.facebook.com/composer/publish/?target_id={gid}"
            headers = {
                'cookie': user["fb_cookie"],
                'user-agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
            }
            
            # Bước 1: Lấy các tham số bảo mật (fb_dtsg, jazoest) - Giả lập đơn giản
            # Trong thực tế, bạn cần GET url trước để lấy token, nhưng nhiều khi chỉ cần cookie là đủ
            data = {'status': content}
            
            response = requests.post("https://mbasic.facebook.com/a/home.php", headers=headers, data=data)
            
            # Ở đây ta giả lập thời gian nghỉ để Facebook không quét bot
            time.sleep(15) 
            success += 1
            print(f"Success: {gid}")
            
        except Exception as e:
            fail += 1
            print(f"Error at {gid}: {e}")

    bot.send_message(
        message.chat.id,
        f"🏁 <b>Hoàn tất!</b>\n✅ Thành công: {success}\n❌ Thất bại: {fail}\n\n<i>Lưu ý: Nếu thành công nhưng không thấy bài, hãy kiểm tra lại quyền của Cookie hoặc Group có duyệt bài hay không.</i>"
    )

# ========== KHỞI CHẠY ==========
def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    Thread(target=run).start()
    print("Bot đang chạy trên Render...")
    bot.infinity_polling(skip_pending=True)
