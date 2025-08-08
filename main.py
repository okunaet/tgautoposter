import os
import time
from zoneinfo import ZoneInfo
import datetime as dt
import requests
from openai import OpenAI
import random

# ====== CONFIG ======
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")  # e.g. @your_channel
OPENAI_KEY = os.getenv("OPENAI_KEY")
KYIV_TZ = ZoneInfo("Europe/Kyiv")
SCHEDULE = ["11:00", "15:00", "15:40", "17:00", "19:00", "21:00"]
# ====================

client = OpenAI(api_key=OPENAI_KEY)

TOPICS = [
    "Поради з Photoshop для рекламних банерів",
    "Добірка безкоштовних шрифтів для комерційних проєктів",
    "Лайфхаки Figma для швидкого прототипування",
    "Композиція та ієрархія у креативах",
    "Підбір кольорів: як не зіпсувати банер",
    "Типові помилки дизайнерів-початківців",
    "Гайд по експорту зображень для Telegram та Instagram",
    "Швидкі гарячі клавіші у Photoshop/Illustrator",
    "Як зробити CTA помітним і клікабельним",
    "Міні-урок: сітки та відступи у макетах"
]

def generate_post():
    topic = random.choice(TOPICS)
    style_prompt = f"""
    Напиши україномовний пост (80–150 слів) про тему: "{topic}".
    Стиль: дружній, легкий, іноді з м'яким гумором без перебору.
    Додай 2–6 релевантних емодзі природно в тексті.
    Уникай токсичності й надмірного пафосу.
    Форматуй абзацами. Дай 1–3 практичні поради.
    """
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": style_prompt.strip()}]
    )
    text = resp.choices[0].message.content.strip()
    return text

def send_text(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHANNEL_ID, "text": text, "parse_mode": "HTML"}
    r = requests.post(url, data=data, timeout=60)
    if not r.ok:
        raise RuntimeError(f"Telegram error: {r.status_code} {r.text}")

def kyiv_now_hhmm():
    return dt.datetime.now(KYIV_TZ).strftime("%H:%M")

def kyiv_today_str():
    return dt.datetime.now(KYIV_TZ).strftime("%Y-%m-%d")

def main():
    print("🟢 TG autoposter started (TEXT ONLY). Timezone: Europe/Kyiv")
    posted_slots = set()
    while True:
        try:
            now_hhmm = kyiv_now_hhmm()
            today = kyiv_today_str()
            slot_id = f"{today} {now_hhmm}"
            if now_hhmm in SCHEDULE and slot_id not in posted_slots:
                print(f"[{slot_id}] Generating post...")
                post_text = generate_post()
                send_text(post_text)
                posted_slots.add(slot_id)
                print(f"[{slot_id}] Posted ✅")
                time.sleep(65)
            else:
                time.sleep(5)
        except Exception as e:
            print("⚠️ Error:", e)
            time.sleep(15)

if __name__ == "__main__":
    missing = [k for k in ["BOT_TOKEN", "CHANNEL_ID", "OPENAI_KEY"] if not os.getenv(k)]
    if missing:
        print("❌ Missing env vars:", ", ".join(missing))
    main()
