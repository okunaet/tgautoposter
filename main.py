import os
import time
import base64
import random
import datetime as dt
import requests

# ---- Timezone handling ----
try:
    from zoneinfo import ZoneInfo
    KYIV_TZ = ZoneInfo("Europe/Kyiv")
except Exception:
    from datetime import timezone, timedelta
    KYIV_TZ = timezone(timedelta(hours=3))  # fallback to UTC+3

# ====== CONFIG ======
BOT_TOKEN = os.getenv("BOT_TOKEN")              # required
CHANNEL_ID = os.getenv("CHANNEL_ID")            # required: @channel or -100...
OPENAI_KEY = os.getenv("OPENAI_KEY")            # required
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
IMAGE_MODEL = os.getenv("IMAGE_MODEL", "gpt-image-1")
SCHEDULE = ["11:00", "15:00", "16:04", "17:00", "19:00", "21:00"]  # Kyiv
IMAGES_PER_DAY = 3                               # exactly 3 image posts per day
RUN_NOW = os.getenv("RUN_NOW") == "1"            # send one post immediately for testing
# ====================

# Lazy OpenAI client
_client = None
def client():
    global _client
    if _client is None:
        from openai import OpenAI
        _client = OpenAI(api_key=OPENAI_KEY)
    return _client

# 30+ diverse directions for topics
TOPIC_DIRECTIONS = [
    "Поради з Photoshop для рекламних банерів",
    "Добірки безкоштовних шрифтів для комерційних проєктів",
    "Лайфхаки Figma для швидкого прототипування",
    "Композиція та ієрархія у креативах",
    "Колірні схеми, контраст та акценти",
    "Типові помилки дизайнерів-початківців і як їх уникати",
    "Сітки, модульність та 8pt-система",
    "Відступи, ритм і вертикальна композиція",
    "Шрифтові пари: Sans + Serif, кейси та приклади",
    "Експорт зображень для Telegram, Instagram, Ads",
    "Побудова ефективного CTA і мікротекст",
    "Трендові стилі: неоморфізм, глассморфізм, плоска графіка",
    "Мікроанімації та як зробити прототип живішим",
    "Організація файлів у Figma: компоненти, варіанти, токени",
    "Система іконок: товщина лінії, сітка, узгодженість",
    "UX-тексти: як не сваритися з копірайтером",
    "Підбір референсів: як швидко знайти ідею",
    "Швидкі гарячі клавіші у Photoshop/Illustrator",
    "Чеклист перед здачею макету: що перевірити",
    "Айдентика для малого бізнесу: що достатньо зробити",
    "Меми про дизайн і як їх використовувати без крінжу",
    "Файлові формати: коли PNG/JPG/WEBP/SVG",
    "Зниження «візуального шуму»: мінімалізм на практиці",
    "Правило близькості, вирівнювання та повторення",
    "Заголовки, підзаголовки та лінійка шрифтів",
    "А/Б тести креативів: як робити швидко",
    "Кольорова психологія у перформанс-креативах",
    "Баланс між брендом і перформансом",
    "Шаблони для сторіз: як зробити, щоб не виглядало шаблонно",
    "Помилки при роботі з брифом і як їх уникати",
    "Фотобанк vs. AI-генерація: де межа",
    "Створення moodboard: інструменти та структура",
    "Клікбейтні заголовки без токсичності: приклади",
    "Типографіка для кирилиці: підводні камені",
    "Побудова модульних сіток під різні банерні формати",
]

def kyiv_now():
    return dt.datetime.now(KYIV_TZ)

def kyiv_now_hhmm():
    return kyiv_now().strftime("%H:%M")

def kyiv_today_str():
    return kyiv_now().strftime("%Y-%m-%d")

def pick_image_slots_for_today():
    # Deterministic 3 slots each day based on date seed
    today = kyiv_today_str()
    rnd = random.Random(today)  # seed by date
    slots = SCHEDULE.copy()
    rnd.shuffle(slots)
    return set(slots[:IMAGES_PER_DAY])

def build_text_prompt(direction):
    return f"""
Ти — експерт з графічного дизайну та креативів. Напиши україномовний пост у дружньому тоні з легким гумором (без перебору) на тему: "{direction}".
Вимоги:
- 90–160 слів.
- 2–6 доречних емодзі у тексті.
- Можна інколи клікбейтний заголовок на першому рядку (короткий і чіпкий), потім — текст.
- Дай 1–3 практичні поради або міні-алгоритм.
- Без токсичності/жаргону. Користь і приклади.
Форматуй абзацами.
""".strip()

