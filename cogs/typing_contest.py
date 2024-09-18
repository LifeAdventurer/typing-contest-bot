import json

import discord
from discord.ext import commands

from constants import (
    ALL_SUBMITTED_SUCCESS,
    ALREADY_JOINED,
    BAN_SUCCESS,
    BANNED_USER_TRY_JOIN,
    CONTEST_ALREADY_ACTIVE,
    END_SUCCESS,
    INVALID_WPM,
    JOIN_SUCCESS,
    MEMBER_NOT_IN_CONTEST,
    MEMBER_NOT_IN_GUILD,
    NO_ACTIVE_CONTEST,
    NO_PARTICIPANTS,
    NOT_CONTEST_CREATOR,
    NOT_IN_CONTEST,
    QUIT_SUCCESS,
    RANKING_EMOJIS,
    REMINDER_SUCCESS,
    REMOVE_SUCCESS,
    ROUND_NOT_STARTED,
    START_SUCCESS,
    STATUS_ACTIVE,
    STATUS_INACTIVE,
)


class TypingContestBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.contest_active = False
        self.contest_creator = None
        self.contest_channel = None
        self.participants = set()
        self.banned_participants = set()
        self.round = 0
        self.wpm_results = {}
        self.top_three_participants = []
        self.ranking_emojis = RANKING_EMOJIS

    def check_contest_channel(self, ctx):
        if self.contest_active and ctx.channel != self.contest_channel:
            return False
        return True

    def get_typist_role(self, ctx):
        with open("./config/config.json") as file:
            typist_role_name = json.load(file)["typist_role_name"]

        typist_role = discord.utils.get(ctx.guild.roles, name=typist_role_name)
        return typist_role

    def get_wpm_result_table(self):
        wpm_result_rows = [
            ["Typist \\ Round"]
            + [str(i + 1) for i in range(self.round)]
            + ["Avg WPM"]
        ]

        participant_averages = {}

        for participant, wpm_list in self.wpm_results.items():
            row = [participant.display_name]
            row.extend(wpm_list)
            average_wpm = "NQ"
            if len(row) - 1 < self.round:
                row.extend(["" for _ in range(self.round - len(row) + 1)])
            elif len(wpm_list) and "-" not in wpm_list:
                wpm_int_list = [int(wpm) for wpm in wpm_list]
                average_wpm = f"{sum(wpm_int_list) / self.round:.2f}"
                participant_averages[participant] = float(average_wpm)

            row.append(average_wpm)

            wpm_result_rows.append(row)

        self.top_three_participants = sorted(
            participant_averages.items(), key=lambda x: x[1], reverse=True
        )[:3]

        transposed_table = list(zip(*wpm_result_rows))
        max_column_lengths = [
            max(len(item) for item in column) for column in transposed_table
        ]
        wpm_result_rows.insert(1, ["-" * len for len in max_column_lengths])

        formatted_rows = [
            "| "
            + " | ".join(
                item.ljust(max_column_lengths[i])
                if i == 0
                else item.rjust(max_column_lengths[i])
                for i, item in enumerate(row)
            )
            + " |"
            for row in wpm_result_rows
        ]

        return "\n".join(formatted_rows)

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Logged in as {self.bot.user.name}")

    @commands.command(name="start")
    async def start(self, ctx):
        if not self.check_contest_channel(ctx):
            return

        if self.contest_active:
            await ctx.reply(CONTEST_ALREADY_ACTIVE)
            return

        self.contest_active = True
        self.contest_creator = ctx.author
        self.contest_channel = ctx.channel
        typist_role = self.get_typist_role(ctx)
        await ctx.reply(START_SUCCESS.format(typist_role=typist_role.mention))

    @commands.command(name="end")
    async def end(self, ctx):
        if not self.check_contest_channel(ctx):
            return

        if not self.contest_active:
            await ctx.reply(NO_ACTIVE_CONTEST)
            return

        if ctx.author != self.contest_creator:
            await ctx.reply(NOT_CONTEST_CREATOR)
            return

        typist_role = self.get_typist_role(ctx)
        await ctx.reply(END_SUCCESS.format(typist_role=typist_role.mention))

        for participant in self.participants:
            if len(self.wpm_results[participant]) != self.round:
                self.wpm_results[participant].append("-")

        wpm_result_table = self.get_wpm_result_table()

        if self.top_three_participants:
            top_three_result = "Top Participants by Avg WPM:\n" + "\n".join(
                [
                    f"{self.ranking_emojis[i]} {participant.mention} - {average_wpm:.2f} WPM"
                    for i, (participant, average_wpm) in enumerate(
                        self.top_three_participants
                    )
                ]
            )
        else:
            top_three_result = "No participants with valid WPM data."

        await ctx.send(
            f"## WPM result table\n\n```{wpm_result_table}```\n{top_three_result}",
        )

        self.contest_active = False
        self.contest_creator = None
        self.contest_channel = None
        self.participants.clear()
        self.banned_participants.clear()
        self.round = 0
        self.wpm_results = {}
        self.top_three_participants = []

    @commands.command(name="status")
    async def status(self, ctx):
        if self.contest_active:
            await ctx.reply(STATUS_ACTIVE)
        else:
            await ctx.reply(STATUS_INACTIVE)

    @commands.command(name="join")
    async def join(self, ctx):
        if not self.check_contest_channel(ctx):
            return

        if not self.contest_active:
            await ctx.reply(NO_ACTIVE_CONTEST)
            return

        if ctx.author in self.banned_participants:
            await ctx.reply(
                BANNED_USER_TRY_JOIN.format(user=ctx.author.mention)
            )
            return

        if ctx.author in self.participants:
            await ctx.reply(ALREADY_JOINED)
        else:
            self.participants.add(ctx.author)
            self.wpm_results[ctx.author] = ["-"] * max(self.round - 1, 0)
            await ctx.reply(JOIN_SUCCESS.format(user=ctx.author.mention))

    @commands.command(name="quit")
    async def quit(self, ctx):
        if not self.check_contest_channel(ctx):
            return

        if not self.contest_active:
            await ctx.reply(NO_ACTIVE_CONTEST)

        if ctx.author not in self.participants:
            await ctx.reply(NOT_IN_CONTEST)
        else:
            self.participants.remove(ctx.author)
            self.wpm_results.pop(ctx.author)
            await ctx.reply(QUIT_SUCCESS.format(user=ctx.author.mention))

    @commands.command(name="list")
    async def list_participants(self, ctx):
        if not self.check_contest_channel(ctx):
            return

        if not self.contest_active:
            await ctx.reply(NO_ACTIVE_CONTEST)
            return

        if not self.participants:
            await ctx.reply(NO_PARTICIPANTS)
            return

        participants_list = "\n".join(
            [participant.mention for participant in self.participants]
        )
        embed = discord.Embed(
            title="Contest Participants",
            description=participants_list,
            color=discord.Color.purple(),
        )
        await ctx.reply(embed=embed)

    @commands.command(name="next")
    async def next(self, ctx):
        if not self.check_contest_channel(ctx):
            return

        if not self.contest_active:
            await ctx.reply(NO_ACTIVE_CONTEST)

        if ctx.author != self.contest_creator:
            await ctx.reply(NOT_CONTEST_CREATOR)
            return

        for participant in self.participants:
            if len(self.wpm_results[participant]) != self.round:
                self.wpm_results[participant].append("-")

        typist_role = self.get_typist_role(ctx)
        await ctx.send(
            f"## WPM result table\n\n```{self.get_wpm_result_table()}```",
        )
        self.round += 1
        await ctx.send(
            f"{typist_role.mention} Get ready! Round {self.round} is starting!"
        )

    @commands.command(name="wpm")
    async def wpm(self, ctx, wpm: str):
        if not self.check_contest_channel(ctx):
            return

        if not self.contest_active:
            await ctx.reply(NO_ACTIVE_CONTEST)
            return

        if ctx.author not in self.participants:
            await ctx.reply(NOT_IN_CONTEST)
            return

        if self.round == 0:
            await ctx.reply(ROUND_NOT_STARTED)
            return

        if not wpm.isdigit() or int(wpm) <= 0:
            await ctx.reply(INVALID_WPM)
            return

        if len(self.wpm_results[ctx.author]) != self.round:
            self.wpm_results[ctx.author].append(wpm)
        self.wpm_results[ctx.author][-1] = wpm
        await ctx.reply(f"You submitted your WPM: {wpm}")

    @commands.command(name="result")
    async def result(self, ctx):
        if not self.check_contest_channel(ctx):
            return

        if not self.contest_active:
            await ctx.reply(NO_ACTIVE_CONTEST)
            return

        await ctx.reply(
            f"## WPM result table\n\n```{self.get_wpm_result_table()}```"
        )

    @commands.command(name="remind")
    async def remind(self, ctx):
        if not self.check_contest_channel(ctx):
            return

        pending_participants = [
            participant.mention
            for participant in self.participants
            if len(self.wpm_results[participant]) < self.round
        ]

        if pending_participants:
            reminder_message = REMINDER_SUCCESS.format(
                pending_participants="\n".join(pending_participants)
            )
        else:
            reminder_message = ALL_SUBMITTED_SUCCESS

        await ctx.send(reminder_message)

    @commands.command(name="remove")
    async def remove(self, ctx, member: discord.Member):
        if not self.check_contest_channel(ctx):
            return

        if ctx.author != self.contest_creator:
            await ctx.reply(NOT_CONTEST_CREATOR)
            return

        if member not in ctx.guild.members:
            await ctx.reply(MEMBER_NOT_IN_GUILD.format(member=member))
            return

        if member not in self.participants:
            await ctx.reply(MEMBER_NOT_IN_CONTEST.format(member=member))
            return

        self.participants.remove(member)
        self.wpm_results.pop(member, None)
        await ctx.reply(REMOVE_SUCCESS.format(member=member.mention))

    @commands.command(name="ban")
    async def ban(self, ctx, member: discord.Member):
        if not self.check_contest_channel(ctx):
            return

        if ctx.author != self.contest_creator:
            await ctx.reply(NOT_CONTEST_CREATOR)
            return

        if member not in ctx.guild.members:
            await ctx.reply(MEMBER_NOT_IN_GUILD.format(member=member))
            return

        if member not in self.participants:
            await ctx.reply(MEMBER_NOT_IN_CONTEST.format(member=member))
            return

        self.participants.remove(member)
        self.wpm_results.pop(member, None)
        self.banned_participants.add(member)
        await ctx.reply(BAN_SUCCESS.format(user=member.mention))

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
            name="!list",
            value="Display all current participants in the typing contest.",
            inline=False,
        )
        embed.add_field(
            name="!next",
            value="Proceed to the next round in the typing contest and view the current WPM results.",
            inline=False,
        )
        embed.add_field(
            name="!wpm {wpm}",
            value="Submit your WPM result for the current round.",
            inline=False,
        )
        embed.add_field(
            name="!result",
            value="View the WPM results table at any time, not just after advancing rounds.",
            inline=False,
        )
        embed.add_field(
            name="!remind",
            value="Sends a reminder to participants who haven't submitted their WPM for the current round. Use this if the round has ended and some participants have not yet submitted their results.",
            inline=False,
        )
        embed.add_field(
            name="!remove {member}",
            value="Remove a participant from the typing contest. Only the contest creator can use this.",
            inline=False,
        )
        embed.add_field(
            name="!ban {member}",
            value="Ban a participant from the typing contest. Once banned, they cannot join again. Only the contest creator can use this.",
            inline=False,
        )
        embed.add_field(
            name="!commands", value="Show this list of commands.", inline=False
        )
        await ctx.reply(embed=embed)


async def setup(bot):
    await bot.add_cog(TypingContestBot(bot))
