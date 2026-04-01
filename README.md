# MC Server TG Bot - Minecraft Server Manager 🤖⛏️

A sleek Telegram bot for managing your Minecraft Server (Purpur, Paper, Spigot, Vanilla, etc.) via convenient inline buttons. Built with Python (`aiogram 3`) to control the server using RCON and the `screen` utility.

## Features
- **Start / Stop** — Launch the server within an isolated `screen` session and gracefully stop it via direct commands.
- **Monitoring** — Check online status and view the latest logs straight from `latest.log`.
- **Game Management** — Change weather and time of day in 1 click.
- **RCON Console** — Execute any Minecraft command directly from Telegram and get the response back.
- **Bilingual Interface** — English and Russian localizations included. Switch anytime with `/lang`.

---

## 🛠 Minecraft Server Preparation

1. Open the `server.properties` file located in your minecraft server folder.
2. Enable RCON and set up a secure password:
   ```properties
   enable-rcon=true
   rcon.password=SUPER_SECRET_PASSWORD
   rcon.port=25575
   ```
3. Save the file and **restart** your Minecraft server normally to apply these changes.
4. Ensure you have the `screen` package installed on your machine (`sudo apt install screen`).

---

## 🚀 Installation & Setup

### 1. Preparation (venv)
It is highly recommended to run the bot in a virtual environment:

```bash
# Clone or move to the bot directory
cd /path/to/mc-server-tg-bot

# Create a virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Bot Configuration
Rename or copy `.env.example` to `.env` and fill in your details:
```bash
cp .env.example .env
nano .env
```

```env
BOT_TOKEN=1234567890:AA...               # Your bot token from @BotFather
ADMIN_IDS=123456,987654                  # Comma-separated Telegram IDs (permitted users)
RCON_HOST=127.0.0.1                      # Default is usually fine
RCON_PORT=25575                          # RCON port from server.properties
RCON_PASSWORD=SUPER_SECRET_PASSWORD      # RCON password from server.properties
SERVER_PATH=/path/to/your/server         # Directory containing start.sh
SCREEN_SESSION_NAME=mc_server            # Name of the screen session to use
```

### 4. Running the Bot
While inside the activated environment (you should see `(venv)` in your terminal), run:
```bash
python main.py
```
*The bot is now up and running! Message it `/menu` in Telegram.*

### Bonus: Background Execution
If you want to keep the bot running after closing the terminal, you can run it inside its own screen session (or set up a systemd service):
```bash
screen -dmS mc_server_tg_bot_runner bash -c "cd /path/to/mc-server-tg-bot && source venv/bin/activate && python main.py"
```
