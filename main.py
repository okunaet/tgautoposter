import os, time, random, re, html, datetime as dt, requests
# ---- TZ: Kyiv ----
try:
    from zoneinfo import ZoneInfo
    KYIV = ZoneInfo("Europe/Kyiv")
except Exception:
    from datetime import timezone, timedelta
    KYIV = timezone(timedelta(hours=3))

# ---- Env (подхватывает старые и новые имена) ----
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID") or os.getenv("CHANNEL_ID")
OPENAI_KEY = os.getenv("OPENAI_KEY") or os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")

if not BOT_TOKEN or not CHANNEL_ID:
    raise RuntimeError("Missing env: set TELEGRAM_BOT_TOKEN/BOT_TOKEN и TELEGRAM_CHANNEL_ID/CHANNEL_ID")
if not OPENAI_KEY:
    raise RuntimeError("Missing env: set OPENAI_KEY (OpenAI API key)")

from openai import OpenAI
client = OpenAI(api_key=OPENAI_KEY)

# ---- Markdown -> HTML для Telegram ----
def md_to_html(s: str) -> str:
    s = s.strip()
    s = html.escape(s)
    s = re.sub(r'(?m)^\s*#{1,6}\s+', '', s)          # убираем ### заголовки
    s = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)    # **bold**
    s = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<i>\1</i>', s)  # *italic*
    s = re.sub(r'_(.+?)_', r'<i>\1</i>', s)          # _italic_
    return s

def send_text(text: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHANNEL_ID, "text": md_to_html(text), "parse_mode": "HTML"}
    r = requests.post(url, data=data, timeout=60)
    if not r.ok:
        raise RuntimeError(f"Telegram error: {r.status_code} {r.text}")

# ---- Тематические направления (30+) ----
TOPICS = [
    "Поради з Photoshop для рекламних банерів",
    "Добірки безкоштовних шрифтів для комерційних проєктів",
    "Лайфхаки Figma для швидкого прототипування",
    "Композиція та ієрархія у креативах",
    "Кольорові схеми, контраст, акценти",
    "Типові помилки дизайнерів-початківців і як їх уникати",
    "Сітки, модульність та 8pt-система",
    "Відступи, ритм, baseline grid",
    "Шрифтові пари: Sans + Serif для кирилиці",
    "Експорт зображень для соцмереж без артефактів",
    "CTA і мікрокопі: як зробити клікабельним",
    "Трендові стилі: плоска графіка, градієнти, glass",
    "Мікроанімації та швидкі прототипи",
    "Компоненти/варіанти/токени у Figma",
    "Єдина система іконок: сітка, товщина лінії, оптика",
    "UX-тексти і співпраця з копірайтером",
    "Пошук референсів і побудова moodboard",
    "Гарячі клавіші у Photoshop/Illustrator",
    "Чеклист перед здачею макета",
    "Айдентика малого бізнесу: що достатньо зробити",
    "Оптимізація фону і зниження «візуального шуму»",
    "CRAP-принципи: близькість, вирівнювання, повторення, контраст",
    "Заголовки/підзаголовки: модульна шкала",
    "Швидкі A/B тести креативів",
    "Баланс бренду та перформансу",
    "Сторіз-шаблони без «шаблонності»",
    "Типографіка для кирилиці: підводні камені",
    "Модульні сітки під банерні формати",
    "Фотобанк vs AI-генерація: юридичні нюанси",
    "Оптимізація файлів: PNG/JPG/WEBP/SVG",
    "Клікбейтні заголовки без токсичності: приклади",
]

def build_prompt():
    direction = random.choice(TOPICS)
    return f"""
Ти — експерт з графічного дизайну. Напиши пост українською на тему: "{direction}".
Вимоги:
- 90–150 слів. Дружній тон, трішки гумору без перегину.
- 2–6 доречних емодзі в тексті.
- Дозволено короткий клікбейтний заголовок у першому рядку, потім — зміст.
- Дай 1–3 практичні поради або міні-алгоритм.
- Жодної токсичності, максимум користі. Форматуй абзацами.
""".strip()

def generate_post_text():
    try:
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": build_prompt()}],
            temperature=0.9,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        # Фолбек, якщо API тимчасово не відповідає
        return ("🎨 Швидка порада: не перевантажуй макет. "
                "Виділи один головний акцент, дай повітря навколо CTA і перевір читабельність на мобільному. 😉")

def sleep_until_next_15min():
    now = dt.datetime.now(KYIV)
    # следующая граница: 0,15,30,45
    minute = (now.minute // 15 + 1) * 15
    next_slot = now.replace(second=0, microsecond=0)
    if minute >= 60:
        next_slot = next_slot.replace(minute=0) + dt.timedelta(hours=1)
    else:
        next_slot = next_slot.replace(minute=minute)
    delay = (next_slot - now).total_seconds()
    if delay < 1: delay = 1
    time.sleep(delay)

def main():
    print("🟢 15-min autoposter started. TZ: Europe/Kyiv", flush=True)
    posted_slots = set()
    while True:
        try:
            # Ждём следующую 15-минутку
            sleep_until_next_15min()
            now = dt.datetime.now(KYIV).strftime("%Y-%m-%d %H:%M")
            if now in posted_slots:
                continue
            text = generate_post_text()
            send_text(text)
            posted_slots.add(now)
            print(f"[{now}] Posted ✅", flush=True)
        except Exception as e:
            print("⚠️ Error:", e, flush=True)
            time.sleep(10)

if __name__ == "__main__":
    main()
