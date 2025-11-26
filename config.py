# config.py
"""
Konfiguratsiya fayli - barcha muhim sozlamalar
"""

from environs import Env


env = Env()
env.read_env()

BOT_TOKEN = env.str("BOT_TOKEN")
ADMIN = env.int("ADMIN")
DATABASE_NAME = env.str("DATABASE_NAME")
ADMIN_PHONES = env.list("ADMIN_PHONES")
GROUP_LINKS = env.list("GROUP_LINKS")


# Vaqt zonasi
TIMEZONE = "Asia/Tashkent"

# Kunlar nomlari (o'zbekcha)
WEEKDAYS = {
    0: "Dushanba",
    1: "Seshanba", 
    2: "Chorshanba",
    3: "Payshanba",
    4: "Juma",
    5: "Shanba",
    6: "Yakshanba"
}

# Oylar nomlari (o'zbekcha)
MONTHS = {
    1: "Yanvar",
    2: "Fevral",
    3: "Mart",
    4: "Aprel",
    5: "May",
    6: "Iyun",
    7: "Iyul",
    8: "Avgust",
    9: "Sentabr",
    10: "Oktabr",
    11: "Noyabr",
    12: "Dekabr"
}

# Vazifa turlari
TASK_TYPES = {
    "daily": "🔴 HAR KUNLIK",
    "monday": "🔵 HAR DUSHANBA", 
    "monthly": "🟢 HAR OY"
}

# Statistika emoji
STATUS_EMOJI = {
    100: "✅",  # 100%
    80: "✅",   # 80-99%
    50: "⚠️",  # 50-79%
    0: "❌"    # 0-49%
}