import asyncio
import struct
import re

class RconError(Exception):
    """Base exception for RCON errors"""
    pass

class RconAuthError(RconError):
    """Raised when authentication fails"""
    pass

class RconConnectionError(RconError):
    """Raised when connecting fails or connection drops"""
    pass

async def rcon_command(host: str, port: int, password: str, command: str, timeout: float = 10.0) -> str:
    """
    Asynchronously executes a command via RCON and returns the response.
    Strips color codes automatically.
    """
    try:
        return await asyncio.wait_for(_execute(host, port, password, command), timeout=timeout)
    except asyncio.TimeoutError:
        raise RconError("Connection timed out")
    except Exception as e:
        if isinstance(e, RconError):
            raise e
        raise RconConnectionError(f"RCON Connection failed: {e}")

async def _execute(host: str, port: int, password: str, command: str) -> str:
    # 1. Connect
    try:
        reader, writer = await asyncio.open_connection(host, port)
    except Exception as e:
        raise RconConnectionError(f"Failed to connect to {host}:{port} - {e}")

    try:
        # 2. Login
        req_id = 42 # arbitrary request id
        payload_bytes = password.encode('utf-8')
        packet_len = len(payload_bytes) + 10
        # Format: packet_len (int), req_id (int), type (int), payload (string), 2 null bytes
        packet = struct.pack(f"<iii{len(payload_bytes)}sBB", packet_len, req_id, 3, payload_bytes, 0, 0)
        
        writer.write(packet)
        await writer.drain()

        # Read response header
        header = await reader.readexactly(12)
        resp_len, resp_id, resp_type = struct.unpack("<iii", header)
        
        # Read the rest of the packet
        remaining = resp_len - 8
        resp_body = await reader.readexactly(remaining)
        
        if resp_id == -1:
            raise RconAuthError("Authentication failed: invalid password")

        # 3. Execute command
        cmd_bytes = command.encode('utf-8')
        packet_len = len(cmd_bytes) + 10
        packet = struct.pack(f"<iii{len(cmd_bytes)}sBB", packet_len, req_id, 2, cmd_bytes, 0, 0)
        
        writer.write(packet)
        await writer.drain()

        # Read response header
        header = await reader.readexactly(12)
        resp_len, resp_id, resp_type = struct.unpack("<iii", header)
        
        remaining = resp_len - 8
        resp_body = await reader.readexactly(remaining)
        
        # Strip final 2 null bytes and decode
        body = resp_body[:-2].decode('utf-8', errors='replace')
        
        # Strip color codes (§x)
        body_clean = re.sub(r'§[0-9a-fk-orA-FK-OR]', '', body)
        
        return body_clean.strip() if body_clean.strip() else "Command executed (no output)"

    finally:
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass
