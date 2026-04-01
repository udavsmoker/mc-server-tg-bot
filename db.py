import json
import os

DB_FILE = 'users.json'

def load_users():
    if not os.path.exists(DB_FILE):
        return {}
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def save_users(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_user_lang(user_id: int) -> str:
    data = load_users()
    return data.get(str(user_id), None)

def set_user_lang(user_id: int, lang: str):
    data = load_users()
    data[str(user_id)] = lang
    save_users(data)
