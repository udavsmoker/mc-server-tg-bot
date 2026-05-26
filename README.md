# MC Server TG Bot - Multi-Server Minecraft Manager 🤖⛏️

A beautiful, premium Telegram bot built with Python (`aiogram 3`) that allows managing multiple Minecraft servers simultaneously from a single bot instance. It supports both local servers (running on the same machine as the bot via agentless direct OS integration) and remote servers (running on separate machines via a secure, lightweight HTTP agent).

---

## ✨ Features

- **Multi-Server Support** — Manage any number of servers using a simple YAML registry.
- **Flexible Management Modes** — Supports both **Local Direct Mode** (direct `screen` and file log management for servers on the same machine) and **Remote Agent Mode** (via lightweight HTTP agent for remote servers).
- **Hybrid Networks** — Manage a combination of local and remote servers seamlessly within the same bot.
- **Smart Restart** — Automates the full restart cycle: stops gracefully via RCON, monitors process shutdown, starts process, and waits for RCON readiness with live progress updates.
- **Console RCON** — Send any custom Minecraft console command and get the output directly in Telegram.
- **Bilingual Interface** — English and Russian localizations included, switchable via `/lang`.
- **Admin Security Whitelist** — Admin access controlled by Telegram IDs.

---

## 🛠 Architecture & Management Modes

The bot operates in two modes depending on your setup:

1. **Local Direct Management (Agentless)** — For Minecraft servers running on the **same machine** as the Telegram bot. The bot controls local server screens directly and reads log files from disk. No agent setup or extra processes are required.
2. **Remote Agent Management (Agent-based)** — For Minecraft servers running on **separate machines**. A lightweight HTTP agent (`mc_agent.py`) is deployed on the server machines. The bot communicates with the agents over secure HTTP endpoints to start servers, fetch logs, and monitor status.

---

## 🚀 1. MC Server Preparation

Regardless of whether the Minecraft server is local or remote, you must configure RCON:

1. Open `server.properties` in your Minecraft server directory and enable RCON:
   ```properties
   enable-rcon=true
   rcon.password=SUPER_SECURE_PASSWORD
   rcon.port=25575
   ```
2. Restart the Minecraft server normally to apply settings.

### Case A: Minecraft Server is on the SAME Machine as the Bot (Local)
* No extra software needed! Simply write down your server folder's absolute path and the name of the screen session you run Minecraft in.

### Case B: Minecraft Server is on a DIFFERENT Machine (Remote)
1. Deploy the agent on the remote Minecraft machine:
   ```bash
   mkdir -p /opt/mc/agent
   # Copy the agent files (agent/mc_agent.py, agent/mc_agent.service) to this directory
   cd /opt/mc/agent
   pip3 install aiohttp
   ```
2. Copy `mc_agent.service` to `/etc/systemd/system/mc-agent.service`, configure it with your paths, ports, and a secure API key, and start it:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable mc-agent
   sudo systemctl start mc-agent
   ```
   > [!NOTE]
   > Detailed agent configuration and systemd templates are located in the [agent documentation](file:///Users/udavsmoker/stuff/git/mc-server-tg-bot/agent/README.md).

---

## 🤖 2. Telegram Bot Installation & Configuration

### A. Prerequisites (Venv Setup)
```bash
# Clone the repository and navigate into it
cd mc-server-tg-bot

# Set up virtual environment and install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### B. Configuration Files

#### 1. `.env` (Bot credentials)
Rename `.env.example` to `.env` and fill in bot token and admin whitelists:
```env
BOT_TOKEN=1234567890:AA...               # Telegram Bot Token from @BotFather
ADMIN_IDS=123456,987654                  # Comma-separated Telegram user IDs
```

#### 2. `servers.yaml` (Servers Registry)
Rename `servers.yaml.example` to `servers.yaml` and configure your Minecraft servers. You can define local servers (agentless) or remote servers (agent-based) in any combination:

```yaml
servers:
  # ── Example 1: Local Server (Runs on the same machine as the bot) ───────────────────────────
  survival:
    display_name: "⛏️ Survival (Local)"
    local:
      server_path: "/home/minecraft/survival"   # Folder where Minecraft lives
      screen_session: "mc_survival"             # Name of the screen session it runs in
    rcon:
      host: "127.0.0.1"
      port: 25575
      password: "your_rcon_password"
    game_port: 25565

  # ── Example 2: Remote Server (Runs on a different machine) ──────────────────────────────────
  creative:
    display_name: "🎨 Creative (Remote)"
    agent:
      url: "http://192.168.1.20:8745"           # URL of the remote mc_agent.py
      api_key: "agent_api_secret_key_2"          # API key secret of the remote agent
    rcon:
      host: "192.168.1.20"
      port: 25576
      password: "another_rcon_password"
    game_port: 25566
```

---

## 🏃 Running the Bot

Start the main Telegram bot runner:
```bash
source venv/bin/activate
python main.py
```

To run the bot persistently in the background, you can deploy it in a screen session or set up a systemd service:
```bash
screen -dmS mc_bot_runner bash -c "cd /path/to/mc-server-tg-bot && source venv/bin/activate && python main.py"
```

---

## 📖 Telegram Commands & UX

- `/start` or `/menu` — Open the main interactive control panel.
- `/servers` — View a status summary of all configured servers at a glance.
- `/switch` — Open the server picker inline keyboard to switch the active server (hidden in single-server setups).
- `/lang` — Toggle language selection (RU/EN).
- `/status` — Quickly check status of the active server process and RCON connection.
- `/help` — View this help menu.

---

## 🔒 Security Best Practices

1. **Firewall Access**: Protect agent port `8745` and RCON port `25575` on the Minecraft servers. Configure your firewall to ONLY allow incoming TCP traffic on these ports from the Telegram Bot machine's IP.
2. **API Keys**: Ensure `api_key` in `servers.yaml` is a long, cryptographically strong random string.
3. **Unprivileged Users**: **Never** run the Telegram bot or the remote agent as `root`. Run them as standard dedicated system users (e.g., `minecraft`).
