import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))  # project root

SETTINGS_PATH = os.path.join(BASE_DIR, "settings.json")
LOCATIONS_PATH = os.path.join(BASE_DIR, "store_locations.json")

DEFAULT_SETTINGS = {
    "auth_token": "",
    "cooldown_seconds": 2.5
}

DEFAULT_LOCATIONS = {
    "Kermanshah - Anahita": [34.389775, 47.087308],
    # ... (you can keep the full list from above,
    # or load from the file if you create it manually)
}


def load_json(filepath, default=None):
    if not os.path.exists(filepath):
        if default is not None:
            save_json(filepath, default)
        return default
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(filepath, data):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def load_settings():
    return load_json(SETTINGS_PATH, DEFAULT_SETTINGS)


def save_settings(data):
    save_json(SETTINGS_PATH, data)


def load_store_locations():
    # If you prefer to always use the file, do not embed the default here.
    # Instead, you can raise an error if the file is missing.
    # I'll provide a fallback to a static dict (copy from above) only as a last resort.
    if not os.path.exists(LOCATIONS_PATH):
        # Provide a minimal default or raise FileNotFoundError.
        # For safety, create the file with the full list from the hardcoded LOCATIONS.
        # Here I'll just raise an error to ensure the user creates it.
        raise FileNotFoundError(
            f"{LOCATIONS_PATH} not found. Please create it with store locations."
        )
    return load_json(LOCATIONS_PATH)
