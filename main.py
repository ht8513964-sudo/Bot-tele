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

# ========== SIÊU CẤU HÌNH v10.0 (FIXED FOR RENDER) ==========
# Khuyến khích đưa TOKEN vào Environment Variables trên Render
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
    return "Ultra Stealth System v10.0 is Active! (Bot is Running)"

# ========== CÔNG CỤ BYPASS NÂNG CAO ==========

def spintax_process(text):
    """Xử lý định dạng {Chào|Hi|Hello} để tạo nội dung ngẫu nhiên"""
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

# ========== CORE ĐĂNG BÀI - STEALTH MODE ==========

def post_to_group_v10(cookie, group_id, content, proxy):
    session = requests.Session(impersonate="chrome110") 
    if proxy:
        session.proxies = {'http': proxy, 'https': proxy}

    ua = get_random_ua()
    headers = {
        'authority': 'mbasic.facebook.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'cookie': cookie,
        'user-agent': ua,
        'referer': f'https://mbasic.facebook.com/groups/{group_id}'
    }
    session.headers.update(headers)

    try:
        # BƯỚC 1: Giả lập xem nhóm
        res_view = session.get(f"https://mbasic.facebook.com/groups/{group_id}", timeout=20)
        if "checkpoint" in res_view.url: return False, "Checkpoint"
        time.sleep(random.randint(5, 10)) # Giảm chút thời gian để test nhanh

        # BƯỚC 2: Lấy Token bảo mật
        fb_dtsg = re.search(r'name="fb_dtsg" value="([^"]+)"', res_view.text)
        jazoest = re.search(r'name="jazoest" value="([^"]+)"', res_view.text)
        if not fb_dtsg: return False, "Cookie die hoặc bị chặn"

        # BƯỚC 3: Xử lý nội dung
        final_content = spintax_process(content)
        final_content += f"\n\n. . ." + "".join(random.choices(string.ascii_letters, k=3)) 

        # BƯỚC 4: Gửi bài
        post_data = {
            "fb_dtsg": fb_dtsg.group(1),
            "jazoest": jazoest.group(1),
            "xhpc_message_text": final_content,
            "xhpc_targetid": group_id,
        }
        
        res_post = session.post(
            f"https://mbasic.facebook.com/a/home.php?refid=7", 
            data=post_data, 
            timeout=25
        )

        if res_post.status_code in (200, 302):
            return True, "Thành công"
        return False, f"Lỗi HTTP {res_post.status_code}"

    except Exception as e:
        return False, str(e)

# ========== MENU VÀ ĐIỀU KHIỂN ==========

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("🔑 Nhập Cookie FB", "📋 Danh sách Group", "➕ Thêm Group", "🛡️ Nhập Proxy", "📝 Bắt đầu Đăng bài", "🛑 Dừng bot")
    return markup

@bot.message_handler(commands=['start'])
def welcome(message):
    bot.send_message(message.chat.id, "🤖 <b>Ultra Stealth System v10.0</b>\nHệ thống auto post bypass 2026 đã sẵn sàng!", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "📝 Bắt đầu Đăng bài")
def request_post(message):
    user = get_user(message.from_user.id)
    if not user["fb_cookie"] or not user["groups"]:
        bot.send_message(message.chat.id, "❌ Lỗi: Bạn chưa nhập Cookie hoặc chưa có danh sách Group!")
        return
    msg = bot.send_message(message.chat.id, "✍️ Nhập nội dung bài đăng (Hỗ trợ {A|B|C}):")
    bot.register_next_step_handler(msg, trigger_auto_post)

def trigger_auto_post(message):
    # Chạy đăng bài trong Thread riêng để Bot không bị treo
    content = message.text
    t = Thread(target=start_auto_post, args=(message, content))
    t.start()

def start_auto_post(message, content):
    user = get_user(message.from_user.id)
    if user["is_running"]:
        bot.send_message(message.chat.id, "⚠️ Bot đang chạy một tiến trình rồi!")
        return

    user["is_running"] = True
    bot.send_message(message.chat.id, "🛡️ Đang bắt đầu chiến dịch đăng bài ngầm...")
    
    success = 0
    groups = list(user["groups"])
    random.shuffle(groups)

    for gid in groups:
        if not user["is_running"]: break
        
        proxy = random.choice(user["proxies"]) if user["proxies"] else None
        ok, result = post_to_group_v10(user["fb_cookie"], gid, content, proxy)
        
        if ok:
            success += 1
            bot.send_message(message.chat.id, f"✅ Group {gid}: Thành công")
        else:
            bot.send_message(message.chat.id, f"❌ Group {gid}: {result}")
            if result == "Checkpoint":
                user["is_running"] = False
                bot.send_message(message.chat.id, "🚨 Dừng Bot do Checkpoint!")
                break

        # Nghỉ giữa các bài (Chia nhỏ sleep để có thể dừng bot ngay lập tức)
        delay = random.randint(2700, 5400) # 45-90 phút
        for _ in range(delay):
            if not user["is_running"]: break
            time.sleep(1)

    user["is_running"] = False
    bot.send_message(message.chat.id, f"🏁 Hoàn tất. Đã đăng thành công {success} nhóm.")

@bot.message_handler(func=lambda m: m.text == "🛑 Dừng bot")
def stop_bot(message):
    user = get_user(message.from_user.id)
    user["is_running"] = False
    bot.send_message(message.chat.id, "🛑 Đã nhận lệnh dừng. Bot sẽ dừng sau khi kết thúc lượt đăng này.")

# --- PHẦN KHỞI CHẠY (QUAN TRỌNG CHO RENDER) ---
if __name__ == "__main__":
    # 1. Tự động lấy Port từ Render
    port = int(os.environ.get("PORT", 10000))
    
    # 2. Chạy Flask trong luồng riêng
    server_thread = Thread(target=lambda: app.run(host="0.0.0.0", port=port))
    server_thread.daemon = True
    server_thread.start()
    
    # 3. Chạy Telegram Bot
    print(f"Bot đang chạy tại Port: {port}")
    bot.infinity_polling(skip_pending=True)
