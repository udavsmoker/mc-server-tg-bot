import argparse
import asyncio
import os
import sys
import shlex
from aiohttp import web

# Settings loaded at runtime
PORT = 8745
API_KEY = ""
SERVER_PATH = ""
SCREEN_SESSION = ""
START_SCRIPT = "start.sh"

async def check_auth(request):
    auth_key = request.headers.get("X-API-Key")
    if not auth_key or auth_key != API_KEY:
        raise web.HTTPForbidden(text="Access Denied: Invalid or missing X-API-Key")

async def get_status(request):
    await check_auth(request)
    
    # Check if screen session is running
    cmd = f"screen -list | grep -q '\\.{SCREEN_SESSION}\\b'"
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    await proc.communicate()
    is_running = proc.returncode == 0
    return web.json_response({"running": is_running, "screen_session": SCREEN_SESSION})

async def start_server(request):
    await check_auth(request)
    
    # Check if screen session is already active
    status_proc = await asyncio.create_subprocess_shell(
        f"screen -list | grep -q '\\.{SCREEN_SESSION}\\b'",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    await status_proc.communicate()
    if status_proc.returncode == 0:
        return web.json_response({"ok": False, "error": "Server already running"})

    # Launch server in background screen session
    quoted_path = shlex.quote(SERVER_PATH)
    quoted_session = shlex.quote(SCREEN_SESSION)
    
    # Prefix relative script names with ./ if they don't contain directory prefix already
    script_cmd = START_SCRIPT
    if not (script_cmd.startswith("/") or script_cmd.startswith("./") or script_cmd.startswith("../")):
        script_cmd = f"./{script_cmd}"
        
    quoted_script = shlex.quote(script_cmd)
    
    cmd = f"cd {quoted_path} && screen -dmS {quoted_session} {quoted_script}"
    proc = await asyncio.create_subprocess_shell(cmd)
    await proc.communicate()
    
    return web.json_response({"ok": proc.returncode == 0})

async def get_logs(request):
    await check_auth(request)
    try:
        lines = int(request.query.get("lines", "20"))
    except ValueError:
        lines = 20
    
    lines = min(max(1, lines), 200) # Cap to protect payload size
    
    log_path = os.path.join(SERVER_PATH, "logs", "latest.log")
    if not os.path.exists(log_path):
        return web.json_response({"logs": f"❌ Log file not found at: {log_path}"})
    
    # Read last N lines using tail
    quoted_log_path = shlex.quote(log_path)
    proc = await asyncio.create_subprocess_shell(
        f"tail -n {lines} {quoted_log_path}",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    
    if proc.returncode != 0:
        return web.json_response({"logs": f"❌ Failed to read logs: {stderr.decode('utf-8')}"})
        
    return web.json_response({"logs": stdout.decode('utf-8', errors='replace')})

async def ping(request):
    await check_auth(request)
    return web.json_response({"ok": True})

def main():
    global PORT, API_KEY, SERVER_PATH, SCREEN_SESSION, START_SCRIPT
    
    parser = argparse.ArgumentParser(description="MC Server TG Bot - Remote Agent")
    parser.add_argument("--port", type=int, default=int(os.getenv("MC_AGENT_PORT", "8745")))
    parser.add_argument("--api-key", default=os.getenv("MC_AGENT_API_KEY", ""))
    parser.add_argument("--server-path", default=os.getenv("MC_AGENT_SERVER_PATH", ""))
    parser.add_argument("--screen-session", default=os.getenv("MC_AGENT_SCREEN_SESSION", ""))
    parser.add_argument("--start-script", default=os.getenv("MC_AGENT_START_SCRIPT", "start.sh"))
    
    args = parser.parse_args()
    
    PORT = args.port
    API_KEY = args.api_key
    SERVER_PATH = args.server_path
    SCREEN_SESSION = args.screen_session
    START_SCRIPT = args.start_script
    
    if not API_KEY:
        print("❌ Error: --api-key or MC_AGENT_API_KEY environment variable is required!")
        sys.exit(1)
        
    if not SERVER_PATH:
        print("❌ Error: --server-path or MC_AGENT_SERVER_PATH environment variable is required!")
        sys.exit(1)
        
    if not SCREEN_SESSION:
        print("❌ Error: --screen-session or MC_AGENT_SCREEN_SESSION environment variable is required!")
        sys.exit(1)
        
    if not os.path.exists(SERVER_PATH):
        print(f"⚠️ Warning: Server path does not exist: {SERVER_PATH}")
        
    start_sh = os.path.join(SERVER_PATH, START_SCRIPT)
    if os.path.exists(SERVER_PATH) and not os.path.exists(start_sh):
        print(f"⚠️ Warning: {START_SCRIPT} not found in server path: {SERVER_PATH}")

    app = web.Application()
    app.router.add_get("/status", get_status)
    app.router.add_post("/start", start_server)
    app.router.add_get("/logs", get_logs)
    app.router.add_get("/ping", ping)
    
    print(f"🚀 Starting MC Server TG Bot Agent on port {PORT}...")
    print(f"📂 Managing server at: {SERVER_PATH}")
    print(f"📜 Startup script: {START_SCRIPT}")
    print(f"🖥️ Screen session name: {SCREEN_SESSION}")
    
    web.run_app(app, port=PORT, host="0.0.0.0")

if __name__ == "__main__":
    main()
