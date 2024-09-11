import asyncio
import json

import discord
from discord.ext import commands


def load_token() -> str:
    with open("./config/config.json") as file:
        return json.load(file)["token"]


class BotSetup:
    def __init__(self, token):
        self.token = token
        self.intents = discord.Intents.default()
        self.intents.message_content = True
        self.bot = commands.Bot(command_prefix="!", intents=self.intents)

    async def setup(self):
        await self.bot.load_extension("cogs.typing_contest")

    async def run(self):
        await self.setup()
        await self.bot.start(self.token)


if __name__ == "__main__":
    bot_instance = BotSetup(load_token())
    asyncio.run(bot_instance.run())
