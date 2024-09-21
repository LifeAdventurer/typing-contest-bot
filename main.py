import argparse
import asyncio
import json
import logging
import os

import discord
from discord.ext import commands

from cogs.typing_contest import TypingContestBot


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Typing Contest Discord Bot")
    parser.add_argument(
        "--debug", action="store_true", help="Enable debug mode"
    )
    return parser.parse_args()


def load_config(file_path: str) -> dict:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"{file_path} does not exist.")

    with open(file_path) as file:
        config = json.load(file)

    required_keys = {
        "token": str,
        "typist_role_name": str,
        "testing_role_name": str,
        "contests_held": int,
    }

    for key, expected_type in required_keys.items():
        if key not in config:
            raise KeyError(f"Missing key in config: {key}")
        if not isinstance(config[key], expected_type):
            raise TypeError(
                f"Incorrect type for key '{key}': Expected {expected_type.__name__}, got {type(config[key]).__name__}"
            )

    return config


class BotSetup:
    def __init__(self, token: str, debug: bool = False) -> None:
        self.token: str = token
        self.debug: bool = debug
        self.intents = discord.Intents.default()
        self.intents.message_content = True
        self.intents.members = True
        self.bot = commands.Bot(command_prefix="!", intents=self.intents)
        self.setup_logging()

    def setup_logging(self) -> None:
        logger = logging.getLogger("discord")
        logger.setLevel(logging.DEBUG if self.debug else logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(discord.utils._ColourFormatter())
        logger.addHandler(handler)

    async def setup(self) -> None:
        await self.bot.add_cog(TypingContestBot(self.bot, self.debug))

    async def run(self) -> None:
        await self.setup()
        await self.bot.start(self.token)


if __name__ == "__main__":
    args = parse_args()
    config = load_config("./config/config.json")
    bot_instance = BotSetup(config["token"], debug=args.debug)
    asyncio.run(bot_instance.run())