def generate_text():
    direction = random.choice(TOPIC_DIRECTIONS)
    prompt = build_text_prompt(direction)
    try:
        resp = client().chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role":"user","content":prompt}],
            temperature=0.8,
        )
        content = resp.choices[0].message.content.strip()
        return content, direction
    except Exception as e:
        print("❌ OpenAI text error:", e, flush=True)
        # fallback plain text to keep posting
        fallback = f"🎨 Швидка порада: тримай композицію чистою, а CTA — помітним. Вирівнюй за сіткою, давай повітря головним елементам і тестуй дві версії копірайту. 😉"
        return fallback, direction

def build_image_prompt(direction, text):
    # Short English prompt, no text overlay
    return (
        "Minimalist clean flat illustration, modern product design style, "
        "subtle gradients, soft lighting, crisp edges, no text overlay. "
        f"Theme: {direction}. Visualize the design tip idea in a friendly way."
    )

def generate_image_bytes(direction, text):
    try:
        img_prompt = build_image_prompt(direction, text)
        resp = client().images.generate(
            model=IMAGE_MODEL,
            prompt=img_prompt,
            size="512x512",
            n=1,
            response_format="b64_json",
        )
        b64 = resp.data[0].b64_json
        return base64.b64decode(b64)
    except Exception as e:
        print("⚠️ OpenAI image error (will send text only):", e, flush=True)
        return None

def send_text(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHANNEL_ID, "text": text, "parse_mode": "HTML"}
    r = requests.post(url, data=data, timeout=60)
    if not r.ok:
        raise RuntimeError(f"Telegram error: {r.status_code} {r.text}")

def send_photo_with_caption(image_bytes, caption):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    files = {"photo": ("img.png", image_bytes, "image/png")}
    data = {"chat_id": CHANNEL_ID, "caption": caption, "parse_mode": "HTML"}
    r = requests.post(url, data=data, files=files, timeout=60)
    if not r.ok:
        raise RuntimeError(f"Telegram error: {r.status_code} {r.text}")

def post_once(force_with_image=None):
    text, direction = generate_text()
    image_bytes = None
    if force_with_image:
        image_bytes = generate_image_bytes(direction, text)
    if image_bytes:
        send_photo_with_caption(image_bytes, text)
    else:
        send_text(text)

def main():
    if not BOT_TOKEN or not CHANNEL_ID or not OPENAI_KEY:
        print("❌ Missing env vars. Need BOT_TOKEN, CHANNEL_ID, OPENAI_KEY", flush=True)
        return

    print("🟢 TG autoposter started (MIX 3/5 with images 512). Timezone: Europe/Kyiv", flush=True)
    print("⏰ Schedule:", SCHEDULE, flush=True)
    print("📣 Channel:", CHANNEL_ID, flush=True)

    # Determine today's image slots
    img_slots = pick_image_slots_for_today()
    print("🖼️ Image slots today:", sorted(img_slots), flush=True)

    # Instant test post if requested
    if RUN_NOW:
        print("🚀 RUN_NOW=1 — sending a test post now...", flush=True)
        try:
            # For the test, send with image to verify pipeline
            post_once(force_with_image=True)
            print("✅ Test post sent", flush=True)
        except Exception as e:
            print("❌ Test post failed:", e, flush=True)
        time.sleep(2)

    posted_slots = set()
    while True:
        try:
            now_hhmm = kyiv_now_hhmm()
            today = kyiv_today_str()
            slot_id = f"{today} {now_hhmm}"

            if now_hhmm in SCHEDULE and slot_id not in posted_slots:
                with_image = now_hhmm in img_slots
                print(f"[{slot_id}] Posting... with_image={with_image}", flush=True)
                text, direction = generate_text()
                image_bytes = generate_image_bytes(direction, text) if with_image else None
                if image_bytes:
                    send_photo_with_caption(image_bytes, text)
                else:
                    send_text(text)
                posted_slots.add(slot_id)
                print(f"[{slot_id}] Posted ✅", flush=True)
                time.sleep(65)
            else:
                time.sleep(5)
        except Exception as e:
            print("⚠️ Loop error:", e, flush=True)
            time.sleep(15)

def kyiv_now_hhmm():
    return dt.datetime.now(KYIV_TZ).strftime("%H:%M")

def kyiv_today_str():
    return dt.datetime.now(KYIV_TZ).strftime("%Y-%m-%d")

if __name__ == "__main__":
    main()
