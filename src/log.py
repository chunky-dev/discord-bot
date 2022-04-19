import logging
from typing import Optional, List, Callable

import discord


class DiscordLogger:
    def __init__(self, channels: List[int]):
        self._client: Optional[discord.Client] = None
        self._raw_channels = channels
        self._channels = None

    def set_channels(self, channels: List[int]):
        self._raw_channels = channels

    async def register(self, client: discord.Client):
        c = []
        for channel in self._raw_channels:
            c.append(client.get_channel(channel))
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
