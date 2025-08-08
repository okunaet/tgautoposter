import os
import time
import requests
from zoneinfo import ZoneInfo
import datetime as dt
from openai import OpenAI
import random
import base64

# ========= CONFIG =========
BOT_TOKEN = os.getenv("BOT_TOKEN")         # <-- set in Railway variables
CHANNEL_ID = os.getenv("CHANNEL_ID")       # e.g. @your_channel
OPENAI_KEY = os.getenv("OPENAI_KEY")       # OpenAI API key
KYIV_TZ = ZoneInfo("Europe/Kyiv")

# Five posts per day (Kyiv time)
SCHEDULE = ["11:00", "15:00","15:12", "17:00", "19:00", "21:00"]
# ==========================

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
    Додай декілька релевантних емодзі (2–6) природно в тексті.
    Уникай токсичності, жаргону та надмірного пафосу.
    Форматуй абзацами та маркерами за потреби.
    Дай 1–3 практичні поради або кроки.
    """
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": style_prompt.strip()}]
    )
    text = resp.choices[0].message.content.strip()
    return text, topic

def generate_image(topic, text):
    # короткий англомовний опис для ілюстрації
    img_prompt = (
        "Minimalist, clean, modern flat illustration, high-quality, "
        "soft lighting, crisp lines, subtle gradients. "
        f"Theme: {topic}. Visualize a graphic design tip or tutorial. No text overlay."
    )
    img = client.images.generate(
        model="gpt-image-1",
        prompt=img_prompt,
        size="1024x1024",
        n=1,
        response_format="b64_json"
    )
    b64 = img.data[0].b64_json
    return base64.b64decode(b64)

def send_photo_with_caption(image_bytes, caption):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    files = {"photo": ("image.png", image_bytes, "image/png")}
    data = {
        "chat_id": CHANNEL_ID,
        "caption": caption,
        "parse_mode": "HTML"
    }
    r = requests.post(url, data=data, files=files, timeout=60)
    if not r.ok:
        raise RuntimeError(f"Telegram error: {r.status_code} {r.text}")

def kyiv_now_hhmm():
    return dt.datetime.now(KYIV_TZ).strftime("%H:%M")

def kyiv_today_str():
    return dt.datetime.now(KYIV_TZ).strftime("%Y-%m-%d")

def main():
    print("🟢 TG autoposter started. Timezone: Europe/Kyiv")
    posted_slots = set()  # remembers "YYYY-MM-DD HH:MM" to avoid duplicates

    while True:
        try:
            now_hhmm = kyiv_now_hhmm()
            today = kyiv_today_str()
            slot_id = f"{today} {now_hhmm}"

            if now_hhmm in SCHEDULE and slot_id not in posted_slots:
                print(f"[{slot_id}] Generating post...")
                text, topic = generate_post()
                image_bytes = generate_image(topic, text)
                send_photo_with_caption(image_bytes, text)
                posted_slots.add(slot_id)
                print(f"[{slot_id}] Posted ✅")

                # sleep a bit to skip the minute
                time.sleep(65)
            else:
                time.sleep(5)
        except Exception as e:
            print("⚠️ Error:", e)
            time.sleep(15)

if __name__ == "__main__":
    # Basic env checks
    missing = [k for k in ["BOT_TOKEN", "CHANNEL_ID", "OPENAI_KEY"] if not os.getenv(k)]
    if missing:
        print("❌ Missing env vars:", ", ".join(missing))
    main()
