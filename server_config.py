from __future__ import annotations

import json
import os
from typing import Optional

from config import REPO_PATH

CONFIG_FILE = os.path.join(REPO_PATH, "config.json")


def _read_config() -> dict:
    """Read config from JSON file."""
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_config(data: dict) -> None:
    """Write config to JSON file."""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get_updates_channel(guild_id: int) -> Optional[int]:
    """Get the configured updates channel ID for a guild, or None if not set."""
    config = _read_config()
    guild_config = config.get("guilds", {}).get(str(guild_id), {})
    return guild_config.get("updates_channel_id")


def set_updates_channel(guild_id: int, channel_id: int) -> None:
    """Set the updates channel ID for a guild."""
    config = _read_config()
    if "guilds" not in config:
        config["guilds"] = {}
    guild_key = str(guild_id)
    if guild_key not in config["guilds"]:
        config["guilds"][guild_key] = {}
    config["guilds"][guild_key]["updates_channel_id"] = channel_id
    _write_config(config)
