import json

import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


def load_token() -> str:
    with open("./config.json") as file:
        return json.load(file)["token"]


@bot.command(name="ping")
async def ping(ctx):
    await ctx.reply("pong")


bot.run(load_token())
