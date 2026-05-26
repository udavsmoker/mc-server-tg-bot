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

### Option A: Single Server (Simple Setup)
To keep a single agent running automatically in the background:

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

### Option B: Multiple Servers on One Machine (Template Setup) 🚀
If you want to run **multiple separate servers** on the same machine, instead of copying the service file multiple times, use the **systemd template unit** `mc-agent@.service`:

1. Copy the template service file to `/etc/systemd/system/`:
   ```bash
   sudo cp mc-agent@.service /etc/systemd/system/mc-agent@.service
   ```
2. Create a configuration directory:
   ```bash
   sudo mkdir -p /etc/mc-agent
   ```
3. Create a configuration `.env` file for **each** server. For example, for a server named `survival`, create `/etc/mc-agent/survival.env`:
   ```bash
   sudo nano /etc/mc-agent/survival.env
   ```
   Fill it with the environment variables for that server instance:
   ```env
   MC_AGENT_PORT=8745
   MC_AGENT_API_KEY=YOUR_SECURE_API_KEY_1
   MC_AGENT_SERVER_PATH=/opt/minecraft/survival
   MC_AGENT_START_SCRIPT=startserver.sh
   MC_AGENT_SCREEN_SESSION=mc_survival
   ```
4. Create another config for your second server, e.g., `/etc/mc-agent/creative.env` (using a **different port** like `8746` and its own path/screen name).
5. Reload systemd, then you can manage each server dynamically using the `@` syntax:
   ```bash
   sudo systemctl daemon-reload

   # Start and enable the survival agent
   sudo systemctl enable mc-agent@survival
   sudo systemctl start mc-agent@survival

   # Start and enable the creative agent
   sudo systemctl enable mc-agent@creative
   sudo systemctl start mc-agent@creative
   ```
6. Check their individual statuses:
   ```bash
   sudo systemctl status mc-agent@survival
   sudo systemctl status mc-agent@creative
   ```


---

## 🔒 Security Recommendations

- **Firewall Rules**: Use `ufw` or `iptables` to block the agent port (default `8745`) from public access. Only allow traffic from the machine running the Telegram Bot.
  ```bash
  sudo ufw allow from BOT_SERVER_IP to any port 8745 proto tcp
  ```
- **Strong API Key**: Use a long, random string (e.g., `openssl rand -hex 24`) for the `--api-key`.
- **Run as Unprivileged User**: Set `User=minecraft` (or your dedicated mc user) in the systemd service. **Never** run the agent as `root`.
