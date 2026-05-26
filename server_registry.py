import asyncio
from typing import Dict, List, Tuple
from models import ServerConfig
from server_manager import ServerManager

class ServerRegistry:
    def __init__(self, configs: Dict[str, ServerConfig]):
        self._servers = {sid: ServerManager(sid, cfg) for sid, cfg in configs.items()}

    def get(self, server_id: str) -> ServerManager | None:
        return self._servers.get(server_id)

    def list_all(self) -> List[Tuple[str, str]]:
        """Returns list of (server_id, display_name) for all servers"""
        return [(sid, mgr.config.display_name) for sid, mgr in self._servers.items()]

    def is_single_server(self) -> bool:
        return len(self._servers) == 1

    def default_server_id(self) -> str | None:
        if self.is_single_server():
            return next(iter(self._servers.keys()))
        return None

    async def status_all(self) -> Dict[str, bool]:
        """Returns dict of {server_id: is_running} for status overview"""
        server_ids = list(self._servers.keys())
        tasks = [mgr.is_running() for mgr in self._servers.values()]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        status_dict = {}
        for sid, res in zip(server_ids, results):
            if isinstance(res, Exception):
                status_dict[sid] = False
            else:
                status_dict[sid] = res
        return status_dict
