import discord
import random
import asyncio
from collections import defaultdict
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class GameConfig:
    channel: discord.TextChannel
    chance: float
    cooldown: int  # in seconds
    role: discord.Role
    game_id: int


@dataclass
class FrenzyRequest:
    length: int
    multiplier: float
    interaction: discord.Interaction
    bot: discord.Client
    log_channel_id: int


# it manages the state of each game including user participation and game rules
class Game:
    def __init__(self, config: GameConfig):
        self.channel = config.channel
        self.chance = config.chance
        self.cooldown = timedelta(seconds=config.cooldown)
        self.role = config.role
        self.paused = False
        self.banned_users = set()
        self.active = True
        self.user_cooldowns = defaultdict(lambda: datetime.min)
        self.user_message_timestamps = defaultdict(list)
        self.spam_timestamps = defaultdict(lambda: datetime.min)
        self.game_id = config.game_id
        self.frenzy_end_time = None
        self.frenzy_multiplier = 1

    def _is_user_eligible(self, message):
        if not self.active:
            return False
        if self.role and self.role not in message.author.roles:
            return False
        if message.author.id in self.banned_users:
            return False
        return True

    def _check_spam_protection(self, message, now):
        # this thing Check for spam
        self.user_message_timestamps[message.author.id].append(now)
        # Keep only the last 5 timestamps
        self.user_message_timestamps[message.author.id] = [
            timestamp
            for timestamp in self.user_message_timestamps[message.author.id]
            if (now - timestamp).seconds <= 3
        ]

        if len(self.user_message_timestamps[message.author.id]) >= 4:
            self.spam_timestamps[message.author.id] = now + timedelta(seconds=15)
            return False
        return True

    def _check_user_timeout(self, message, now):
        return now >= self.spam_timestamps[message.author.id]

    def _check_cooldown(self, message, now):
        if now < self.user_cooldowns[message.author.id]:
            return False
        self.user_cooldowns[message.author.id] = now + self.cooldown
        return True

    def _calculate_win_chance(self, now):
        current_chance = self.chance
        if self.frenzy_end_time and now < self.frenzy_end_time:
            current_chance *= (
                self.frenzy_multiplier
            )  # incrase the chances by frenzy multiplier function
        return current_chance

    async def _send_spam_warning(self, message, now):
        remaining_time = int(
            (self.spam_timestamps[message.author.id] - now).total_seconds()
        )
        await message.author.send(
            f"You are sending messages too quickly in {self.channel.mention}. Please wait for {remaining_time} seconds before your messages count towards the game again."
        )

    async def _send_timeout_warning(self, message, now):
        remaining_time = int(
            (self.spam_timestamps[message.author.id] - now).total_seconds()
        )
        await message.author.send(
            f"Please wait for {remaining_time} more seconds before your messages count towards the game again in {self.channel.mention}."
        )

    async def _handle_win(self, message, bot, log_channel_id):
        self.active = False
        await self.channel.send(
            f"{message.author.mention}, you have won the message game! Make a ticket in <#1356907860659011727> to claim your prize."
        )
        log_channel = bot.get_channel(log_channel_id)
        if log_channel:
            embed = discord.Embed(
                title="We have a winner!",
                description=f"{message.author.mention} has won the message game (ID: {self.game_id}).",
                color=0xE18FEB,
            )
            await log_channel.send(embed=embed)

    async def check_message(self, message, bot, log_channel_id):
        if not self._is_user_eligible(message):
            return

        now = datetime.now()

        if not self._check_spam_protection(message, now):
            await self._send_spam_warning(message, now)
            return

        if not self._check_user_timeout(message, now):
            await self._send_timeout_warning(message, now)
            return

        if not self._check_cooldown(message, now):
            return

        current_chance = self._calculate_win_chance(now)
        if random.uniform(0, 100) <= current_chance:
            await self._handle_win(message, bot, log_channel_id)

    async def start_frenzy(self, request: FrenzyRequest):
        if self.frenzy_end_time and datetime.now() < self.frenzy_end_time:
            await request.interaction.response.send_message(
                "A frenzy is already active for this game.", ephemeral=True
            )
            return

        self.frenzy_end_time = datetime.now() + timedelta(
            seconds=request.length
        )  # custom set time and date
        self.frenzy_multiplier = request.multiplier
        await self.channel.send(
            f"A Message Drop frenzy has started from {self.channel.mention}!\n<@&1261807842579583026>"
        )
        log_channel = request.bot.get_channel(request.log_channel_id)
        if log_channel:
            embed = discord.Embed(
                title="Frenzy has just started",
                description=f"Frenzy has just started in {self.channel.mention}.\nResponsible user for this frenzy: {request.interaction.user.mention}",
                color=0x66ADF4,
            )
            await log_channel.send(embed=embed)
        await asyncio.sleep(request.length)
        self.frenzy_end_time = None
        self.frenzy_multiplier = 1
