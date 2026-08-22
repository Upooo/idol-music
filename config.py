"""Configuration — loads settings from .env"""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _require(key: str) -> str:
    val = os.getenv(key)
    if not val:
        raise RuntimeError(f"Missing required env var: {key}")
    return val


def _optional(key: str, default: str = "") -> str:
    return os.getenv(key, default)


@dataclass(frozen=True)
class Config:
    bot_token: str
    api_id: int
    api_hash: str
    assistant_session: str
    developer_id: int
    mongo_uri: str
    log_group_id: int

    @classmethod
    def load(cls) -> "Config":
        log_group = _optional("LOG_GROUP_ID", "0")
        try:
            log_group_id = int(log_group)
        except ValueError:
            log_group_id = 0

        return cls(
            bot_token=_require("BOT_TOKEN"),
            api_id=int(_require("API_ID")),
            api_hash=_require("API_HASH"),
            assistant_session=_require("ASSISTANT_SESSION"),
            developer_id=int(_require("DEVELOPER_ID")),
            mongo_uri=_optional("MONGO_URI"),
            log_group_id=log_group_id,
        )


config = Config.load()
