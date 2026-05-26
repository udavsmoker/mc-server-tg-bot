import asyncio
import logging
import aiohttp
from pathlib import Path
from models import ServerConfig
from rcon_client import rcon_command, RconError

logger = logging.getLogger(__name__)

class ServerManager:
    def __init__(self, server_id: str, config: ServerConfig):
        self.server_id = server_id
        self.config = config
        self.is_local = config.local is not None
        self.lock = asyncio.Lock()  # Per-server startup/shutdown lock

    async def _agent_request(self, method: str, path: str, **kwargs) -> dict:
        """Helper to make authenticated HTTP requests to the server's agent (remote only)"""
        if self.is_local:
            raise RuntimeError("Cannot request remote agent on local server.")
            
        url = f"{self.config.agent.url.rstrip('/')}{path}"
        headers = {"X-API-Key": self.config.agent.api_key}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(method, url, headers=headers, timeout=5, **kwargs) as resp:
                    if resp.status == 403:
                        return {"ok": False, "error": "Invalid Agent API Key"}
                    resp.raise_for_status()
                    return await resp.json()
        except aiohttp.ClientError as e:
            logger.error(f"[{self.server_id}] Agent HTTP Error: {e}")
            return {"ok": False, "error": f"Agent connection error: {e}"}
        except Exception as e:
            logger.error(f"[{self.server_id}] Agent Error: {e}")
            return {"ok": False, "error": str(e)}

    async def run_command(self, command: str) -> str:
        """Sends a command to the server via RCON"""
        try:
            return await rcon_command(
                self.config.rcon.host,
                self.config.rcon.port,
                self.config.rcon.password,
                command
            )
        except RconError as e:
            logger.error(f"[{self.server_id}] RCON Error: {e}")
            return f"❌ RCON Error: {e}"
        except Exception as e:
            logger.error(f"[{self.server_id}] RCON Connection Exception: {e}")
            return f"❌ RCON Connection failed: {e}"

    async def is_rcon_alive(self) -> bool:
        """Checks if RCON port is accessible (server fully booted)"""
        def _check():
            import socket
            try:
                with socket.create_connection((self.config.rcon.host, self.config.rcon.port), timeout=2):
                    return True
            except Exception:
                return False
        return await asyncio.to_thread(_check)

    async def is_running(self) -> bool:
        """Checks if server process is running (via agent or local screen session)"""
        if self.is_local:
            try:
                proc = await asyncio.create_subprocess_shell(
                    f"screen -list | grep -q '\\.{self.config.local.screen_session}\\b'",
                    stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )
                await proc.communicate()
                return proc.returncode == 0
            except Exception as e:
                logger.error(f"[{self.server_id}] Local screen session check failed: {e}")
                return False
        else:
            resp = await self._agent_request("GET", "/status")
            return resp.get("running", False)

    async def start_server(self) -> bool:
        """Starts the server in background (locally or via remote agent)"""
        if self.is_local:
            try:
                cmd = f"cd {self.config.local.server_path} && screen -dmS {self.config.local.screen_session} ./start.sh"
                proc = await asyncio.create_subprocess_shell(
                    cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )
                await proc.communicate()
                return proc.returncode == 0
            except Exception as e:
                logger.error(f"[{self.server_id}] Local server start failed: {e}")
                return False
        else:
            resp = await self._agent_request("POST", "/start")
            return resp.get("ok", False)

    async def stop_server(self) -> str:
        """Stops the server gracefully via RCON"""
        if not await self.is_running():
            return "❌ Server is already off."
            
        response = await self.run_command("stop")
        return f"Stop command sent... Response: {response}"

    async def get_logs(self, lines: int = 20) -> str:
        """Returns the last lines of the log (locally or via remote agent)"""
        if self.is_local:
            log_path = Path(self.config.local.server_path) / "logs" / "latest.log"
            if not log_path.exists():
                return "❌ Local log file not found. Make sure server path is correct."
            
            try:
                def read_tail(path, n):
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        all_lines = f.readlines()
                        return "".join(all_lines[-n:])
                
                return await asyncio.to_thread(read_tail, log_path, lines)
            except Exception as e:
                logger.error(f"[{self.server_id}] Failed to read local log: {e}")
                return f"❌ Error reading local logs: {e}"
        else:
            resp = await self._agent_request("GET", f"/logs?lines={lines}")
            if "error" in resp:
                return f"❌ Error reading logs: {resp['error']}"
            return resp.get("logs", "No logs returned")

