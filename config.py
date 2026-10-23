import os
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "subscriptions.db"

BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Настройки по умолчанию
DEFAULT_CURRENCY = "₽"
DEFAULT_NOTIFY_HOUR = 10  # 10:00 утра
DEFAULT_TIMEZONE = "Europe/Moscow"
