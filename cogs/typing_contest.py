import json
from datetime import datetime, timedelta

import discord
from discord.ext import commands, tasks

from constants import (
    ALL_SUBMITTED_SUCCESS,
    ALREADY_JOINED,
    BAN_SUCCESS,
    BANNED_USER_TRY_JOIN,
    CHECKMARK_EMOJI,
    CONFIG_JSON_FILE_PATH,
    CONTEST_ALREADY_ACTIVE,
    END_SUCCESS,
    IDLE_THRESHOLD_MINUTES,
    INVALID_WPM,
    JOIN_SUCCESS,
    MEMBER_NOT_IN_CONTEST,
    MEMBER_NOT_IN_GUILD,
    NO_ACTIVE_CONTEST,
    NO_PARTICIPANTS,
    NOT_CONTEST_CREATOR,
    NOT_IN_CONTEST,
    PARTICIPANT_ROLE_NAME,
    QUIT_SUCCESS,
    RANKING_EMOJIS,
    REMINDER_SUCCESS,
    REMOVE_SUCCESS,
    ROUND_NOT_STARTED,
    START_SUCCESS,
    STATUS_ACTIVE,
    STATUS_INACTIVE,
)

IDLE_THRESHOLD = timedelta(minutes=IDLE_THRESHOLD_MINUTES)


