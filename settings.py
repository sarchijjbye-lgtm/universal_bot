# settings.py

import time
from google_sheets import connect_to_sheet

SETTINGS_CACHE = None
SETTINGS_TS = 0
SETTINGS_TTL = 60  # обновлять раз в минуту


def load_settings():
    global SETTINGS_CACHE, SETTINGS_TS

    now = time.time()
    if SETTINGS_CACHE and now - SETTINGS_TS < SETTINGS_TTL:
        return SETTINGS_CACHE

    sheet = connect_to_sheet("Settings")
    data = sheet.get_all_records()

    settings = {row["key"]: row["value"] for row in data}

    SETTINGS_CACHE = settings
    SETTINGS_TS = now
    return settings


def get_setting(key: str, default=""):
    settings = load_settings()
    return settings.get(key, default)
