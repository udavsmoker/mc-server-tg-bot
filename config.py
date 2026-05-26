import os
import yaml
from pathlib import Path
from dotenv import load_dotenv
from models import AppConfig, BotConfig

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
_admin_ids_str = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(x.strip()) for x in _admin_ids_str.split(",") if x.strip().isdigit()]

YAML_PATH = "servers.yaml"

def auto_migrate_env_to_yaml():
    """Migrates legacy single-server environment variables to servers.yaml if it doesn't exist."""
    if Path(YAML_PATH).exists():
        return

    rcon_host = os.getenv("RCON_HOST")
    if not rcon_host:
        return  # No legacy config to migrate

    rcon_port = int(os.getenv("RCON_PORT", "25575"))
    rcon_password = os.getenv("RCON_PASSWORD", "")
    server_path = os.getenv("SERVER_PATH", "/home/minecraft/server")
    screen_session = os.getenv("SCREEN_SESSION_NAME", "mc_server")
    
    # Generate a local migration config
    server_config = {
        "servers": {
            "default": {
                "display_name": "⛏️ Minecraft Server",
                "local": {
                    "server_path": server_path,
                    "screen_session": screen_session
                },
                "rcon": {
                    "host": rcon_host,
                    "port": rcon_port,
                    "password": rcon_password
                },
                "game_port": 25565
            }
        }
    }

    try:
        with open(YAML_PATH, "w", encoding="utf-8") as f:
            yaml.dump(server_config, f, default_flow_style=False, allow_unicode=True)
        print(f"✅ Auto-migrated legacy single-server configuration to {YAML_PATH}")
    except Exception as e:
        print(f"❌ Failed to auto-migrate legacy config: {e}")

def load_config() -> AppConfig:
    auto_migrate_env_to_yaml()
    
    if not Path(YAML_PATH).exists():
        return AppConfig(
            bot=BotConfig(bot_token=BOT_TOKEN, admin_ids=ADMIN_IDS),
            servers={}
        )

    with open(YAML_PATH, "r", encoding="utf-8") as f:
        yaml_data = yaml.safe_load(f) or {}

    servers_dict = yaml_data.get("servers", {})
    
    return AppConfig(
        bot=BotConfig(bot_token=BOT_TOKEN, admin_ids=ADMIN_IDS),
        servers=servers_dict
    )

# Load configuration at import time
app_config = load_config()
SERVERS = app_config.servers
