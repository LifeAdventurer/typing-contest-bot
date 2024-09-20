import argparse
import asyncio
import json
import logging

import discord
from discord.ext import commands

from cogs.typing_contest import TypingContestBot


def parse_args():
    parser = argparse.ArgumentParser(description="Typing Contest Discord Bot")
    parser.add_argument(
        "--debug", action="store_true", help="Enable debug mode"
    )
    return parser.parse_args()


def load_token() -> str:
    with open("./config/config.json") as file:
        return json.load(file)["token"]


class BotSetup:
    def __init__(self, token, debug=False):
        self.token = token
        self.debug = debug
        self.intents = discord.Intents.default()
        self.intents.message_content = True
        self.intents.members = True
        self.bot = commands.Bot(command_prefix="!", intents=self.intents)
        self.setup_logging()

    def setup_logging(self):
        logger = logging.getLogger("discord")
        logger.setLevel(logging.DEBUG if self.debug else logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(discord.utils._ColourFormatter())
        logger.addHandler(handler)

    async def setup(self):
        await self.bot.add_cog(TypingContestBot(self.bot, self.debug))

    async def run(self):
        await self.setup()
        await self.bot.start(self.token)


if __name__ == "__main__":
    args = parse_args()
    bot_instance = BotSetup(load_token(), debug=args.debug)
    asyncio.run(bot_instance.run())
