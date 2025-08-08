
import os
import time
import telebot
from datetime import datetime

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")

bot = telebot.TeleBot(BOT_TOKEN)

def generate_post():
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return f"Автопостинг! Время: {now}"

while True:
    try:
        text = generate_post()
        bot.send_message(CHANNEL_ID, text)
        print(f"[{datetime.now()}] Posted: {text}")
    except Exception as e:
        print(f"Error: {e}")
    time.sleep(15 * 60)  # каждые 15 минут
