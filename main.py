import asyncio
import json

import discord
from discord.ext import commands


def load_token() -> str:
    with open("./config.json") as file:
        return json.load(file)["token"]


class TypingContestBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.contest_active = False
        self.contest_creator = None
        self.contest_channel = None
        self.participants = set()

    def check_contest_channel(self, ctx):
        if self.contest_active and ctx.channel != self.contest_channel:
            return False
        return True

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Logged in as {self.bot.user.name}")

    @commands.command(name="start")
    async def start(self, ctx):
        if not self.check_contest_channel(ctx):
            return

        if self.contest_active:
            await ctx.reply("The typing contest is already active!")
            return

        self.contest_active = True
        self.contest_creator = ctx.author
        self.contest_channel = ctx.channel
        await ctx.reply("The typing contest has started!")

    @commands.command(name="end")
    async def end(self, ctx):
        if not self.check_contest_channel(ctx):
            return

        if not self.contest_active:
            await ctx.reply("No typing contest is currently active.")
            return

        if ctx.author != self.contest_creator:
            await ctx.reply(
                "You are not authorized to end the contest. Only the user who started it can end it."
            )
            return

        self.contest_active = False
        self.contest_creator = None
        self.contest_channel = None
        self.participants.clear()
        await ctx.reply("The typing contest has ended!")

    @commands.command(name="status")
    async def status(self, ctx):
        if self.contest_active:
            await ctx.reply("A typing contest is currently active!")
        else:
            await ctx.reply("No active contest at the moment.")

    @commands.command(name="join")
    async def join(self, ctx):
        if not self.check_contest_channel(ctx):
            return

        if not self.contest_active:
            await ctx.reply("No typing contest is currently active.")
            return

        if ctx.author in self.participants:
            await ctx.reply("You are already in the contest.")
        else:
            self.participants.add(ctx.author)
            await ctx.reply(
                f"{ctx.author.mention} has joined the typing contest!"
            )

    @commands.command(name="quit")
    async def quit(self, ctx):
        if not self.check_contest_channel(ctx):
            return

        if not self.contest_active:
            await ctx.reply("No typing contest is currently active.")

        if ctx.author not in self.participants:
            await ctx.reply("You are not in the contest.")
        else:
            self.participants.remove(ctx.author)
            await ctx.reply(
                f"{ctx.author.mention} has quit the typing contest!"
            )

    @commands.command(name="commands")
    async def commands(self, ctx):
        embed = discord.Embed(
            title="Typing Contest Bot Commands",
            description="Here are the available commands:",
            color=discord.Color.purple(),
        )
        embed.add_field(
            name="!start",
            value="Start a typing contest in the current channel.",
            inline=False,
        )
        embed.add_field(
            name="!end", value="End the current typing contest.", inline=False
        )
        embed.add_field(
            name="!status",
            value="Check the status of the typing contest.",
            inline=False,
        )
        embed.add_field(
            name="!join",
            value="Join the typing contest.",
            inline=False,
        )
        embed.add_field(
            name="!quit",
            value="Quit the typing contest.",
            inline=False,
        )
        embed.add_field(
            name="!commands", value="Show this list of commands.", inline=False
        )
        await ctx.reply(embed=embed)


class BotSetup:
    def __init__(self, token):
        self.token = token
        self.intents = discord.Intents.default()
        self.intents.message_content = True
        self.bot = commands.Bot(command_prefix="!", intents=self.intents)

    async def setup(self):
        await self.bot.add_cog(TypingContestBot(self.bot))

    async def run(self):
        await self.setup()
        await self.bot.start(self.token)


if __name__ == "__main__":
    bot_instance = BotSetup(load_token())
    asyncio.run(bot_instance.run())
