# Telegram Autoposter — MIX (3/5 images 512) — PATCHED

Фікси:
- Вилучено параметр `response_format` (у деяких версіях API викликає 400 Unknown parameter).
- Додано конвертацію Markdown → HTML (прибирає ** та ### у Telegram).
- Змінна `FORCE_IMAGES=1` для примусової відправки зображень під час тесту.

## Variables
- `BOT_TOKEN`, `CHANNEL_ID`, `OPENAI_KEY`
- (опц.) `RUN_NOW=1` — тестовий пост одразу
- (опц.) `FORCE_IMAGES=1` — примусові зображення

Start command: `python -u main.py`