class TypingContestBot(commands.Cog):
    """A cog for managing a typing contest in a Discord server.

    This bot allows users to join a typing contest, track their typing speed
    (WPM), and display the results after each round.

    Attributes:
        bot: The Discord bot instance.
        debug: Debug flag for testing purposes.
        contest_active: Indicates whether a contest is currently active.
        contest_creator: The user who started the contest.
        contest_channel: The channel where the contest is being held.
        participants: The set of participants in the contest.
        banned_participants: The set of banned participants.
        round: The current round number.
        wpm_results: WPM results for each participant.
        top_three_participants: The top three participant based on average WPM.
        ranking_emojis: Emojis used to represent rankings.
        participant_role: The temporary role assigned to participants during the contest.
        last_activity_time: The last time an activity was recorded during the contest.
    """

    def __init__(self, bot: commands.Bot, debug: bool) -> None:
        """Initialize the TypingContestBot cog.

        Args:
            bot: The bot instance.
            debug: If true, enable debugging behavior.
        """
        self.bot: commands.Bot = bot
        self.debug: bool = debug
        self.contest_active: bool = False
        self.contest_creator: discord.Member | None = None
        self.contest_channel: discord.TextChannel | None = None
        self.participants: set[discord.Member] = set()
        self.banned_participants: set[discord.Member] = set()
        self.round: int = 0
        self.wpm_results: dict[discord.Member, list[str]] = {}
        self.top_three_participants: list[tuple[discord.Member, float]] = []
        self.ranking_emojis: list[str] = RANKING_EMOJIS
        self.participant_role: discord.Role | None = None
        self.last_activity_time: datetime = datetime.now()
        self.check_idle_status.start()

    def load_config(self) -> dict:
        """Load configuration from the config file

        Returns:
            dict: The loaded configuration as a dictionary.
        """
        with open(CONFIG_JSON_FILE_PATH) as file:
            return json.load(file)

    def update_contest_held(self) -> None:
        """Increment and update the total number of contests held in the config file."""
        config = self.load_config()
        config["contests_held"] += 1
        with open(CONFIG_JSON_FILE_PATH, "w") as file:
            json.dump(config, file, indent=4)

    async def update_presence(self) -> None:
        """Update the bot's presence to reflect the number of contests held."""
        config = self.load_config()
        contests_held = config["contests_held"]
        presence_message = f"The bot held {contests_held} contests."
        activity = discord.CustomActivity(name=presence_message)
        await self.bot.change_presence(activity=activity)

    @tasks.loop(minutes=1)
    async def check_idle_status(self) -> None:
        """Periodically check if the contest has been idle for too long."""
        if (
            self.contest_active
            and self.contest_creator
            and self.contest_channel
        ):
            idle_time = datetime.now() - self.last_activity_time
            if idle_time > IDLE_THRESHOLD:
                await self.contest_channel.send(
                    f"{self.contest_creator.mention}, the contest has been idle for more than {IDLE_THRESHOLD_MINUTES} minutes."
                )

    @check_idle_status.before_loop
    async def before_check_idle_status(self) -> None:
        """Wait until the bot is ready before starting the idle check."""
        await self.bot.wait_until_ready()

    def update_activity_time(self) -> None:
        """Update the last activity time to the current time."""
        self.last_activity_time = datetime.now()

    async def validate_contest_status(self, ctx) -> bool:
        """Validates if a contest is active and if the command is issued in the correct channel.

        Args:
            ctx: The command context.

        Return:
            bool: True if in the contest channel and the contest is active; False otherwise.
        """
        if not self.contest_active:
            await ctx.reply(NO_ACTIVE_CONTEST)
            return False

        if ctx.channel != self.contest_channel:
            return False

        return True

    async def get_typist_role(self, ctx) -> discord.Role:
        """Retrieve the typist role for the current server

        The role is determined by the `debug` flag.

        Args:
            ctx: The command context.

        Return:
            discord.Role: The typist role if found; None otherwise.
        """
        config = self.load_config()
        role_name = config[
            "testing_role_name" if self.debug else "typist_role_name"
        ]
        role = discord.utils.get(ctx.guild.roles, name=role_name)

        if role is None:
            role = ctx.guild.create_role(name=role_name)
        return role

    async def create_participant_role(self, ctx) -> None:
        """Create the temporary participant role for the typing contest.

        This method checks if the participant role already exists. If the role
        does not exist, it creates a new one with the name specified by
        `PARTICIPANT_ROLE_NAME`. The role is intended to be temporary for
        contest participants.

        Args:
            ctx: The command context, used to get the guild in which the role
                 will be created.

        Returns:
            None: The method does not return a value.
        """
        if self.participant_role:
            return

        guild = ctx.guild
        self.participant_role = discord.utils.get(
            guild.roles, name=PARTICIPANT_ROLE_NAME
        )
        if self.participant_role is None:
            self.participant_role = await guild.create_role(
                name=PARTICIPANT_ROLE_NAME, reason="Temporary contest role"
            )
        return

    async def assign_participant_role(self, member: discord.Member) -> None:
        """Assign the participant role to the specified member.

        This method adds the temporary participant role to the provided member.

        Args:
            member: The discord.Member to which the participant role will be
            assigned.

        Returns:
            None: The method does not return a value.
        """
        if self.participant_role:
            await member.add_roles(self.participant_role)

    async def remove_participant_role(self, member: discord.Member) -> None:
        """Remove the participant role from the specified member.

        This method removes the temporary participant role from the provided
        member.

        Args:
            member: The discord.Member from whom the participant role will be
                    removed.

        Returns:
            None: The method does not return a value.
        """
        if self.participant_role:
            await member.remove_roles(self.participant_role)

    def get_wpm_result_table(self) -> str:
        """Generate and return a table of WPM results for all participants.

        Returns:
            str: The formatted WPM result table.
        """
        wpm_result_rows = [
            ["Typist \\ Round"]
            + [str(i + 1) for i in range(self.round)]
            + ["Avg WPM"]
        ]

        participant_averages: dict[discord.Member, float] = {}

        for participant, wpm_list in self.wpm_results.items():
            row = [participant.display_name]
            row.extend(wpm_list)
            average_wpm = "NQ"  # Not Qualified

            if len(row) - 1 < self.round:
                # Fill in the missing rounds with blank spaces
                row.extend(["" for _ in range(self.round - len(row) + 1)])
            elif len(wpm_list) and "-" not in wpm_list:
                # Compute average WPM if valid
                wpm_int_list = [int(wpm) for wpm in wpm_list]
                average_wpm = f"{sum(wpm_int_list) / self.round:.2f}"
                participant_averages[participant] = float(average_wpm)

            row.append(average_wpm)

            wpm_result_rows.append(row)

        self.top_three_participants = sorted(
            participant_averages.items(), key=lambda x: x[1], reverse=True
        )[:3]

        # Transpose table for formatting
        transposed_table = list(zip(*wpm_result_rows))
        max_column_lengths = [
            max(len(item) for item in column) for column in transposed_table
        ]

        # Insert row of dashes after headers
        wpm_result_rows.insert(1, ["-" * len for len in max_column_lengths])

        # Format each row
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
    async def on_ready(self) -> None:
        """Event listener that runs when the bot is ready."""
        print(f"Logged in as {self.bot.user.name}")
        await self.update_presence()

    @commands.command(name="start")
    async def start(self, ctx) -> None:
        """Start a typing contest.

        This command initiates a typing contest in the current channel.
        The contest can only be started if no contest is currently active.

        Args:
            ctx: The command context.
        """
        if self.contest_active:
            await ctx.reply(CONTEST_ALREADY_ACTIVE)
            return

        self.contest_active = True
        self.contest_creator = ctx.author
        self.contest_channel = ctx.channel

        if self.participant_role is None:
            await self.create_participant_role(ctx)

        typist_role = await self.get_typist_role(ctx)
        await ctx.reply(START_SUCCESS.format(typist_role=typist_role.mention))

        self.update_activity_time()

    @commands.command(name="end")
    async def end(self, ctx) -> None:
        """End the typing contest

        Only the contest creator can end the contest.
        This command also shows the WPM result table and top three participants.

        Args:
            ctx: The command context.
        """
        if not await self.validate_contest_status(ctx):
            return

        if ctx.author != self.contest_creator:
            await ctx.reply(NOT_CONTEST_CREATOR)
            return

        await ctx.reply(
            END_SUCCESS.format(typist_role=self.participant_role.mention)
        )

        # Append "-" for participants without full results
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

        for participant in self.participants:
            await self.remove_participant_role(participant)

        # Reset contest state
        self.contest_active = False
        self.contest_creator = None
        self.contest_channel = None
        self.participants.clear()
        self.banned_participants.clear()
        self.round = 0
        self.wpm_results = {}
        self.top_three_participants = []
        self.update_contest_held()
        await self.update_presence()

    @commands.command(name="status")
    async def status(self, ctx) -> None:
        """Check the status of the typing contest.

        This command replies with the current status of the contest, indicating
        whether it is active or inactive.

        Args:
            ctx: The command context.
        """
        if self.contest_active:
            await ctx.reply(STATUS_ACTIVE)
        else:
            await ctx.reply(STATUS_INACTIVE)

    @commands.command(name="join")
    async def join(self, ctx) -> None:
        """Join the typing contest.

        This command allows a user to join the active typing contest if
        they are not banned and if the contest is currently active.

        Args:
            ctx: The command context.
        """
        if not await self.validate_contest_status(ctx):
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
            await self.assign_participant_role(ctx.author)
            print(self.participant_role)
            await ctx.reply(JOIN_SUCCESS.format(user=ctx.author.mention))

        self.update_activity_time()

    @commands.command(name="quit")
    async def quit(self, ctx) -> None:
        """Quit the typing contest.

        This command allow a user to leave the typing contest. The user
        must be a participant in the contest to successfully quit.

        Args:
            ctx: The command context.
        """
        if not await self.validate_contest_status(ctx):
            return

        if ctx.author not in self.participants:
            await ctx.reply(NOT_IN_CONTEST)
        else:
            self.participants.remove(ctx.author)
            self.wpm_results.pop(ctx.author)
            await self.remove_participant_role(ctx.author)
            await ctx.reply(QUIT_SUCCESS.format(user=ctx.author.mention))

        self.update_activity_time()

    @commands.command(name="list")
    async def list_participants(self, ctx) -> None:
        """List participants in the typing contest.

        This command displays the current participants in the typing contest.
        If no participants are present, it notifies the user accordingly.

        Args:
            ctx: The command context.
        """
        if not await self.validate_contest_status(ctx):
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

        self.update_activity_time()

    @commands.command(name="next")
    async def next(self, ctx) -> None:
        """Proceed to the next round of the typing contest.

        This command advances the contest to the next round. Only the contest
        creator can use this command. It also displays the current WPM results.

        Args:
            ctx: The command context.
        """
        if not await self.validate_contest_status(ctx):
            return

        if ctx.author != self.contest_creator:
            await ctx.reply(NOT_CONTEST_CREATOR)
            return

        for participant in self.participants:
            if len(self.wpm_results[participant]) != self.round:
                self.wpm_results[participant].append("-")

        await ctx.send(
            f"## WPM result table\n\n```{self.get_wpm_result_table()}```",
        )
        self.round += 1
        if self.participant_role is None:
            await self.create_participant_role(ctx)
        await ctx.send(
            f"{self.participant_role.mention} Get ready! Round {self.round} is starting!"
        )

        self.update_activity_time()

    @commands.command(name="wpm")
    async def wpm(self, ctx, wpm: str) -> None:
        """Submit WPM result for the current round.

        This command allows a participant to submit their WPM result for the
        current round. The result must be a positive integer. If the submission
        is valid, the bot will react to the user's message with a checkmark
        emoji.

        Args:
            ctx: The command context.
            wpm: The WPM result submitted by the participant.
        """
        if not await self.validate_contest_status(ctx):
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
        await ctx.message.add_reaction(CHECKMARK_EMOJI)

        self.update_activity_time()

    @commands.command(name="result")
    async def result(self, ctx) -> None:
        """View the WPM results table.

        This command displays the WPM results table for the current contest.
        It can be called at any time while the contest is active.

        Args:
            ctx: The command context.
        """
        if not await self.validate_contest_status(ctx):
            return

        await ctx.reply(
            f"## WPM result table\n\n```{self.get_wpm_result_table()}```"
        )

    @commands.command(name="remind")
    async def remind(self, ctx) -> None:
        """Send reminders to participants.

        This command sends a reminder to participants who haven't submitted
        their WPM for the current round. If all participants have submitted,
        it sends a confirmation message.

        Args:
            ctx: The command context.
        """
        if not await self.validate_contest_status(ctx):
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

        self.update_activity_time()

    @commands.command(name="remove")
    async def remove(self, ctx, member: discord.Member) -> None:
        """Remove a participant form the typing contest.

        This command allows the contest creator to remove a participant from
        the contest. The participant must be present in the contest to be
        removed.

        Args:
            ctx: The command context.
            member: The participant to be removed.
        """
        if not await self.validate_contest_status(ctx):
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
        await self.remove_participant_role(member)
        await ctx.reply(REMOVE_SUCCESS.format(member=member.mention))

        self.update_activity_time()

    @commands.command(name="ban")
    async def ban(self, ctx, member: discord.Member) -> None:
        """Ban a participant from the typing contest.

        This command allows the contest creator to ban a participant, preventing
        them from rejoining the contest. The participant must be present in the
        contest to be banned.

        Args:
            ctx: The command context.
            member: The participant to be banned.
        """
        if not await self.validate_contest_status(ctx):
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
        await self.remove_participant_role(member)
        await ctx.reply(BAN_SUCCESS.format(user=member.mention))

        self.update_activity_time()

    @commands.command(name="getrole")
    async def get_role(self, ctx) -> None:
        """Assign the Typist role to a user if they don't already have it.

        This command checks if the user already has the Typist role. If they do,
        it informs the user that they already have the role. Otherwise, the role
        is assigned to them.

        Args:
            ctx: The command context.
        """
        typist_role = await self.get_typist_role(ctx)
        if typist_role in ctx.author.roles:
            await ctx.reply(f"You already have the '{typist_role.name}' role!")
        else:
            await ctx.author.add_roles(typist_role)
            await ctx.reply(
                f"'{typist_role.name}' role has been assigned to you!"
            )

    @commands.command(name="commands")
    async def commands(self, ctx) -> None:
        """Display the list of available commands.

        This command sens an embed containing all available commands for the
        typing contest bot.

        Args:
            ctx: The commands context.
        """
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
            name="!getrole",
            value="Assign yourself the typist role.",
            inline=False,
        )
        embed.add_field(
            name="!commands", value="Show this list of commands.", inline=False
        )
        await ctx.reply(embed=embed)
