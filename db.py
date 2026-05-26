import json
import os
from typing import Dict, Any

DB_FILE = 'users.json'

def load_users() -> Dict[str, Dict[str, Any]]:
    if not os.path.exists(DB_FILE):
        return {}
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError:
        data = {}

    # Auto-migration of legacy users.json format (bare lang string -> dictionary)
    migrated = False
    for uid, val in data.items():
        if isinstance(val, str):
            data[uid] = {"lang": val, "last_server": None}
            migrated = True
        elif isinstance(val, dict):
            # Ensure keys exist
            if "lang" not in val:
                val["lang"] = "en"
                migrated = True
            if "last_server" not in val:
                val["last_server"] = None
                migrated = True
            
    if migrated:
        save_users(data)
        
    return data

def save_users(data: Dict[str, Dict[str, Any]]):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_user_lang(user_id: int) -> str:
    data = load_users()
    user_data = data.get(str(user_id))
    return user_data.get("lang") if user_data else None

def set_user_lang(user_id: int, lang: str):
    data = load_users()
    uid_str = str(user_id)
    if uid_str not in data:
        data[uid_str] = {"lang": lang, "last_server": None}
    else:
        data[uid_str]["lang"] = lang
    save_users(data)

def get_last_server(user_id: int) -> str:
    data = load_users()
    user_data = data.get(str(user_id))
    return user_data.get("last_server") if user_data else None

def set_last_server(user_id: int, server_id: str):
    data = load_users()
    uid_str = str(user_id)
    if uid_str not in data:
        data[uid_str] = {"lang": "en", "last_server": server_id}
    else:
        data[uid_str]["last_server"] = server_id
    save_users(data)
