import logging
from typing import Optional, List, Callable

import discord


class DiscordLogger:
    _LOGGER = logging.getLogger("discord_logger")

    def __init__(self, channels: List[int]):
        self._client: Optional[discord.Client] = None
        self._raw_channels = channels
        self._channels = None

    def set_channels(self, channels: List[int]):
        self._raw_channels = channels

    def get_channels(self) -> List[int]:
        return self._raw_channels

    async def register(self, client: discord.Client):
        c = []
        for channel in self._raw_channels:
            channel = client.get_channel(channel)
            if channel is not None:
                c.append(channel)
        self._LOGGER.info(f"Logging to {len(c)} channels.")
        self._channels = c
        self._client = client

    async def log(self, embed_supplier: Callable[[], discord.Embed]):
        if self._client is not None:
            try:
                embed = embed_supplier()
                channel: discord.TextChannel
                for channel in self._channels:
                    await channel.send(embed=embed)
            except Exception as e:
                logging.getLogger("bot_logger").error("Failed to log message", e)
