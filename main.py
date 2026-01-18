import requests
import json
import time
import os
import random
import asyncio
import pytz
import re
import phonenumbers
from phonenumbers import geocoder, carrier
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from flask import Flask
from threading import Thread

# ===== CẤU HÌNH WEB SERVER (ĐỂ RENDER KHÔNG TẮT BOT) =====
app = Flask(__name__)

@app.route('/')
def home():
    return "Xcat Tool Bot is Active & Online!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# ===== DATABASE LƯU TRỮ (VIP & BAN) =====
DB_FILE = "database.json"

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except: pass
    return {"vip_users": [], "banned_users": {}}

def save_db():
    data = {"vip_users": list(vip_users), "banned_users": banned_users}
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

db_data = load_db()
vip_users = set(db_data.get("vip_users", []))
banned_users = db_data.get("banned_users", {})

# ===== CẤU HÌNH BOT =====
BOT_TOKEN = "6556057870:AAFPx3CJpAcGt-MfKRoAo00SlAEQ26XSS-s"
ADMIN_ID = 6090612274
USER_COOLDOWN = 5
last_used = {}

# ===== HỆ THỐNG KIỂM TRA QUYỀN =====
async def is_allowed(update: Update):
    uid = update.effective_user.id
    now = time.time()
    
    if str(uid) in banned_users:
        remaining = int(banned_users[str(uid)] - now)
        if remaining > 0:
            await update.message.reply_text(f"⛔ Bạn đang bị chặn! Còn lại: {remaining // 60} phút.")
            return False
        else:
            del banned_users[str(uid)]
            save_db()

    if uid not in vip_users and uid != ADMIN_ID:
        if uid in last_used:
            if now - last_used[uid] < USER_COOLDOWN:
                await update.message.reply_text(f"⚠️ Thao tác quá nhanh! Chờ {int(USER_COOLDOWN - (now - last_used[uid]))}s.")
                return False
        last_used[uid] = now
    return True

# ===== CÁC LỆNH CHỨC NĂNG =====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_allowed(update): return
    text = (
        "👋 <b>Chào mừng đến với Xcat Tool!</b>\n"
        "--------------------------\n"
        "🛠 <b>LỆNH HỖ TRỢ:</b>\n"
        "• /check &lt;SĐT&gt; - Thông tin chủ SĐT\n"
        "• /bienso &lt;Biển&gt; - Phạt nguội xe\n"
        "• /link &lt;URL&gt; - Lấy UID Facebook\n"
        "• /ip &lt;Địa chỉ IP&gt; - Định vị IP\n"
        "• /uid &lt;ID FreeFire&gt; - Tra cứu Game\n"
        "• /tx &lt;Mã MD5&gt; - Dự đoán Tài Xỉu\n"
        "--------------------------\n"
        "👑 <b>Admin:</b> /addvip, /xoavip, /ban, /unban"
    )
    await update.message.reply_text(text, parse_mode="HTML")

async def check_sdt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_allowed(update): return
    if not context.args:
        return await update.message.reply_text("📌 Dùng: /check 037xxxxxxx")
    
    sdt = context.args[0]
    await update.message.reply_text("⏳ Đang tra cứu số điện thoại...")
    try:
        r = requests.get(f"https://acclv5.site/xapi/vtp.php?phone={sdt}", timeout=10).json()
        data = r.get("login", {}).get("data", {})
        if data:
            res = (f"📱 <b>KẾT QUẢ SĐT:</b>\n"
                   f"👤 Tên: {data.get('displayNameAccent', 'N/A')}\n"
                   f"🆔 ID: {data.get('accountId', 'N/A')}\n"
                   f"🖼 Ảnh: {data.get('avatar', 'N/A')}")
            await update.message.reply_text(res, parse_mode="HTML")
        else:
            await update.message.reply_text("❌ Không tìm thấy thông tin trên hệ thống.")
    except:
        await update.message.reply_text("❌ Lỗi API kết nối.")

async def tx(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_allowed(update): return
    if not context.args: return
    md5 = " ".join(context.args)
    res = random.choice(["🎯 TÀI (Lớn)", "🎯 XỈU (Nhỏ)"])
    percent = random.randint(70, 99)
    await update.message.reply_text(f"🔍 <b>MD5:</b> <code>{md5}</code>\n📊 <b>Dự đoán:</b> {res}\n✅ <b>Độ chính xác:</b> {percent}%", parse_mode="HTML")

async def ip_lookup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_allowed(update): return
    if not context.args: return
    ip = context.args[0]
    try:
        data = requests.get(f"https://acclv5.site/xapi/ip.php?ip={ip}").json().get("other", {})
        text = (f"🔎 <b>IP: {ip}</b>\n🌍 Quốc gia: {data.get('quốc_gia')}\n📍 Khu vực: {data.get('khu_vực')}\n🏢 ISP: {data.get('nhà_cung_cấp')}")
        await update.message.reply_text(text, parse_mode="HTML")
    except: await update.message.reply_text("❌ Lỗi API IP.")

async def bienso(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_allowed(update): return
    if not context.args: return
    bs = context.args[0].upper()
    try:
        data = requests.get(f"https://acclv5.site/xapi/apiphatnguoi.php?code={bs}&type=2").json()
        if data.get("success"):
            d = data["data"]
            res = (f"🚗 <b>BIỂN SỐ: {bs}</b>\n🧾 Trạng thái: {d.get('trang_thai_text')}\n🟢 Kết luận: {d.get('ket_luan')}")
            await update.message.reply_text(res, parse_mode="HTML")
        else: await update.message.reply_text("⚠️ Không tìm thấy phạt nguội.")
    except: await update.message.reply_text("❌ Lỗi API Biển số.")

async def link_fb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_allowed(update): return
    if not context.args: return
    try:
        res = requests.get(f"https://acclv5.site/xapi/getidfb.php?link={context.args[0]}").json()
        await update.message.reply_text(f"👤 Tên: {res.get('name')}\n🆔 UID: <code>{res.get('id')}</code>", parse_mode="HTML")
    except: await update.message.reply_text("❌ Lỗi lấy UID.")

# ===== LỆNH ADMIN =====

async def addvip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        target = int(context.args[0]); vip_users.add(target); save_db()
        await update.message.reply_text(f"✅ Đã thêm VIP: {target}")
    except: pass

async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        target = context.args[0]; hours = int(context.args[1].replace("h",""))
        banned_users[str(target)] = time.time() + (hours * 3600); save_db()
        await update.message.reply_text(f"🚫 Đã BAN {target} trong {hours}h.")
    except: pass

# ===== KHỞI CHẠY =====
def main():
    Thread(target=run_web).start()
    app_bot = ApplicationBuilder().token(BOT_TOKEN).build()

    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("check", check_sdt))
    app_bot.add_handler(CommandHandler("tx", tx))
    app_bot.add_handler(CommandHandler("ip", ip_lookup))
    app_bot.add_handler(CommandHandler("bienso", bienso))
    app_bot.add_handler(CommandHandler("link", link_fb))
    app_bot.add_handler(CommandHandler("addvip", addvip))
    app_bot.add_handler(CommandHandler("ban", ban_user))

    print("🤖 Bot Xcat v10.0 is Running...")
    app_bot.run_polling()

if __name__ == "__main__":
    main()
