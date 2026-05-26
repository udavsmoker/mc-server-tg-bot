from pydantic import BaseModel, Field, model_validator
from typing import Dict, List, Optional

class AgentConfig(BaseModel):
    url: str
    api_key: str

class LocalConfig(BaseModel):
    server_path: str
    screen_session: str

class RconConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = Field(..., ge=1024, le=65535)
    password: str

class ServerConfig(BaseModel):
    display_name: str
    agent: Optional[AgentConfig] = None
    local: Optional[LocalConfig] = None
    rcon: RconConfig
    game_port: int = 25565

    @model_validator(mode="after")
    def validate_management_type(self) -> "ServerConfig":
        if (self.agent is None) == (self.local is None):
            raise ValueError("Each server must have either 'agent' or 'local' configured, but not both.")
        return self

class BotConfig(BaseModel):
    bot_token: str
    admin_ids: List[int]

class AppConfig(BaseModel):
    bot: BotConfig
    servers: Dict[str, ServerConfig]

