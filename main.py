import argparse
import asyncio
import json
import logging
import os

import discord
from discord.ext import commands

from cogs.typing_contest import TypingContestBot
from constants import CONFIG_JSON_FILE_PATH


def parse_args() -> argparse.Namespace:
    """Parses command-line arguments.

    Returns:
        argparse.Namespace: A namespace containing the parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Typing Contest Discord Bot")
    parser.add_argument(
        "--debug", action="store_true", help="Enable debug mode"
    )
    return parser.parse_args()


def load_config(file_path: str, debug: bool) -> dict:
    """Loads configuration from a JSON file and validates required fields.

    Args:
        file_path: Path to the JSON configuration file.
        debug: Whether to enable debug mode.

    Returns:
        dict: The configuration dictionary.

    Raises:
        FileNotFoundError: If the specified config file does not exist.
        KeyError: If any required key is missing from the config.
        TypeError: If any required key's value has the wrong type.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"{file_path} does not exist.")

    with open(file_path) as file:
        config = json.load(file)

    # The required keys and their expected types
    required_keys = {
        "token": str,
        "typist_role_name": str,
        "contests_held": int,
    }

    # If debug mode is enabled, add testing_role_name to the required keys
    if debug:
        required_keys["testing_role_name"] = str

    # Validate that the required keys are present and of the correct type
    for key, expected_type in required_keys.items():
        if key not in config:
            raise KeyError(f"Missing key in config: {key}")
        if not isinstance(config[key], expected_type):
            raise TypeError(
                f"Incorrect type for key '{key}': Expected {expected_type.__name__}, got {type(config[key]).__name__}"
            )

    return config


class BotSetup:
    """Handles setting up and running the Discord bot.

    Attributes:
        token: The bot token used for authentication.
        debug: Whether to enable debug mode.
        intents: Intents for the bot.
        bot: The bot instance.
    """

    def __init__(self, token: str, debug: bool = False) -> None:
        """Initializes the bot setup with the token and debug mode.

        Args:
            token: The bot token.
            debug: If true, enables debug. Defaults to False.
        """
        self.token: str = token
        self.debug: bool = debug
        self.intents: discord.Intents = discord.Intents.default()
        self.intents.message_content = True
        self.intents.members = True
        self.bot: commands.Bot = commands.Bot(
            command_prefix="!", intents=self.intents
        )
        self.setup_logging()

    def setup_logging(self) -> None:
        """Sets logging to DEBUG if debug mode is enabled, otherwise INFO."""
        logger = logging.getLogger("discord")
        logger.setLevel(logging.DEBUG if self.debug else logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(discord.utils._ColourFormatter())
        logger.addHandler(handler)

    async def setup(self) -> None:
        """Sets up the bot by adding necessary cog."""
        await self.bot.add_cog(TypingContestBot(self.bot, self.debug))

    async def run(self) -> None:
        """Runs the bot, connecting to Discord using the provided token."""
        await self.setup()
        await self.bot.start(self.token)


if __name__ == "__main__":
    # Parse command-line arguments
    args = parse_args()

    # Load configuration from JSON file
    config = load_config(CONFIG_JSON_FILE_PATH, debug=args.debug)

    # Initialize and run the bot
    bot_instance = BotSetup(config["token"], debug=args.debug)
    asyncio.run(bot_instance.run())
