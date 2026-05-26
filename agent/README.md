# MC Server TG Bot - Remote Agent 🌐

This is a lightweight agent designed to run on your Minecraft server machine. It communicates with the main Telegram bot over HTTP to provide server lifecycle management (starting, status monitoring, log reading) without requiring SSH access or passwords.

> [!NOTE]
> This remote agent is **ONLY required for remote Minecraft servers** (running on separate machines). If your Minecraft server and the Telegram bot are running on the **same machine**, you can skip this agent entirely and configure the bot to use **Local Direct Management** (agentless mode) instead.

---

## 🛠 Deployment & Setup

Follow these steps on each Minecraft server machine you want to manage.

### 1. Place the Agent Script
Create a directory for the agent and place the `mc_agent.py` script inside it:
```bash
mkdir -p /opt/mc/agent
cd /opt/mc/agent
# Copy mc_agent.py to this directory
```

### 2. Install Dependencies
The agent only needs `aiohttp`. You can install it globally or in a virtual environment:
```bash
pip3 install aiohttp
```

### 3. Run Manually (Testing)
Test the agent by running it from the command line:
```bash
python3 mc_agent.py \
  --port 8745 \
  --api-key "YOUR_CHOSEN_API_KEY" \
  --server-path "/path/to/minecraft/server" \
  --start-script "startserver.sh" \
  --screen-session "mc_survival"
```

#### 💡 Configuration Details:
- **`--server-path`**: The absolute path to the directory containing your Minecraft server files.
  - The agent uses this directory to `cd` into before running your start script.
  - The agent reads logs from `{server-path}/logs/latest.log`.
- **`--start-script`** *(Optional, default: `start.sh`)*: The script inside the server directory used to launch your server.
  - If your script has a custom name or spaces (like `start server.sh` or `run.sh`), specify it here!
  - The agent will automatically run it as `./"start server.sh"` in the screen session.
- **`--screen-session`**: The name of the `screen` session to run the Minecraft server inside.

Verify that the agent works using `curl` from another shell or machine:
```bash
curl -H "X-API-Key: YOUR_CHOSEN_API_KEY" http://127.0.0.1:8745/status
# Expected: {"running": false, "screen_session": "mc_survival"}
```

---

## 🤖 Running as a Systemd Service

To keep the agent running automatically in the background and start on system boot:

1. Copy the systemd service template `mc_agent.service` to `/etc/systemd/system/`:
   ```bash
   sudo cp mc_agent.service /etc/systemd/system/mc-agent.service
   ```
2. Edit the service file and fill in your values (User, port, api-key, server-path, screen-session):
   ```bash
   sudo nano /etc/systemd/system/mc-agent.service
   ```
3. Reload systemd, enable the service, and start it:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable mc-agent
   sudo systemctl start mc-agent
   ```
4. Verify the status:
   ```bash
   sudo systemctl status mc-agent
   ```

---

## 🔒 Security Recommendations

- **Firewall Rules**: Use `ufw` or `iptables` to block the agent port (default `8745`) from public access. Only allow traffic from the machine running the Telegram Bot.
  ```bash
  sudo ufw allow from BOT_SERVER_IP to any port 8745 proto tcp
  ```
- **Strong API Key**: Use a long, random string (e.g., `openssl rand -hex 24`) for the `--api-key`.
- **Run as Unprivileged User**: Set `User=minecraft` (or your dedicated mc user) in the systemd service. **Never** run the agent as `root`.
