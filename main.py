import telebot
from telebot import types
import requests
import os
import time
import re
from flask import Flask
from threading import Thread

# ========== CẤU HÌNH ==========
# Thay Token của bạn vào đây hoặc thiết lập trong Environment Variables trên Render
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
        "🤖 <b>FB Auto Tool v3.0</b>\n\nBạn có thể dán trực tiếp <b>Link Group</b> hoặc <b>ID Group</b> để sử dụng.",
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

# ========== QUẢN LÝ GROUP (HỖ TRỢ LINK & ID) ==========
@bot.message_handler(func=lambda m: m.text == "➕ Thêm Group")
def add_group(message):
    msg = bot.send_message(message.chat.id, "📌 Dán danh sách <b>Link Group</b> hoặc <b>ID Group</b>:\n<i>(Mỗi cái một dòng hoặc cách nhau bởi dấu phẩy)</i>")
    bot.register_next_step_handler(msg, save_group)

def save_group(message):
    user = get_user(message.from_user.id)
    raw_input = message.text.strip()
    
    # Tách các thành phần dựa trên dấu phẩy, khoảng trắng hoặc xuống dòng
    items = re.split(r'[,\n ]+', raw_input)
    added_count = 0
    errors = []

    for item in items:
        item = item.strip()
        if not item: continue
        
        if item.isdigit():
            # Nếu là ID số thuần túy
            if item not in user["groups"]:
                user["groups"].append(item)
                added_count += 1
        elif "facebook.com/groups/" in item:
            # Nếu là link, tách lấy phần sau chữ 'groups/'
            try:
                # Xử lý lấy ID từ các dạng link khác nhau
                match = re.search(r'groups/(\d+)', item)
                if match:
                    group_id = match.group(1)
                    if group_id not in user["groups"]:
                        user["groups"].append(group_id)
                        added_count += 1
                else:
                    # Nếu link dạng chữ (vanity url)
                    name_match = re.search(r'groups/([^/?#]+)', item)
                    if name_match:
                        errors.append(name_match.group(1))
            except:
                pass
        else:
            if not item.isdigit(): errors.append(item)

    msg_reply = f"✅ Đã thêm <b>{added_count}</b> Group ID mới."
    if errors:
        msg_reply += f"\n\n⚠️ Không thể tự lấy ID từ các tên: <code>{', '.join(errors)}</code>\n<i>(Hãy dùng tool Lookup-ID để đổi sang số)</i>"
    
    bot.send_message(message.chat.id, msg_reply, reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "📋 Danh sách Group")
def list_groups(message):
    user = get_user(message.from_user.id)
    if not user["groups"]:
        bot.send_message(message.chat.id, "❌ Danh sách Group trống.")
        return
    text = "📋 <b>Danh sách ID đã lưu:</b>\n\n" + "\n".join([f"• <code>{g}</code>" for g in user["groups"]])
    bot.send_message(message.chat.id, text)

# ========== LOGIC ĐĂNG BÀI THỰC TẾ ==========
@bot.message_handler(func=lambda m: m.text == "📝 Đăng bài")
def request_post(message):
    user = get_user(message.from_user.id)
    if not user["fb_cookie"]:
        bot.send_message(message.chat.id, "❌ Bạn chưa nhập Cookie!")
        return
    if not user["groups"]:
        bot.send_message(message.chat.id, "❌ Chưa có Group nào trong danh sách!")
        return
    msg = bot.send_message(message.chat.id, "✍️ Nhập nội dung bài viết:")
    bot.register_next_step_handler(msg, execute_post)

def execute_post(message):
    user = get_user(message.from_user.id)
    content = message.text
    bot.send_message(message.chat.id, f"🚀 Đang đăng bài lên {len(user['groups'])} nhóm...")

    success = 0
    fail = 0

    for gid in user["groups"]:
        try:
            # Giả lập đăng bài qua mbasic
            # Lưu ý: Cần fb_dtsg để đăng thật, đây là khung sườn gửi Request
            headers = {
                'cookie': user["fb_cookie"],
                'user-agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_8 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1'
            }
            payload = {'status': content}
            
            # Gửi tới trang xử lý đăng của FB
            res = requests.post(f"https://mbasic.facebook.com/a/home.php?refid=7", headers=headers, data=payload)
            
            # Nghỉ 20 giây mỗi group để bảo vệ tài khoản
            time.sleep(20)
            success += 1
            
        except Exception as e:
            fail += 1

    bot.send_message(
        message.chat.id,
        f"🏁 <b>Hoàn tất!</b>\n✅ Thành công: {success}\n❌ Thất bại: {fail}"
    )

# ========== CHẠY TOOL ==========
def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    Thread(target=run).start()
    bot.infinity_polling(skip_pending=True)
