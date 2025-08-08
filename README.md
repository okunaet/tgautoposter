# Telegram Autoposter — MIX (3/5 images) — 1024 size

Причина, чому не йшли картинки: `gpt-image-1` підтримує розміри **1024x1024, 1024x1536, 1536x1024** або `auto`. 512x512 не приймається, тому була помилка 400.

Ця версія ставить `IMAGE_SIZE=1024x1024` (за замовчуванням). Можна змінити через змінну оточення `IMAGE_SIZE` на інші підтримувані.

## Variables
- `BOT_TOKEN`, `CHANNEL_ID`, `OPENAI_KEY`
- (опц.) `MODEL_NAME`, `IMAGE_MODEL`, `IMAGE_SIZE`

Start command: `python -u main.py`