import asyncio
from mcrcon import MCRcon
import config
import logging
import re

class ServerManager:
    is_busy = False

    @staticmethod
    async def run_command(command: str) -> str:
        """Sends a command to the server via RCON"""
        try:
            # mcrcon triggers signal internally, which fails in asyncio.to_thread
            # So we run it synchronously in the main thread (blocking for ms is fine)
            with MCRcon(config.RCON_HOST, config.RCON_PASSWORD, config.RCON_PORT) as mcr:
                response = mcr.command(command)
                if response:
                    # Strip color codes like §c or §4 returned by the server
                    response = re.sub(r'§[0-9a-fk-orA-FK-OR]', '', response)
                return response if response else "Command executed (no output)"
        except Exception as e:
            logging.error(f"RCON Error: {e}")
            return f"❌ RCON Error (server off or not configured?): {e}"

    @staticmethod
    async def is_rcon_alive() -> bool:
        """Checks if RCON port is accessible (server fully booted)"""
        def _check():
            import socket
            try:
                # Simple port check (takes milliseconds)
                with socket.create_connection((config.RCON_HOST, config.RCON_PORT), timeout=2):
                    return True
            except Exception:
                return False
        return await asyncio.to_thread(_check)

    @staticmethod
    async def is_running() -> bool:
        """Checks if server is running (screen session is alive)"""
        process = await asyncio.create_subprocess_shell(
            f"screen -list | grep -q '\\.{config.SCREEN_SESSION_NAME}\\b'",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()
        return process.returncode == 0

    @staticmethod
    async def start_server() -> bool:
        """Starts the server in background via screen"""
        if await ServerManager.is_running():
            return False  # Already running
            
        cmd = f"cd {config.SERVER_PATH} && screen -dmS {config.SCREEN_SESSION_NAME} ./start.sh"
        process = await asyncio.create_subprocess_shell(cmd)
        await process.communicate()
        return process.returncode == 0

    @staticmethod
    async def stop_server() -> str:
        """Stops the server gracefully via RCON"""
        if not await ServerManager.is_running():
            return "❌ Server is already off."
            
        response = await ServerManager.run_command("stop")
        return f"Stop command sent... Response: {response}"

    @staticmethod
    async def get_logs(lines: int = 20) -> str:
        """Returns the last lines of the log"""
        log_path = f"{config.SERVER_PATH}/logs/latest.log"
        try:
            process = await asyncio.create_subprocess_shell(
                f"tail -n {lines} {log_path}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await process.communicate()
            return stdout.decode('utf-8')[-4000:] # Protect against Telegram message limits (4096 chars)
        except Exception as e:
            return f"❌ Error reading logs: {e}"
