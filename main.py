import telebot
import requests
import time
from flask import Flask
from threading import Thread

# --- CẤU HÌNH ---
BOT_TOKEN = 'TOKEN_BOT_CUA_BAN'
bot = telebot.TeleBot(BOT_TOKEN)

# --- PHẦN WEB SERVER ĐỂ GIỮ BOT LUÔN THỨC ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- PHẦN LOGIC BOT ĐĂNG BÀI ---
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Chào bạn! Gửi nội dung bài viết để mình đăng lên Facebook.")

# Thêm các xử lý đăng bài Facebook ở đây (như đã hướng dẫn ở trên)

# --- CHẠY BOT ---
if __name__ == "__main__":
    keep_alive() # Khởi động web server
    print("Bot is starting...")
    bot.infinity_polling() # Chạy bot liên tục