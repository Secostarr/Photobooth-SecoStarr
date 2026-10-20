"""Settings JSON persisten (stdlib). Tetap kompatibel Windows."""
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE, "config", "settings.json")

DEFAULTS = {
    "default_camera": 0,
    "default_filter": "Normal",
    "default_layout": "Strip Vert",
    "default_photo_count": 4,
    "default_countdown": 3,
    "default_save_format": "png",
    "output_folder": "photos",
    "auto_save": False,
    "auto_open_preview": True,
    "sound_effect": False,
    "flash_effect": True,
    "fullscreen": True,
    "admin_pin": "1234",
}


def load_settings(path=CONFIG_PATH):
    data = dict(DEFAULTS)
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                user = json.load(f)
            for k in DEFAULTS:
                if k in user:
                    data[k] = user[k]
    except Exception:
        pass
    return data


def save_settings(data, path=CONFIG_PATH):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        merged = dict(DEFAULTS)
        merged.update(data or {})
        with open(path, "w", encoding="utf-8") as f:
            json.dump(merged, f, indent=2)
        return True
    except Exception:
        return False
