import asyncio
from typing import List, Optional, Union

import discord
from discord.ext import commands


from .exceptions import MissingAttributeException


class Paginator:
    def __init__(
        self,
        bot: Union[
            discord.Client,
            discord.AutoShardedClient,
            commands.Bot,
            commands.AutoShardedBot,
        ],
        message: discord.Message,
        contents: Optional[List[str]] = None,
        embeds: Optional[List[discord.Embed]] = None,
        timeout: int = 30,
        use_extend: bool = False,
        only: Optional[discord.abc.User] = None,
        clear_react: bool = False,
    ) -> None:
        self.bot = bot
        self.message = message
        self.contents = contents
        self.embeds = embeds
        self.timeout = timeout
        self.use_extend = use_extend
        self.only = only
        self.basic_emojis = ["⬅️", "➡️"]
        self.extended_emojis = ["⏪", "⬅️", "➡️", "⏩"]
        self.clear_rect = clear_react
        # TODO : 이모지 커스텀
        self.index = 0

        if not (
            isinstance(bot, discord.Client)
            or isinstance(bot, discord.AutoShardedClient)
            or isinstance(bot, commands.Bot)
            or isinstance(bot, commands.AutoShardedBot)
        ):
            raise TypeError

        if contents is None and embeds is None:
            raise MissingAttributeException(
                "Both contents and embeds are None."
            )

        if not isinstance(timeout, int):
            raise TypeError("timeout must be int.")

    def emoji_check(self, payload: discord.RawReactionActionEvent) -> bool:
        if payload.user_id == self.bot.user.id:
            return False

        if payload.message_id != self.message.id:
            return False

        if self.only is not None:
            if payload.user_id != self.only.id:
                return False

        if self.use_extend:
            if str(payload.emoji) not in self.extended_emojis:
                return False
        else:
            if str(payload.emoji) not in self.basic_emojis:
                return False

        return True

    async def start(self) -> None:
        await self.add_reaction()

        while True:
            try:
                add_reaction = asyncio.ensure_future(
                    self.bot.wait_for(
                        "raw_reaction_add", check=self.emoji_check
                    )
                )

                remove_reaction = asyncio.ensure_future(
                    self.bot.wait_for(
                        "raw_reaction_remove", check=self.emoji_check
                    )
                )

                done, pending = await asyncio.wait(
                    (add_reaction, remove_reaction),
                    return_when=asyncio.FIRST_COMPLETED,
                    timeout=self.timeout,
                )

                for i in pending:
                    i.cancel()

                if len(done) == 0:
                    raise asyncio.TimeoutError

                payload = done.pop().result()
                await self.handle_pagination(payload.emoji)

            except:
                pass

    async def add_reaction(self) -> None:

        if self.use_extend:
            for i in self.extended_emojis:
                await self.message.add_reaction(i)
        else:
            for i in self.basic_emojis:
                await self.message.add_reaction(i)

    async def handle_pagination(self, emoji: discord.PartialEmoji) -> None:
        if str(emoji) == "⬅️":
            await self.go_previous()
        elif str(emoji) == "➡️":
            await self.go_next()

        elif str(emoji) == "⏪":
            await self.go_first()
        elif str(emoji) == "⏩":
            await self.go_last()

    async def go_previous(self) -> None:
        if self.index == 0:
            return

        self.index -= 1
        if self.contents is None:
            await self.message.edit(embed=self.embeds[self.index])
        else:
            await self.message.edit(content=self.contents[self.index])

    async def go_next(self) -> None:
        if self.embeds is not None:
            if self.index != len(self.embeds) - 1:
                self.index += 1
                await self.message.edit(embed=self.embeds[self.index])

        elif self.contents is not None:
            if self.index != len(self.contents) - 1:
                self.index += 1
                await self.message.edit(content=self.contents[self.index])

    async def go_first(self) -> None:
        if self.index == 0:
            return

        self.index = 0

        if self.contents is None:
            await self.message.edit(embed=self.embeds[self.index])
        else:
            await self.message.edit(content=self.contents[self.index])

    async def go_last(self) -> None:
        if self.embeds is not None:
            if self.index != len(self.embeds) - 1:
                self.index = len(self.embeds) - 1
                await self.message.edit(embed=self.embeds[self.index])

        elif self.contents is not None:
            if self.index != len(self.contents) - 1:
                self.index = len(self.contents) - 1
                await self.message.edit(content=self.contents[self.index])
